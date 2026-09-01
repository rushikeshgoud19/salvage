"""Policy tests: every stopping rule is proven by a pair, and timing is proven by a pair.

Each stopping rule gets two records that differ only in the input that rule reads, so a
rule that stopped working would let the second record act and fail the test — a single
"it was suppressed" assertion proves nothing about which rule did the suppressing.
"""
from __future__ import annotations

import dataclasses
import time

import pytest

from salvage.pipeline import PipelineConfig
from salvage.policy import decide
from salvage.types import ActionKind, FailedPayment, FailureReason, Intervention, RootCause

HOUR = 3600.0
DAY = 86400.0


class FakeStore:
    """Only the two reads `decide` makes. Attempts and spend are the inputs to two of
    the four stopping rules, so the test drives them directly."""

    def __init__(self, attempts: int = 0, spend: int = 0) -> None:
        self._attempts = attempts
        self._spend = spend

    def attempts_for(self, payment_id: str) -> int:
        return self._attempts

    def spend_for(self, payment_id: str) -> int:
        return self._spend


def at(year: int, month: int, day: int, hour: int = 12) -> float:
    """A local-time instant. Built through mktime so quiet-hours and payday assertions
    do not change meaning on a machine in another timezone."""
    return time.mktime((year, month, day, hour, 0, 0, 0, 0, -1))


NOW = at(2026, 9, 10, 12)  # a plain weekday noon: not payday, not quiet hours


def payment(**over) -> FailedPayment:
    fields = dict(
        payment_id="pay_A1",
        order_id="order_A1",
        customer_id="cust_A1",
        amount_paise=45000,
        currency="INR",
        method="card",
        failed_at=NOW - 2 * HOUR,
        gateway_code="insufficient_funds",
        gateway_description="Insufficient balance in the account",
        source="customer",
        attempt_no=1,
        customer_email="cust0001@example.invalid",
        customer_phone="+919000000001",
    )
    fields.update(over)
    return FailedPayment(**fields)


def cause(reason: FailureReason) -> RootCause:
    return RootCause(payment_id="pay_A1", reason=reason, confidence=0.9, rationale="")


def plan_for(
    reason: FailureReason,
    elapsed: float,
    *,
    now: float = NOW,
    store: FakeStore | None = None,
    cfg: PipelineConfig | None = None,
) -> Intervention:
    p = payment(failed_at=now - elapsed)
    return decide(p, cause(reason), store or FakeStore(), cfg or PipelineConfig(), now)


# --- Contract §3: the harness constructs PipelineConfig, so its shape is contract ----


def test_pipeline_config_has_exactly_the_seven_contract_fields():
    fields = {f.name: f.default for f in dataclasses.fields(PipelineConfig)}
    assert fields == {
        "db_path": "run/salvage.db",
        "ledger_path": "run/ledger.jsonl",
        "offline": True,
        "max_attempts": 3,
        "cost_cap_paise": 2000,
        "quiet_hours": (22, 8),
        "seed": 7,
    }


# --- Contract §10.3: timing is the policy -------------------------------------------


def test_insufficient_funds_at_one_hour_is_suppressed_by_timing():
    got = plan_for(FailureReason.INSUFFICIENT_FUNDS, 1 * HOUR)
    assert got.kind is ActionKind.NONE
    assert got.suppressed_by == "timing_window"
    # the reason names the hold this record has not yet cleared
    assert "retry opens at 3.0d" in got.reason


def test_insufficient_funds_at_seventy_three_hours_retries():
    got = plan_for(FailureReason.INSUFFICIENT_FUNDS, 73 * HOUR)
    assert got.kind is ActionKind.RETRY
    assert got.suppressed_by == ""


def test_payday_shortens_the_insufficient_funds_hold():
    """Same record, same elapsed time, different day of month — the 15th pays out."""
    payday = at(2026, 9, 15, 12)
    ordinary = at(2026, 9, 10, 12)
    assert plan_for(FailureReason.INSUFFICIENT_FUNDS, 50 * HOUR, now=payday).kind is (
        ActionKind.RETRY
    )
    assert plan_for(FailureReason.INSUFFICIENT_FUNDS, 50 * HOUR, now=ordinary).kind is (
        ActionKind.NONE
    )


def test_bank_down_waits_out_a_short_backoff_then_retries():
    early = plan_for(FailureReason.BANK_DOWN, 60.0)
    assert early.kind is ActionKind.NONE and early.suppressed_by == "timing_window"
    assert plan_for(FailureReason.BANK_DOWN, 30 * 60.0).kind is ActionKind.RETRY


def test_auth_failed_gets_a_payment_link_never_a_silent_retry():
    got = plan_for(FailureReason.AUTH_FAILED, 2 * HOUR)
    assert got.kind is ActionKind.PAYMENT_LINK
    assert "re-authenticate" in got.reason


@pytest.mark.parametrize(
    "reason", [FailureReason.CARD_EXPIRED, FailureReason.MANDATE_EXPIRED]
)
def test_dead_instruments_get_a_payment_link(reason):
    assert plan_for(reason, 6 * HOUR).kind is ActionKind.PAYMENT_LINK


def test_checkout_dropoff_nudges_inside_twenty_four_hours():
    assert plan_for(FailureReason.CHECKOUT_DROPOFF, 3 * HOUR).kind is ActionKind.NUDGE


def test_checkout_dropoff_switches_to_a_link_after_twenty_four_hours():
    assert plan_for(FailureReason.CHECKOUT_DROPOFF, 40 * HOUR).kind is (
        ActionKind.PAYMENT_LINK
    )


