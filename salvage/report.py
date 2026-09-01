"""Renders RESULTS.md — the only artefact a judge actually reads.

Prevents two specific failures. First, a headline number quoted without the split,
the calibration band, or the chain check that makes it meaningful. Second, machine
values leaking into a human document: raw paise, a `nan` from a zero denominator, or a
`None` where a root cause was never settled. Every value that reaches this file goes
through a formatter that has an answer for the empty case.

`Metrics` is imported for typing only. This module reads the fields, it does not need
the class at runtime, and keeping the import out of the runtime path means the report
never drags the scorer in behind it.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Sequence

from salvage.types import GroundTruth, Outcome, RecoveryOutcome

if TYPE_CHECKING:  # pragma: no cover - typing only
    from salvage.audit import AuditSummary
    from salvage.metrics import Metrics

# Contract §10.2. Quoted beside the measured rate so the number is read in context
# instead of doubted.
SMART_RETRY_BAND = (0.45, 0.65)
UNCALIBRATED_ABOVE = 0.80


def rupees(paise: int) -> str:
    """Integer paise -> `₹45,000.00`. Never divides: a float rupee is a rounding bug."""
    value = int(paise)
    sign = "-" if value < 0 else ""
    whole, remainder = divmod(abs(value), 100)
    return f"{sign}₹{whole:,}.{remainder:02d}"


def percent(ratio: float) -> str:
    """Ratio -> `54.2%`, with an answer for the undefined case that is not `nan`."""
    value = float(ratio)
    if value != value or value in (float("inf"), float("-inf")):
        return "not defined"
    return f"{value * 100:.1f}%"


def _count_line(n: int, total: int) -> str:
    return f"{n} of {total} ({percent(n / total if total else 0.0)})"


def _calibration(rate: float) -> str:
    low, high = SMART_RETRY_BAND
    if rate > UNCALIBRATED_ABOVE:
        return (
            f"{percent(rate)} is above {percent(UNCALIBRATED_ABOVE)} — treat this run as "
            "uncalibrated. Published recovery tops out at 70–85% for best-in-class SaaS, "
            "so a figure this high means the batch generator is too generous to quote "
            "(Contract §10.2)."
        )
    if rate > high:
        return (
            f"{percent(rate)} sits above the 45–65% band published for reason-specific "
            "smart retries and inside the 70–85% best-in-class range (Contract §10.2)."
        )
    if rate >= low:
        return (
            f"{percent(rate)} sits inside the 45–65% band published for reason-specific "
            "smart retries, and above the 20–30% a generic daily retry earns "
            "(Contract §10.2)."
        )
    return (
        f"{percent(rate)} sits below the 45–65% band published for reason-specific smart "
        "retries (Contract §10.2). The policy is leaving money on the table."
    )


def _reason_text(outcome: RecoveryOutcome) -> str:
    """Why this record did not end in verified money, in the operator's words."""
    parts: list[str] = []
    if outcome.cause is not None:
        parts.append(f"cause {outcome.cause.reason.value}")
    if outcome.intervention.suppressed_by:
        parts.append(f"suppressed by {outcome.intervention.suppressed_by}")
    if outcome.intervention.reason:
        parts.append(outcome.intervention.reason)
    if outcome.evidence:
        parts.append(outcome.evidence)
    return "; ".join(parts) if parts else "no observation was recorded"


def _classifier_accuracy(
    outcomes: Sequence[RecoveryOutcome], truth: Iterable[GroundTruth], split: str
) -> tuple[int, int]:
    """(agreements, records scored) between the settled root cause and the label."""
    labels = {t.payment_id: t.true_reason for t in truth if t.split == split}
    scored = [o for o in outcomes if o.payment_id in labels and o.cause is not None]
    agreed = sum(1 for o in scored if o.cause.reason is labels[o.payment_id])
    return agreed, len(scored)


