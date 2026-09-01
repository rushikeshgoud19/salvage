"""Tests for the second money path.

`refunds.py` exists to answer one question: is the failure this project describes about
*revenue recovery*, or about *agents*? If it is about agents, the same gate must catch the
same bug on a money path that shares no client, no store and no policy with recovery.

So the property under test is not "refunds work". It is that **a 200 from the create call
is not evidence a customer got their money**, and that the seal, not the response, decides.
"""
from __future__ import annotations

import os

import pytest

import stepproof
from salvage.refunds import RefundClient, RefundOutcome, refund


@pytest.fixture(autouse=True)
def isolated_ledger(tmp_path):
    """One ledger per test. `set_ledger` is a module global in stepproof."""
    previous = stepproof.get_ledger()
    stepproof.set_ledger(stepproof.Ledger(str(tmp_path / "refunds.jsonl")))
    yield
    stepproof.set_ledger(previous)


def test_the_api_says_success_for_every_refund():
    """The premise: the create call never tells you anything useful about the money."""
    client = RefundClient()
    outcomes = [refund(client, f"pay_{i:04d}", 50000) for i in range(40)]
    assert all(o.claimed_ok for o in outcomes), (
        "the demonstration depends on the API reporting success every time"
    )


def test_fewer_refunds_processed_than_claimed():
    """The finding: some of those successes never moved money."""
    client = RefundClient()
    outcomes = [refund(client, f"pay_{i:04d}", 50000) for i in range(40)]
    claimed = [o for o in outcomes if o.claimed_ok]
    processed = [o for o in outcomes if o.processed is True]
    assert len(processed) < len(claimed)


def test_a_refund_stuck_at_pending_is_never_marked_processed():
    """The expensive case: the customer has no money and believes they were refunded."""
    client = RefundClient()
    outcomes = [refund(client, f"pay_{i:04d}", 50000) for i in range(40)]
    stuck = [o for o in outcomes if "status=pending" in o.evidence]
    assert stuck, "the stuck cohort must be reachable or the demonstration is empty"
    for o in stuck:
        assert o.claimed_ok is True, "the API reported success for this refund"
        assert o.processed is False, "and the seal must still refuse to call it processed"


def test_evidence_quotes_the_observed_status_not_a_verdict():
    client = RefundClient()
    outcome = refund(client, "pay_0001", 50000)
    assert "status=" in outcome.evidence
    assert "expected status=processed" in outcome.evidence
    assert outcome.evidence.strip() not in {"True", "False", "ok", "failed"}


def test_every_refund_is_sealed_and_the_chain_holds():
    client = RefundClient()
    outcomes = [refund(client, f"pay_{i:04d}", 50000) for i in range(12)]
    intact, detail = stepproof.get_ledger().verify_chain()
    assert intact, detail
    assert all(o.seal_hash for o in outcomes), "every refund must tie to a ledger record"
    assert len({o.seal_hash for o in outcomes}) == len(outcomes), "seals must be distinct"


def test_the_cohort_is_deterministic():
    """Same ids, same stuck set — on any machine, in any order."""
    ids = [f"pay_{i:04d}" for i in range(40)]
    first = {o.payment_id for o in (refund(RefundClient(), p, 50000) for p in ids)
             if o.processed is False}
    second = {o.payment_id for o in (refund(RefundClient(), p, 50000) for p in reversed(ids))
              if o.processed is False}
    assert first == second


def test_a_refund_never_raises_even_when_the_provider_misbehaves(monkeypatch):
    """One bad refund must not end a batch, same contract as `run_one`."""
    client = RefundClient()

    def broken(_refund_id):
        raise RuntimeError("gateway returned something unparseable")

    monkeypatch.setattr(client, "fetch_refund", broken)
    outcome = refund(client, "pay_0001", 50000)
    assert isinstance(outcome, RefundOutcome)
    assert outcome.processed is False
    assert "RuntimeError" in outcome.evidence


def test_money_stays_an_integer():
    outcome = refund(RefundClient(), "pay_0001", 50000)
    assert isinstance(outcome.amount_paise, int)


def test_refunds_import_nothing_from_the_recovery_loop():
    """The generalisation claim is only worth anything if the two share no code."""
    source = open(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "salvage", "refunds.py"),
        encoding="utf-8",
    ).read()
    for forbidden in ("from salvage.execute", "from salvage.policy", "from salvage.rzp",
                      "from salvage.store", "from salvage.pipeline", "from salvage.classify"):
        assert forbidden not in source, (
            f"refunds.py imports {forbidden!r} — it must share nothing with recovery "
            f"except stepproof, or it proves nothing about generalisation"
        )
