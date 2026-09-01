"""Execution tests: the claim is not the verdict.

The centrepiece is `test_created_link_that_never_pays_is_failed_verification` — a
payment link whose create call returns a clean 201 and whose link never reaches `paid`.
A naive agent books that as recovered revenue. If that test ever goes green on
Outcome.RECOVERED, the project's entire claim is false.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest
import stepproof

from salvage.execute import ACTOR, execute
from salvage.types import (
    ActionKind,
    FailedPayment,
    Intervention,
    Outcome,
)

AMOUNT = 45000


# --- doubles -------------------------------------------------------------------------


class SqliteStore:
    """The Contract §8 schema on a real file, because `sqlite_row_exists` opens the
    database itself — verifying against an in-process mock would verify nothing."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.con = sqlite3.connect(path)
        self.con.executescript(
            """
            CREATE TABLE IF NOT EXISTS payments (
                payment_id   TEXT PRIMARY KEY,
                order_id     TEXT NOT NULL,
                customer_id  TEXT NOT NULL,
                amount_paise INTEGER NOT NULL,
                failed_at    REAL NOT NULL,
                gateway_code TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS attempts (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id   TEXT NOT NULL,
                kind         TEXT NOT NULL,
                provider_ref TEXT NOT NULL DEFAULT '',
                cost_paise   INTEGER NOT NULL DEFAULT 0,
                created_at   REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settlements (
                payment_id   TEXT PRIMARY KEY,
                provider_ref TEXT NOT NULL,
                amount_paise INTEGER NOT NULL,
                settled_at   REAL NOT NULL
            );
            """
        )
        self.con.commit()

    def record_attempt(self, payment_id, kind, provider_ref, cost_paise) -> int:
        cur = self.con.execute(
            "INSERT INTO attempts (payment_id, kind, provider_ref, cost_paise, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (payment_id, kind.value, provider_ref, int(cost_paise), time.time()),
        )
        self.con.commit()
        return int(cur.lastrowid or 0)

    def mark_settled(self, payment_id, provider_ref, amount_paise) -> None:
        self.con.execute(
            "INSERT OR REPLACE INTO settlements VALUES (?, ?, ?, ?)",
            (payment_id, provider_ref, int(amount_paise), time.time()),
        )
        self.con.commit()

    def attempts_for(self, payment_id) -> int:
        return int(
            self.con.execute(
                "SELECT COUNT(*) FROM attempts WHERE payment_id = ?", (payment_id,)
            ).fetchone()[0]
        )

    def spend_for(self, payment_id) -> int:
        return int(
            self.con.execute(
                "SELECT COALESCE(SUM(cost_paise), 0) FROM attempts WHERE payment_id = ?",
                (payment_id,),
            ).fetchone()[0]
        )

    def settlements(self) -> list[tuple]:
        return self.con.execute("SELECT * FROM settlements").fetchall()

    def close(self) -> None:
        self.con.close()


class SilentStore(SqliteStore):
    """Claims to have recorded the outreach and records nothing — the database
    equivalent of an agent reporting a nudge it never sent."""

    def record_attempt(self, payment_id, kind, provider_ref, cost_paise) -> int:
        return 0


class StuckLinkRzp:
    """The engineered failure. `create_payment_link` returns a well-formed 201 with a
    real link id; the link never leaves `created` and `amount_paid` stays 0 forever."""

    def __init__(self) -> None:
        self.created: dict[str, dict] = {}

    def create_payment_link(self, payment_id, amount_paise, email) -> dict:
        link_id = f"plink_{payment_id.split('_')[-1]}"
        self.created[link_id] = {
            "id": link_id,
            "status": "created",
            "amount": amount_paise,
            "short_url": f"https://rzp.io/i/{link_id}",
        }
        return self.created[link_id]

    def fetch_payment_link(self, link_id) -> dict:
        return {"id": link_id, "status": "created", "amount_paid": 0, "payments": []}

    def fetch_payment(self, rzp_payment_id) -> dict:
        return {"id": rzp_payment_id, "status": "failed", "amount": AMOUNT}


