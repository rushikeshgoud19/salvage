"""Synthetic Razorpay failure batch carrying a counterfactual label.

Prevents the failure this project exists to prevent, one step upstream: a
recovery headline computed against data that does not resemble the real world.
Every ``gateway_code`` and ``source`` below is copied verbatim from Razorpay's
own error table (CONTRACT §10.1) and the reason mix is tuned so that a competent
reason-specific policy lands inside the published 45-65% band (§10.2) instead of
at a fictional 95%.

``GroundTruth.would_self_heal`` is the label nothing else can supply. Without it
the cost of intervening on a payment that was going to succeed anyway is
unmeasurable, and "did the agent actually help?" has no answer at all.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
from dataclasses import dataclass

from salvage.types import FailedPayment, FailureReason, GroundTruth

# Fixed anchor instead of time.time(): the same seed must produce byte-identical
# files on any day, or "two runs at the same seed agree" is untestable.
BATCH_ANCHOR_S = 1788220800.0            # 2026-09-01T00:00:00Z
_WINDOW_S = 14 * 24 * 3600.0             # the 10-14 day recovery window of §10.3

# self_heal_after_s when the payment never heals on its own. 0.0 would read as
# "healed instantly", which is the opposite of what is meant.
NEVER_SELF_HEALS = -1.0

_ID_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

_MIN_RUPEES = 99.0
_MAX_RUPEES = 85_000.0
_LOG_MU = 7.31       # exp(7.31) ~ Rs 1500 median ticket
_LOG_SIGMA = 1.10

# India method mix, restricted per reason to whatever that reason can physically
# happen on (an invalid_vpa on a netbanking payment would not survive a judge).
_METHOD_WEIGHTS = {"upi": 45, "card": 30, "netbanking": 12, "wallet": 8, "emi": 5}

_ALL_RAILS = ("card", "upi", "netbanking", "wallet")


@dataclass(frozen=True)
class _Reason:
    """One row of CONTRACT §10.1. ``family`` is None only for card_declined."""
    code: str
    source: str
    family: FailureReason | None
    description: str
    weight: float
    methods: tuple[str, ...]


# CONTRACT §10.1 verbatim. 23 rows, no additions, no renames.
REASONS: tuple[_Reason, ...] = (
    _Reason("bank_not_available", "gateway", FailureReason.BANK_DOWN,
            "Payment failed because the bank was not available. Try again in some time.",
            0.055, _ALL_RAILS),
    _Reason("bank_technical_error", "gateway", FailureReason.BANK_DOWN,
            "Payment failed due to a technical error at the bank's end. Try again.",
            0.055, _ALL_RAILS),
    _Reason("bank_cutoff_in_progress", "gateway", FailureReason.BANK_DOWN,
            "Payment failed because the bank's end-of-day cut-off is in progress.",
            0.025, ("netbanking", "upi")),
    _Reason("gateway_technical_error", "gateway", FailureReason.BANK_DOWN,
            "Payment processing failed due to a technical error at the gateway.",
            0.035, _ALL_RAILS),

    _Reason("insufficient_funds", "customer", FailureReason.INSUFFICIENT_FUNDS,
            "Payment failed due to insufficient balance in the account. "
            "Try another payment method.",
            0.110, _ALL_RAILS),
    _Reason("transaction_limit_exceeded", "customer", FailureReason.INSUFFICIENT_FUNDS,
            "Payment failed because the amount exceeds the transaction limit on the account.",
            0.040, ("upi", "netbanking", "card")),
    _Reason("transaction_daily_limit_exceeded", "customer", FailureReason.INSUFFICIENT_FUNDS,
            "Payment failed because the daily transaction limit on the account is exhausted.",
            0.030, ("upi", "netbanking")),
    _Reason("credit_limit_exceeded", "gateway", FailureReason.INSUFFICIENT_FUNDS,
            "Payment failed because the available credit limit on the card was exceeded.",
            0.020, ("card", "emi")),

    _Reason("authentication_failed", "customer", FailureReason.AUTH_FAILED,
            "Payment failed because the customer could not be authenticated.",
            0.070, ("card", "upi", "netbanking")),
    _Reason("incorrect_otp", "customer", FailureReason.AUTH_FAILED,
            "Payment failed because an incorrect OTP was entered.",
            0.060, ("card", "netbanking")),
    _Reason("otp_expired", "customer", FailureReason.AUTH_FAILED,
            "Payment failed because the OTP expired before it was submitted.",
            0.045, ("card", "netbanking")),
    _Reason("incorrect_cvv", "customer", FailureReason.AUTH_FAILED,
            "Payment failed because an incorrect CVV was entered.",
            0.035, ("card",)),
    _Reason("invalid_vpa", "customer", FailureReason.AUTH_FAILED,
            "Payment failed because the UPI ID entered is invalid.",
            0.055, ("upi",)),
    _Reason("card_number_invalid", "customer", FailureReason.AUTH_FAILED,
            "Payment failed because the card number entered is invalid.",
            0.020, ("card",)),
    _Reason("incorrect_card_details", "customer", FailureReason.AUTH_FAILED,
            "Payment failed because the card details entered are incorrect.",
            0.020, ("card",)),
    _Reason("user_not_registered_for_netbanking", "customer", FailureReason.AUTH_FAILED,
            "Payment failed because the customer is not registered for netbanking.",
            0.015, ("netbanking",)),

    _Reason("card_expired", "customer", FailureReason.CARD_EXPIRED,
            "Payment failed because the card has expired. Try a different card.",
            0.050, ("card", "emi")),

    _Reason("mandate_creation_declined", "gateway", FailureReason.MANDATE_EXPIRED,
            "Mandate creation was declined by the bank. A fresh mandate must be authorised.",
            0.040, ("emi", "upi")),

    _Reason("payment_risk_check_failed", "gateway", FailureReason.RISK_BLOCKED,
            "Payment failed because it did not clear the risk check.",
            0.025, _ALL_RAILS),
    _Reason("compliance_violation", "business", FailureReason.RISK_BLOCKED,
            "Payment was blocked because it violates a compliance rule on the account.",
            0.010, ("card", "netbanking")),
    _Reason("debit_instrument_blocked", "customer", FailureReason.RISK_BLOCKED,
            "Payment failed because the payment instrument is blocked by the issuer.",
            0.015, ("card", "upi", "wallet")),

    # Genuinely ambiguous (§10.4): funds, risk or issuer. The true family is
    # sampled here; the rules classifier cannot recover it, which is exactly
    # why this is the one code the model is allowed to look at.
    _Reason("card_declined", "gateway", None,
            "Payment was declined by the issuing bank without a specific reason.",
            0.040, ("card", "emi")),

    _Reason("", "customer", FailureReason.CHECKOUT_DROPOFF,
            "Customer abandoned the checkout before the payment was submitted.",
            0.130, ("card", "upi", "netbanking", "wallet", "emi")),
)

# What card_declined actually was, when you can see the ledger the merchant cannot.
_CARD_DECLINED_FAMILIES = (
    (FailureReason.INSUFFICIENT_FUNDS, 0.50),
    (FailureReason.RISK_BLOCKED, 0.30),
    (FailureReason.AUTH_FAILED, 0.20),
)

# Published recovery propensity per failure family for a competent
# reason-specific policy (§10.2 / §10.3). Calibration only — no runtime code
# reads this, and the agent lane must never see it. It is how we check the
# generator is not handing the policy a 95% batch.
RECOVERY_PROPENSITY: dict[FailureReason, float] = {
    FailureReason.BANK_DOWN: 0.80,           # transient, a prompt retry usually wins
    FailureReason.INSUFFICIENT_FUNDS: 0.45,  # ~1 in 5 per well-timed attempt, 2-3 attempts
    FailureReason.AUTH_FAILED: 0.60,         # re-auth link, highest-volume and recovers well
    FailureReason.CARD_EXPIRED: 0.35,        # needs a new instrument from the customer
    FailureReason.MANDATE_EXPIRED: 0.30,
    FailureReason.CHECKOUT_DROPOFF: 0.40,    # decays sharply after 72h
    FailureReason.RISK_BLOCKED: 0.02,        # escalate only; almost never recovered
    FailureReason.UNKNOWN: 0.20,
}

# Probability the payment would have settled with zero intervention. Concentrated
# in BANK_DOWN and CHECKOUT_DROPOFF because those are the two that genuinely do.
_SELF_HEAL_P: dict[FailureReason, float] = {
    FailureReason.BANK_DOWN: 0.53,
    FailureReason.CHECKOUT_DROPOFF: 0.31,
    FailureReason.INSUFFICIENT_FUNDS: 0.12,
    FailureReason.AUTH_FAILED: 0.06,
    FailureReason.CARD_EXPIRED: 0.0,
    FailureReason.MANDATE_EXPIRED: 0.0,
    FailureReason.RISK_BLOCKED: 0.0,
    FailureReason.UNKNOWN: 0.0,
}

# How long the self-heal takes, in seconds. Bank downtime clears in hours; an
# empty wallet waits for payday.
_SELF_HEAL_WINDOW_S: dict[FailureReason, tuple[float, float]] = {
    FailureReason.BANK_DOWN: (1_200.0, 21_600.0),
    FailureReason.CHECKOUT_DROPOFF: (3_600.0, 172_800.0),
    FailureReason.INSUFFICIENT_FUNDS: (172_800.0, 691_200.0),
    FailureReason.AUTH_FAILED: (600.0, 86_400.0),
}


_RECURRING_DIGITS = re.compile(r"(\d)\1{3,}")

def generate_batch(n: int = 240, seed: int = 7,
                   holdout_frac: float = 0.20) -> tuple[list[FailedPayment], list[GroundTruth]]:
    """Build `n` failed payments and their hidden labels, deterministically."""
    if n <= 0:
        raise ValueError(f"generate_batch needs a positive n, observed n={n}")
    if not 0.0 < holdout_frac < 1.0:
        raise ValueError(
            f"holdout_frac must be strictly between 0 and 1, observed {holdout_frac}")

    rng = random.Random(seed)
    weights = [r.weight for r in REASONS]

    payments: list[FailedPayment] = []
    families: dict[str, FailureReason] = {}
    self_heal: dict[str, tuple[bool, float]] = {}

    for i in range(n):
        reason = rng.choices(REASONS, weights=weights, k=1)[0]
        family = reason.family or _pick_card_declined_family(rng)

        payment_id = "pay_" + "".join(rng.choices(_ID_ALPHABET, k=14))
        order_id = "order_" + "".join(rng.choices(_ID_ALPHABET, k=14))
        method = _pick_method(rng, reason.methods)
        amount_paise = _sample_amount_paise(rng)
        failed_at = round(BATCH_ANCHOR_S - rng.uniform(0.0, _WINDOW_S), 3)
        attempt_no = rng.choices((1, 2, 3), weights=(0.75, 0.18, 0.07), k=1)[0]
        # Razorpay rejects a contact with four or more of the same digit in a row --
        # "Recurring digits in customer contact are disallowed", HTTP 400, confirmed against
        # live test mode. One number in 240 tripped it, which is one dead record in a
        # --record run and a confusing one to debug. Resample instead of shipping it.
        while True:
            phone = "+91" + rng.choice("6789") + "".join(rng.choices("0123456789", k=9))
            if not _RECURRING_DIGITS.search(phone):
                break
        heals = rng.random() < _SELF_HEAL_P[family]
        heal_after = _sample_self_heal_after(rng, family) if heals else NEVER_SELF_HEALS

        payments.append(FailedPayment(
            payment_id=payment_id,
            order_id=order_id,
            customer_id=f"cust_{i:04d}",
            amount_paise=amount_paise,
            currency="INR",
            method=method,
            failed_at=failed_at,
            gateway_code=reason.code,
            gateway_description=reason.description,
            source=reason.source,
            attempt_no=attempt_no,
            customer_email=f"cust{i:04d}@example.invalid",
            customer_phone=phone,
        ))
        families[payment_id] = family
        self_heal[payment_id] = (heals, heal_after)

    splits = _assign_splits(families, holdout_frac, n)
    truth = [
        GroundTruth(
            payment_id=p.payment_id,
            true_reason=families[p.payment_id],
            would_self_heal=self_heal[p.payment_id][0],
            self_heal_after_s=self_heal[p.payment_id][1],
            split=splits[p.payment_id],
        )
        for p in payments
    ]
    return payments, truth


def write_batch(payments: list[FailedPayment], truth: list[GroundTruth],
                out_dir: str = "data") -> tuple[str, str]:
    """Write payments.json and truth.json. Same seed in, same bytes out."""
    os.makedirs(out_dir, exist_ok=True)
    payments_path = os.path.join(out_dir, "payments.json")
    truth_path = os.path.join(out_dir, "truth.json")
    _write_json(payments_path, [_payment_to_dict(p) for p in payments])
    _write_json(truth_path, [_truth_to_dict(t) for t in truth])
    return payments_path, truth_path


def load_batch(out_dir: str = "data") -> tuple[list[FailedPayment], list[GroundTruth]]:
    """Exact inverse of `write_batch`."""
    payments_path = os.path.join(out_dir, "payments.json")
    truth_path = os.path.join(out_dir, "truth.json")
    for path in (payments_path, truth_path):
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"no batch at {path} — run `salvage generate` before `salvage run`")

    with open(payments_path, encoding="utf-8") as fh:
        payments = [FailedPayment(**row) for row in json.load(fh)]
    with open(truth_path, encoding="utf-8") as fh:
        truth = [
            GroundTruth(
                payment_id=row["payment_id"],
                true_reason=FailureReason(row["true_reason"]),
                would_self_heal=row["would_self_heal"],
                self_heal_after_s=row["self_heal_after_s"],
                split=row["split"],
            )
            for row in json.load(fh)
        ]
    return payments, truth


def expected_recovery_value_rate(payments: list[FailedPayment], truth: list[GroundTruth],
                                 split: str | None = None) -> float:
    """Value-weighted recovery a competent policy should reach on this batch.

    Calibration instrument, not a metric: it answers "is the generated batch
    winnable at the published rate (§10.2), or did we hand the policy a gift?"
    """
    by_id = {t.payment_id: t for t in truth}
    at_risk = 0
    winnable = 0.0
    for p in payments:
        t = by_id.get(p.payment_id)
        if t is None or (split is not None and t.split != split):
            continue
        at_risk += p.amount_paise
        winnable += p.amount_paise * RECOVERY_PROPENSITY[t.true_reason]
    return winnable / at_risk if at_risk else 0.0


def _pick_card_declined_family(rng: random.Random) -> FailureReason:
    fams = [f for f, _ in _CARD_DECLINED_FAMILIES]
    ws = [w for _, w in _CARD_DECLINED_FAMILIES]
    return rng.choices(fams, weights=ws, k=1)[0]


def _pick_method(rng: random.Random, allowed: tuple[str, ...]) -> str:
    return rng.choices(list(allowed), weights=[_METHOD_WEIGHTS[m] for m in allowed], k=1)[0]


def _sample_amount_paise(rng: random.Random) -> int:
    rupees = min(_MAX_RUPEES, max(_MIN_RUPEES, rng.lognormvariate(_LOG_MU, _LOG_SIGMA)))
    return int(round(rupees * 100))


def _sample_self_heal_after(rng: random.Random, family: FailureReason) -> float:
    lo, hi = _SELF_HEAL_WINDOW_S[family]
    return round(rng.uniform(lo, hi), 1)


def _digest(payment_id: str) -> int:
    """Stable across processes — `hash()` is salted per interpreter run."""
    return int.from_bytes(hashlib.blake2b(payment_id.encode(), digest_size=8).digest(), "big")


def _assign_splits(families: dict[str, FailureReason], holdout_frac: float,
                   n: int) -> dict[str, str]:
    """Deterministic train/holdout split, stratified by true failure family.

    A plain hash threshold drifts by ±6 records at n=240 and can leave a rare
    family entirely absent from holdout — which makes the per-family reading of
    the results a coin flip. Ranking each family's ids by digest keeps the split
    a pure function of the ids while pinning both the total and the coverage.
    """
    by_family: dict[FailureReason, list[str]] = {}
    for pid, fam in families.items():
        by_family.setdefault(fam, []).append(pid)

    target = round(n * holdout_frac)
    quotas: dict[FailureReason, int] = {}
    remainders: list[tuple[float, str, FailureReason]] = []
    for fam, ids in by_family.items():
        exact = len(ids) * holdout_frac
        quotas[fam] = int(exact)
        remainders.append((exact - int(exact), fam.value, fam))

    # Largest remainder first, family name as the deterministic tie-break.
    short = target - sum(quotas.values())
    for _, _, fam in sorted(remainders, key=lambda r: (-r[0], r[1]))[:max(0, short)]:
        quotas[fam] += 1

    # Every family must appear on both sides of the split or the per-family
    # numbers in the report are unreadable.
    bounds = {
        fam: (1, len(ids) - 1) if len(ids) >= 2 else (0, 0)
        for fam, ids in by_family.items()
    }
    for fam, (lo, hi) in bounds.items():
        quotas[fam] = min(max(quotas[fam], lo), hi)

    _rebalance(quotas, bounds, target - sum(quotas.values()))

    splits: dict[str, str] = {}
    for fam, ids in by_family.items():
        ranked = sorted(ids, key=_digest)
        take = quotas[fam]
        for pid in ranked[:take]:
            splits[pid] = "holdout"
        for pid in ranked[take:]:
            splits[pid] = "train"
    return splits


def _rebalance(quotas: dict[FailureReason, int],
               bounds: dict[FailureReason, tuple[int, int]], delta: int) -> None:
    """Nudge quotas back onto the target after clamping, one record at a time."""
    order = sorted(quotas, key=lambda f: f.value)
    while delta != 0:
        moved = False
        for fam in order:
            if delta == 0:
                break
            lo, hi = bounds[fam]
            if delta > 0 and quotas[fam] < hi:
                quotas[fam] += 1
                delta -= 1
                moved = True
            elif delta < 0 and quotas[fam] > lo:
                quotas[fam] -= 1
                delta += 1
                moved = True
        if not moved:      # every family is pinned at a bound; closest we can get
            return


def _payment_to_dict(p: FailedPayment) -> dict:
    return {
        "payment_id": p.payment_id,
        "order_id": p.order_id,
        "customer_id": p.customer_id,
        "amount_paise": p.amount_paise,
        "currency": p.currency,
        "method": p.method,
        "failed_at": p.failed_at,
        "gateway_code": p.gateway_code,
        "gateway_description": p.gateway_description,
        "source": p.source,
        "attempt_no": p.attempt_no,
        "customer_email": p.customer_email,
        "customer_phone": p.customer_phone,
    }


def _truth_to_dict(t: GroundTruth) -> dict:
    return {
        "payment_id": t.payment_id,
        "true_reason": t.true_reason.value,
        "would_self_heal": t.would_self_heal,
        "self_heal_after_s": t.self_heal_after_s,
        "split": t.split,
    }


def _write_json(path: str, rows: list[dict]) -> None:
    # newline="\n" so the same seed produces the same bytes on Windows too.
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rows, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
