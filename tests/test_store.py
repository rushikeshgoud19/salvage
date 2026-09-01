"""A1 + A2: the lane's two I/O boundaries.

`Store` (A1) and `RzpClient` (A2) are tested together because `tests/test_rzp.py` is not in
the PLAN lane-ownership table and this lane may not create files outside it. The two share
one subject anyway: the boundary where a claim ("I issued a link") must not be allowed to
become a fact ("money arrived").
"""
from __future__ import annotations

import sqlite3

import httpx
import pytest

from salvage.rzp import RzpClient, _is_stuck, _link_id
from salvage.store import Store
from salvage.types import ActionKind, FailedPayment

FIXTURES = "fixtures"


def make_payment(payment_id: str = "pay_0001", amount_paise: int = 45000) -> FailedPayment:
    return FailedPayment(
        payment_id=payment_id,
        order_id="order_0001",
        customer_id="cust_0001",
        amount_paise=amount_paise,
        currency="INR",
        method="card",
        failed_at=1756684800.0,
        gateway_code="insufficient_funds",
        gateway_description="Your payment did not go through as your account does not "
                            "have sufficient funds.",
        source="customer",
        attempt_no=1,
        customer_email="cust0001@example.invalid",
        customer_phone="+919000000001",
    )


# -- A1: the system of record ------------------------------------------------------------


def test_schema_matches_contract_section_8(tmp_path):
    store = Store(str(tmp_path / "salvage.db"))
    db = sqlite3.connect(str(tmp_path / "salvage.db"))
    columns = {
        table: [(row[1], row[2]) for row in db.execute(f"PRAGMA table_info({table})")]
        for table in ("payments", "attempts", "settlements")
    }
    db.close()
    store.close()

    assert columns["payments"] == [
        ("payment_id", "TEXT"), ("order_id", "TEXT"), ("customer_id", "TEXT"),
        ("amount_paise", "INTEGER"), ("failed_at", "REAL"), ("gateway_code", "TEXT"),
    ]
    assert columns["attempts"] == [
        ("id", "INTEGER"), ("payment_id", "TEXT"), ("kind", "TEXT"),
        ("provider_ref", "TEXT"), ("cost_paise", "INTEGER"), ("created_at", "REAL"),
    ]
    assert columns["settlements"] == [
        ("payment_id", "TEXT"), ("provider_ref", "TEXT"),
        ("amount_paise", "INTEGER"), ("settled_at", "REAL"),
    ]


def test_attempts_and_spend_accumulate_across_three_attempts(tmp_path):
    store = Store(str(tmp_path / "salvage.db"))
    payment = make_payment()
    store.upsert_payment(payment)

    first = store.record_attempt(payment.payment_id, ActionKind.NUDGE, "", 25)
    second = store.record_attempt(payment.payment_id, ActionKind.PAYMENT_LINK, "plink_a", 0)
    third = store.record_attempt(payment.payment_id, ActionKind.ESCALATE, "", 1500)

    assert {first, second, third} == {1, 2, 3}
    assert store.attempts_for(payment.payment_id) == 3
    assert store.spend_for(payment.payment_id) == 1525
    assert store.attempts_for("pay_absent") == 0
    assert store.spend_for("pay_absent") == 0
    store.close()


def test_rows_survive_reopening_the_same_path(tmp_path):
    path = str(tmp_path / "salvage.db")
    store = Store(path)
    payment = make_payment()
    store.upsert_payment(payment)
    store.record_attempt(payment.payment_id, ActionKind.RETRY, "pay_x", 0)
    store.mark_settled(payment.payment_id, "plink_a", payment.amount_paise)
    store.close()

    reopened = Store(path)
    assert reopened.attempts_for(payment.payment_id) == 1
    row = reopened._db.execute(
        "SELECT provider_ref, amount_paise FROM settlements WHERE payment_id = ?",
        (payment.payment_id,),
    ).fetchone()
    assert (row["provider_ref"], row["amount_paise"]) == ("plink_a", 45000)
    reopened.close()


def test_upsert_is_idempotent_and_updates_in_place(tmp_path):
    store = Store(str(tmp_path / "salvage.db"))
    store.upsert_payment(make_payment(amount_paise=45000))
    store.upsert_payment(make_payment(amount_paise=99000))
    rows = store._db.execute("SELECT amount_paise FROM payments").fetchall()
    assert [row["amount_paise"] for row in rows] == [99000]
    store.close()


def test_an_attempt_alone_never_writes_a_settlement(tmp_path):
    """The project's thesis at the storage layer: issuing a link is not being paid."""
    store = Store(str(tmp_path / "salvage.db"))
    payment = make_payment()
    store.upsert_payment(payment)
    store.record_attempt(payment.payment_id, ActionKind.PAYMENT_LINK, "plink_a", 0)

    settlements = store._db.execute("SELECT COUNT(*) AS n FROM settlements").fetchone()
    assert settlements["n"] == 0
    store.close()


def test_settlement_without_a_provider_reference_is_refused(tmp_path):
    store = Store(str(tmp_path / "salvage.db"))
    payment = make_payment()
    store.upsert_payment(payment)

    with pytest.raises(ValueError, match="provider_ref is empty"):
        store.mark_settled(payment.payment_id, "", payment.amount_paise)

    settlements = store._db.execute("SELECT COUNT(*) AS n FROM settlements").fetchone()
    assert settlements["n"] == 0
    store.close()


@pytest.mark.parametrize("amount", [0, -1])
def test_settlement_of_a_non_positive_amount_is_refused(tmp_path, amount):
    store = Store(str(tmp_path / "salvage.db"))
    store.upsert_payment(make_payment())
    with pytest.raises(ValueError, match="expected a positive integer"):
        store.mark_settled("pay_0001", "plink_a", amount)
    store.close()


