"""Root-cause classification — rules first, model last (Contract §10.4).

The failure this module prevents: reaching for an LLM where a lookup table is both cheaper
and more accurate. Razorpay already names the cause in `reason`; 21 of the 23 real reasons
invert to a `FailureReason` deterministically, with no model call, no credentials and no
network. `classify_rules` is that table and it always works.

`classify` reaches for a model only where the rules genuinely cannot settle the record:
`card_declined`, which names no cause at all (funds, risk or issuer — Contract §10.1), and
a `reason` string that is not in the table. That is a few percent of a batch, comfortably
under the 15% cap, and the split is reported: the first token of `RootCause.rationale` is
`"rules"` or `"llm"`, and the harness counts it.

The model is sandboxed exactly as Contract §10.4 requires — it reads context and returns a
typed diagnostic. It never selects an action, never touches money, and its prose is never
evidence (Contract §5.3): a rationale used as a stepproof evidence string would be flipped
to `verified=False` by the narration guard, turning a real recovery into a reported failure.

With no `ANTHROPIC_API_KEY` set — the state of the machine this was built on — no call is
attempted and every record is settled by the rules. A record the rules cannot settle then
stays `UNKNOWN`: an honest "no cause established" beats a guess dressed as a diagnosis.
"""
from __future__ import annotations

import json
import os

from salvage.types import FailedPayment, FailureReason, RootCause

_MODEL = "claude-opus-5"
_MAX_TOKENS = 2048
# Below this the model has not settled anything the rules had not already settled better.
_MIN_MODEL_CONFIDENCE = 0.5

# Contract §10.1, inverted. The 21 reasons a rule settles outright.
_REASON_BY_CODE: dict[str, FailureReason] = {
    "bank_not_available": FailureReason.BANK_DOWN,
    "bank_technical_error": FailureReason.BANK_DOWN,
    "bank_cutoff_in_progress": FailureReason.BANK_DOWN,
    "gateway_technical_error": FailureReason.BANK_DOWN,
    "insufficient_funds": FailureReason.INSUFFICIENT_FUNDS,
    "transaction_limit_exceeded": FailureReason.INSUFFICIENT_FUNDS,
    "transaction_daily_limit_exceeded": FailureReason.INSUFFICIENT_FUNDS,
    "credit_limit_exceeded": FailureReason.INSUFFICIENT_FUNDS,
    "authentication_failed": FailureReason.AUTH_FAILED,
    "incorrect_otp": FailureReason.AUTH_FAILED,
    "otp_expired": FailureReason.AUTH_FAILED,
    "incorrect_cvv": FailureReason.AUTH_FAILED,
    "invalid_vpa": FailureReason.AUTH_FAILED,
    "card_number_invalid": FailureReason.AUTH_FAILED,
    "incorrect_card_details": FailureReason.AUTH_FAILED,
    "user_not_registered_for_netbanking": FailureReason.AUTH_FAILED,
    "card_expired": FailureReason.CARD_EXPIRED,
    "mandate_creation_declined": FailureReason.MANDATE_EXPIRED,
    "payment_risk_check_failed": FailureReason.RISK_BLOCKED,
    "compliance_violation": FailureReason.RISK_BLOCKED,
    "debit_instrument_blocked": FailureReason.RISK_BLOCKED,
}

# The 23rd row: no reason recorded at all. Razorpay's own table reads this as an abandoned
# checkout, so it is a lookup too — asking a model to re-derive it would be the exact
# reflex judging criterion #1 marks down.
_ABANDONED = FailureReason.CHECKOUT_DROPOFF

# The 22nd row: names an outcome, not a cause. This is where a model earns its place.
_AMBIGUOUS_CODE = "card_declined"

_SYSTEM = (
    "You are a payments failure analyst. You are given one failed Razorpay payment whose"
    " gateway reason does not name a cause. Return ONLY a JSON object with keys"
    ' "reason", "confidence", "rationale". "reason" must be exactly one of:'
    " bank_down, insufficient_funds, auth_failed, mandate_expired, checkout_dropoff,"
    " card_expired, risk_blocked, unknown."
    ' "confidence" is a number between 0 and 1. "rationale" is one sentence, under 30'
    " words, citing the fields you used. You are diagnosing only: you do not choose an"
    " action and you do not decide whether money moved. If the fields do not support a"
    ' diagnosis, answer "unknown" with low confidence.'
)


