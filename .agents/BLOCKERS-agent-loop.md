# BLOCKERS — lane agent-loop (A4, A5, A6)

Nothing stopped the lane. Everything below is a contract tension I resolved in code and
a decision the integrator needs to see before merge.

---

## 1. `execute()` cannot build the §5.8 authorization string as written

Contract §5.8 specifies `authorization=f"policy:{plan.kind.value} cap={cfg.cost_cap_paise}p"`,
but §4 freezes the signature as `execute(p, plan, store, rzp)` — no `cfg`. The frozen
signature wins. Composed from what `execute` actually has:

```
policy:payment_link cost=0p
policy:escalate cost=1500p
```

Non-empty on every seal, names the policy that authorised the action, and carries the
money figure. If the integrator wants the cap in there instead, `PipelineConfig` has to
reach `execute` and that is a §4 signature change, not a lane fix.

## 2. NUDGE and ESCALATE map `verified=True` to UNRESOLVED, not RECOVERED

**This is the one place I diverged from the literal instruction, and it is deliberate.**

§5.7 says map `True -> RECOVERED`. That is correct for the two actions whose verifier
observes money arriving — RETRY (`status=captured`) and PAYMENT_LINK (`status=paid`).
It is wrong for NUDGE and ESCALATE, whose verifier is `sqlite_row_exists` on the
`attempts` table (A5, and it is the right verifier — outreach has no rail to re-fetch).
A true seal there proves *the nudge was really sent*, not *the customer paid*.

Mapping that to RECOVERED would put every nudged and escalated rupee into
`amount_recovered_paise` (§7: "counts a record only when its seal has verified is True"),
which would (a) push `recovery_rate_value` well past the 0.80 credibility ceiling §10.2
warns about, and (b) re-introduce the exact "claimed success, no money" bug the project
exists to catch, one layer up from where we caught it.

So:

| kind | seal True | seal False |
|---|---|---|
| RETRY, PAYMENT_LINK | RECOVERED (+ settlement row) | FAILED_VERIFICATION |
| NUDGE, ESCALATE | UNRESOLVED ("acted, no money") | FAILED_VERIFICATION |

`False -> FAILED_VERIFICATION` is unchanged everywhere. Pinned by
`test_nudge_verifies_the_attempts_row_and_is_not_a_recovery` and
`test_escalate_is_verified_but_never_recovered`.

## 3. `Store` must expose its file path — request to agent-io

`sqlite_row_exists(db, table, where)` takes a path, but §4 hands `execute` only the
`Store` object. `execute._db_path()` reads `store.path`, falls back to `store.db_path`,
and raises a named `AttributeError` if neither exists. **Please make `Store.__init__`
assign `self.path = path`.**

## 4. `record_attempt` must persist `kind` as `ActionKind.value` — request to agent-io

The NUDGE/ESCALATE verifier matches `kind = 'nudge'` / `kind = 'escalate'`. Binding the
enum straight into a sqlite parameter gives that for free (it is a `str` subclass). But
`str(ActionKind.NUDGE)` is `"ActionKind.NUDGE"` on Python 3.12 — if `record_attempt`
stringifies the enum, every outreach seal fails verification. Use the parameter or
`kind.value`.

## 5. `record_attempt` must COMMIT before returning — request to agent-io

`sqlite_row_exists` opens its own connection. An uncommitted row is invisible to it, so
an uncommitted `record_attempt` turns every NUDGE and ESCALATE into
FAILED_VERIFICATION.

## 6. `build_pipeline` binds the ledger

§5.5 puts `set_ledger` at CLI start and forbids it inside `run_one`. I call it in
`build_pipeline`, which runs exactly once per batch and is the only place that knows
`cfg.ledger_path` — without it, seals land in the default `.stepproof/ledger.jsonl` and
`audit(cfg.ledger_path)` reads an empty chain. If harness-report's CLI also calls
`set_ledger` with the same `cfg`, it is a harmless same-path re-bind.

## 7. `execute` returns `cause=None`; the pipeline attaches it

`execute(p, plan, store, rzp)` has no `cause` argument, so `RecoveryPipeline._run`
attaches the `RootCause` with `dataclasses.replace` after the verdict is sealed. The
rationale goes into `notes` as `classifier(0.92): ...` and never into `evidence` (§5.3).
Anyone calling `execute` directly gets `cause=None` — that is expected.

## 8. Not a blocker, recorded for QA

`stepproof.verified` seals the attempt **and then re-raises** when the wrapped function
throws (verified empirically against 0.1.0). `execute` relies on that: it catches the
exception and carries the seal hash that stepproof already appended, so a crashed action
stays on the audit chain instead of vanishing. A verifier that raises, by contrast,
propagates uncaught — so every verifier in `execute.py` wraps its provider/database
lookup and returns the failure *as evidence*.
