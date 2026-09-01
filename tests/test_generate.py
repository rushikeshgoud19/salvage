"""Tests for the synthetic batch.

The load-bearing assertions here are the ones that check the generated data
against an *independent* copy of the Razorpay table in CONTRACT §10.1 — written
out below by hand. A test that re-reads `generate.REASONS` would agree with any
typo the generator contains, including an invented reason code.
"""
from __future__ import annotations

import filecmp
import json
from collections import Counter

import pytest

from salvage.generate import (
    NEVER_SELF_HEALS,
    _assign_splits,
    expected_recovery_value_rate,
    generate_batch,
    load_batch,
    write_batch,
)
from salvage.types import FailedPayment, FailureReason, GroundTruth

# CONTRACT §10.1, transcribed independently of salvage/generate.py.
# (razorpay reason, source, FailureReason) — card_declined is ambiguous by design.
CONTRACT_TABLE = {
    "bank_not_available": ("gateway", FailureReason.BANK_DOWN),
    "bank_technical_error": ("gateway", FailureReason.BANK_DOWN),
    "bank_cutoff_in_progress": ("gateway", FailureReason.BANK_DOWN),
    "gateway_technical_error": ("gateway", FailureReason.BANK_DOWN),
    "insufficient_funds": ("customer", FailureReason.INSUFFICIENT_FUNDS),
    "transaction_limit_exceeded": ("customer", FailureReason.INSUFFICIENT_FUNDS),
    "transaction_daily_limit_exceeded": ("customer", FailureReason.INSUFFICIENT_FUNDS),
    "credit_limit_exceeded": ("gateway", FailureReason.INSUFFICIENT_FUNDS),
    "authentication_failed": ("customer", FailureReason.AUTH_FAILED),
    "incorrect_otp": ("customer", FailureReason.AUTH_FAILED),
    "otp_expired": ("customer", FailureReason.AUTH_FAILED),
    "incorrect_cvv": ("customer", FailureReason.AUTH_FAILED),
    "invalid_vpa": ("customer", FailureReason.AUTH_FAILED),
    "card_number_invalid": ("customer", FailureReason.AUTH_FAILED),
    "incorrect_card_details": ("customer", FailureReason.AUTH_FAILED),
    "user_not_registered_for_netbanking": ("customer", FailureReason.AUTH_FAILED),
    "card_expired": ("customer", FailureReason.CARD_EXPIRED),
    "mandate_creation_declined": ("gateway", FailureReason.MANDATE_EXPIRED),
    "payment_risk_check_failed": ("gateway", FailureReason.RISK_BLOCKED),
    "compliance_violation": ("business", FailureReason.RISK_BLOCKED),
    "debit_instrument_blocked": ("customer", FailureReason.RISK_BLOCKED),
    "card_declined": ("gateway", None),
    "": ("customer", FailureReason.CHECKOUT_DROPOFF),
}

AMBIGUOUS_CODE = "card_declined"
CARD_DECLINED_FAMILIES = {
    FailureReason.INSUFFICIENT_FUNDS,
    FailureReason.RISK_BLOCKED,
    FailureReason.AUTH_FAILED,
}
SEVEN_FAMILIES = {
    FailureReason.BANK_DOWN,
    FailureReason.INSUFFICIENT_FUNDS,
    FailureReason.AUTH_FAILED,
    FailureReason.MANDATE_EXPIRED,
    FailureReason.CHECKOUT_DROPOFF,
    FailureReason.CARD_EXPIRED,
    FailureReason.RISK_BLOCKED,
}


@pytest.fixture(scope="module")
def batch() -> tuple[list[FailedPayment], list[GroundTruth]]:
    return generate_batch()


def test_default_shape(batch):
    payments, truth = batch
    assert len(payments) == 240
    assert len(truth) == 240
    assert [p.payment_id for p in payments] == [t.payment_id for t in truth]
    assert len({p.payment_id for p in payments}) == 240


def test_every_gateway_code_is_a_real_razorpay_reason(batch):
    payments, _ = batch
    for p in payments:
        assert p.gateway_code in CONTRACT_TABLE, (
            f"invented gateway_code {p.gateway_code!r} on {p.payment_id}")


def test_every_source_matches_the_contract_table(batch):
    payments, _ = batch
    for p in payments:
        assert p.source in ("customer", "gateway", "business"), (
            f"invented source {p.source!r} on {p.payment_id}")
        assert p.source == CONTRACT_TABLE[p.gateway_code][0], (
            f"{p.gateway_code!r} carries source {p.source!r}, "
            f"contract says {CONTRACT_TABLE[p.gateway_code][0]!r}")