@pytest.mark.parametrize("amount", [450.0, "45000", True])
def test_money_that_is_not_integer_paise_is_refused(tmp_path, amount):
    store = Store(str(tmp_path / "salvage.db"))
    store.upsert_payment(make_payment())
    with pytest.raises(TypeError, match="integer paise"):
        store.mark_settled("pay_0001", "plink_a", amount)
    with pytest.raises(TypeError, match="integer paise"):
        store.record_attempt("pay_0001", ActionKind.NUDGE, "", amount)
    store.close()


# -- A2: the Razorpay boundary -----------------------------------------------------------


def test_offline_client_opens_no_socket(monkeypatch):
    """Contract §9.8: offline=True performs zero network calls."""
    def explode(*args, **kwargs):
        raise AssertionError("offline mode constructed an httpx.Client")

    monkeypatch.setattr(httpx, "Client", explode)

    rzp = RzpClient(offline=True, fixtures_dir=FIXTURES)
    created = rzp.create_payment_link("pay_0001", 45000, "cust0001@example.invalid")
    rzp.fetch_payment_link(created["id"])
    rzp.fetch_payment("pay_0001")
    rzp.close()


def test_online_without_keys_raises_naming_the_missing_variable(monkeypatch):
    monkeypatch.delenv("RAZORPAY_KEY_ID", raising=False)
    monkeypatch.delenv("RAZORPAY_KEY_SECRET", raising=False)
    with pytest.raises(RuntimeError) as excinfo:
        RzpClient(offline=False, fixtures_dir=FIXTURES)
    message = str(excinfo.value)
    assert "RAZORPAY_KEY_ID" in message
    assert "RAZORPAY_KEY_SECRET" in message


def test_online_names_only_the_variable_that_is_missing(monkeypatch):
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_dummy")
    monkeypatch.delenv("RAZORPAY_KEY_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="RAZORPAY_KEY_SECRET"):
        RzpClient(offline=False, fixtures_dir=FIXTURES)


def test_create_returns_a_link_that_has_not_been_paid():
    """A well-formed create is an action, not money: amount_paid is 0 on every one."""
    rzp = RzpClient(fixtures_dir=FIXTURES)
    body = rzp.create_payment_link("pay_0001", 123400, "cust0001@example.invalid")
    assert body["id"].startswith("plink_")
    assert body["status"] == "created"
    assert body["amount"] == 123400 and isinstance(body["amount"], int)
    assert body["amount_paid"] == 0
    assert body["short_url"].startswith("https://rzp.io/i/")


def test_create_rejects_float_money():
    rzp = RzpClient(fixtures_dir=FIXTURES)
    with pytest.raises(TypeError, match="integer paise"):
        rzp.create_payment_link("pay_0001", 1234.0, "cust0001@example.invalid")


def _ids(n: int) -> list[str]:
    return [f"pay_{i:06d}" for i in range(n)]


def test_engineered_cohort_returns_a_201_and_then_never_pays():
    """The demo moment: create succeeds, and every later fetch says created / 0."""
    rzp = RzpClient(fixtures_dir=FIXTURES)
    stuck = next(pid for pid in _ids(500) if _is_stuck(_link_id(pid)))

    created = rzp.create_payment_link(stuck, 45000, "cust@example.invalid")
    assert created["status"] == "created" and created["id"].startswith("plink_")

    for _ in range(3):
        fetched = rzp.fetch_payment_link(created["id"])
        assert fetched["status"] == "created"
        assert fetched["amount_paid"] == 0
        assert fetched["amount"] == 45000


def test_a_paying_link_reports_the_full_amount():
    rzp = RzpClient(fixtures_dir=FIXTURES)
    payer = next(
        pid for pid in _ids(500)
        if not _is_stuck(_link_id(pid))
        and rzp.fetch_payment_link(
            rzp.create_payment_link(pid, 45000, "cust@example.invalid")["id"]
        )["status"] == "paid"
    )
    body = rzp.fetch_payment_link(_link_id(payer))
    assert body["status"] == "paid"
    assert body["amount_paid"] == body["amount"] == 45000


def test_cohort_is_deterministic_and_the_right_size():
    """Same batch, same cohort — on every run, in any order, from any client instance."""
    first = {pid for pid in _ids(240) if _is_stuck(_link_id(pid))}
    second = {pid for pid in _ids(240)[::-1] if _is_stuck(_link_id(pid))}
    assert first == second
    # 12% of issued links. Roughly half a 240-record batch earns a link, so this lands the
    # ~8-record demo cohort; over all 240 ids the count is about double that. Raised from 6%
    # at integration: at 6% only 4 records actually surfaced as stuck in a full run, which is
    # too thin to carry the failure segment of the pitch.
    assert 20 <= len(first) <= 55


def test_fetching_a_link_this_client_never_issued_says_so():
    rzp = RzpClient(fixtures_dir=FIXTURES)
    with pytest.raises(LookupError, match="no recorded create"):
        rzp.fetch_payment_link("plink_neverissued")


def test_fetch_payment_reports_a_real_status():
    rzp = RzpClient(fixtures_dir=FIXTURES)
    statuses = {rzp.fetch_payment(pid)["status"] for pid in _ids(50)}
    assert statuses <= {"captured", "failed"}
    assert len(statuses) == 2  # both fates occur, so a verifier is actually exercised
    assert rzp.fetch_payment("pay_000001")["status"] == rzp.fetch_payment("pay_000001")["status"]
