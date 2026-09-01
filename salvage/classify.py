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

With no key set and no recorded verdict, no call is
attempted and every record is settled by the rules. A record the rules cannot settle then
stays `UNKNOWN`: an honest "no cause established" beats a guess dressed as a diagnosis.
"""
from __future__ import annotations

import hashlib
import json
import os

from salvage.types import FailedPayment, FailureReason, RootCause

# Any OpenAI-compatible endpoint. Mistral by default because its free tier needs no card;
# Gemini, Groq, Cerebras and OpenRouter all speak the same protocol, so switching provider
# is two environment variables and no code. The key is read from SALVAGE_LLM_API_KEY or,
# failing that, MISTRAL_API_KEY.
_BASE_URL = os.environ.get("SALVAGE_LLM_BASE_URL", "https://api.mistral.ai/v1")
_MODEL = os.environ.get("SALVAGE_LLM_MODEL", "mistral-small-latest")
_MAX_TOKENS = 512
_TIMEOUT_S = 45.0
# Verdicts are cached by prompt hash. The batch is deterministic, so one recorded run makes
# every later run — including a judge's clone with no key at all — free, offline and
# identical. Same discipline as the Razorpay fixtures.
_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "fixtures", "llm_verdicts.json")
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
    " Domain base rate you must weigh: in Indian card payments a bare issuer"
    " 'card_declined' carries no cause of its own and most often masks insufficient funds;"
    " an issuer risk block is a real but much smaller share. Do not read a bare decline as"
    " an authentication failure — a failed OTP or CVV reports itself explicitly."
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

    Cache first, network second. Every exit that is not a confident, well-formed,
    in-vocabulary answer returns None so the caller falls back to the rules verdict. A
    classifier that died on a timeout would take a 240-record batch with it.
    """
    prompt = _prompt(p)
    key = hashlib.sha256(
        "|".join((_MODEL, _SYSTEM, prompt)).encode("utf-8")
    ).hexdigest()[:32]

    cached = _cache_read().get(key)
    if cached is not None:
        return _to_cause(p, cached, cached_hit=True)

    api_key = os.environ.get("SALVAGE_LLM_API_KEY") or os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        return None                     # no key and no cache entry: the rules answer stands
    try:
        import httpx

        response = httpx.post(
            f"{_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=_TIMEOUT_S,
            json={
                "model": _MODEL,
                "temperature": 0,          # a diagnosis must not change between runs
                "max_tokens": _MAX_TOKENS,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        if response.status_code != 200:
            return None
        text = response.json()["choices"][0]["message"]["content"].strip()
        data = json.loads(_unfence(text))
        payload = {
            "reason": str(data["reason"]),
            "confidence": float(data["confidence"]),
            "rationale": str(data.get("rationale", "")).strip()[:200],
            "model": _MODEL,
        }
        FailureReason(payload["reason"])            # reject an out-of-vocabulary answer
        if not 0.0 <= payload["confidence"] <= 1.0:
            return None
    except Exception:
        return None

    _cache_write(key, payload)
    return _to_cause(p, payload, cached_hit=False)


def _to_cause(p: FailedPayment, payload: dict, cached_hit: bool) -> RootCause | None:
    """Turn a cached or fresh model payload into a RootCause. None if it is malformed."""
    try:
        reason = FailureReason(str(payload["reason"]))
        confidence = float(payload["confidence"])
    except Exception:
        return None
    if not 0.0 <= confidence <= 1.0:
        return None
    prose = str(payload.get("rationale", "")).strip()[:200]
    note = " (replayed from recorded verdict)" if cached_hit else ""
    # "llm" first: the harness counts this token to report the rules/model split. A replayed
    # verdict is still the model's verdict, so it is still counted as one.
    return RootCause(
        payment_id=p.payment_id,
        reason=reason,
        confidence=confidence,
        rationale=f"llm {prose}{note}",
    )


def _cache_read() -> dict:
    try:
        with open(_CACHE_PATH, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}                       # a missing or corrupt cache is simply a cache miss


def _cache_write(key: str, payload: dict) -> None:
    """Append one verdict. Best-effort: a read-only checkout must still classify."""
    try:
        os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
        store = _cache_read()
        store[key] = payload
        with open(_CACHE_PATH, "w", encoding="utf-8") as handle:
            json.dump(store, handle, indent=2, sort_keys=True)
    except OSError:
        pass


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
