"""The naive baseline — what the same run reports if you trust your tools.

The failure this module makes visible: an agent that books a recovery when the provider API
returns success will report a number that is mostly fiction, and nothing inside that agent
can tell it so. Every layer is honest. The tool returned 2xx. The agent relayed 2xx. An
output-level judge reads a confident success and agrees.

So this scores one identical run twice — once the naive way, once against sealed evidence —
and reports the difference. That difference is not a hypothetical: it is the same 240
records, the same policy, the same actions, the same provider responses. Only the scoring
rule changes.

**The baseline is deliberately conservative, because a strawman proves nothing.** It counts
a record as recovered only when a *money rail* action (RETRY or PAYMENT_LINK) returned
success. Outreach — NUDGE, ESCALATE — is never counted, even though a careless agent would
count it and the gap would look worse. A comparison that has to be generous to itself is
not a comparison worth publishing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from salvage.types import ActionKind, GroundTruth, Outcome, RecoveryOutcome

# Only these two move money. The baseline is not allowed to book an outreach as a recovery.
_MONEY_RAILS = frozenset({ActionKind.RETRY, ActionKind.PAYMENT_LINK})


@dataclass(frozen=True)
class BaselineComparison:
    """One run, scored two ways. Every field is paise or a ratio; no floats hold money."""

    split: str
    n_records: int
    amount_at_risk_paise: int

    naive_reported_paise: int      # what a success-trusting agent would put in its slide
    naive_records: int
    verified_arrived_paise: int    # what a stepproof seal actually confirmed
    verified_records: int

    fiction_paise: int             # naive - verified: money claimed that never landed
    fiction_records: int

    naive_rate: float              # naive_reported / at_risk
    verified_rate: float           # verified_arrived / at_risk
    fiction_share: float           # fiction / naive_reported -- the share of the claim that is air


def _booked_by_naive(outcome: RecoveryOutcome) -> bool:
    """The rule every un-verified agent uses: the call came back OK, so log the win."""
    result = outcome.result
    return result is not None and result.ok and result.kind in _MONEY_RAILS


def _confirmed_by_seal(outcome: RecoveryOutcome) -> bool:
    """salvage's rule: a stepproof seal looked at real provider state and saw the money."""
    return outcome.verified is True and outcome.outcome is Outcome.RECOVERED


def compare(
    outcomes: Sequence[RecoveryOutcome],
    truth: Iterable[GroundTruth],
    split: str = "holdout",
) -> BaselineComparison:
    """Score one run both ways. `truth` is used only to select the split, never to score."""
    in_split = {t.payment_id for t in truth if t.split == split}
    rows = [o for o in outcomes if o.payment_id in in_split]

    at_risk = sum(o.amount_paise for o in rows)
    naive = [o for o in rows if _booked_by_naive(o)]
    real = [o for o in rows if _confirmed_by_seal(o)]

    naive_paise = sum(o.amount_paise for o in naive)
    real_paise = sum(o.amount_paise for o in real)
    fiction_paise = naive_paise - real_paise

    # Every ratio guards its denominator: an empty split must render as 0.0, never as a
    # ZeroDivisionError and never as a silent nan in a slide someone presents.
    return BaselineComparison(
        split=split,
        n_records=len(rows),
        amount_at_risk_paise=at_risk,
        naive_reported_paise=naive_paise,
        naive_records=len(naive),
        verified_arrived_paise=real_paise,
        verified_records=len(real),
        fiction_paise=fiction_paise,
        fiction_records=len(naive) - len(real),
        naive_rate=(naive_paise / at_risk) if at_risk else 0.0,
        verified_rate=(real_paise / at_risk) if at_risk else 0.0,
        fiction_share=(fiction_paise / naive_paise) if naive_paise else 0.0,
    )
