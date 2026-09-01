"""The audit reader is the only thing standing between a tampered ledger and a report
that quotes it as fact, so the tamper case is built here rather than asserted by hand."""
from __future__ import annotations

import json

from stepproof import Ledger

from salvage.audit import audit, seals_for

SEALS = [
    dict(
        action="create_payment_link",
        claimed="issued a fresh link for pay_0001",
        verified=True,
        evidence="rzp plink_A1 status=created amount=450000 fetched 2026-09-02",
        args={"payment_id": "pay_0001", "amount_paise": 450000},
    ),
    dict(
        action="retry_payment",
        claimed="re-presented the instrument for pay_0002",
        verified=False,
        evidence="rzp pay_LmN status=failed error_code=insufficient_funds",
        args={"payment_id": "pay_0002", "amount_paise": 120000},
    ),
    dict(
        action="settle_payment_link",
        claimed="link paid for pay_0001",
        verified=None,
        evidence="rzp plink_A1 status=created amount_paid=0 fetched 2026-09-02",
        args={"payment_id": "pay_0001", "amount_paise": 450000},
    ),
]


def _build(path) -> str:
    ledger = Ledger(str(path))
    for seal in SEALS:
        ledger.append(
            actor="salvage-agent",
            authorization="policy:payment_link cap=2000p",
            **seal,
        )
    return str(path)


def test_intact_chain_is_reported_intact(tmp_path):
    path = _build(tmp_path / "ledger.jsonl")

    summary = audit(path)

    assert summary.chain_intact is True
    assert summary.seals_total == 3
    assert "3" in summary.detail
    assert [s.action for s in summary.failures] == ["retry_payment"]
    assert [s.action for s in summary.unverified] == ["settle_payment_link"]


def test_edited_record_breaks_the_chain_and_is_named(tmp_path):
    path = _build(tmp_path / "ledger.jsonl")

    lines = open(path, encoding="utf-8").read().splitlines()
    record = json.loads(lines[1])
    record["claimed"] = "re-presented the instrument for pay_0002 and it worked"
    lines[1] = json.dumps(record)
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    summary = audit(path)

    assert summary.chain_intact is False
    assert "1" in summary.detail
    assert "retry_payment" in summary.detail


def test_seals_for_filters_on_the_payment_id_in_args(tmp_path):
    path = _build(tmp_path / "ledger.jsonl")

    assert [s.action for s in seals_for(path, "pay_0001")] == [
        "create_payment_link",
        "settle_payment_link",
    ]
    assert [s.action for s in seals_for(path, "pay_0002")] == ["retry_payment"]
    assert seals_for(path, "pay_9999") == []


def test_absent_ledger_is_not_reported_as_intact(tmp_path):
    path = str(tmp_path / "never" / "written.jsonl")

    summary = audit(path)

    # stepproof answers "chain intact (0 records)" here; passing that through would let
    # the report claim an audit trail that was never written.
    assert summary.chain_intact is False
    assert path in summary.detail
    assert summary.seals_total == 0
    assert summary.failures == []
    assert seals_for(path, "pay_0001") == []