class PaidLinkRzp(StuckLinkRzp):
    def fetch_payment_link(self, link_id) -> dict:
        return {"id": link_id, "status": "paid", "amount_paid": AMOUNT, "payments": [{}]}


class CapturedRzp(StuckLinkRzp):
    def fetch_payment(self, rzp_payment_id) -> dict:
        return {"id": rzp_payment_id, "status": "captured", "amount": AMOUNT}


class ShortPaidLinkRzp(StuckLinkRzp):
    """Paid, but not in full — a partial payment is not a recovery."""

    def fetch_payment_link(self, link_id) -> dict:
        return {"id": link_id, "status": "paid", "amount_paid": AMOUNT - 1}


class BoomRzp(StuckLinkRzp):
    def create_payment_link(self, payment_id, amount_paise, email) -> dict:
        raise FileNotFoundError("fixtures/payment_links__pay_A1.json")


class LookupBoomRzp(StuckLinkRzp):
    def fetch_payment_link(self, link_id) -> dict:
        raise ConnectionError("razorpay unreachable")


# --- fixtures ------------------------------------------------------------------------


@pytest.fixture
def ledger(tmp_path: Path):
    led = stepproof.Ledger(str(tmp_path / "ledger.jsonl"))
    stepproof.set_ledger(led)
    return led


@pytest.fixture
def store(tmp_path: Path):
    st = SqliteStore(str(tmp_path / "salvage.db"))
    yield st
    st.close()


def seals(ledger) -> list:
    return list(ledger.read())


def payment(payment_id: str = "pay_A1") -> FailedPayment:
    return FailedPayment(
        payment_id=payment_id,
        order_id="order_A1",
        customer_id="cust_A1",
        amount_paise=AMOUNT,
        currency="INR",
        method="card",
        failed_at=time.time() - 7200,
        gateway_code="authentication_failed",
        gateway_description="Payment failed due to authentication",
        source="customer",
        attempt_no=1,
        customer_email="cust0001@example.invalid",
        customer_phone="+919000000001",
    )


def plan(kind: ActionKind, cost: int = 0) -> Intervention:
    return Intervention(
        payment_id="pay_A1",
        kind=kind,
        reason=f"test plan for {kind.value}",
        cost_paise=cost,
    )


# --- THE test ------------------------------------------------------------------------


def test_created_link_that_never_pays_is_failed_verification(ledger, store):
    got = execute(payment(), plan(ActionKind.PAYMENT_LINK), store, StuckLinkRzp())

    assert got.outcome is Outcome.FAILED_VERIFICATION
    assert got.outcome is not Outcome.RECOVERED
    assert got.verified is False
    # The action itself reported success — that is exactly the trap.
    assert got.result is not None and got.result.ok is True
    assert got.result.provider_ref.startswith("plink_")
    # The verdict rests on re-read provider state, quoted in the evidence.
    assert "status=created" in got.evidence
    assert "amount_paid=0" in got.evidence
    assert str(AMOUNT) in got.evidence
    # ...and no settlement row was written, so the money is not booked anywhere.
    assert store.settlements() == []
    assert got.seal_hash and seals(ledger)[-1].hash == got.seal_hash


def test_partially_paid_link_is_not_a_recovery(ledger, store):
    got = execute(payment(), plan(ActionKind.PAYMENT_LINK), store, ShortPaidLinkRzp())
    assert got.outcome is Outcome.FAILED_VERIFICATION
    assert f"amount_paid={AMOUNT - 1}" in got.evidence
    assert store.settlements() == []


