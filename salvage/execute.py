"""stepproof-gated execution: the claim and the verdict are never the same thing.

Prevents the failure this whole project exists to catch — a `201 Created` from a
payment-link call being booked as recovered revenue. Every action here is sealed by
stepproof, and the verdict comes from re-reading provider or database state *after*
the action, never from the action's own return value. A link that was created and
never paid comes back `status=created amount_paid=0` and is routed to
FAILED_VERIFICATION with that observation as its evidence.

Three rules from Contract §5 are load-bearing and easy to break by accident:
every verifier takes `**kwargs` (§5.1), evidence is composed from observed values and
never from model prose (§5.3), and the batch path uses `raises=False` so one
unverifiable record cannot kill the run (§5.7).
"""
from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Any, Callable

import stepproof
from stepproof import Seal, sqlite_row_exists, verified

from salvage.types import (
    ActionKind,
    ActionResult,
    FailedPayment,
    Intervention,
    Outcome,
    RecoveryOutcome,
)

if TYPE_CHECKING:  # imported for types only — no runtime dependency on either module
    from salvage.rzp import RzpClient
    from salvage.store import Store

ACTOR = "salvage-agent"

# Only these two actually move money on a rail we can observe. A nudge or an
# escalation can be proven to have happened, but proving it happened is not proving
# the customer paid — booking those as recovered is the fake-revenue bug itself.
_MONEY_ARRIVAL = (ActionKind.RETRY, ActionKind.PAYMENT_LINK)


def execute(
    p: FailedPayment,
    plan: Intervention,
    store: Store,
    rzp: RzpClient,
) -> RecoveryOutcome:
    """Carry out one intervention and return the verdict stepproof sealed for it."""
    if plan.kind is ActionKind.NONE:
        return _no_action(p, plan, store)

    observed: dict[str, Any] = {"provider_ref": ""}

    try:
        act = _build_action(p, plan, store, rzp, observed)
    except Exception as exc:  # nothing was sealed yet, so there is no hash to carry
        return _blew_up(p, plan, store, observed, exc, seal_hash="")

    try:
        claim = act(payment_id=p.payment_id, amount_paise=p.amount_paise)
    except Exception as exc:
        # stepproof seals the attempt before re-raising, so the tail seal is this
        # record's and the failure stays on the audit chain.
        tail = _last_seal()
        return _blew_up(
            p, plan, store, observed, exc,
            seal_hash=tail.hash if tail is not None else "",
        )

    seal = _last_seal()
    # No seal means nothing independent looked at this action, and an action nobody
    # checked is not a recovery.
    is_verified = bool(seal.verified) if seal is not None else False
    evidence = (
        seal.evidence
        if seal is not None
        else f"no stepproof seal was appended for {plan.kind.value} on {p.payment_id}"
    )

    ref = str(observed["provider_ref"])
    notes: list[str] = []

    if plan.kind in _MONEY_ARRIVAL and is_verified:
        outcome = Outcome.RECOVERED
        try:
            # Contract §8: the settlement row is written only once the provider has
            # confirmed the money arrived. Writing it on a 201 would defeat the project.
            store.mark_settled(p.payment_id, ref, p.amount_paise)
        except Exception as exc:
            notes.append(f"settlement row not written: {type(exc).__name__}: {exc}")
    elif is_verified:
        outcome = Outcome.UNRESOLVED  # the outreach really happened; the money did not
    else:
        outcome = Outcome.FAILED_VERIFICATION

    return RecoveryOutcome(
        payment_id=p.payment_id,
        amount_paise=p.amount_paise,
        outcome=outcome,
        cause=None,  # the pipeline attaches the root cause it classified
        intervention=plan,
        result=ActionResult(
            payment_id=p.payment_id,
            kind=plan.kind,
            ok=True,
            provider_ref=ref,
            detail=str(claim)[:200],
        ),
        verified=is_verified,
        evidence=evidence,
        seal_hash=seal.hash if seal is not None else "",
        attempts=_attempts(store, p.payment_id),
        notes=notes,
    )


def _build_action(
    p: FailedPayment,
    plan: Intervention,
    store: Store,
    rzp: RzpClient,
    observed: dict[str, Any],
) -> Callable[..., dict]:
    if plan.kind is ActionKind.PAYMENT_LINK:
        return _payment_link_action(p, plan, store, rzp, observed)
    if plan.kind is ActionKind.RETRY:
        return _retry_action(p, plan, store, rzp, observed)
    return _outreach_action(p, plan, store, observed)


def _payment_link_action(p, plan, store, rzp, observed) -> Callable[..., dict]:
    def _verify_link_paid(**kw) -> tuple[bool, str]:
        # Contract §5.1: `**kw` or stepproof calls this with zero arguments.
        link_id = str(observed["provider_ref"])
        if not link_id:
            return False, f"rzp create_payment_link for {p.payment_id} returned no link id"
        try:
            link = rzp.fetch_payment_link(link_id)
        except Exception as exc:
            # A verifier that raises kills the batch, so a failed lookup is evidence
            # of non-recovery rather than an exception.
            return False, (
                f"rzp fetch_payment_link {link_id} raised {type(exc).__name__}: {exc}"
            )
        status = str(link.get("status", ""))
        paid = int(link.get("amount_paid", 0) or 0)
        return (
            status == "paid" and paid >= p.amount_paise,
            f"rzp {link_id} status={status} amount_paid={paid} "
            f"expected>={p.amount_paise} for {p.payment_id}",
        )

    @verified(
        proves="payment link for {payment_id} is paid in full",
        verifier=_verify_link_paid,
        actor=ACTOR,
        authorization=_authorization(plan),
        raises=False,
    )
    def issue_payment_link(payment_id: str, amount_paise: int) -> dict:
        link = rzp.create_payment_link(payment_id, amount_paise, p.customer_email)
        observed["provider_ref"] = str(link.get("id", ""))
        store.record_attempt(
            payment_id, ActionKind.PAYMENT_LINK, observed["provider_ref"], plan.cost_paise
        )
        return {
            "link_id": observed["provider_ref"],
            "create_status": str(link.get("status", "")),
        }

    return issue_payment_link


