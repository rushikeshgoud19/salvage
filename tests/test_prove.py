"""Tests for the self-check.

`salvage prove` exists so a reviewer does not have to trust the README. That only works if
the checks genuinely check something — a check that has quietly stopped testing anything
still prints PASS, and "all 5 claims held" becomes exactly the kind of unearned success
this project was built to catch.

So these tests do two things: confirm each check passes on a healthy system, and confirm
the harness cannot report a pass it did not earn.
"""
from __future__ import annotations

import tempfile

import pytest

from salvage import prove as prove_mod
from salvage.prove import CHECKS, Proof, run_all


@pytest.fixture()
def work(tmp_path) -> str:
    return str(tmp_path)


# ── every check passes on a healthy system ──────────────────────────────────────

@pytest.mark.parametrize("check", CHECKS, ids=[c.__name__ for c in CHECKS])
def test_each_check_passes(check, work):
    result = check(work)
    assert isinstance(result, Proof)
    assert result.passed, f"{result.name}: {result.evidence}"
    assert result.evidence.strip(), "a passing check must still say what it observed"
    assert result.claim.strip()


def test_run_all_reports_every_check():
    results = run_all()
    assert len(results) == len(CHECKS)
    assert all(r.passed for r in results), [r for r in results if not r.passed]


# ── the harness cannot report an unearned pass ──────────────────────────────────

def test_a_check_that_raises_is_a_failure_not_a_skip(monkeypatch):
    """An absent result is not a passing result — the same rule the project runs on."""
    def exploding(_work):
        raise RuntimeError("the check itself is broken")

    exploding.__doc__ = "Claim: something that never got measured."
    monkeypatch.setattr(prove_mod, "CHECKS", (CHECKS[0], exploding))

    results = run_all()
    assert len(results) == 2
    assert results[0].passed
    assert not results[1].passed, "a check that could not run must never report PASS"
    assert "the check itself is broken" in results[1].evidence


def test_run_all_leaves_no_workspace_behind(monkeypatch):
    made: list[str] = []
    real = tempfile.mkdtemp

    def tracked(*a, **k):
        path = real(*a, **k)
        made.append(path)
        return path

    monkeypatch.setattr(tempfile, "mkdtemp", tracked)
    run_all()
    import os
    assert made and not any(os.path.exists(p) for p in made)


# ── the checks are actually sensitive to the thing they test ────────────────────

def test_the_forgery_check_depends_on_the_chain_being_broken(work, monkeypatch):
    """If tamper detection stopped working, this check must go red rather than green."""
    import salvage.prove as m

    class AlwaysIntact:
        chain_intact = True
        detail = "chain intact (5 records)"
        seals_total = 5
        failures: list = []
        unverified: list = []

    monkeypatch.setattr(m, "audit", lambda _p: AlwaysIntact())
    assert not m.prove_forged_seal_is_caught(work).passed, (
        "the check passed while the chain reported intact after a forgery"
    )


def test_the_double_charge_check_depends_on_the_settlement_guard(work, monkeypatch):
    """If already_settled stopped firing, this check must go red."""
    import salvage.prove as m
    from salvage.types import ActionKind, Intervention

    monkeypatch.setattr(
        m, "decide",
        lambda p, c, s, cfg, now: Intervention(p.payment_id, ActionKind.RETRY, "always acts", 0),
    )
    assert not m.prove_a_paid_customer_is_never_charged_again(work).passed, (
        "the check passed while the policy charged a settled payment"
    )
