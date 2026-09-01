"""Tests for scoring.

The centre of gravity is `test_recovered_but_unverified_contributes_nothing`.
Everything else in salvage can be right and the submission is still worthless if
an unverified claim moves `amount_recovered_paise`.

The fixture below is ten hand-built outcomes with values chosen so every field
of `Metrics` can be checked against arithmetic done on paper, not against a
second implementation of the same formula.
"""
from __future__ import annotations

import math

from salvage.metrics import COST_TABLE, Metrics, RecoveryPipeline, exceptions, score
from salvage.types import (
    ActionKind,
    ActionResult,
    FailureReason,
    GroundTruth,
    Intervention,
    Outcome,
    RecoveryOutcome,
    RootCause,
)


def _outcome(pid: str, amount: int, outcome: Outcome, verified: bool | None,
             kind: ActionKind, cost: int, rationale: str,
             seal: str = "") -> RecoveryOutcome:
    cause = RootCause(pid, FailureReason.UNKNOWN, 0.9, rationale) if rationale else None
    return RecoveryOutcome(
        payment_id=pid,
        amount_paise=amount,
        outcome=outcome,
        cause=cause,
        intervention=Intervention(pid, kind, "fixture", cost,
                                  "budget" if kind is ActionKind.NONE else ""),
        result=ActionResult(pid, kind, verified is True, seal, "fixture"),
        verified=verified,
        evidence="fixture evidence",
        seal_hash=seal,
    )


def _truth(pid: str, self_heal: bool, split: str = "holdout") -> GroundTruth:
    return GroundTruth(pid, FailureReason.UNKNOWN, self_heal,
                       3600.0 if self_heal else -1.0, split)


# id, amount_paise, outcome, verified, kind, cost_paise, rationale, seal, self_heal
FIXTURE = [
    ("p01", 100_000, Outcome.RECOVERED, True, ActionKind.RETRY, 0, "rules: bank_down", "s01", False),
    ("p02", 200_000, Outcome.RECOVERED, True, ActionKind.PAYMENT_LINK, 0, "rules: card_expired", "s02", True),
    # Claims recovery, seal says otherwise. Must contribute zero rupees and zero count.
    ("p03", 50_000, Outcome.RECOVERED, False, ActionKind.PAYMENT_LINK, 0, "rules: auth_failed", "s03", False),
    ("p04", 300_000, Outcome.FAILED_VERIFICATION, False, ActionKind.PAYMENT_LINK, 0, "llm: card_declined", "s04", False),
    ("p05", 150_000, Outcome.FAILED_VERIFICATION, False, ActionKind.ESCALATE, 1500, "rules: risk_blocked", "s05", True),
    ("p06", 75_000, Outcome.UNRESOLVED, False, ActionKind.NUDGE, 25, "rules: checkout_dropoff", "s06", False),
    ("p07", 25_000, Outcome.UNRESOLVED, False, ActionKind.NUDGE, 25, "rules: insufficient_funds", "s07", True),
    ("p08", 400_000, Outcome.SUPPRESSED, None, ActionKind.NONE, 0, "rules: risk_blocked", "", True),
    ("p09", 60_000, Outcome.SUPPRESSED, None, ActionKind.NONE, 0, "llm: unrecognised reason", "", False),
    ("p10", 90_000, Outcome.RECOVERED, True, ActionKind.ESCALATE, 1500, "rules: risk_blocked", "s10", False),
]

# Two train records with large amounts: if the split filter leaks, every total moves.
TRAIN_FIXTURE = [
    ("t01", 999_999, Outcome.RECOVERED, True, ActionKind.RETRY, 0, "rules: bank_down", "t1", False),
    ("t02", 888_888, Outcome.SUPPRESSED, None, ActionKind.NONE, 0, "rules: risk_blocked", "", True),
]


def _build(rows, split):
    outcomes = [_outcome(pid, amt, out, ver, kind, cost, rat, seal)
                for pid, amt, out, ver, kind, cost, rat, seal, _ in rows]
    truth = [_truth(pid, heal, split) for pid, *_rest, heal in rows]
    return outcomes, truth


def _holdout():
    return _build(FIXTURE, "holdout")


def _full():
    ho, ht = _holdout()
    to, tt = _build(TRAIN_FIXTURE, "train")
    return ho + to, ht + tt