def test_checkout_dropoff_is_dead_after_fourteen_days():
    got = plan_for(FailureReason.CHECKOUT_DROPOFF, 15 * DAY)
    assert got.kind is ActionKind.NONE
    assert got.suppressed_by == "timing_window"


# --- Contract §10.3: risk_blocked is a compliance escalation, never a retry ----------


@pytest.mark.parametrize("elapsed", [0.0, 1 * HOUR, 73 * HOUR, 15 * DAY, 400 * DAY])
@pytest.mark.parametrize("method", ["card", "upi", "netbanking", "wallet", "emi"])
def test_risk_blocked_never_yields_a_retry(elapsed, method):
    p = payment(failed_at=NOW - elapsed, method=method, gateway_code="payment_risk_check_failed")
    got = decide(p, cause(FailureReason.RISK_BLOCKED), FakeStore(), PipelineConfig(), NOW)
    assert got.kind is ActionKind.ESCALATE
    assert got.kind is not ActionKind.RETRY


def test_risk_blocked_escalates_even_when_the_record_is_cold():
    assert plan_for(FailureReason.RISK_BLOCKED, 60 * DAY).kind is ActionKind.ESCALATE


# --- the four stopping rules, each proven against a control that acts ----------------


def test_max_attempts_stops_and_one_fewer_attempt_does_not():
    cfg = PipelineConfig()
    stopped = plan_for(FailureReason.BANK_DOWN, 2 * HOUR, store=FakeStore(attempts=3), cfg=cfg)
    acting = plan_for(FailureReason.BANK_DOWN, 2 * HOUR, store=FakeStore(attempts=2), cfg=cfg)
    assert stopped.kind is ActionKind.NONE and stopped.suppressed_by == "max_attempts"
    assert acting.kind is ActionKind.RETRY


def test_cost_cap_stops_an_escalation_that_would_cross_the_cap():
    cfg = PipelineConfig(cost_cap_paise=2000)
    stopped = plan_for(
        FailureReason.RISK_BLOCKED, 2 * HOUR, store=FakeStore(spend=600), cfg=cfg
    )
    acting = plan_for(
        FailureReason.RISK_BLOCKED, 2 * HOUR, store=FakeStore(spend=400), cfg=cfg
    )
    assert stopped.kind is ActionKind.NONE and stopped.suppressed_by == "cost_cap"
    assert acting.kind is ActionKind.ESCALATE


def test_quiet_hours_stops_a_nudge_that_noon_would_allow():
    night = at(2026, 9, 10, 23)
    noon = at(2026, 9, 10, 12)
    stopped = plan_for(FailureReason.CHECKOUT_DROPOFF, 3 * HOUR, now=night)
    acting = plan_for(FailureReason.CHECKOUT_DROPOFF, 3 * HOUR, now=noon)
    assert stopped.kind is ActionKind.NONE and stopped.suppressed_by == "quiet_hours"
    assert acting.kind is ActionKind.NUDGE


def test_quiet_hours_do_not_stop_a_payment_link():
    """Quiet hours are about waking a customer up, not about issuing a link."""
    night = at(2026, 9, 10, 23)
    assert plan_for(FailureReason.AUTH_FAILED, 3 * HOUR, now=night).kind is (
        ActionKind.PAYMENT_LINK
    )


def test_stopping_rules_are_checked_in_the_contracted_order():
    """A record that trips attempts, cost and timing at once reports attempts."""
    cfg = PipelineConfig(max_attempts=1, cost_cap_paise=0)
    got = plan_for(
        FailureReason.INSUFFICIENT_FUNDS, 1 * HOUR, store=FakeStore(attempts=5, spend=9000), cfg=cfg
    )
    assert got.suppressed_by == "max_attempts"

    # ...and with the attempts rule satisfied, cost is reported before timing.
    got = plan_for(
        FailureReason.CHECKOUT_DROPOFF, 30 * DAY, store=FakeStore(spend=1999), cfg=PipelineConfig()
    )
    assert got.suppressed_by == "timing_window"  # a link costs 0, so cost cannot fire
    got = plan_for(
        FailureReason.RISK_BLOCKED, 30 * DAY, store=FakeStore(spend=1999), cfg=PipelineConfig()
    )
    assert got.suppressed_by == "cost_cap"


# --- invariants ---------------------------------------------------------------------


ALL_REASONS = list(FailureReason)
ELAPSED_GRID = [0.0, 1 * HOUR, 20 * HOUR, 73 * HOUR, 8 * DAY, 30 * DAY]


@pytest.mark.parametrize("reason", ALL_REASONS)
@pytest.mark.parametrize("elapsed", ELAPSED_GRID)
@pytest.mark.parametrize("hour", [3, 12, 23])
def test_suppressed_by_is_non_empty_exactly_when_the_kind_is_none(reason, elapsed, hour):
    now = at(2026, 9, 10, hour)
    got = plan_for(reason, elapsed, now=now)
    assert (got.kind is ActionKind.NONE) == bool(got.suppressed_by)


@pytest.mark.parametrize("reason", ALL_REASONS)
@pytest.mark.parametrize("elapsed", ELAPSED_GRID)
def test_cost_is_an_integer_from_the_cost_table(reason, elapsed):
    from salvage.metrics import COST_TABLE

    got = plan_for(reason, elapsed)
    assert isinstance(got.cost_paise, int)
    assert got.cost_paise == COST_TABLE[got.kind]


@pytest.mark.parametrize("reason", ALL_REASONS)
def test_decide_never_returns_an_unmapped_kind(reason):
    got = plan_for(reason, 2 * HOUR)
    assert got.kind in set(ActionKind)
    assert got.payment_id == "pay_A1"
    assert got.reason  # a decision that cannot explain itself is not auditable