def render(
    metrics: "Metrics",
    outcomes: Sequence[RecoveryOutcome],
    audit_summary: "AuditSummary",
    out_path: str = "RESULTS.md",
    *,
    truth: Sequence[GroundTruth] | None = None,
) -> str:
    """Write RESULTS.md and return exactly what was written.

    `truth` is keyword-only and optional so the frozen Contract §4 call still works;
    without it the report simply omits the classifier-accuracy line rather than
    guessing at it.
    """
    classified = metrics.n_rules_classified + metrics.n_llm_classified
    rules_share = metrics.n_rules_classified / classified if classified else 0.0
    llm_share = metrics.n_llm_classified / classified if classified else 0.0

    lines: list[str] = []
    add = lines.append

    add("# salvage — verified recovery results")
    add("")
    add(
        f"**Every metric on this page is computed on the `{metrics.split}` split.** "
        "Nothing here is a training number, and nothing here counts a rupee that a "
        "stepproof seal did not confirm arrived."
    )
    add("")

    add("## AI judgment")
    add("")
    if classified:
        add(
            f"Root cause settled deterministically on {metrics.n_rules_classified} of "
            f"{classified} records ({percent(rules_share)}); the model was invoked on the "
            f"remaining {percent(llm_share)} ({metrics.n_llm_classified} records), where "
            "the gateway reason was absent or ambiguous."
        )
    else:
        add(
            "No records reached the classifier in this run, so there is no deterministic "
            "versus model split to report."
        )
    add("")
    add(
        "The model reads unstructured context and returns a typed diagnostic. It never "
        "chooses an action, never touches money, and its prose is never used as evidence."
    )
    add("")

    add("## Headline")
    add("")
    add("| Measure | Value |")
    add("|---|---|")
    add(f"| Records at risk | {metrics.n_at_risk} |")
    add(f"| Value at risk | {rupees(metrics.amount_at_risk_paise)} |")
    add(f"| Recovered, seal-verified | {metrics.n_recovered} |")
    add(f"| **Value recovered** | **{rupees(metrics.amount_recovered_paise)}** |")
    add(f"| **Recovery rate by value** | **{percent(metrics.recovery_rate_value)}** |")
    add(f"| Recovery rate by count | {percent(metrics.recovery_rate_count)} |")
    add(f"| Interventions | {metrics.n_interventions} |")
    add(f"| Intervention precision | {percent(metrics.intervention_precision)} |")
    add(
        f"| False positives (would have self-healed) | {metrics.n_false_positive} "
        f"({percent(metrics.fp_rate)}) |"
    )
    add(f"| False-positive cost | {rupees(metrics.false_positive_cost_paise)} |")
    add(f"| Suppressed by policy | {metrics.n_suppressed} |")
    add(f"| Unresolved | {metrics.n_unresolved} |")
    add(f"| **Failed verification** | **{metrics.n_failed_verification}** |")
    add(f"| **Verification gap** | **{rupees(metrics.verification_gap_paise)}** |")
    add("")
    add(f"Calibration: {_calibration(metrics.recovery_rate_value)}")
    add("")
    add(
        f"The verification gap is {rupees(metrics.verification_gap_paise)} across "
        f"{metrics.n_failed_verification} records: money an agent that trusted its own "
        "success claim would have booked as recovered and never received."
    )
    add("")

    add("## Audit trail")
    add("")
    status = "INTACT" if audit_summary.chain_intact else "BROKEN"
    add(f"- Hash chain: **{status}** — {audit_summary.detail}")
    add(f"- Seals written: {audit_summary.seals_total}")
    add(f"- Seals that failed verification: {len(audit_summary.failures)}")
    add(f"- Seals left unverified: {len(audit_summary.unverified)}")
    add("")

    if truth is not None:
        agreed, scored = _classifier_accuracy(outcomes, truth, metrics.split)
        add("## Root-cause accuracy")
        add("")
        if scored:
            add(
                f"The settled root cause matched the ground-truth label on "
                f"{_count_line(agreed, scored)} scored records. Accuracy is reported here "
                "and not in `Metrics`, which stays frozen at Contract §7."
            )
        else:
            add(
                f"No `{metrics.split}` record carried both a settled root cause and a "
                "label, so accuracy is not reported for this run."
            )
        add("")

    failed_verification = [o for o in outcomes if o.outcome is Outcome.FAILED_VERIFICATION]
    add("## Failed verification — claimed, not confirmed")
    add("")
    if failed_verification:
        add(
            "Each line quotes the sealed observation verbatim. These are the records where "
            "the action reported success and the payment state disagreed."
        )
        add("")
        for o in failed_verification:
            seal = o.seal_hash[:12] if o.seal_hash else "no seal recorded"
            add(
                f"- `{o.payment_id}` {rupees(o.amount_paise)} via "
                f"{o.intervention.kind.value} — seal `{seal}` — evidence: "
                f"`{o.evidence or 'no evidence recorded'}`"
            )
    else:
        add("No record in this run claimed a success the payment state disagreed with.")
    add("")

    exceptions = [
        o
        for o in outcomes
        if o.outcome in (Outcome.UNRESOLVED, Outcome.FAILED_VERIFICATION)
    ]
    add("## Exceptions — every record that did not end in verified money")
    add("")
    if exceptions:
        add(f"{len(exceptions)} of {len(outcomes)} records in this run need a human.")
        add("")
        add("| Payment | Amount | Outcome | Action | Attempts | Why |")
        add("|---|---|---|---|---|---|")
        for o in exceptions:
            add(
                f"| `{o.payment_id}` | {rupees(o.amount_paise)} | {o.outcome.value} "
                f"| {o.intervention.kind.value} | {o.attempts} | {_reason_text(o)} |"
            )
    else:
        add(
            f"No exceptions. All {len(outcomes)} records in this run ended in verified "
            "money or a deliberate suppression."
        )
    add("")

    text = "\n".join(lines) + "\n"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text