def test_paid_link_is_recovered_and_settled(ledger, store):
    got = execute(payment(), plan(ActionKind.PAYMENT_LINK), store, PaidLinkRzp())

    assert got.outcome is Outcome.RECOVERED
    assert got.verified is True
    assert "status=paid" in got.evidence
    settled = store.settlements()
    assert len(settled) == 1
    assert settled[0][0] == "pay_A1" and settled[0][2] == AMOUNT


# --- retry: only a captured payment counts -------------------------------------------


def test_retry_is_recovered_only_when_the_payment_is_captured(ledger, store):
    got = execute(payment(), plan(ActionKind.RETRY), store, CapturedRzp())
    assert got.outcome is Outcome.RECOVERED
    assert "status=captured" in got.evidence


def test_retry_on_a_still_failed_payment_fails_verification(ledger, store):
    got = execute(payment(), plan(ActionKind.RETRY), store, StuckLinkRzp())
    assert got.outcome is Outcome.FAILED_VERIFICATION
    assert "status=failed" in got.evidence
    assert store.settlements() == []


# --- nudge and escalate verify the attempts row, and never book revenue ---------------


def test_nudge_verifies_the_attempts_row_and_is_not_a_recovery(ledger, store):
    got = execute(payment(), plan(ActionKind.NUDGE, cost=25), store, StuckLinkRzp())

    assert got.verified is True
    # The nudge provably happened; the customer provably did not pay. Booking outreach
    # as revenue is the fake-recovery bug this project exists to prevent.
    assert got.outcome is Outcome.UNRESOLVED
    assert got.outcome is not Outcome.RECOVERED
    assert "attempts" in got.evidence and "pay_A1" in got.evidence
    assert store.settlements() == []


def test_escalate_is_verified_but_never_recovered(ledger, store):
    got = execute(payment(), plan(ActionKind.ESCALATE, cost=1500), store, StuckLinkRzp())
    assert got.verified is True
    assert got.outcome is Outcome.UNRESOLVED
    assert store.settlements() == []


def test_outreach_with_no_row_written_fails_verification(ledger, tmp_path):
    silent = SilentStore(str(tmp_path / "silent.db"))
    try:
        got = execute(payment(), plan(ActionKind.NUDGE, cost=25), silent, StuckLinkRzp())
    finally:
        silent.close()
    assert got.outcome is Outcome.FAILED_VERIFICATION
    assert got.verified is False
    assert "no row in attempts" in got.evidence


def test_the_where_clause_names_the_kind_so_a_nudge_cannot_prove_an_escalation(
    ledger, store
):
    execute(payment(), plan(ActionKind.NUDGE, cost=25), store, StuckLinkRzp())
    got = execute(payment(), plan(ActionKind.ESCALATE, cost=1500), store, StuckLinkRzp())
    assert "kind = 'escalate'" in got.evidence


# --- Contract §5.8: no money action seal without an actor and an authorization --------


@pytest.mark.parametrize(
    "kind,cost",
    [
        (ActionKind.PAYMENT_LINK, 0),
        (ActionKind.RETRY, 0),
        (ActionKind.NUDGE, 25),
        (ActionKind.ESCALATE, 1500),
    ],
)
def test_every_seal_carries_an_actor_and_an_authorization(ledger, store, kind, cost):
    execute(payment(), plan(kind, cost=cost), store, StuckLinkRzp())
    seal = seals(ledger)[-1]
    assert seal.actor == ACTOR == "salvage-agent"
    assert seal.authorization
    assert kind.value in seal.authorization


# --- Contract §5.3: model prose is never evidence ------------------------------------


def test_narration_is_rejected_as_evidence_by_the_seal(ledger):
    """An LLM rationale passed off as evidence is flipped to unverified — asserted
    explicitly, because this is the guard that stops prose from booking revenue."""
    rationale = "I'll check whether the customer completed the payment link."
    assert stepproof.is_narration(rationale)

    @stepproof.verified(
        proves="link for {payment_id} is paid",
        verifier=lambda **kw: (True, rationale),
        actor=ACTOR,
        authorization="policy:payment_link cost=0p",
        raises=False,
    )
    def claim_recovered(payment_id: str) -> dict:
        return {"ok": True}

    claim_recovered(payment_id="pay_A1")
    seal = seals(ledger)[-1]
    assert seal.verified is False  # a True verdict, flipped by the narration guard
    assert rationale not in seal.evidence