def test_every_metric_matches_hand_calculation():
    outcomes, truth = _full()
    m = score(outcomes, truth, "holdout")

    assert m.split == "holdout"
    assert m.n_at_risk == 10
    assert m.amount_at_risk_paise == 1_450_000

    # p01 + p02 + p10 only. p03 claims RECOVERED with verified False.
    assert m.n_recovered == 3
    assert m.amount_recovered_paise == 390_000
    assert m.recovery_rate_count == 3 / 10
    assert m.recovery_rate_value == 390_000 / 1_450_000

    # Every kind except NONE (p08, p09).
    assert m.n_interventions == 8
    assert m.intervention_precision == 3 / 8

    # Intervened AND would_self_heal: p02, p05, p07. p08 self-heals but was suppressed.
    assert m.n_false_positive == 3
    assert m.false_positive_cost_paise == 0 + 1500 + 25
    assert m.fp_rate == 3 / 8

    assert m.n_suppressed == 2
    assert m.n_unresolved == 2
    assert m.n_failed_verification == 2
    assert m.verification_gap_paise == 300_000 + 150_000

    assert m.n_rules_classified == 8
    assert m.n_llm_classified == 2
    assert m.seals_total == 8
    assert m.chain_intact is False


def test_train_split_is_scored_separately():
    outcomes, truth = _full()
    m = score(outcomes, truth, "train")
    assert m.split == "train"
    assert m.n_at_risk == 2
    assert m.amount_at_risk_paise == 999_999 + 888_888
    assert m.amount_recovered_paise == 999_999


def test_recovered_but_unverified_contributes_nothing():
    """The single most important line in the codebase (CONTRACT §7).

    p03 is an executor that believes it succeeded. Without a passing seal it is
    worth zero rupees, no matter what `ActionResult.ok` says.
    """
    outcomes, truth = _holdout()
    baseline = score(outcomes, truth)

    p03 = next(o for o in outcomes if o.payment_id == "p03")
    assert p03.outcome is Outcome.RECOVERED
    assert p03.result.ok is False and p03.verified is False

    without_p03 = [o for o in outcomes if o.payment_id != "p03"]
    trimmed = score(without_p03, [t for t in truth if t.payment_id != "p03"])
    assert baseline.amount_recovered_paise == trimmed.amount_recovered_paise
    assert baseline.n_recovered == trimmed.n_recovered


def test_verified_none_never_counts_as_recovered():
    """`verified` is `bool | None`. A pipeline that forgot to seal is not a recovery."""
    rows = [("x1", 100_000, Outcome.RECOVERED, None, ActionKind.RETRY, 0, "rules: x", "s", False)]
    outcomes, truth = _build(rows, "holdout")
    m = score(outcomes, truth)
    assert m.n_recovered == 0
    assert m.amount_recovered_paise == 0


def test_verified_true_without_recovered_outcome_counts_nothing():
    rows = [("x1", 100_000, Outcome.UNRESOLVED, True, ActionKind.RETRY, 0, "rules: x", "s", False)]
    outcomes, truth = _build(rows, "holdout")
    m = score(outcomes, truth)
    assert m.n_recovered == 0
    assert m.amount_recovered_paise == 0


def test_recovered_amount_never_exceeds_amount_at_risk():
    outcomes, truth = _holdout()
    m = score(outcomes, truth)
    assert 0 <= m.amount_recovered_paise <= m.amount_at_risk_paise
    assert 0.0 <= m.recovery_rate_value <= 1.0


def test_money_fields_stay_integers():
    outcomes, truth = _holdout()
    m = score(outcomes, truth)
    for field in ("amount_at_risk_paise", "amount_recovered_paise",
                  "false_positive_cost_paise", "verification_gap_paise"):
        value = getattr(m, field)
        assert type(value) is int, f"{field} is {type(value).__name__}, must be int paise"


def test_empty_batch_yields_zero_ratios_and_no_exception():
    m = score([], [])
    assert m.n_at_risk == 0
    assert m.amount_at_risk_paise == 0
    for field in ("recovery_rate_count", "recovery_rate_value",
                  "intervention_precision", "fp_rate"):
        value = getattr(m, field)
        assert value == 0.0, f"{field} is {value}"
        assert not math.isnan(value), f"{field} is nan — that lands on a slide"


def test_no_interventions_yields_zero_precision_not_a_crash():
    rows = [("x1", 100_000, Outcome.SUPPRESSED, None, ActionKind.NONE, 0, "rules: x", "", True)]
    outcomes, truth = _build(rows, "holdout")
    m = score(outcomes, truth)
    assert m.n_interventions == 0
    assert m.intervention_precision == 0.0
    assert m.fp_rate == 0.0
    assert m.n_false_positive == 0


