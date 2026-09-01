"""Revenue-at-risk detector — the first step of the loop.

The failure this module prevents: spending the recovery budget, and the batch's credibility,
on records no rail in this loop can move. A zero-amount record has nothing to recover; a
non-INR record has no rail here (every Razorpay call salvage makes is INR); a record the
gateway has already re-presented past the published attempt budget is out of the 10-14 day
window in which recovery is still real (Contract §10.3), and one more attempt on it buys
nothing but cost.

`detect` judges the record alone, deliberately. Store state (has it settled? how much have
we spent?) and elapsed time belong to `policy.decide`, which is handed the store, the
config and an explicit `now`. Keeping clock and state out of here is what makes the at-risk
set identical on every run of the same batch.
"""
from __future__ import annotations

from salvage.types import FailedPayment

# Contract §10.3: 3-5 attempts inside a 10-14 day window. A record the gateway has already
# carried to the top of that band is spent, not at risk.
_GATEWAY_ATTEMPT_BUDGET = 5

_RECOVERABLE_CURRENCY = "INR"


def detect(payments: list[FailedPayment]) -> list[FailedPayment]:
    """Return the subset of `payments` this loop can still recover."""
    return [p for p in payments if _at_risk(p)]


def _at_risk(p: FailedPayment) -> bool:
    if isinstance(p.amount_paise, bool) or not isinstance(p.amount_paise, int):
        return False
    if p.amount_paise <= 0:
        return False
    if p.currency != _RECOVERABLE_CURRENCY:
        return False
    return p.attempt_no < _GATEWAY_ATTEMPT_BUDGET