def test_true_reason_inverts_the_contract_table(batch):
    payments, truth = batch
    by_id = {t.payment_id: t for t in truth}
    for p in payments:
        expected = CONTRACT_TABLE[p.gateway_code][1]
        actual = by_id[p.payment_id].true_reason
        if expected is None:
            assert p.gateway_code == AMBIGUOUS_CODE
            assert actual in CARD_DECLINED_FAMILIES, (
                f"card_declined resolved to {actual}, not one of the three "
                f"causes the contract calls ambiguous")
        else:
            assert actual is expected, (
                f"{p.gateway_code!r} labelled {actual}, contract says {expected}")


def test_all_twenty_three_reasons_appear(batch):
    payments, _ = batch
    assert set(p.gateway_code for p in payments) == set(CONTRACT_TABLE)


def test_gateway_description_is_present_and_stable_per_code(batch):
    payments, _ = batch
    seen: dict[str, str] = {}
    for p in payments:
        assert p.gateway_description.strip(), f"empty description on {p.gateway_code!r}"
        seen.setdefault(p.gateway_code, p.gateway_description)
        assert p.gateway_description == seen[p.gateway_code], (
            f"{p.gateway_code!r} has two different descriptions")


def test_money_is_positive_integer_paise(batch):
    payments, _ = batch
    for p in payments:
        assert type(p.amount_paise) is int, (
            f"{p.payment_id} amount is {type(p.amount_paise).__name__}, must be int paise")
        assert p.amount_paise > 0
        # Rs 99 - Rs 85,000, per H1.
        assert 9_900 <= p.amount_paise <= 8_500_000, (
            f"{p.payment_id} amount {p.amount_paise}p is outside the Rs99-Rs85,000 band")
    assert all(p.currency == "INR" for p in payments)


