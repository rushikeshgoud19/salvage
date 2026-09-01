"""Scoring for a salvage run, and the two symbols both lanes agree on.

Prevents the failure the whole submission is about: booking money that never
arrived. `amount_recovered_paise` moves only for a record whose stepproof seal
came back `verified is True`. An `ActionResult.ok` — the executor's own claim
that it succeeded — never moves it, and a `201 Created` from Razorpay is not
money. Everything else in this module exists to make that distinction
countable, especially `n_failed_verification` and `verification_gap_paise`:
the value a naive agent would have reported as recovered and did not receive.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from salvage.types import ActionKind, GroundTruth, Outcome, RecoveryOutcome

# CONTRACT §7. Harness-owned, agent lane imports it. Integer paise, no floats:
# a per-record cost cap compared against a float is a cap that leaks.
COST_TABLE = {
    ActionKind.RETRY: 0,
    ActionKind.PAYMENT_LINK: 0,
    ActionKind.NUDGE: 25,
    ActionKind.ESCALATE: 1500,
    ActionKind.NONE: 0,
}


class RecoveryPipeline(Protocol):
    """CONTRACT §3. The only seam between the harness and the agent lane."""

    def run_one(self, payment) -> RecoveryOutcome: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class Metrics:
    split: str
    n_at_risk: int
    amount_at_risk_paise: int
    n_recovered: int
    amount_recovered_paise: int
    recovery_rate_count: float
    recovery_rate_value: float
    n_interventions: int
    intervention_precision: float
    n_false_positive: int
    false_positive_cost_paise: int
    fp_rate: float
    n_suppressed: int
    n_unresolved: int
    n_failed_verification: int
    verification_gap_paise: int
    n_rules_classified: int
    n_llm_classified: int
    chain_intact: bool
    seals_total: int


def score(outcomes: list[RecoveryOutcome], truth: list[GroundTruth],
          split: str = "holdout") -> Metrics:
    """Score the outcomes whose ground-truth row falls in `split`.

    `chain_intact` is left False here on purpose: `score` cannot see the
    ledger, and a metric that claims an intact chain without reading one is the
    same lie this project exists to catch. The CLI overwrites `chain_intact`
    and `seals_total` from `audit()` with `dataclasses.replace`.
    """
    truth_by_id = {t.payment_id: t for t in truth}
    selected = [o for o in outcomes
                if o.payment_id in truth_by_id
                and truth_by_id[o.payment_id].split == split]

    n_at_risk = len(selected)
    amount_at_risk = sum(o.amount_paise for o in selected)

    recovered = [o for o in selected if _is_recovered(o)]
    n_recovered = len(recovered)
    amount_recovered = sum(o.amount_paise for o in recovered)

    intervened = [o for o in selected if o.intervention.kind is not ActionKind.NONE]
    n_interventions = len(intervened)

    # A false positive is an intervention we paid for on a payment that would
    # have settled on its own. Without the counterfactual label this is
    # invisible, which is why the generator carries it.
    false_positives = [o for o in intervened
                       if truth_by_id[o.payment_id].would_self_heal]
    n_false_positive = len(false_positives)
    false_positive_cost = sum(o.intervention.cost_paise for o in false_positives)

    failed_verification = [o for o in selected
                           if o.outcome is Outcome.FAILED_VERIFICATION]

    n_rules = sum(1 for o in selected if _classifier_of(o) == "rules")
    n_llm = sum(1 for o in selected if _classifier_of(o) == "llm")

    return Metrics(
        split=split,
        n_at_risk=n_at_risk,
        amount_at_risk_paise=amount_at_risk,
        n_recovered=n_recovered,
        amount_recovered_paise=amount_recovered,
        recovery_rate_count=_ratio(n_recovered, n_at_risk),
        recovery_rate_value=_ratio(amount_recovered, amount_at_risk),
        n_interventions=n_interventions,
        intervention_precision=_ratio(n_recovered, n_interventions),
        n_false_positive=n_false_positive,
        false_positive_cost_paise=false_positive_cost,
        fp_rate=_ratio(n_false_positive, n_interventions),
        n_suppressed=sum(1 for o in selected if o.outcome is Outcome.SUPPRESSED),
        n_unresolved=sum(1 for o in selected if o.outcome is Outcome.UNRESOLVED),
        n_failed_verification=len(failed_verification),
        verification_gap_paise=sum(o.amount_paise for o in failed_verification),
        n_rules_classified=n_rules,
        n_llm_classified=n_llm,
        chain_intact=False,
        seals_total=sum(1 for o in selected if o.seal_hash),
    )


def exceptions(outcomes: list[RecoveryOutcome]) -> list[RecoveryOutcome]:
    """The human review queue, largest amount first.

    Two kinds of record earn a person's attention: one where the executor
    claimed success and the seal disagreed, and one the policy deliberately
    handed to a human. Ordered by amount because that is the order an ops team
    works the queue in.
    """
    flagged = [o for o in outcomes
               if o.outcome is Outcome.FAILED_VERIFICATION
               or o.intervention.kind is ActionKind.ESCALATE]
    return sorted(flagged, key=lambda o: (-o.amount_paise, o.payment_id))


def _is_recovered(o: RecoveryOutcome) -> bool:
    """`verified is True` is the load-bearing half.

    `is True` and not truthiness — `verified` is `bool | None`, and a `None`
    from a pipeline that forgot to seal must never read as recovered. The
    `Outcome.RECOVERED` check is the belt to that suspenders: a row claiming
    recovery without a passing seal contributes zero rupees and zero count.
    """
    return o.verified is True and o.outcome is Outcome.RECOVERED


def _classifier_of(o: RecoveryOutcome) -> str:
    """First token of `RootCause.rationale` — "rules" or "llm" (§7).

    This is the numeric answer to the AI Judgment criterion: how much of the
    batch a lookup settled without reaching for a model.
    """
    if o.cause is None:
        return ""
    head = o.cause.rationale.strip().split(maxsplit=1)
    if not head:
        return ""
    return head[0].strip(":-").lower()


def _ratio(numerator: int, denominator: int) -> float:
    """Zero denominator is 0.0, never a ZeroDivisionError and never a nan on a slide."""
    return numerator / denominator if denominator else 0.0
