"""RESULTS.md is the artefact a judge reads, so these tests assert on what a human
would see: rupees not paise, a stated split, a quotable AI-judgment line, and no
machine leftovers (`nan`, `None`) anywhere in the page.

`Metrics` lives in the sibling harness lane. The stand-in below carries exactly the
Contract §7 fields, so the renderer is exercised against the frozen shape rather than
against whatever that file happens to contain mid-merge.
"""
from __future__ import annotations

from dataclasses import dataclass

from salvage.audit import AuditSummary
from salvage.report import percent, render, rupees
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


@dataclass(frozen=True)
class FakeMetrics:
    """Contract §7, field for field."""

    split: str = "holdout"
    n_at_risk: int = 48
    amount_at_risk_paise: int = 4500000
    n_recovered: int = 26
    amount_recovered_paise: int = 2430000
    recovery_rate_count: float = 26 / 48
    recovery_rate_value: float = 0.54
    n_interventions: int = 40
    intervention_precision: float = 0.65
    n_false_positive: int = 4
    false_positive_cost_paise: int = 6000
    fp_rate: float = 0.10
    n_suppressed: int = 8
    n_unresolved: int = 12
    n_failed_verification: int = 2
    verification_gap_paise: int = 120000
    n_rules_classified: int = 42
    n_llm_classified: int = 6
    chain_intact: bool = True
    seals_total: int = 128


def _outcome(
    payment_id: str,
    outcome: Outcome,
    *,
    amount_paise: int = 60000,
    kind: ActionKind = ActionKind.PAYMENT_LINK,
    verified: bool | None = None,
    evidence: str = "",
    reason: FailureReason = FailureReason.AUTH_FAILED,
    rationale: str = "rules: gateway reason maps straight to auth failure",
    suppressed_by: str = "",
    seal_hash: str = "a1b2c3d4e5f60718",
) -> RecoveryOutcome:
    return RecoveryOutcome(
        payment_id=payment_id,
        amount_paise=amount_paise,
        outcome=outcome,
        cause=RootCause(payment_id, reason, 0.9, rationale),
        intervention=Intervention(
            payment_id=payment_id,
            kind=kind,
            reason="instrument needs re-authentication",
            cost_paise=0,
            suppressed_by=suppressed_by,
        ),
        result=ActionResult(payment_id, kind, True, "plink_A1", "created"),
        verified=verified,
        evidence=evidence,
        seal_hash=seal_hash,
    )


FAILED_EVIDENCE = "rzp plink_B2 status=created amount_paid=0 fetched 2026-09-02"

OUTCOMES = [
    _outcome("pay_0001", Outcome.RECOVERED, verified=True, evidence="rzp plink_A1 status=paid"),
    _outcome(
        "pay_0002",
        Outcome.FAILED_VERIFICATION,
        amount_paise=120000,
        verified=False,
        evidence=FAILED_EVIDENCE,
    ),
    _outcome(
        "pay_0003",
        Outcome.UNRESOLVED,
        kind=ActionKind.RETRY,
        verified=False,
        evidence="rzp pay_LmN status=failed error_code=insufficient_funds",
        reason=FailureReason.INSUFFICIENT_FUNDS,
    ),
    _outcome(
        "pay_0004",
        Outcome.SUPPRESSED,
        kind=ActionKind.NONE,
        suppressed_by="cost-cap",
        seal_hash="",
        reason=FailureReason.RISK_BLOCKED,
        rationale="llm: gateway said card_declined, which is ambiguous",
    ),
]

TRUTH = [
    GroundTruth("pay_0001", FailureReason.AUTH_FAILED, False, 0.0, "holdout"),
    GroundTruth("pay_0002", FailureReason.AUTH_FAILED, False, 0.0, "holdout"),
    GroundTruth("pay_0003", FailureReason.BANK_DOWN, True, 7200.0, "holdout"),
    GroundTruth("pay_0004", FailureReason.RISK_BLOCKED, False, 0.0, "train"),
]

AUDIT = AuditSummary(
    chain_intact=True,
    detail="chain intact (128 records)",
    seals_total=128,
    failures=[],
    unverified=[],
)


def _render(tmp_path, metrics=None, outcomes=None, audit_summary=None, truth=TRUTH) -> str:
    out = tmp_path / "RESULTS.md"
    text = render(
        metrics or FakeMetrics(),
        OUTCOMES if outcomes is None else outcomes,
        audit_summary or AUDIT,
        out_path=str(out),
        truth=truth,
    )
    assert out.read_text(encoding="utf-8") == text
    return text


