# BLOCKERS — harness-data (H1, H2)

Neither entry blocked the lane. Both are contract-level facts the integrator has to
decide on, raised here rather than "fixed" by diverging from the contract.

## 1. `score()` cannot fill `chain_intact` or `seals_total`

CONTRACT §7 puts `chain_intact: bool` and `seals_total: int` in `Metrics`. CONTRACT §4
freezes `score(outcomes, truth, split)` — no ledger path, no `AuditSummary`. `score()`
therefore cannot observe the ledger it is being asked to report on.

What `metrics.py` does now:

- `chain_intact=False`. Not a claim of a broken chain — a refusal to claim an intact one
  without reading it. The safe direction: a forgotten audit shows as "unverified", never
  as "verified".
- `seals_total` = the number of scored outcomes carrying a non-empty `seal_hash`. That is
  a real observable, but it counts seals *attributed to this split*, not the ledger total.

Required of the CLI (harness-report lane), after `audit()`:

```python
m = dataclasses.replace(score(outcomes, truth), 
                        chain_intact=summary.chain_intact,
                        seals_total=summary.seals_total)
```

If that call is missed, `RESULTS.md` reports an unverified chain and a split-local seal
count. Alternative, if the planner prefers: add `audit_summary` to the `score()` signature
— but that is a contract change and not a Builder's to make.

## 2. The 48-record holdout is too small to pin the headline inside 45-65%

CONTRACT §10.2 targets 45-65% recovery by value on the holdout split. The generator is
calibrated to that: expected value-weighted recovery is **0.519 on the full batch and
0.528 on the seed-7 holdout** (`generate.expected_recovery_value_rate`, asserted in
`tests/test_generate.py`).

But holdout is 48 records with log-normally distributed amounts. Simulating a policy that
recovers at exactly the published per-reason propensity, 400 runs:

| split | n | mean | sd | p5 | p95 | share inside 45-65% |
|---|---|---|---|---|---|---|
| holdout | 48 | 0.526 | 0.113 | 0.336 | 0.698 | **58%** |
| train | 192 | 0.514 | 0.065 | 0.412 | 0.625 | 81% |

So roughly two runs in five land outside the band on luck alone — a handful of large-ticket
records flipping is enough. Raising the generator's propensities to compensate would move
the *mean* out of band, which is the failure §10.2 explicitly forbids, so the generator was
left honest.

Two options for the integrator, neither of which is mine to choose:

1. Report the full-batch rate next to the holdout rate in `RESULTS.md`. Same calibration,
   a quarter of the variance.
2. Keep holdout as the headline and state the amount at risk beside it, so a 0.34 or a 0.70
   reads as a 48-record sample and not as a result.

Whichever is chosen, do not re-tune `RECOVERY_PROPENSITY` in `generate.py` to make a single
run look better. That is the number the video is about.