def test_unknown_split_scores_nothing():
    outcomes, truth = _full()
    m = score(outcomes, truth, "does-not-exist")
    assert m.n_at_risk == 0
    assert m.recovery_rate_value == 0.0


def test_outcome_without_a_truth_row_is_not_scored():
    outcomes, truth = _holdout()
    stray = _outcome("ghost", 500_000, Outcome.RECOVERED, True, ActionKind.RETRY, 0,
                     "rules: x", "sg")
    m = score(outcomes + [stray], truth)
    assert m.n_at_risk == 10
    assert m.amount_recovered_paise == 390_000


def test_classifier_split_covers_the_whole_batch():
    outcomes, truth = _holdout()
    m = score(outcomes, truth)
    assert m.n_rules_classified + m.n_llm_classified == m.n_at_risk


def test_classifier_token_is_case_and_punctuation_tolerant():
    rows = [
        ("a1", 1_000, Outcome.UNRESOLVED, False, ActionKind.RETRY, 0, "Rules: matched table", "s", False),
        ("a2", 1_000, Outcome.UNRESOLVED, False, ActionKind.RETRY, 0, "LLM proposed AUTH_FAILED", "s", False),
        ("a3", 1_000, Outcome.UNRESOLVED, False, ActionKind.RETRY, 0, "  rules  lookup", "s", False),
    ]
    outcomes, truth = _build(rows, "holdout")
    m = score(outcomes, truth)
    assert m.n_rules_classified == 2
    assert m.n_llm_classified == 1


def test_missing_cause_counts_as_neither_classifier():
    rows = [("a1", 1_000, Outcome.UNRESOLVED, False, ActionKind.RETRY, 0, "", "s", False)]
    outcomes, truth = _build(rows, "holdout")
    m = score(outcomes, truth)
    assert m.n_at_risk == 1
    assert m.n_rules_classified == 0
    assert m.n_llm_classified == 0


def test_suppressed_self_healer_is_not_a_false_positive():
    """Correctly declining to act on a payment that heals itself is the win, not the miss."""
    outcomes, truth = _holdout()
    m = score(outcomes, truth)
    p08 = next(t for t in truth if t.payment_id == "p08")
    assert p08.would_self_heal is True
    assert m.n_false_positive == 3       # p02, p05, p07 — p08 excluded


def test_exceptions_queue_is_failed_verification_and_escalations():
    outcomes, _ = _full()
    queue = exceptions(outcomes)
    assert [o.payment_id for o in queue] == ["p04", "p05", "p10"]


def test_exceptions_is_empty_when_nothing_needs_a_human():
    rows = [("x1", 100_000, Outcome.RECOVERED, True, ActionKind.RETRY, 0, "rules: x", "s", False)]
    outcomes, _ = _build(rows, "holdout")
    assert exceptions(outcomes) == []
    assert exceptions([]) == []


def test_cost_table_is_the_contract_table():
    assert COST_TABLE == {
        ActionKind.RETRY: 0,
        ActionKind.PAYMENT_LINK: 0,
        ActionKind.NUDGE: 25,
        ActionKind.ESCALATE: 1500,
        ActionKind.NONE: 0,
    }
    assert set(COST_TABLE) == set(ActionKind)
    for kind, cost in COST_TABLE.items():
        assert type(cost) is int, f"{kind} costs a {type(cost).__name__}, must be int paise"


def test_metrics_is_frozen_and_carries_the_contract_fields():
    outcomes, truth = _holdout()
    m = score(outcomes, truth)
    assert isinstance(m, Metrics)
    assert [f for f in m.__dataclass_fields__] == [
        "split", "n_at_risk", "amount_at_risk_paise", "n_recovered",
        "amount_recovered_paise", "recovery_rate_count", "recovery_rate_value",
        "n_interventions", "intervention_precision", "n_false_positive",
        "false_positive_cost_paise", "fp_rate", "n_suppressed", "n_unresolved",
        "n_failed_verification", "verification_gap_paise", "n_rules_classified",
        "n_llm_classified", "chain_intact", "seals_total",
    ]


def test_recovery_pipeline_protocol_declares_the_seam():
    assert getattr(RecoveryPipeline, "_is_protocol", False)
    assert hasattr(RecoveryPipeline, "run_one")
    assert hasattr(RecoveryPipeline, "close")
