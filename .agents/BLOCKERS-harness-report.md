# BLOCKERS — harness-report (H3, H4, H5, H6)

Nothing stopped the lane. These are the judgment calls and contract wrinkles the
integrator has to see, in the order they matter.

## 1. `render()` needs ground truth, Contract §4 does not give it one

H4 requires a root-cause accuracy line against `GroundTruth.true_reason`, but the frozen
§4 signature is `render(metrics, outcomes, audit_summary, out_path)`. Resolved by adding
a **keyword-only, optional** `truth` parameter. Every §4-shaped call still works, and
without `truth` the report omits the accuracy section rather than guessing at it. Nothing
else in the signature moved.

## 2. `score()` structurally cannot fill `Metrics.chain_intact` / `seals_total`

§7 puts both fields on `Metrics`; §4 gives `score(outcomes, truth, split)` no ledger path
to read them from. `cli._write_report` fills them with `dataclasses.replace()` from the
`AuditSummary` that `audit()` produced, so the shipped `Metrics` agrees with the ledger
beside it. `report.py` reads the chain facts off `audit_summary`, not off `metrics`, so
the report is correct either way. If harness-data's `score()` already fills them, the
`replace` is redundant but not wrong — drop it at merge if so.

## 3. An absent ledger is reported as NOT intact

`stepproof.Ledger.verify_chain()` answers `(True, "chain intact (0 records)")` for a file
that does not exist. `audit()` returns `chain_intact=False` with a detail naming the
missing path instead. Reporting "intact" over an audit trail that was never written is
the exact claim this project exists to refuse. A real run seals money actions, so the
normal path is unaffected. Flagging it because it is a deliberate divergence from what
the dependency says.

## 4. The rupee sign crashes a default Windows console

`rich` raises `UnicodeEncodeError` printing `₹` when stdout is cp1252, which is the
Windows default — confirmed on this machine, not assumed. `cli.py` reconfigures stdout
and stderr to UTF-8 at import. Without that line `python -m salvage demo` dies mid-batch
on a judge's laptop.

## 5. One ledger and one database per run means clearing them

Contract §9.5 says one ledger and one SQLite file per run. `_run_batch` therefore deletes
an existing `cfg.ledger_path` and `cfg.db_path` before starting, printing a line for each.
Left in place, a second `demo` would count yesterday's seals into today's audit summary
and yesterday's attempts would suppress today's actions. **Agent lane: if `Store` is
expected to persist across runs, this is the line to argue with.**

## 6. H6 has no home for a test

The PLAN ownership table gives the harness lane `test_generate`, `test_metrics`,
`test_audit`, `test_report` — there is no `tests/test_cli.py` in any lane, so the H6
done-when ("a pipeline that raises on record 3 of 10 still produces 10 rows, exit code 0")
was verified with a throwaway script outside the repo, against stubs for the three sibling
lanes. Result: exit code 0, 10 outcome rows, record 3 isolated as `UNRESOLVED` with the
exception text in `evidence`, `RESULTS.md` written. If a `tests/test_cli.py` is wanted,
someone has to own it.
