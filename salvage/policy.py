"""Timing-aware intervention policy: what to do, and — mostly — when not to.

Prevents the two ways an automated recovery agent ends up worse than doing nothing.
The first is acting at the wrong moment: re-presenting an `insufficient_funds` decline
an hour after it failed simply re-declines, burns an attempt, and trains the issuer to
distrust the merchant. The second is acting where compliance forbids it: a
`risk_blocked` payment must reach a human, never a retry loop.

Every refusal names the stopping rule that produced it in `Intervention.suppressed_by`,
so a record the agent declined to touch is auditable rather than merely absent.
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from salvage.metrics import COST_TABLE
from salvage.types import (
    ActionKind,
    FailedPayment,
    FailureReason,
    Intervention,
    RootCause,
)

if TYPE_CHECKING:  # imported for types only — no runtime dependency on either module
    from salvage.pipeline import PipelineConfig
    from salvage.store import Store

_HOUR = 3600.0
_DAY = 86400.0

# Contract §10.3: the published recovery window is 10-14 days. Past the far edge the
# customer has moved on and every further rupee spent chasing them is waste.
_WINDOW_S = 14 * _DAY

# Bank and gateway downtime clears in minutes, but re-presenting straight back into the
# same outage only burns an attempt out of a budget of three.
_BANK_DOWN_BACKOFF_S = 15 * 60.0

# A soft decline is a balance problem, not an instrument problem: repetition inside the
# hold re-declines. Day 3 and day 7 are when salary and top-ups have landed.
_FUNDS_HOLD_S = 72 * _HOUR

# ...and on the 1st and the 15th the money has demonstrably just arrived, so the hold
# opens a day early rather than waiting for a balance that is already there.
_FUNDS_PAYDAY_HOLD_S = 48 * _HOUR
_PAYDAYS = (1, 15)

# Checkout abandonment decays sharply; a reminder only lands while the intent is warm.
_NUDGE_WINDOW_S = 24 * _HOUR

# The instrument or the authentication is dead, so no retry can revive it — the
# customer has to come back through a rail they can authenticate on.
_LINK_REASON = {
    FailureReason.AUTH_FAILED:
        "auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP",
    FailureReason.CARD_EXPIRED:
        "card_expired: the instrument is dead, only a fresh link can collect",
    FailureReason.MANDATE_EXPIRED:
        "mandate_expired: the mandate cannot be re-presented, only re-authorised",
    FailureReason.UNKNOWN:
        "unknown decline: a link is the zero-cost rail that cannot re-present a blocked card",
}


def decide(
    p: FailedPayment,
    cause: RootCause,
    store: Store,
    cfg: PipelineConfig,
    now: float,
) -> Intervention:
    """Choose one intervention for one payment, or decline and say which rule declined.

    Five stopping rules, checked in a fixed order — settled, attempts, cost, timing,
    quiet hours — because the order is what makes a suppression explainable: the first
    rule that fires is the one reported.

    `already_settled` is first and is not negotiable. Every other rule is a budget; this
    one is a safety property. Charging a customer who has already paid is the worst thing
    a recovery agent can do, and it is the failure mode a rerun produces by default.
    """
    kind, in_window, why = _plan(cause.reason, now - p.failed_at, now)
    cost = COST_TABLE[kind]

    # FIRST, before anything else. A customer who has already paid must never be charged
    # again, and no attempt budget, cost cap or timing window is a reason to reconsider
    # that. Everything downstream assumes this has already been ruled out.
    if store.is_settled(p.payment_id):
        return _declined(
            p, "already_settled",
            f"{p.payment_id} already has a settlement row; money arrived, nothing to recover",
        )

    attempts = store.attempts_for(p.payment_id)
    if attempts >= cfg.max_attempts:
        return _declined(
            p, "max_attempts",
            f"{attempts} attempts already made on {p.payment_id}, budget is {cfg.max_attempts}",
        )

    spend = store.spend_for(p.payment_id)
    if spend + cost > cfg.cost_cap_paise:
        return _declined(
            p, "cost_cap",
            f"{spend}p spent + {cost}p for {kind.value} exceeds cap {cfg.cost_cap_paise}p",
        )

    if not in_window:
        return _declined(p, "timing_window", why)

    if kind is ActionKind.NUDGE and _in_quiet_hours(now, cfg.quiet_hours):
        start, end = cfg.quiet_hours
        return _declined(
            p, "quiet_hours",
            f"local hour {time.localtime(now).tm_hour} falls inside quiet hours {start}-{end}",
        )

    return Intervention(payment_id=p.payment_id, kind=kind, reason=why, cost_paise=cost)


def _declined(p: FailedPayment, rule: str, detail: str) -> Intervention:
    return Intervention(
        payment_id=p.payment_id,
        kind=ActionKind.NONE,
        reason=detail,
        cost_paise=COST_TABLE[ActionKind.NONE],
        suppressed_by=rule,
    )


def _plan(
    reason: FailureReason, elapsed: float, now: float
) -> tuple[ActionKind, bool, str]:
    """Map a root cause to (action, is the timing window open, why).

    The action is returned even when the window is shut, because the cost-cap rule is
    checked first and needs to know what the action would have cost.
    """
    if reason is FailureReason.RISK_BLOCKED:
        # Never an automated retry, and never expires either: a blocked payment is a
        # compliance event, and the only compliant move is to put it in front of a
        # human however old it is.
        return (
            ActionKind.ESCALATE,
            True,
            "risk_blocked: compliance escalation to a human, never an automated retry",
        )

    cold = elapsed > _WINDOW_S
    stale = f"{_fmt(elapsed)} since failure is past the {_fmt(_WINDOW_S)} recovery window"

    if reason is FailureReason.BANK_DOWN:
        if cold:
            return ActionKind.RETRY, False, stale
        if elapsed < _BANK_DOWN_BACKOFF_S:
            return (
                ActionKind.RETRY,
                False,
                f"bank_down backoff: {_fmt(elapsed)} elapsed, retry opens at "
                f"{_fmt(_BANK_DOWN_BACKOFF_S)}",
            )
        return (
            ActionKind.RETRY,
            True,
            f"bank_down is transient: re-present the same instrument at {_fmt(elapsed)}",
        )

    if reason is FailureReason.INSUFFICIENT_FUNDS:
        if cold:
            return ActionKind.RETRY, False, stale
        hold = _funds_hold(now)
        if elapsed < hold:
            return (
                ActionKind.RETRY,
                False,
                f"insufficient_funds hold: {_fmt(elapsed)} elapsed, retry opens at "
                f"{_fmt(hold)}",
            )
        return (
            ActionKind.RETRY,
            True,
            f"insufficient_funds held {_fmt(hold)}, re-presenting at {_fmt(elapsed)}",
        )

    if reason is FailureReason.CHECKOUT_DROPOFF:
        if cold:
            return ActionKind.PAYMENT_LINK, False, stale
        if elapsed <= _NUDGE_WINDOW_S:
            return (
                ActionKind.NUDGE,
                True,
                f"checkout_dropoff {_fmt(elapsed)} old: remind while the intent is warm",
            )
        return (
            ActionKind.PAYMENT_LINK,
            True,
            f"checkout_dropoff {_fmt(elapsed)} old: past nudging, issue a fresh link",
        )

    if cold:
        return ActionKind.PAYMENT_LINK, False, stale
    return ActionKind.PAYMENT_LINK, True, _LINK_REASON.get(
        reason, f"{reason.value}: a fresh link is the safe default"
    )


def _funds_hold(now: float) -> float:
    if time.localtime(now).tm_mday in _PAYDAYS:
        return _FUNDS_PAYDAY_HOLD_S
    return _FUNDS_HOLD_S


def _in_quiet_hours(now: float, quiet_hours: tuple[int, int]) -> bool:
    start, end = quiet_hours
    if start == end:
        return False
    hour = time.localtime(now).tm_hour
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end  # the window wraps midnight, e.g. (22, 8)


def _fmt(seconds: float) -> str:
    """Durations read as durations in evidence and audit trails, never as raw seconds."""
    if abs(seconds) < _HOUR:
        return f"{seconds / 60:.0f}m"
    if abs(seconds) < _DAY:
        return f"{seconds / _HOUR:.0f}h"
    return f"{seconds / _DAY:.1f}d"