def _retry_action(p, plan, store, rzp, observed) -> Callable[..., dict]:
    def _verify_payment_captured(**kw) -> tuple[bool, str]:
        try:
            payment = rzp.fetch_payment(p.payment_id)
        except Exception as exc:
            return False, (
                f"rzp fetch_payment {p.payment_id} raised {type(exc).__name__}: {exc}"
            )
        status = str(payment.get("status", ""))
        amount = int(payment.get("amount", 0) or 0)
        return (
            status == "captured" and amount >= p.amount_paise,
            f"rzp {p.payment_id} status={status} amount={amount} "
            f"expected status=captured amount>={p.amount_paise}",
        )

    @verified(
        proves="retry of {payment_id} is captured at the gateway",
        verifier=_verify_payment_captured,
        actor=ACTOR,
        authorization=_authorization(plan),
        raises=False,
    )
    def retry_payment(payment_id: str, amount_paise: int) -> dict:
        observed["provider_ref"] = payment_id  # the same instrument, re-presented
        store.record_attempt(payment_id, ActionKind.RETRY, payment_id, plan.cost_paise)
        return {"re_presented": payment_id, "amount_paise": amount_paise}

    return retry_payment


def _outreach_action(p, plan, store, observed) -> Callable[..., dict]:
    """NUDGE and ESCALATE: no rail, so the provable effect is the attempts row itself."""
    db = _db_path(store)
    # Contract §5.9: `sqlite_row_exists` interpolates `where` verbatim, so every value
    # in it is a typed Python value from our own records — an id we generated and an
    # enum member. Nothing derived from a model reaches this string.
    where = (
        f"payment_id = {_sql_literal(p.payment_id)} "
        f"AND kind = {_sql_literal(plan.kind.value)}"
    )

    def _verify_attempt_row(**kw) -> tuple[bool, str]:
        try:
            return sqlite_row_exists(db, "attempts", where)
        except Exception as exc:
            return False, f"sqlite attempts lookup raised {type(exc).__name__}: {exc}"

    @verified(
        proves="{payment_id} has a recorded outreach attempt",
        verifier=_verify_attempt_row,
        actor=ACTOR,
        authorization=_authorization(plan),
        raises=False,
    )
    def send_outreach(payment_id: str, amount_paise: int) -> dict:
        store.record_attempt(payment_id, plan.kind, "", plan.cost_paise)
        return {"channel": plan.kind.value, "payment_id": payment_id}

    return send_outreach


def _no_action(p: FailedPayment, plan: Intervention, store: Store) -> RecoveryOutcome:
    return RecoveryOutcome(
        payment_id=p.payment_id,
        amount_paise=p.amount_paise,
        outcome=Outcome.SUPPRESSED,
        cause=None,
        intervention=plan,
        result=None,
        verified=None,
        evidence=f"no rail used for {p.payment_id}: {plan.suppressed_by} ({plan.reason})",
        seal_hash="",
        attempts=_attempts(store, p.payment_id),
    )


def _blew_up(p, plan, store, observed, exc: Exception, seal_hash: str) -> RecoveryOutcome:
    detail = f"{type(exc).__name__}: {exc}"
    return RecoveryOutcome(
        payment_id=p.payment_id,
        amount_paise=p.amount_paise,
        outcome=Outcome.UNRESOLVED,
        cause=None,
        intervention=plan,
        result=ActionResult(
            payment_id=p.payment_id,
            kind=plan.kind,
            ok=False,
            provider_ref=str(observed["provider_ref"]),
            detail=detail,
        ),
        verified=False,
        evidence=f"{plan.kind.value} for {p.payment_id} raised {detail}",
        seal_hash=seal_hash,
        attempts=_attempts(store, p.payment_id),
    )


def _authorization(plan: Intervention) -> str:
    """Contract §5.8: an empty authorization is the first thing an auditor flags."""
    return f"policy:{plan.kind.value} cost={plan.cost_paise}p"


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _last_seal() -> Seal | None:
    return next(iter(deque(stepproof.get_ledger().read(), maxlen=1)), None)


def _db_path(store: Store) -> str:
    path = getattr(store, "path", None) or getattr(store, "db_path", None)
    if not path:
        raise AttributeError(
            f"{type(store).__name__} exposes neither .path nor .db_path; "
            "sqlite_row_exists needs the sqlite file to verify an outreach attempt"
        )
    return str(path)


def _attempts(store: Store, payment_id: str) -> int:
    """A bookkeeping read must never cost us a verdict stepproof already sealed."""
    try:
        return int(store.attempts_for(payment_id))
    except Exception:
        return 1
