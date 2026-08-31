"""Frozen shared vocabulary for salvage.

Both lanes import from here and neither owns it. Money is integer paise everywhere:
a float rupee is a rounding bug waiting to be reported as a recovery figure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class FailureReason(str, Enum):
    BANK_DOWN = "bank_down"                    # gateway/bank downtime — transient, retry wins
    INSUFFICIENT_FUNDS = "insufficient_funds"  # soft decline — timing wins, not repetition
    AUTH_FAILED = "auth_failed"                # OTP/3DS/CVV/VPA — endemic in India, recovers well
    MANDATE_EXPIRED = "mandate_expired"
    CHECKOUT_DROPOFF = "checkout_dropoff"
    CARD_EXPIRED = "card_expired"
    RISK_BLOCKED = "risk_blocked"              # never auto-retry. escalate. see §10
    UNKNOWN = "unknown"


class ActionKind(str, Enum):
    RETRY = "retry"                  # re-present the same instrument
    PAYMENT_LINK = "payment_link"    # issue a fresh link
    NUDGE = "nudge"                  # remind the customer, no new rail
    ESCALATE = "escalate"            # hand to a human
    NONE = "none"                    # policy declined to act


class Outcome(str, Enum):
    RECOVERED = "recovered"                      # money actually arrived, verified
    UNRESOLVED = "unresolved"                    # acted, no money
    SUPPRESSED = "suppressed"                    # policy deliberately did not act
    FAILED_VERIFICATION = "failed_verification"  # action CLAIMED success, state disagreed


@dataclass(frozen=True)
class FailedPayment:
    """What the agent lane is allowed to see. No ground truth lives here."""
    payment_id: str
    order_id: str
    customer_id: str
    amount_paise: int
    currency: str                # "INR"
    method: str                  # card | upi | netbanking | wallet | emi
    failed_at: float
    gateway_code: str            # a REAL Razorpay `reason`, e.g. "insufficient_funds" — §10
    gateway_description: str     # Razorpay's own description string for that reason
    source: str                  # "customer" | "gateway" | "business" — real Razorpay field,
                                 # and the single best policy signal you get for free (§10)
    attempt_no: int
    customer_email: str
    customer_phone: str


@dataclass(frozen=True)
class GroundTruth:
    """Harness lane ONLY. Importing this from the agent lane is a contract violation
    and is checked at QA — it is the label the agent is being scored against."""
    payment_id: str
    true_reason: FailureReason
    would_self_heal: bool        # would this have paid with zero intervention?
    self_heal_after_s: float     # ...and how long it would have taken
    split: str                   # "train" | "holdout"


@dataclass(frozen=True)
class RootCause:
    payment_id: str
    reason: FailureReason
    confidence: float            # 0.0-1.0
    rationale: str               # model prose. NEVER used as stepproof evidence (§5).


@dataclass(frozen=True)
class Intervention:
    payment_id: str
    kind: ActionKind
    reason: str                  # why the policy chose this, composed by salvage code
    cost_paise: int              # from COST_TABLE, §7
    suppressed_by: str = ""      # non-empty iff kind is NONE; names the stopping rule


@dataclass(frozen=True)
class ActionResult:
    """The CLAIM. What the executor believes happened. Never scored on its own."""
    payment_id: str
    kind: ActionKind
    ok: bool
    provider_ref: str            # rzp link id / payment id / "" when no rail was used
    detail: str


@dataclass(frozen=True)
class RecoveryOutcome:
    """The VERDICT. `outcome` is decided by stepproof's seal, not by ActionResult.ok."""
    payment_id: str
    amount_paise: int
    outcome: Outcome
    cause: RootCause | None
    intervention: Intervention
    result: ActionResult | None
    verified: bool | None        # mirrors the stepproof Seal.verified for the money action
    evidence: str                # the observation the verdict rests on
    seal_hash: str               # ties this row to a ledger record. "" iff no action taken
    attempts: int = 1
    notes: list[str] = field(default_factory=list)
