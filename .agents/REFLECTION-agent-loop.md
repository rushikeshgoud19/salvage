# REFLECTION — lane agent-loop (A4, A5, A6)

## What shipped

| Task | File | What it prevents |
|---|---|---|
| A4 | `salvage/policy.py` | acting at the wrong moment, and acting where compliance forbids it |
| A4 | `tests/test_policy.py` | a stopping rule silently going dead |
| A5 | `salvage/execute.py` | a `201 Created` being booked as recovered revenue |
| A5 | `tests/test_execute.py` | the gate above regressing without anyone noticing |
| A6 | `salvage/pipeline.py` | one bad record killing a 240-record batch |

265 tests, all passing.

## The three landmines, and how each is disarmed

1. **Verifiers take `**kwargs`.** All three (`_verify_link_paid`,
   `_verify_payment_captured`, `_verify_attempt_row`) are `def _verify_x(**kw)`. They
   close over the payment, the plan and the client rather than taking bound arguments,
   so `_accepts_kwargs` can never fall through to the zero-argument call.
2. **Model output is never evidence.** `execute.py` does not import `classify` and never
   sees a `RootCause`. Every evidence string is an f-string over values observed after
   the action — a re-fetched link status, a gateway amount, a row count. The rationale
   is attached in `pipeline._run` as a note, after the seal exists.
   `test_evidence_execute_produces_is_never_narration` asserts `is_narration` is False on
   every string the executor actually emits, and
   `test_narration_is_rejected_as_evidence_by_the_seal` asserts the flip explicitly.
3. **`raises=False` everywhere**, with the verdict read from the tail seal's `verified`
   and `hash` carried into `RecoveryOutcome.seal_hash`.

## Decisions worth arguing about

- **Outreach is not recovery.** NUDGE and ESCALATE seal true when the attempts row is
  really there, and that maps to UNRESOLVED, not RECOVERED. Full reasoning in
  `BLOCKERS-agent-loop.md` §2. This is the single judgement call in the lane and it
  moves the headline number, so it should be reviewed rather than assumed.
- **Timing suppression reports a reason, not a silence.** Every NONE carries both the
  rule name (`max_attempts`, `cost_cap`, `timing_window`, `quiet_hours`) and a sentence
  naming the observed number that tripped it — `"insufficient_funds hold: 1h elapsed,
  retry opens at 3.0d"`. A suppressed record is as auditable as an acted one.
- **Payday bias is 48h instead of 72h on the 1st and the 15th.** §10.3 asks for a bias
  toward payday without giving a number; shortening the hold on the two days the money
  demonstrably lands is the smallest encoding of it that is testable, and
  `test_payday_shortens_the_insufficient_funds_hold` pins it with two records that differ
  only in the day of the month.
- **`RISK_BLOCKED` has no timing gate at all.** A compliance escalation does not expire,
  so a 60-day-old risk block still goes to a human. Twenty-five parametrised cases assert
  it can never come back as RETRY.

## What I could not test in-lane

`salvage/pipeline.py` has no committed test file — `tests/test_pipeline.py` is not in my
ownership row. I smoke-tested it out of tree against the same doubles used in
`tests/test_execute.py`: ten records through `build_pipeline` → `run_one`, chain intact,
rationale in notes and absent from evidence, and a `run_one` whose classifier throws
returning UNRESOLVED with the exception text as evidence. That coverage should become a
real test file after the merge.

The other three lanes' modules did not exist while I worked, so the suite ran with a
throwaway pytest plugin standing in for `metrics`, `store`, `rzp`, `detect` and
`classify`. It lives outside the worktree and is not committed; after the merge the suite
runs with `python -m pytest tests/test_policy.py tests/test_execute.py -q` and no plugin.
