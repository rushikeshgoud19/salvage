"""The record loop — detect, classify, decide, execute — with a hard floor under it.

Prevents one malformed record from killing a 240-record batch. `run_one` converts any
exception into an UNRESOLVED outcome carrying the exception text as its evidence, so a
run always yields a complete, scoreable result set instead of a traceback and a partial
one. It is also the single place the ledger is bound to the configured path, so no seal
can quietly land in a stray file the audit never reads.
"""
from __future__ import annotations

import dataclasses
import os
import time
from dataclasses import dataclass

import stepproof

from salvage.classify import classify
from salvage.detect import detect
from salvage.execute import execute
from salvage.policy import decide
from salvage.rzp import RzpClient
from salvage.store import Store
from salvage.types import (
    ActionKind,
    FailedPayment,
    Intervention,
    Outcome,
    RecoveryOutcome,
)


@dataclass(frozen=True)
class PipelineConfig:
    """Contract §3 — the harness constructs this, so the field names are contract."""

    db_path: str = "run/salvage.db"
    ledger_path: str = "run/ledger.jsonl"
    offline: bool = True
    max_attempts: int = 3
    cost_cap_paise: int = 2000
    quiet_hours: tuple[int, int] = (22, 8)
    seed: int = 7


class RecoveryPipeline:
    def __init__(self, cfg: PipelineConfig) -> None:
        self.cfg = cfg
        self.store = Store(cfg.db_path)
        self.rzp = RzpClient(offline=cfg.offline)

    def run_one(self, payment: FailedPayment) -> RecoveryOutcome:
        """Never raises. A record that blows up becomes an UNRESOLVED row, not a crash."""
        try:
            return self._run(payment)
        except Exception as exc:
            return _crashed(payment, exc)

    def _run(self, payment: FailedPayment) -> RecoveryOutcome:
        self.store.upsert_payment(payment)

        if not detect([payment]):
            return execute(
                payment,
                Intervention(
                    payment_id=payment.payment_id,
                    kind=ActionKind.NONE,
                    reason="detector found no recoverable risk on this record",
                    cost_paise=0,
                    suppressed_by="not_at_risk",
                ),
                self.store,
                self.rzp,
            )

        cause = classify(payment)
        plan = decide(payment, cause, self.store, self.cfg, time.time())
        outcome = execute(payment, plan, self.store, self.rzp)

        notes = list(outcome.notes)
        if cause.rationale:
            # Contract §5.3: model prose lives in notes. It is never evidence, and the
            # verdict above was already sealed without it.
            notes.append(f"classifier({cause.confidence:.2f}): {cause.rationale}")
        return dataclasses.replace(outcome, cause=cause, notes=notes)

    def close(self) -> None:
        self.store.close()


def build_pipeline(cfg: PipelineConfig) -> RecoveryPipeline:
    """Contract §5.5: one ledger per run, bound exactly once, here.

    `build_pipeline` runs once per batch and is the only place that knows both the
    configured ledger path and the moment the run begins, so binding it here keeps
    `set_ledger` out of `run_one` where it would re-open the chain 240 times.
    """
    for path in (cfg.db_path, cfg.ledger_path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    stepproof.set_ledger(stepproof.Ledger(cfg.ledger_path))
    return RecoveryPipeline(cfg)


def _crashed(payment: FailedPayment, exc: Exception) -> RecoveryOutcome:
    return RecoveryOutcome(
        payment_id=payment.payment_id,
        amount_paise=payment.amount_paise,
        outcome=Outcome.UNRESOLVED,
        cause=None,
        intervention=Intervention(
            payment_id=payment.payment_id,
            kind=ActionKind.NONE,
            reason="the record failed before a verdict could be sealed",
            cost_paise=0,
            suppressed_by="exception",
        ),
        result=None,
        verified=False,
        evidence=(
            f"run_one on {payment.payment_id} raised {type(exc).__name__}: {exc}"
        ),
        seal_hash="",
        attempts=0,
    )