@pytest.mark.parametrize(
    "kind,cost",
    [
        (ActionKind.PAYMENT_LINK, 0),
        (ActionKind.RETRY, 0),
        (ActionKind.NUDGE, 25),
        (ActionKind.ESCALATE, 1500),
    ],
)
def test_evidence_execute_produces_is_never_narration(ledger, store, kind, cost):
    got = execute(payment(), plan(kind, cost=cost), store, StuckLinkRzp())
    assert not stepproof.is_narration(got.evidence)
    assert len(got.evidence) <= 300  # Contract §5.4


# --- failure isolation ----------------------------------------------------------------


def test_an_action_that_raises_becomes_unresolved_not_recovered(ledger, store):
    got = execute(payment(), plan(ActionKind.PAYMENT_LINK), store, BoomRzp())
    assert got.outcome is Outcome.UNRESOLVED
    assert got.verified is False
    assert "FileNotFoundError" in got.evidence
    assert store.settlements() == []


def test_a_verifier_that_cannot_reach_the_provider_fails_verification(ledger, store):
    got = execute(payment(), plan(ActionKind.PAYMENT_LINK), store, LookupBoomRzp())
    assert got.outcome is Outcome.FAILED_VERIFICATION
    assert "ConnectionError" in got.evidence
    assert store.settlements() == []


def test_a_suppressed_plan_touches_no_rail_and_seals_nothing(ledger, store):
    suppressed = Intervention(
        payment_id="pay_A1",
        kind=ActionKind.NONE,
        reason="72h hold not yet cleared",
        cost_paise=0,
        suppressed_by="timing_window",
    )
    got = execute(payment(), suppressed, store, BoomRzp())

    assert got.outcome is Outcome.SUPPRESSED
    assert got.verified is None
    assert got.seal_hash == ""
    assert got.result is None
    assert "timing_window" in got.evidence
    assert seals(ledger) == []


# --- the ledger stays auditable across a mixed batch ---------------------------------


def test_the_chain_stays_intact_across_a_mixed_batch(ledger, store):
    outcomes = [
        execute(payment("pay_A1"), plan(ActionKind.PAYMENT_LINK), store, StuckLinkRzp()),
        execute(payment("pay_A2"), plan(ActionKind.PAYMENT_LINK), store, PaidLinkRzp()),
        execute(payment("pay_A3"), plan(ActionKind.RETRY), store, CapturedRzp()),
        execute(payment("pay_A4"), plan(ActionKind.NUDGE, 25), store, StuckLinkRzp()),
        execute(payment("pay_A5"), plan(ActionKind.PAYMENT_LINK), store, BoomRzp()),
    ]
    intact, detail = ledger.verify_chain()
    assert intact, detail
    assert len({o.seal_hash for o in outcomes}) == len(outcomes)  # no reused hashes
    assert [o.outcome for o in outcomes][:4] == [
        Outcome.FAILED_VERIFICATION,
        Outcome.RECOVERED,
        Outcome.RECOVERED,
        Outcome.UNRESOLVED,
    ]


# --- Contract §9.2: the agent lane never sees the labels it is scored against ---------


def test_the_agent_loop_never_touches_ground_truth():
    root = Path(__file__).resolve().parent.parent / "salvage"
    banned = ("GroundTruth", "truth.json", "would_self_heal", "true_reason")
    for name in ("policy.py", "execute.py", "pipeline.py"):
        source = (root / name).read_text(encoding="utf-8")
        for token in banned:
            assert token not in source, f"{name} references {token}"
