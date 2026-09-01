"""Tests for the batch driver and the one-command demo.

Written at integration: `tests/test_cli.py` was in no lane's ownership row, so H6 — "a
record that blows up must not end the batch" — shipped with no committed guard. That was a
planning gap, and this file closes it.

Two properties are load-bearing for the submission:

1. **The batch is isolated from any single record.** A judge running the demo must never
   see a traceback where a 240-row table should be.
2. **The outcomes JSON round-trips exactly.** `run` writes `run/outcomes.json` and `report`
   reads it back; `demo` passes objects in-process and would never catch a drift between
   the two. That asymmetry is the seam most likely to rot silently.
"""
from __future__ import annotations

import json

import pytest

import salvage.cli as cli_mod
from salvage.cli import _outcomes_from_json, _outcomes_to_json, _run_batch
from salvage.generate import generate_batch, write_batch
from salvage.pipeline import PipelineConfig
from salvage.types import (
    ActionKind, ActionResult, FailureReason, Intervention, Outcome, RecoveryOutcome, RootCause,
)


@pytest.fixture()
def batch_dir(tmp_path):
    """A small real batch on disk, so _run_batch has something to load."""
    payments, truth = generate_batch(n=10, seed=7)
    write_batch(payments, truth, out_dir=str(tmp_path / "data"))
    return str(tmp_path / "data")


@pytest.fixture()
def cfg(tmp_path) -> PipelineConfig:
    return PipelineConfig(
        db_path=str(tmp_path / "run" / "salvage.db"),
        ledger_path=str(tmp_path / "run" / "ledger.jsonl"),
        offline=True,
    )


class _Pipeline:
    """A contract-shaped pipeline that explodes on one nominated record."""

    def __init__(self, explode_on: str | None = None) -> None:
        self.explode_on = explode_on
        self.seen: list[str] = []

    def run_one(self, payment) -> RecoveryOutcome:
        self.seen.append(payment.payment_id)
        if payment.payment_id == self.explode_on:
            raise RuntimeError("deliberate mid-batch failure")
        return RecoveryOutcome(
            payment_id=payment.payment_id,
            amount_paise=payment.amount_paise,
            outcome=Outcome.RECOVERED,
            cause=RootCause(payment.payment_id, FailureReason.BANK_DOWN, 0.95, "rules x"),
            intervention=Intervention(payment.payment_id, ActionKind.RETRY, "transient", 0),
            result=ActionResult(payment.payment_id, ActionKind.RETRY, True, "pay_x", "ok"),
            verified=True,
            evidence=f"rzp {payment.payment_id} status=captured",
            seal_hash="ab" * 32,
        )

    def close(self) -> None:
        pass


# ── H6: one record must never end the batch ─────────────────────────────────────

def test_a_record_that_explodes_does_not_end_the_batch(cfg, batch_dir, tmp_path, monkeypatch):
    payments, _ = generate_batch(n=10, seed=7)
    victim = payments[2].payment_id                      # record 3 of 10
    pipeline = _Pipeline(explode_on=victim)
    monkeypatch.setattr(cli_mod, "build_pipeline", lambda _cfg: pipeline)

    outcomes = _run_batch(cfg, batch_dir, str(tmp_path / "outcomes.json"))

    assert len(outcomes) == 10, "the batch must produce a row for every record"
    assert len(pipeline.seen) == 10, "every record must have been attempted"
    crashed = [o for o in outcomes if o.payment_id == victim]
    assert len(crashed) == 1
    assert crashed[0].outcome is Outcome.UNRESOLVED
    assert "deliberate mid-batch failure" in crashed[0].evidence
    assert crashed[0].amount_paise == payments[2].amount_paise


def test_a_clean_batch_reports_every_record(cfg, batch_dir, tmp_path, monkeypatch):
    monkeypatch.setattr(cli_mod, "build_pipeline", lambda _cfg: _Pipeline())
    outcomes = _run_batch(cfg, batch_dir, str(tmp_path / "outcomes.json"))
    assert len(outcomes) == 10
    assert all(o.outcome is Outcome.RECOVERED for o in outcomes)


def test_run_batch_writes_readable_json(cfg, batch_dir, tmp_path, monkeypatch):
    path = tmp_path / "outcomes.json"
    monkeypatch.setattr(cli_mod, "build_pipeline", lambda _cfg: _Pipeline())
    _run_batch(cfg, batch_dir, str(path))
    rows = json.loads(path.read_text(encoding="utf-8"))
    assert len(rows) == 10
    assert all(isinstance(r["amount_paise"], int) for r in rows)


# ── the asymmetric seam: run writes JSON, report reads it back ──────────────────

def test_outcomes_survive_the_json_round_trip(tmp_path):
    """`demo` passes objects in-process, so only `run` + `report` exercises this path.

    Every field is checked, including the ones a partial rebuild would quietly drop: the
    nested cause, the intervention, the seal hash that ties the row to the ledger, and the
    notes list.
    """
    original = RecoveryOutcome(
        payment_id="pay_0001",
        amount_paise=45000,
        outcome=Outcome.FAILED_VERIFICATION,
        cause=RootCause("pay_0001", FailureReason.INSUFFICIENT_FUNDS, 0.85, "llm because"),
        intervention=Intervention(
            "pay_0001", ActionKind.PAYMENT_LINK, "instrument is dead", 0, suppressed_by=""
        ),
        result=ActionResult("pay_0001", ActionKind.PAYMENT_LINK, True, "plink_a1", "created"),
        verified=False,
        evidence="rzp plink_a1 status=created amount_paid=0 expected>=45000",
        seal_hash="cd" * 32,
        attempts=2,
        notes=["first note", "second note"],
    )
    path = tmp_path / "outcomes.json"
    _outcomes_to_json([original], str(path))
    (restored,) = _outcomes_from_json(str(path))

    assert restored == original, "the JSON round trip is lossy"


def test_round_trip_preserves_a_suppressed_record(tmp_path):
    """A NONE intervention carries `suppressed_by`, which names the stopping rule that fired."""
    original = RecoveryOutcome(
        payment_id="pay_0002",
        amount_paise=99900,
        outcome=Outcome.SUPPRESSED,
        cause=RootCause("pay_0002", FailureReason.CHECKOUT_DROPOFF, 0.8, "rules x"),
        intervention=Intervention(
            "pay_0002", ActionKind.NONE, "held", 0, suppressed_by="timing_window"
        ),
        result=None,
        verified=None,
        evidence="",
        seal_hash="",
    )
    path = tmp_path / "outcomes.json"
    _outcomes_to_json([original], str(path))
    (restored,) = _outcomes_from_json(str(path))
    assert restored == original
    assert restored.intervention.suppressed_by == "timing_window"
    assert restored.verified is None, "None must not collapse to False — it means 'not checked'"


def test_round_trip_of_a_whole_real_batch(cfg, batch_dir, tmp_path, monkeypatch):
    monkeypatch.setattr(cli_mod, "build_pipeline", lambda _cfg: _Pipeline())
    path = tmp_path / "outcomes.json"
    written = _run_batch(cfg, batch_dir, str(path))
    assert _outcomes_from_json(str(path)) == written
