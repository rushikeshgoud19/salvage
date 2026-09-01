"""Command line entry point — `python -m salvage`.

Prevents the two ways a batch run lies. First, a record that blows up mid-batch taking
the other 239 with it and leaving a report that quietly describes a partial run: every
record is isolated, a crash becomes an UNRESOLVED row with the exception in its
evidence, and the failures are listed once at the end instead of as a traceback through
the progress bar. Second, a forked audit trail: `set_ledger` is a module-global in
stepproof (Contract §5.5), so it is called exactly once here, for the whole batch, and
nowhere else in the codebase.

`demo` is the offline path a reviewer runs on a clean checkout: generate, run, report,
zero network.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, replace

import stepproof
import typer
from rich.console import Console
from rich.progress import track

from salvage.audit import audit
from salvage.generate import generate_batch, load_batch, write_batch
from salvage.metrics import score
from salvage.pipeline import PipelineConfig, build_pipeline
from salvage.report import render, rupees
from salvage.types import (
    ActionKind,
    ActionResult,
    FailedPayment,
    FailureReason,
    Intervention,
    Outcome,
    RecoveryOutcome,
    RootCause,
)

app = typer.Typer(
    add_completion=False,
    help="Verified revenue recovery: an agent that cannot claim money it did not receive.",
)

# A Windows console defaults to cp1252, which cannot encode ₹ and raises
# UnicodeEncodeError mid-batch instead of printing. Every rupee figure this CLI shows
# carries that sign, so the streams are moved to UTF-8 before anything is written.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

console = Console()


def _ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)


def _crash_outcome(payment: FailedPayment, exc: BaseException) -> RecoveryOutcome:
    """A record whose pipeline raised. Contract §3: never a recovery, never a halt."""
    observed = f"{type(exc).__name__}: {exc}"
    return RecoveryOutcome(
        payment_id=payment.payment_id,
        amount_paise=payment.amount_paise,
        outcome=Outcome.UNRESOLVED,
        cause=None,
        intervention=Intervention(
            payment_id=payment.payment_id,
            kind=ActionKind.NONE,
            reason="the pipeline raised before an action was taken",
            cost_paise=0,
            suppressed_by="pipeline-crash",
        ),
        result=None,
        verified=False,
        evidence=observed[:300],
        seal_hash="",
        notes=["record isolated by the batch runner; the rest of the batch continued"],
    )


def _outcomes_to_json(outcomes: list[RecoveryOutcome], path: str) -> None:
    # str-Enum members serialise as their value, so no custom encoder is needed.
    _ensure_parent(path)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([asdict(o) for o in outcomes], fh, indent=2)


def _outcomes_from_json(path: str) -> list[RecoveryOutcome]:
    with open(path, encoding="utf-8") as fh:
        rows = json.load(fh)
    return [_outcome_from_dict(row) for row in rows]


def _outcome_from_dict(row: dict) -> RecoveryOutcome:
    cause = row["cause"]
    result = row["result"]
    plan = row["intervention"]
    return RecoveryOutcome(
        payment_id=row["payment_id"],
        amount_paise=int(row["amount_paise"]),
        outcome=Outcome(row["outcome"]),
        cause=(
            RootCause(
                payment_id=cause["payment_id"],
                reason=FailureReason(cause["reason"]),
                confidence=float(cause["confidence"]),
                rationale=cause["rationale"],
            )
            if cause
            else None
        ),
        intervention=Intervention(
            payment_id=plan["payment_id"],
            kind=ActionKind(plan["kind"]),
            reason=plan["reason"],
            cost_paise=int(plan["cost_paise"]),
            suppressed_by=plan.get("suppressed_by", ""),
        ),
        result=(
            ActionResult(
                payment_id=result["payment_id"],
                kind=ActionKind(result["kind"]),
                ok=bool(result["ok"]),
                provider_ref=result["provider_ref"],
                detail=result["detail"],
            )
            if result
            else None
        ),
        verified=row["verified"],
        evidence=row["evidence"],
        seal_hash=row["seal_hash"],
        attempts=int(row.get("attempts", 1)),
        notes=list(row.get("notes", [])),
    )


def _run_batch(
    cfg: PipelineConfig, data_dir: str, outcomes_path: str
) -> list[RecoveryOutcome]:
    payments, _truth = load_batch(data_dir)
    _ensure_parent(cfg.ledger_path)
    _ensure_parent(cfg.db_path)

    # One ledger and one database per run (Contract §9.5). Left in place, yesterday's
    # seals would be counted into today's audit summary and yesterday's attempts would
    # suppress today's actions, so a second demo would report a run that never happened.
    for stale in (cfg.ledger_path, cfg.db_path):
        if os.path.exists(stale):
            os.remove(stale)
            console.print(f"cleared previous run artefact {stale}")

    # The ledger is bound inside build_pipeline, which is the only place that knows both
    # the configured path and the moment the run begins -- and which also binds it when the
    # pipeline is driven from a script instead of this CLI. Binding it a second time here
    # worked, because stepproof reads the previous hash off disk on every append, but two
    # owners of one global is a trap the moment the two paths ever differ (Contract §5.5).
    pipeline = build_pipeline(cfg)
    outcomes: list[RecoveryOutcome] = []
    crashed: list[tuple[str, str]] = []
    try:
        for payment in track(
            payments, description="recovering", console=console, transient=True
        ):
            try:
                outcomes.append(pipeline.run_one(payment))
            except Exception as exc:  # one record must never end the batch
                crashed.append((payment.payment_id, f"{type(exc).__name__}: {exc}"))
                outcomes.append(_crash_outcome(payment, exc))
    finally:
        pipeline.close()

    _outcomes_to_json(outcomes, outcomes_path)

    recovered = sum(1 for o in outcomes if o.outcome is Outcome.RECOVERED)
    console.print(
        f"ran {len(outcomes)} records: {recovered} seal-verified recoveries, "
        f"{len(crashed)} isolated failures -> {outcomes_path}"
    )
    for payment_id, observed in crashed:
        console.print(f"[yellow]isolated[/yellow] {payment_id}: {observed}")
    return outcomes


def _write_report(
    data_dir: str,
    ledger_path: str,
    outcomes: list[RecoveryOutcome],
    out_path: str,
    split: str,
) -> str:
    _payments, truth = load_batch(data_dir)
    audit_summary = audit(ledger_path)
    # score() has no ledger to read, so the chain facts are filled from the audit that
    # does — a Metrics that disagrees with the ledger beside it is worse than no Metrics.
    metrics = replace(
        score(outcomes, truth, split=split),
        chain_intact=audit_summary.chain_intact,
        seals_total=audit_summary.seals_total,
    )
    _ensure_parent(out_path)
    render(metrics, outcomes, audit_summary, out_path=out_path, truth=truth)
    console.print(
        f"{rupees(metrics.amount_recovered_paise)} recovered of "
        f"{rupees(metrics.amount_at_risk_paise)} at risk on the {metrics.split} split; "
        f"verification gap {rupees(metrics.verification_gap_paise)} -> {out_path}"
    )
    return out_path


@app.command()
def generate(n: int = 240, seed: int = 7, out_dir: str = "data") -> None:
    """Write a synthetic failed-payment batch and its ground-truth labels."""
    payments, truth = generate_batch(n=n, seed=seed)
    payments_path, truth_path = write_batch(payments, truth, out_dir=out_dir)
    console.print(
        f"wrote {len(payments)} payments -> {payments_path} and "
        f"{len(truth)} labels -> {truth_path}"
    )


@app.command()
def run(
    data_dir: str = "data",
    db_path: str = "run/salvage.db",
    ledger_path: str = "run/ledger.jsonl",
    outcomes_path: str = "run/outcomes.json",
    offline: bool = True,
    seed: int = 7,
) -> None:
    """Run the recovery pipeline over the batch, sealing every money action."""
    cfg = PipelineConfig(
        db_path=db_path, ledger_path=ledger_path, offline=offline, seed=seed
    )
    _run_batch(cfg, data_dir, outcomes_path)


@app.command()
def report(
    data_dir: str = "data",
    ledger_path: str = "run/ledger.jsonl",
    outcomes_path: str = "run/outcomes.json",
    out_path: str = "RESULTS.md",
    split: str = "holdout",
) -> None:
    """Score a finished run against the labels and render RESULTS.md."""
    outcomes = _outcomes_from_json(outcomes_path)
    _write_report(data_dir, ledger_path, outcomes, out_path, split)


@app.command()
def demo(
    n: int = 240,
    seed: int = 7,
    data_dir: str = "data",
    db_path: str = "run/salvage.db",
    ledger_path: str = "run/ledger.jsonl",
    outcomes_path: str = "run/outcomes.json",
    out_path: str = "RESULTS.md",
    split: str = "holdout",
) -> None:
    """Generate, run and report end to end, offline, with zero network calls."""
    generate(n=n, seed=seed, out_dir=data_dir)
    cfg = PipelineConfig(
        db_path=db_path, ledger_path=ledger_path, offline=True, seed=seed
    )
    outcomes = _run_batch(cfg, data_dir, outcomes_path)
    _write_report(data_dir, ledger_path, outcomes, out_path, split)