def test_amounts_are_spread_not_uniform(batch):
    """A log-normal ticket size, not 240 copies of the same number."""
    payments, _ = batch
    amounts = sorted(p.amount_paise for p in payments)
    assert len(set(amounts)) > 200
    median = amounts[len(amounts) // 2]
    assert amounts[-1] > 10 * median, "no long tail — the amount draw is not log-normal"


def test_split_is_deterministic_and_correctly_sized(batch):
    _, truth = batch
    counts = Counter(t.split for t in truth)
    assert set(counts) == {"train", "holdout"}
    assert 46 <= counts["holdout"] <= 50, counts


def test_split_is_a_function_of_payment_id_not_of_generation_order(batch):
    """H1 asks for a hashed split, not a sliced shuffle.

    Feeding the same records in reverse order must produce the same assignment;
    if it does not, the split is riding on list position.
    """
    _, truth = batch
    families = {t.payment_id: t.true_reason for t in truth}
    forward = _assign_splits(families, 0.20, len(truth))
    reversed_in = _assign_splits(dict(reversed(list(families.items()))), 0.20, len(truth))
    assert forward == reversed_in
    assert forward == {t.payment_id: t.split for t in truth}


def test_every_family_present_in_both_splits(batch):
    _, truth = batch
    for split in ("train", "holdout"):
        present = {t.true_reason for t in truth if t.split == split}
        assert present == SEVEN_FAMILIES, f"{split} is missing {SEVEN_FAMILIES - present}"


def test_would_self_heal_share_is_in_band(batch):
    _, truth = batch
    share = sum(t.would_self_heal for t in truth) / len(truth)
    assert 0.15 <= share <= 0.22, f"would_self_heal at {share:.3f}, contract band is 0.15-0.22"


def test_self_heal_is_concentrated_in_bank_down_and_dropoff(batch):
    _, truth = batch
    healers = [t for t in truth if t.would_self_heal]
    concentrated = sum(
        1 for t in healers
        if t.true_reason in (FailureReason.BANK_DOWN, FailureReason.CHECKOUT_DROPOFF))
    assert concentrated / len(healers) >= 0.60, (
        "self-healing is meant to sit in the two families that genuinely resolve alone")
    # Nothing dead recovers on its own.
    for t in healers:
        assert t.true_reason not in (
            FailureReason.CARD_EXPIRED,
            FailureReason.MANDATE_EXPIRED,
            FailureReason.RISK_BLOCKED,
        ), f"{t.true_reason} cannot self-heal — the instrument is dead or blocked"


def test_self_heal_after_s_uses_the_sentinel_when_it_never_heals(batch):
    _, truth = batch
    for t in truth:
        if t.would_self_heal:
            assert t.self_heal_after_s > 0.0
            assert t.self_heal_after_s <= 8 * 24 * 3600
        else:
            assert t.self_heal_after_s == NEVER_SELF_HEALS


def test_calibrated_to_the_published_recovery_band(batch):
    """CONTRACT §10.2: a competent policy lands at 45-65% by value, not 95%."""
    payments, truth = batch
    full = expected_recovery_value_rate(payments, truth)
    holdout = expected_recovery_value_rate(payments, truth, "holdout")
    assert 0.45 <= full <= 0.65, f"batch is winnable at {full:.3f}, band is 0.45-0.65"
    assert 0.45 <= holdout <= 0.65, f"holdout winnable at {holdout:.3f}, band is 0.45-0.65"


def test_calibration_holds_across_seeds():
    """Guards against a mix that only happens to be honest at seed 7."""
    for seed in (0, 1, 13, 42, 99):
        payments, truth = generate_batch(seed=seed)
        rate = expected_recovery_value_rate(payments, truth)
        assert 0.45 <= rate <= 0.65, f"seed {seed} is winnable at {rate:.3f}"
        share = sum(t.would_self_heal for t in truth) / len(truth)
        assert 0.10 <= share <= 0.26, f"seed {seed} self-heal share {share:.3f} has drifted"


def test_contact_details_are_synthetic(batch):
    payments, _ = batch
    for p in payments:
        assert p.customer_email.endswith("@example.invalid")
        assert p.customer_phone.startswith("+91") and len(p.customer_phone) == 13
        assert p.customer_phone[3] in "6789"


def test_method_is_coherent_with_the_reason(batch):
    payments, _ = batch
    assert {p.method for p in payments} <= {"card", "upi", "netbanking", "wallet", "emi"}
    for p in payments:
        if p.gateway_code == "invalid_vpa":
            assert p.method == "upi"
        if p.gateway_code in ("incorrect_cvv", "card_number_invalid",
                              "incorrect_card_details", "card_declined"):
            assert p.method in ("card", "emi")
        if p.gateway_code == "user_not_registered_for_netbanking":
            assert p.method == "netbanking"


def test_failed_at_is_inside_the_recovery_window(batch):
    payments, _ = batch
    newest = max(p.failed_at for p in payments)
    oldest = min(p.failed_at for p in payments)
    assert newest - oldest <= 14 * 24 * 3600
    assert all(isinstance(p.failed_at, float) for p in payments)


def test_attempt_no_is_within_the_budget(batch):
    payments, _ = batch
    assert {p.attempt_no for p in payments} <= {1, 2, 3}
    assert all(type(p.attempt_no) is int for p in payments)


def test_same_seed_same_objects():
    assert generate_batch(seed=7) == generate_batch(seed=7)


def test_different_seed_different_batch():
    payments_a, _ = generate_batch(seed=7)
    payments_b, _ = generate_batch(seed=8)
    assert [p.payment_id for p in payments_a] != [p.payment_id for p in payments_b]


def test_same_seed_writes_byte_identical_files(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    write_batch(*generate_batch(seed=7), out_dir=str(a))
    write_batch(*generate_batch(seed=7), out_dir=str(b))
    for name in ("payments.json", "truth.json"):
        assert filecmp.cmp(a / name, b / name, shallow=False), f"{name} is not reproducible"


def test_round_trip_through_disk(tmp_path, batch):
    payments, truth = batch
    out = str(tmp_path / "data")
    payments_path, truth_path = write_batch(payments, truth, out_dir=out)
    assert payments_path.endswith("payments.json")
    assert truth_path.endswith("truth.json")
    assert load_batch(out) == (payments, truth)


def test_written_amounts_are_json_integers(tmp_path, batch):
    """A float rupee surviving to disk is the rounding bug §9.1 forbids."""
    out = str(tmp_path / "data")
    write_batch(*batch, out_dir=out)
    rows = json.loads((tmp_path / "data" / "payments.json").read_text(encoding="utf-8"))
    for row in rows:
        assert isinstance(row["amount_paise"], int)
        assert not isinstance(row["amount_paise"], bool)


def test_payments_file_carries_no_ground_truth(tmp_path, batch):
    """The agent lane reads payments.json. A label leaking into it voids the score."""
    out = str(tmp_path / "data")
    write_batch(*batch, out_dir=out)
    text = (tmp_path / "data" / "payments.json").read_text(encoding="utf-8")
    for leaked in ("would_self_heal", "self_heal_after_s", "true_reason", "split"):
        assert leaked not in text


def test_load_batch_names_the_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError) as err:
        load_batch(str(tmp_path / "nothing"))
    assert "payments.json" in str(err.value)


def test_small_n_still_produces_both_splits():
    payments, truth = generate_batch(n=40, seed=3)
    assert len(payments) == 40
    counts = Counter(t.split for t in truth)
    assert counts["holdout"] > 0 and counts["train"] > 0


@pytest.mark.parametrize("n, frac", [(0, 0.2), (-5, 0.2), (10, 0.0), (10, 1.0)])
def test_bad_arguments_report_what_was_observed(n, frac):
    with pytest.raises(ValueError) as err:
        generate_batch(n=n, holdout_frac=frac)
    assert "observed" in str(err.value)
