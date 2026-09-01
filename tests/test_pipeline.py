"""Tests for the record loop.

Written at integration, not in a lane: `salvage/pipeline.py` sat in the agent lane but
`tests/test_pipeline.py` was in no lane's ownership row, so the wiring shipped with no
committed guard. That was a planning gap, and this file closes it.

The property that matters here is negative: `run_one` must **never** raise. A 240-record
batch that dies on record 3 because one gateway response was malformed is worthless, and
the failure would look like a crash rather than an unresolved record.
"""
from __future__ import annotations

import dataclasses

import pytest

import stepproof
from salvage.pipeline import PipelineConfig, RecoveryPipeline, build_pipeline
from salvage.types import FailedPayment, Outcome


def make_payment(payment_id: str = "pay_0001", code: str = "insufficient_funds") -> FailedPayment:
    return FailedPayment(
        payment_id=payment_id,
        order_id="order_0001",
        customer_id="cust_0001",
        amount_paise=45000,
        currency="INR",
        method="card",
        failed_at=1.0,
        gateway_code=code,
        gateway_description="The customer does not have sufficient funds in the account.",
        source="customer",
        attempt_no=1,
        customer_email="cust0001@example.invalid",
        customer_phone="+919845273610",
    )


@pytest.fixture()
def cfg(tmp_path) -> PipelineConfig:
    return PipelineConfig(
        db_path=str(tmp_path / "salvage.db"),
        ledger_path=str(tmp_path / "ledger.jsonl"),
        offline=True,
    )


# ── the contract shape ──────────────────────────────────────────────────────────

def test_pipeline_config_carries_exactly_the_contract_fields():
    """Contract §3 freezes these names and defaults — the harness constructs this object."""
    fields = {f.name: f.default for f in dataclasses.fields(PipelineConfig)}
    assert set(fields) == {
        "db_path", "ledger_path", "offline", "max_attempts",
        "cost_cap_paise", "quiet_hours", "seed",
    }
    assert fields["offline"] is True
    assert fields["max_attempts"] == 3
    assert fields["cost_cap_paise"] == 2000
    assert fields["quiet_hours"] == (22, 8)
    assert fields["seed"] == 7


def test_build_pipeline_binds_the_ledger_to_the_configured_path(cfg):
    """Contract §5.5: one ledger per run, bound exactly once, and bound *here*.

    build_pipeline is the sole owner. cli.py used to bind a second one at the same path;
    it worked, because stepproof reads the previous hash off disk on every append, but two
    owners of one module-global is a trap the moment the paths ever differ.
    """
    pipeline = build_pipeline(cfg)
    try:
        assert stepproof.get_ledger().path == cfg.ledger_path
    finally:
        pipeline.close()


# ── the negative property: run_one never raises ─────────────────────────────────

def test_run_one_isolates_an_exploding_record(cfg, monkeypatch):
    """A record whose internals throw becomes UNRESOLVED, carrying the exception text."""
    pipeline = build_pipeline(cfg)
    try:
        def boom(*_args, **_kwargs):
            raise RuntimeError("gateway returned something unparseable")

        monkeypatch.setattr(RecoveryPipeline, "_run", boom)
        outcome = pipeline.run_one(make_payment())

        assert outcome.outcome is Outcome.UNRESOLVED
        assert outcome.payment_id == "pay_0001"
        assert outcome.amount_paise == 45000
        assert "gateway returned something unparseable" in outcome.evidence
        assert "RuntimeError" in outcome.evidence
    finally:
        pipeline.close()


@pytest.mark.parametrize(
    "exc",
    [RuntimeError("boom"), ValueError("bad json"), KeyError("status"), TypeError("nope")],
)
def test_run_one_isolates_every_exception_type(cfg, monkeypatch, exc):
    """Not just RuntimeError. Whatever a gateway client can throw, the batch survives."""
    pipeline = build_pipeline(cfg)
    try:
        monkeypatch.setattr(
            RecoveryPipeline, "_run", lambda *_a, **_k: (_ for _ in ()).throw(exc)
        )
        outcome = pipeline.run_one(make_payment())
        assert outcome.outcome is Outcome.UNRESOLVED
        assert type(exc).__name__ in outcome.evidence
    finally:
        pipeline.close()


def test_a_batch_survives_one_bad_record_in_the_middle(cfg, monkeypatch):
    """The H6 property at the loop level: record 3 of 10 explodes, ten rows still come out."""
    pipeline = build_pipeline(cfg)
    try:
        real = RecoveryPipeline._run

        def sometimes(self, payment):
            if payment.payment_id == "pay_0003":
                raise RuntimeError("deliberate")
            return real(self, payment)

        monkeypatch.setattr(RecoveryPipeline, "_run", sometimes)
        outcomes = [pipeline.run_one(make_payment(f"pay_{i:04d}")) for i in range(1, 11)]

        assert len(outcomes) == 10
        exploded = [o for o in outcomes if o.payment_id == "pay_0003"]
        assert len(exploded) == 1
        assert exploded[0].outcome is Outcome.UNRESOLVED
        assert "deliberate" in exploded[0].evidence
    finally:
        pipeline.close()


def test_every_outcome_carries_the_records_own_amount(cfg):
    """A crashed row must still report the money at stake, or the batch total silently drops."""
    pipeline = build_pipeline(cfg)
    try:
        outcome = pipeline.run_one(make_payment())
        assert outcome.amount_paise == 45000
        assert isinstance(outcome.amount_paise, int)
    finally:
        pipeline.close()


def test_offline_pipeline_opens_no_socket(cfg, monkeypatch):
    """offline=True is the demo path and a judge's clone. It must not touch the network."""
    import httpx

    def forbidden(*_a, **_k):
        raise AssertionError("the offline pipeline made a network call")

    monkeypatch.setattr(httpx, "post", forbidden)
    monkeypatch.setattr(httpx, "get", forbidden)
    monkeypatch.setattr(httpx, "Client", forbidden)

    pipeline = build_pipeline(cfg)
    try:
        for i in range(1, 6):
            assert pipeline.run_one(make_payment(f"pay_{i:04d}")) is not None
    finally:
        pipeline.close()
