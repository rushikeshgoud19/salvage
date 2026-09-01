"""Read side of the stepproof ledger.

Prevents a report that quotes recovery figures from a ledger that was edited after the
run. Every number in RESULTS.md is worth exactly as much as the chain check printed
beside it, so that check has to come from the ledger file on disk, not from memory of
what the run believed it wrote.

Write side lives in the agent lane (`execute.py`); nothing here appends.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from stepproof import Ledger, Seal


@dataclass(frozen=True)
class AuditSummary:
    """What an auditor needs before believing a single rupee in the report."""

    chain_intact: bool
    detail: str
    seals_total: int
    failures: list[Seal] = field(default_factory=list)
    unverified: list[Seal] = field(default_factory=list)


def audit(ledger_path: str) -> AuditSummary:
    """Verify the hash chain and collect the seals a human has to look at."""
    if not os.path.exists(ledger_path):
        # stepproof answers "chain intact (0 records)" for a file that is not there.
        # Passing that through would let salvage print "chain intact" over an audit
        # trail it never wrote, which is the exact claim this project exists to refuse.
        return AuditSummary(
            chain_intact=False,
            detail=(
                f"no ledger file at {ledger_path}: nothing was sealed, "
                "so there is no chain to verify"
            ),
            seals_total=0,
        )

    ledger = Ledger(ledger_path)
    intact, detail = ledger.verify_chain()
    return AuditSummary(
        chain_intact=intact,
        detail=detail,
        seals_total=sum(1 for _ in ledger.read()),
        failures=ledger.failures(),
        unverified=ledger.unverified(),
    )


def seals_for(ledger_path: str, payment_id: str) -> list[Seal]:
    """Every seal recorded against one payment, in ledger order.

    The payment id travels in `Seal.args` because that is what the sealed action was
    called with; matching on the action string instead would break the moment an action
    is renamed.
    """
    if not os.path.exists(ledger_path):
        return []
    return [s for s in Ledger(ledger_path).read() if s.args.get("payment_id") == payment_id]