def test_rupees_render_from_paise_never_as_floats():
    assert rupees(4500000) == "₹45,000.00"
    assert rupees(100) == "₹1.00"
    assert rupees(99) == "₹0.99"
    assert rupees(0) == "₹0.00"
    assert rupees(-2500) == "-₹25.00"


def test_percent_has_an_answer_for_the_undefined_case():
    assert percent(0.542) == "54.2%"
    assert percent(0.0) == "0.0%"
    assert percent(float("nan")) == "not defined"
    assert percent(float("inf")) == "not defined"


def test_report_states_the_split_and_leads_with_the_ai_judgment_line(tmp_path):
    text = _render(tmp_path)

    assert "holdout" in text
    assert "Root cause settled deterministically on 42 of 48 records (87.5%)" in text
    assert "the model was invoked on the remaining 12.5% (6 records)" in text
    # The judge-facing line has to come before the metrics table it explains.
    assert text.index("Root cause settled deterministically") < text.index("## Headline")


def test_report_shows_rupees_and_never_raw_paise_or_machine_leftovers(tmp_path):
    text = _render(tmp_path)

    assert "₹45,000.00" in text  # amount at risk
    assert "₹24,300.00" in text  # amount recovered
    assert "₹1,200.00" in text  # verification gap
    assert "4500000" not in text
    assert "2430000" not in text
    assert "nan" not in text
    assert "None" not in text


def test_report_carries_calibration_chain_and_accuracy_lines(tmp_path):
    text = _render(tmp_path)

    assert "54.0%" in text
    assert "45–65%" in text
    assert "INTACT" in text
    assert "chain intact (128 records)" in text
    # pay_0001 and pay_0002 agree with the label, pay_0003 does not; pay_0004 is train.
    assert "2 of 3 (66.7%)" in text


def test_broken_chain_is_stated_as_broken(tmp_path):
    broken = AuditSummary(
        chain_intact=False,
        detail="record 1 ('retry_payment') was modified after sealing",
        seals_total=128,
    )
    text = _render(tmp_path, audit_summary=broken)

    assert "BROKEN" in text
    assert "record 1 ('retry_payment') was modified after sealing" in text


def test_failed_verification_evidence_is_quoted_verbatim(tmp_path):
    text = _render(tmp_path)

    assert FAILED_EVIDENCE in text
    assert "pay_0002" in text


def test_every_unresolved_record_appears_in_the_exception_list(tmp_path):
    text = _render(tmp_path)

    exceptions = text.split("## Exceptions")[1]
    assert "pay_0002" in exceptions
    assert "pay_0003" in exceptions
    assert "insufficient_funds" in exceptions
    assert "pay_0001" not in exceptions  # recovered
    assert "pay_0004" not in exceptions  # deliberately suppressed


def test_report_with_no_exceptions_is_still_legible(tmp_path):
    clean = [OUTCOMES[0], OUTCOMES[3]]
    metrics = FakeMetrics(
        n_unresolved=0,
        n_failed_verification=0,
        verification_gap_paise=0,
        recovery_rate_value=0.61,
    )
    text = _render(tmp_path, metrics=metrics, outcomes=clean)

    assert "No exceptions." in text
    assert "No record in this run claimed a success" in text
    assert "## Headline" in text
    assert "nan" not in text
    assert "None" not in text


def test_empty_run_renders_zeros_instead_of_nan(tmp_path):
    metrics = FakeMetrics(
        n_at_risk=0,
        amount_at_risk_paise=0,
        n_recovered=0,
        amount_recovered_paise=0,
        recovery_rate_count=0.0,
        recovery_rate_value=0.0,
        n_interventions=0,
        intervention_precision=0.0,
        n_false_positive=0,
        false_positive_cost_paise=0,
        fp_rate=0.0,
        n_suppressed=0,
        n_unresolved=0,
        n_failed_verification=0,
        verification_gap_paise=0,
        n_rules_classified=0,
        n_llm_classified=0,
        seals_total=0,
    )
    empty_audit = AuditSummary(
        chain_intact=False,
        detail="no ledger file at run/ledger.jsonl: nothing was sealed",
        seals_total=0,
    )
    text = _render(tmp_path, metrics=metrics, outcomes=[], audit_summary=empty_audit, truth=[])

    assert "₹0.00" in text
    assert "No records reached the classifier" in text
    assert "nan" not in text
    assert "None" not in text