def classify_rules(p: FailedPayment) -> RootCause:
    """Deterministic root cause. No model, no credentials, no network. Never raises."""
    code = (p.gateway_code or "").strip().lower()
    reason = _REASON_BY_CODE.get(code)
    if reason is not None:
        return RootCause(
            payment_id=p.payment_id,
            reason=reason,
            confidence=0.95,
            rationale=(
                f"rules gateway reason {code!r} (source={p.source}) maps to"
                f" {reason.value} in the Razorpay reason table"
            ),
        )
    if code == "":
        return RootCause(
            payment_id=p.payment_id,
            reason=_ABANDONED,
            confidence=0.80,
            rationale=(
                f"rules no gateway reason recorded on a {p.method} attempt"
                f" (source={p.source}): the checkout was abandoned before the gateway"
                " declined anything"
            ),
        )
    if code == _AMBIGUOUS_CODE:
        return RootCause(
            payment_id=p.payment_id,
            reason=FailureReason.UNKNOWN,
            confidence=0.40,
            rationale=(
                "rules gateway reason 'card_declined' names the outcome, not the cause"
                " — funds, risk and issuer policy all present this way"
            ),
        )
    return RootCause(
        payment_id=p.payment_id,
        reason=FailureReason.UNKNOWN,
        confidence=0.30,
        rationale=f"rules gateway reason {code!r} is not in the Razorpay reason table",
    )


def needs_model(p: FailedPayment) -> bool:
    """True only where the reason table genuinely cannot settle the record."""
    code = (p.gateway_code or "").strip().lower()
    return code == _AMBIGUOUS_CODE or (code != "" and code not in _REASON_BY_CODE)


def classify(p: FailedPayment) -> RootCause:
    """Root cause for one record. Rules settle it unless they demonstrably cannot."""
    rules = classify_rules(p)
    if not needs_model(p):
        return rules
    proposal = _ask_model(p)
    if proposal is None:
        return RootCause(
            payment_id=rules.payment_id,
            reason=rules.reason,
            confidence=rules.confidence,
            rationale=rules.rationale + "; no model was reachable, so no cause was invented",
        )
    if proposal.confidence < _MIN_MODEL_CONFIDENCE:
        return RootCause(
            payment_id=rules.payment_id,
            reason=rules.reason,
            confidence=rules.confidence,
            rationale=(
                rules.rationale
                + f"; the model answered {proposal.reason.value} at"
                f" confidence {proposal.confidence:.2f}, below the 0.5 floor, and was"
                " not used"
            ),
        )
    return proposal


def _ask_model(p: FailedPayment) -> RootCause | None:
    """Ask the model for a typed diagnostic. Returns None on any failure — never raises.

    Every exit that is not a confident, well-formed, in-vocabulary answer returns None so
    the caller falls back to the rules verdict. A classifier that dies on a timeout would
    take a 240-record batch with it.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic

        response = anthropic.Anthropic().messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=_SYSTEM,
            messages=[{"role": "user", "content": _prompt(p)}],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        ).strip()
        data = json.loads(_unfence(text))
        reason = FailureReason(str(data["reason"]))
        confidence = float(data["confidence"])
    except Exception:
        return None
    if not 0.0 <= confidence <= 1.0:
        return None
    prose = str(data.get("rationale", "")).strip()[:200]
    # "llm" first: the harness counts this token to report the rules/model split.
    return RootCause(
        payment_id=p.payment_id,
        reason=reason,
        confidence=confidence,
        rationale=f"llm {prose}",
    )


def _prompt(p: FailedPayment) -> str:
    return (
        f"gateway_code: {p.gateway_code!r}\n"
        f"gateway_description: {p.gateway_description!r}\n"
        f"source: {p.source}\n"
        f"method: {p.method}\n"
        f"attempt_no: {p.attempt_no}\n"
        f"amount_paise: {p.amount_paise}\n"
    )


def _unfence(text: str) -> str:
    """Strip a ```json fence if the model wrapped its object in one."""
    if not text.startswith("```"):
        return text
    body = text.split("\n", 1)[-1]
    return body.rsplit("```", 1)[0].strip()
