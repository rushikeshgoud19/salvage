# REFLECTION — harness-report (H3, H4, H5, H6)

## What shipped

- `salvage/audit.py` — `AuditSummary`, `audit()`, `seals_for()`. Read side only; nothing
  here appends to the ledger.
- `salvage/report.py` — `render()` plus the two formatters (`rupees`, `percent`) that
  every human-facing number in the project goes through.
- `salvage/cli.py` + `salvage/__main__.py` — typer app with `generate`, `run`, `report`,
  `demo`, one `set_ledger` call for the whole batch, per-record failure isolation.
- `tests/test_audit.py`, `tests/test_report.py` — 14 tests, all passing.

## What is actually verified

The tamper case is built in the test rather than asserted by hand: three seals are
appended, one byte of the middle record is rewritten on disk, and `audit()` reports the
chain broken with stepproof's own detail naming record 1 and its action.

The report tests assert on what a reader sees, not on internals — the split stated on the
page, the AI-judgment sentence ahead of the metrics table it explains, `₹45,000.00` present
and `4500000` absent, `nan` and `None` absent, evidence quoted verbatim, and the
zero-denominator run rendering `₹0.00` instead of a crash.

The CLI was driven end to end against stubs for the three sibling lanes: `demo` exits 0,
isolates a record whose `run_one` raises, still writes a complete outcome set, and renders
`RESULTS.md`. `python -m salvage --help` lists all four commands.

## What is not verified until merge

Everything `cli.py` imports across the seam — `generate_batch` / `load_batch` / `score` /
`build_pipeline` — was exercised against stubs shaped from the contract, not the real
modules. The outcome JSON round trip is the seam most likely to bite: `run` writes
outcomes with `dataclasses.asdict` and `report` rebuilds them field by field, so any drift
in `RecoveryOutcome` breaks the two-command path (`demo` passes the objects in process and
would not notice).

## The decision worth keeping

`report.py` imports `Metrics` under `TYPE_CHECKING` only. It reads the fields, it never
needs the class, and keeping the import out of the runtime path meant the renderer could
be built and tested to the frozen §7 shape while `metrics.py` was still being written in
another worktree. The report does not drag the scorer in behind it at merge either.
