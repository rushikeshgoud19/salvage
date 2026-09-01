"""A second money path, to show the verification layer is not about recovery.

The claim this project keeps making is that the interesting failure is not specific to
revenue recovery. It is specific to *agents*: a tool returns success, an agent relays it,
and nobody looks at the world it was supposed to change. If that is true, the same gate
should catch the same bug on a money path that shares no logic with recovery at all.

So: refunds. A different endpoint, a different direction of money, a different failure
state, written independently of `execute.py` and importing none of it.

**The failure it catches is worse than the recovery one.** `POST /payments/{id}/refund`
returns `200` with a refund id and `status: "pending"` — which is correct and normal, since
refunds settle asynchronously. An agent that treats that `200` as done tells the merchant
the customer was refunded. If the refund never leaves `pending`, the customer has no money
and believes they were refunded, and the next thing that happens is a chargeback plus a
support ticket. Nobody in the chain lied.

This module is deliberately ~120 lines. It is a demonstration that the layer generalises,
not a second product.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from stepproof import VerificationError, verified  # noqa: F401  (VerificationError re-exported)

# Refund states Razorpay actually reports. Only one of them means the customer has money.
_PROCESSED = "processed"
_PENDING = "pending"
_FAILED = "failed"

# Deterministic stuck cohort, chosen by hashing the payment id so it is stable across runs
# and across machines. These are the refunds that return a clean 200 and never process --
# the exact shape of the failure this module exists to demonstrate.
_STUCK_PCT = 25


def _bucket(payment_id: str) -> int:
    return int(hashlib.sha256(f"refund:{payment_id}".encode("utf-8")).hexdigest()[:8], 16) % 100


@dataclass(frozen=True)
class RefundOutcome:
    """The verdict, not the claim. `processed` is decided by observation, never by the call."""
    payment_id: str
    refund_id: str
    amount_paise: int
    claimed_ok: bool          # what the API said — never scored on its own
    processed: bool | None    # what the seal concluded after looking
    evidence: str
    seal_hash: str


class RefundClient:
    """Offline stand-in for Razorpay's refund endpoints, shaped like the real bodies.

    Self-contained on purpose: this module shares no client, no store and no policy with
    the recovery loop, so a reviewer can see that what carries over between them is the
    verification discipline and nothing else.
    """

    def __init__(self) -> None:
        self._issued: dict[str, dict] = {}

    def create_refund(self, payment_id: str, amount_paise: int) -> dict:
        """POST /payments/{id}/refund — returns 200 with a real id and `pending` status.

        This is a *correct* response. Refunds are asynchronous; pending is what you get.
        Treating it as completion is the bug.
        """
        refund_id = "rfnd_" + hashlib.sha256(payment_id.encode()).hexdigest()[:14]
        body = {"id": refund_id, "entity": "refund", "amount": amount_paise,
                "currency": "INR", "payment_id": payment_id, "status": _PENDING}
        self._issued[refund_id] = {**body, "_stuck": _bucket(payment_id) < _STUCK_PCT}
        return body

    def fetch_refund(self, refund_id: str) -> dict:
        """GET /refunds/{id} — the only call that can tell you the customer has money."""
        issued = self._issued.get(refund_id)
        if issued is None:
            raise LookupError(f"no refund issued in this session with id {refund_id!r}")
        if issued["_stuck"]:
            status = _PENDING            # never leaves pending. the money never moves.
        elif _bucket(issued["payment_id"]) < 92:
            status = _PROCESSED
        else:
            status = _FAILED
        return {k: v for k, v in issued.items() if not k.startswith("_")} | {"status": status}


def refund(client: RefundClient, payment_id: str, amount_paise: int) -> RefundOutcome:
    """Issue a refund and seal whether the customer actually got their money back.

    The `**kwargs` on the verifier is not optional styling: stepproof calls
    `verifier(**fields)` only when every bound argument of the wrapped function is a
    parameter of the verifier, and otherwise calls it with no arguments at all.
    """
    observed: dict = {}

    def _verify_refund_processed(**_kw) -> tuple[bool, str]:
        refund_id = observed.get("refund_id", "")
        try:
            state = client.fetch_refund(refund_id)
        except Exception as exc:
            return False, f"rzp fetch_refund {refund_id} raised {type(exc).__name__}: {exc}"
        status = str(state.get("status", ""))
        amount = int(state.get("amount", 0) or 0)
        # Evidence is composed here from observed values. Never from model prose, which
        # stepproof's narration guard would reject anyway.
        return (
            status == _PROCESSED and amount >= amount_paise,
            f"rzp {refund_id} status={status} amount={amount} "
            f"expected status=processed amount>={amount_paise}",
        )

    @verified(
        proves=None,
        verifier=_verify_refund_processed,
        actor="salvage-agent",
        authorization="policy:refund",
        raises=False,                    # a batch must survive one bad refund
    )
    def issue_refund(payment_id: str, amount_paise: int) -> dict:
        body = client.create_refund(payment_id, amount_paise)
        observed["refund_id"] = body["id"]
        observed["claimed_ok"] = True    # the API returned 200. this is the CLAIM.
        return body

    issue_refund(payment_id=payment_id, amount_paise=amount_paise)

    from stepproof import get_ledger
    seal = list(get_ledger().read())[-1]
    return RefundOutcome(
        payment_id=payment_id,
        refund_id=observed.get("refund_id", ""),
        amount_paise=amount_paise,
        claimed_ok=bool(observed.get("claimed_ok")),
        processed=seal.verified,
        evidence=seal.evidence,
        seal_hash=seal.hash,
    )
