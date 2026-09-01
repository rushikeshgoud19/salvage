# CONTRACT — salvage

Frozen. Builders implement this; no Builder may change it. If you believe a clause is
wrong or unimplementable, write it in `.agents/BLOCKERS.md` and keep going on everything
else. Do not "fix" the contract by diverging from it — a lane that silently improves a
shape ships code the other lane cannot import.

Read this file **before** `PLAN.md`.

---

## §1 — Environment

| Fact | Value |
|---|---|
| Python | 3.12.10 (floor: 3.10 — use `from __future__ import annotations`) |
| Test runner | `pytest` 9.1.1 (installed) |
| Money | **integer paise**, never float rupees, never `Decimal` in a dataclass field |
| Timestamps | float unix seconds (`time.time()`), never `datetime` in stored records |
| Randomness | every generator/sampler takes an explicit `seed: int`. No bare `random.*`. |

**Already installed — use these, do not add alternatives:** `httpx`, `pandas`, `numpy`,
`pydantic`, `rich`, `typer`, `jinja2`, `matplotlib`, `anthropic`, `openai`.

**Not installed:** `razorpay` (the SDK), `faker`. Do **not** add either.
Talk to Razorpay over `httpx` + HTTP Basic auth directly (§6). Generate names and emails
from a seeded `random.Random` — a plausible address is `f"cust{n:04d}@example.invalid"`,
not a dependency.

**stepproof is a dependency you never edit.** It is a local clone at
`C:\Users\rushi\OneDrive\Desktop\agentse` (package `stepproof/`, version 0.1.0, remote
`rushikeshgoud19/stepproof`). It is not on PyPI and not currently installed. Install it
editable, once, in the venv you run from:

```
pip install -e "C:/Users/rushi/OneDrive/Desktop/agentse"
```

Never vendor, copy, patch, monkey-patch, or `sys.path`-hack stepproof. If stepproof has a
bug, that is a `BLOCKERS.md` entry, not an edit. The submission's entire claim rests on
salvage being audited by an independent library.

---

## §2 — Shared types — `salvage/types.py`

**This file ships in the seed commit on `main`. Neither lane owns it. Neither lane may
edit it.** Both lanes import from it for real — there is no stub and no post-merge
reconciliation. Reproduced here verbatim so the contract and the code cannot drift.

```python
"""Frozen shared vocabulary for salvage.

Both lanes import from here and neither owns it. Money is integer paise everywhere:
a float rupee is a rounding bug waiting to be reported as a recovery figure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class FailureReason(str, Enum):
    BANK_DOWN = "bank_down"                    # gateway/bank downtime — transient, retry wins
    INSUFFICIENT_FUNDS = "insufficient_funds"  # soft decline — timing wins, not repetition
    AUTH_FAILED = "auth_failed"                # OTP/3DS/CVV/VPA — endemic in India, recovers well
    MANDATE_EXPIRED = "mandate_expired"
    CHECKOUT_DROPOFF = "checkout_dropoff"
    CARD_EXPIRED = "card_expired"
    RISK_BLOCKED = "risk_blocked"              # never auto-retry. escalate. see §10
    UNKNOWN = "unknown"


class ActionKind(str, Enum):
    RETRY = "retry"                  # re-present the same instrument
    PAYMENT_LINK = "payment_link"    # issue a fresh link
    NUDGE = "nudge"                  # remind the customer, no new rail
    ESCALATE = "escalate"            # hand to a human
    NONE = "none"                    # policy declined to act


class Outcome(str, Enum):
    RECOVERED = "recovered"                      # money actually arrived, verified
    UNRESOLVED = "unresolved"                    # acted, no money
    SUPPRESSED = "suppressed"                    # policy deliberately did not act
    FAILED_VERIFICATION = "failed_verification"  # action CLAIMED success, state disagreed


@dataclass(frozen=True)
class FailedPayment:
    """What the agent lane is allowed to see. No ground truth lives here."""
    payment_id: str
    order_id: str
    customer_id: str
    amount_paise: int
    currency: str                # "INR"
    method: str                  # card | upi | netbanking | wallet | emi
    failed_at: float
    gateway_code: str            # a REAL Razorpay `reason`, e.g. "insufficient_funds" — §10
    gateway_description: str     # Razorpay's own description string for that reason
    source: str                  # "customer" | "gateway" | "business" — real Razorpay field,
                                 # and the single best policy signal you get for free (§10)
    attempt_no: int
    customer_email: str
    customer_phone: str


@dataclass(frozen=True)
class GroundTruth:
    """Harness lane ONLY. Importing this from the agent lane is a contract violation
    and is checked at QA — it is the label the agent is being scored against."""
    payment_id: str
    true_reason: FailureReason
    would_self_heal: bool        # would this have paid with zero intervention?
    self_heal_after_s: float     # ...and how long it would have taken
    split: str                   # "train" | "holdout"


@dataclass(frozen=True)
class RootCause:
    payment_id: str
    reason: FailureReason
    confidence: float            # 0.0-1.0
    rationale: str               # model prose. NEVER used as stepproof evidence (§5).


@dataclass(frozen=True)
class Intervention:
    payment_id: str
    kind: ActionKind
    reason: str                  # why the policy chose this, composed by salvage code
    cost_paise: int              # from COST_TABLE, §7
    suppressed_by: str = ""      # non-empty iff kind is NONE; names the stopping rule


@dataclass(frozen=True)
class ActionResult:
    """The CLAIM. What the executor believes happened. Never scored on its own."""
    payment_id: str
    kind: ActionKind
    ok: bool
    provider_ref: str            # rzp link id / payment id / "" when no rail was used
    detail: str


@dataclass(frozen=True)
class RecoveryOutcome:
    """The VERDICT. `outcome` is decided by stepproof's seal, not by ActionResult.ok."""
    payment_id: str
    amount_paise: int
    outcome: Outcome
    cause: RootCause | None
    intervention: Intervention
    result: ActionResult | None
    verified: bool | None        # mirrors the stepproof Seal.verified for the money action
    evidence: str                # the observation the verdict rests on
    seal_hash: str               # ties this row to a ledger record. "" iff no action taken
    attempts: int = 1
    notes: list[str] = field(default_factory=list)
```

---

## §3 — The lane seam

Exactly one seam. The harness lane drives; the agent lane implements the loop.

**Agent lane provides** — `salvage/pipeline.py`:

```python
def build_pipeline(cfg: PipelineConfig) -> RecoveryPipeline: ...
```

**Harness lane codes against this Protocol** (declare it in `salvage/metrics.py`; do not
create a shared protocols module — one owner per file):

```python
class RecoveryPipeline(Protocol):
    def run_one(self, payment: FailedPayment) -> RecoveryOutcome: ...
    def close(self) -> None: ...
```

`PipelineConfig` is a frozen dataclass in `salvage/pipeline.py`, agent-owned, with these
fields and these defaults — the harness constructs it, so the names are contract:

```python
@dataclass(frozen=True)
class PipelineConfig:
    db_path: str = "run/salvage.db"
    ledger_path: str = "run/ledger.jsonl"
    offline: bool = True          # True = fixtures only, no network
    max_attempts: int = 3
    cost_cap_paise: int = 2000    # per record, across all attempts
    quiet_hours: tuple[int, int] = (22, 8)   # local hours, no NUDGE inside
    seed: int = 7
```

`run_one` **must not raise** for an individual record. A record that blows up is a
`RecoveryOutcome` with `outcome=Outcome.UNRESOLVED`, `verified=False`, and the exception
text in `evidence`. One bad record must never kill a 240-record batch.

---

## §4 — Module surface

Every symbol below is public API between lanes. Signatures are frozen.

### Harness lane

```python
# salvage/generate.py
def generate_batch(n: int = 240, seed: int = 7,
                   holdout_frac: float = 0.20) -> tuple[list[FailedPayment], list[GroundTruth]]
def write_batch(payments, truth, out_dir: str = "data") -> tuple[str, str]   # (payments.json, truth.json)
def load_batch(out_dir: str = "data") -> tuple[list[FailedPayment], list[GroundTruth]]

# salvage/metrics.py
@dataclass(frozen=True)
class Metrics: ...          # fields exactly as named in §7
def score(outcomes: list[RecoveryOutcome], truth: list[GroundTruth],
          split: str = "holdout") -> Metrics
def exceptions(outcomes: list[RecoveryOutcome]) -> list[RecoveryOutcome]

# salvage/audit.py
def audit(ledger_path: str) -> AuditSummary      # wraps stepproof Ledger.verify_chain()
def seals_for(ledger_path: str, payment_id: str) -> list[Seal]

# salvage/report.py
def render(metrics: Metrics, outcomes, audit_summary, out_path: str = "RESULTS.md") -> str

# salvage/cli.py   — typer app, entry point `python -m salvage`
#   salvage generate    salvage run    salvage report    salvage demo
```

### Agent lane

```python
# salvage/store.py       SQLite system of record — see §8
class Store:
    def __init__(self, path: str) -> None: ...
    def upsert_payment(self, p: FailedPayment) -> None: ...
    def record_attempt(self, payment_id: str, kind: ActionKind,
                       provider_ref: str, cost_paise: int) -> int: ...
    def mark_settled(self, payment_id: str, provider_ref: str, amount_paise: int) -> None: ...
    def attempts_for(self, payment_id: str) -> int: ...
    def spend_for(self, payment_id: str) -> int: ...
    def close(self) -> None: ...

# salvage/rzp.py
class RzpClient:
    def __init__(self, offline: bool = True, fixtures_dir: str = "fixtures") -> None: ...
    def create_payment_link(self, payment_id: str, amount_paise: int, email: str) -> dict: ...
    def fetch_payment_link(self, link_id: str) -> dict: ...
    def fetch_payment(self, rzp_payment_id: str) -> dict: ...

# salvage/detect.py
def detect(payments: list[FailedPayment]) -> list[FailedPayment]   # at-risk subset

# salvage/classify.py
def classify(p: FailedPayment) -> RootCause        # LLM when keys present, rules otherwise
def classify_rules(p: FailedPayment) -> RootCause  # deterministic, always available

# salvage/policy.py
def decide(p: FailedPayment, cause: RootCause, store: Store,
           cfg: PipelineConfig, now: float) -> Intervention

# salvage/execute.py
def execute(p: FailedPayment, plan: Intervention, store: Store,
            rzp: RzpClient) -> RecoveryOutcome    # every money path stepproof-gated
```

---

## §5 — stepproof integration rules

Cited from the real source. Violating any one of these produces a submission that
silently reports fake recoveries — the exact failure the project claims to prevent.

1. **Every custom verifier MUST accept `**kwargs`.**
   `verify.py:191` calls `verifier(**fields)` only when `_accepts_kwargs` passes, and
   `_accepts_kwargs` (`verify.py:216-223`) requires **every** bound argument name of the
   decorated function to be a parameter of the verifier — otherwise it calls `verifier()`
   with no arguments and you get a `TypeError` at the worst possible moment.
   Write `def _verify_link_paid(**kw) -> tuple[bool, str]:` — always.

2. **A verifier returns `(ok: bool, evidence: str)`.** Nothing else. `collectors.py` is
   the reference for tone: `"no such file: /tmp/r.txt"`, never `"False"`.

3. **Model output is never evidence.** `verify.py:199-200` flips a `True` to `False` when
   `is_narration(evidence)` fires, and `narration.py:25-34` triggers on openings like
   "I'll check…" or "I don't have access…". `RootCause.rationale` is model prose — it may
   go in `notes`, never in `evidence`. Compose evidence in salvage code from observed
   values: `f"rzp plink_A1 status=paid amount_paid=45000 fetched 2026-09-02"`.

4. **Evidence truncates at 300 chars, `claimed` at 300, each `args` value at 120**
   (`verify.py:203-205`). Front-load the decisive observation; never bury the verdict
   behind a preamble.

5. **One ledger per batch run, set once.** `get_ledger()` is a module-global singleton
   (`verify.py:22-29`). At CLI start call
   `stepproof.set_ledger(stepproof.Ledger(cfg.ledger_path))` exactly once. Never call
   `set_ledger` inside `run_one`.

6. **`Ledger.append` re-reads the whole file to find the previous hash**
   (`ledger.py:56-60`) — appending is O(n), so a batch is O(n²). Seal **money actions and
   terminal verdicts only**. Do not seal classification, detection, or policy decisions.
   At 240 records that is the difference between a snappy demo and a stalled one.

7. **`raises=False` on the batch path.** The default is `raises=True` (`verify.py:155`),
   which throws `VerificationError` and would kill the run. Use `raises=False` and read the
   returned `Seal.verified`. `@verified` seals either way (`verify.py:202`).

   **How the seal maps to an `Outcome` depends on what the verifier actually proved.**
   `False -> FAILED_VERIFICATION` always. `True` maps by action:

   | Action | What its verifier proves | Seal `True` maps to |
   |---|---|---|
   | `RETRY`, `PAYMENT_LINK` | money arrived at the provider | `RECOVERED` |
   | `NUDGE`, `ESCALATE` | the outreach was recorded | `UNRESOLVED` |

   *Corrected at integration.* This clause originally said `True -> RECOVERED` flatly, and
   the agent-loop Builder refused it: a sealed NUDGE proves an outreach happened, not that
   money moved. Counting it would push those rupees into `amount_recovered_paise` and
   rebuild the fake-revenue bug one layer up — the exact failure this project exists to
   prevent. The Builder was right and the contract was wrong.

8. **`actor` and `authorization` are mandatory on every money action.**
   `actor="salvage-agent"`, and an `authorization` naming the policy that permitted it.
   *Corrected at integration:* the example string here referenced `cfg`, which §4 never
   passes to `execute()`. Compose it from what `execute` actually holds —
   `f"policy:{plan.kind.value} cost={plan.cost_paise}p"`.
   Both default to empty (`ledger.py:31-32`), and an empty actor is the first thing an
   auditor flags.

9. **`sqlite_row_exists(db, table, where)` interpolates `where` directly**
   (`collectors.py:83`; the docstring at `:77` says so). The `where` clause must be
   composed from typed Python values in salvage code. Never from model output. Ever.

10. **`http_ok` cannot authenticate** — no headers, no auth argument
    (`collectors.py:56-70`). It cannot verify a Razorpay endpoint. Use a custom
    `verifier=` built on `RzpClient`. Do not try to bend `http_ok` into it.

---

## §6 — Razorpay boundary

Direct REST over `httpx`, HTTP Basic auth (`key_id`, `key_secret`), base
`https://api.razorpay.com/v1`. No SDK.

Keys come from `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`. **Neither is set right now.** So:

- `RzpClient(offline=True)` is the **default and the demo path**. It reads recorded JSON
  from `fixtures/` and never touches the network.
- `offline=False` requires both env vars. If either is missing, raise at construction with
  a message naming the missing variable. Never silently fall back — a silent fallback is a
  fake recovery, which is the one thing this project may not ship.
- Fixtures are **recorded from real test-mode responses** the first time keys exist
  (`salvage run --record`), not hand-written. A hand-invented fixture verified against
  itself is circular, and a judge will say so on camera.
- Fixture path: `fixtures/<endpoint>__<key>.json`, holding the raw response body.

Shapes salvage depends on (subset — ignore every other field):

```
POST /payment_links   -> {"id": "plink_...", "status": "created", "amount": <paise>,
                          "short_url": "https://rzp.io/i/..."}
GET  /payment_links/{id}
                      -> {"id": "plink_...", "status": "created|paid|cancelled|expired",
                          "amount_paid": <paise>, "payments": [...]}
GET  /payments/{id}   -> {"id": "pay_...", "status": "created|authorized|captured|failed|refunded",
                          "amount": <paise>, "error_code": "...", "error_description": "..."}
```

**Recovered means `status == "paid"` and `amount_paid >= amount_paise`** for a payment
link. A `201` from the create call is *not* recovery — closing that exact gap is the whole
project.

**For a payment, recovery means `status == "captured"` and nothing more.** *Corrected at
integration:* this clause originally also demanded `amount >= amount_paise`, which
`fetch_payment` cannot satisfy — it takes an id and nothing else (§4), so offline it can
only echo the recorded fixture amount. Gating on it failed 78 genuinely-captured retries
for a reason unrelated to whether money arrived. The evidence string must state plainly
that the amount was not independently confirmed. Online, with a real per-payment response,
the amount is observable and the check is worth restoring.

---

## §7 — Metric definitions

Computed on the **holdout split only** unless a field says otherwise. Frozen formulas —
the harness implements exactly these, and the numbers in the video are these numbers.

```python
@dataclass(frozen=True)
class Metrics:
    split: str
    n_at_risk: int
    amount_at_risk_paise: int
    n_recovered: int
    amount_recovered_paise: int
    recovery_rate_count: float        # n_recovered / n_at_risk
    recovery_rate_value: float        # amount_recovered / amount_at_risk   <- HEADLINE
    n_interventions: int              # records where kind != NONE
    intervention_precision: float     # n_recovered / n_interventions
    n_false_positive: int             # intervened AND ground truth would_self_heal
    false_positive_cost_paise: int    # sum of cost_paise over those
    fp_rate: float                    # n_false_positive / n_interventions
    n_suppressed: int
    n_unresolved: int
    n_failed_verification: int        # claimed success, real state disagreed  <- THE PITCH
    verification_gap_paise: int       # money a naive agent would have BOOKED and not received
    n_rules_classified: int           # root cause settled deterministically, no model call
    n_llm_classified: int             # model invoked — only where rules genuinely could not
    chain_intact: bool
    seals_total: int
```

`n_rules_classified` / `n_llm_classified` exist because the first judging criterion is **AI
Judgment**: forcing an LLM where a rule wins is explicitly marked down. Reporting that the
rules settled most of the batch and the model was reached for only the ambiguous tail is the
direct, numeric answer to that criterion. Do not hide it — lead with it.

Two hard rules:

- **`amount_recovered_paise` counts a record only when its stepproof seal has
  `verified is True`.** `ActionResult.ok` alone never moves the number. This is the single
  most important line in the codebase.
- **`verification_gap_paise` = Σ amount over `FAILED_VERIFICATION`.** Report it out loud.
  It is the number that proves the thesis, and no competitor will have it.

Every ratio guards its denominator: zero denominator yields `0.0`, never a `ZeroDivisionError`
and never a silent `nan` in a slide.

`COST_TABLE` — canonical, harness-owned in `metrics.py`; the agent lane imports it:

```python
COST_TABLE = {ActionKind.RETRY: 0, ActionKind.PAYMENT_LINK: 0,
              ActionKind.NUDGE: 25, ActionKind.ESCALATE: 1500, ActionKind.NONE: 0}
```

---

## §8 — SQLite system of record

Agent-owned (`salvage/store.py`), but the schema is contract because verifiers read it.

```sql
CREATE TABLE IF NOT EXISTS payments (
    payment_id   TEXT PRIMARY KEY,
    order_id     TEXT NOT NULL,
    customer_id  TEXT NOT NULL,
    amount_paise INTEGER NOT NULL,
    failed_at    REAL NOT NULL,
    gateway_code TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id   TEXT NOT NULL REFERENCES payments(payment_id),
    kind         TEXT NOT NULL,
    provider_ref TEXT NOT NULL DEFAULT '',
    cost_paise   INTEGER NOT NULL DEFAULT 0,
    created_at   REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS settlements (
    payment_id    TEXT PRIMARY KEY REFERENCES payments(payment_id),
    provider_ref  TEXT NOT NULL,
    amount_paise  INTEGER NOT NULL,
    settled_at    REAL NOT NULL
);
```

A settlement row is written **only after** the provider confirms the money arrived (§6).
The `settlements` table is what `sqlite_row_exists` checks. Writing that row on a `201`
would defeat the entire project.

---

## §9 — Invariants both lanes assume and neither may break

1. Money is `int` paise. No floats, anywhere, in any money field.
2. The agent lane never imports `GroundTruth` and never reads `truth.json`. QA greps for it.
3. `Outcome` is decided by a stepproof seal, never by `ActionResult.ok`.
4. `run_one` never raises. Records fail individually or not at all.
5. One ledger, one SQLite file, per run — paths come from `PipelineConfig`.
6. Nothing writes to `stepproof/` or to `C:\Users\rushi\OneDrive\Desktop\agentse`.
7. Every seal for a money action carries a non-empty `actor` and `authorization`.
8. `offline=True` performs zero network calls. Assert it in a test.
9. No file outside your lane's ownership table in `PLAN.md` is created, edited, or deleted.

---

## §10 — Domain calibration (researched, not invented)

Every number and identifier below came from Razorpay's own error documentation and from
published failed-payment recovery benchmarks. **Do not invent alternatives.** Synthetic data
that does not look like the real distribution is the fastest way to lose a payments judge.

### 10.1 — Real Razorpay `reason` → `FailureReason`

`gateway_code` holds the left column verbatim. `source` holds the middle column verbatim.
The generator samples from this table; the rules classifier inverts it.

| Razorpay `reason` | `source` | `FailureReason` |
|---|---|---|
| `bank_not_available` | gateway | BANK_DOWN |
| `bank_technical_error` | gateway | BANK_DOWN |
| `bank_cutoff_in_progress` | gateway | BANK_DOWN |
| `gateway_technical_error` | gateway | BANK_DOWN |
| `insufficient_funds` | customer | INSUFFICIENT_FUNDS |
| `transaction_limit_exceeded` | customer | INSUFFICIENT_FUNDS |
| `transaction_daily_limit_exceeded` | customer | INSUFFICIENT_FUNDS |
| `credit_limit_exceeded` | gateway | INSUFFICIENT_FUNDS |
| `authentication_failed` | customer | AUTH_FAILED |
| `incorrect_otp` | customer | AUTH_FAILED |
| `otp_expired` | customer | AUTH_FAILED |
| `incorrect_cvv` | customer | AUTH_FAILED |
| `invalid_vpa` | customer | AUTH_FAILED |
| `card_number_invalid` | customer | AUTH_FAILED |
| `incorrect_card_details` | customer | AUTH_FAILED |
| `user_not_registered_for_netbanking` | customer | AUTH_FAILED |
| `card_expired` | customer | CARD_EXPIRED |
| `mandate_creation_declined` | gateway | MANDATE_EXPIRED |
| `payment_risk_check_failed` | gateway | RISK_BLOCKED |
| `compliance_violation` | business | RISK_BLOCKED |
| `debit_instrument_blocked` | customer | RISK_BLOCKED |
| `card_declined` | gateway | **ambiguous — see 10.4** |
| `""` (abandoned, no gateway reason) | customer | CHECKOUT_DROPOFF |

### 10.2 — Recovery-rate calibration

The generator must be tuned so that a *good* policy lands inside the published band. A
submission reporting 95% recovery is not impressive, it is disbelieved.

| Approach | Published recovery rate |
|---|---|
| Generic daily retries | 20–30% |
| Dunning emails alone | ~30% ceiling |
| Fixed 1/3/7-day schedule | 40–60% |
| Reason-specific smart retries | 50–65% |
| Best-in-class SaaS | 70–85% |

**Target for salvage on the holdout split: 45–65% by value.** If `recovery_rate_value`
exceeds 0.80, the generator is too generous and the number is worthless — say so in
`BLOCKERS.md` rather than shipping it. Roughly **1 in 5 soft declines approves on a properly
timed second attempt with no change to the instrument**; that is the physical mechanism the
generator is modelling, and `would_self_heal` at 15–22% is consistent with it.

### 10.3 — Timing is the policy (this is what "smart" means)

Retrying the same instrument immediately is the naive baseline that recovers 20–30%. Timing
by decline reason is what lifts it. Encode this in `policy.decide()`:

| Reason | Action and timing |
|---|---|
| BANK_DOWN | RETRY quickly — downtime is transient. Same instrument, short backoff. |
| INSUFFICIENT_FUNDS | **Wait 72h**, retry day 3 and day 7; bias toward the 1st and 15th (payday). Retrying at hour 1 is worse than not retrying. |
| AUTH_FAILED | PAYMENT_LINK — the customer must re-authenticate; a silent retry cannot fix an OTP. |
| CARD_EXPIRED / MANDATE_EXPIRED | PAYMENT_LINK — the instrument is dead, no retry can revive it. |
| CHECKOUT_DROPOFF | NUDGE inside 24h, then PAYMENT_LINK. Recovery decays sharply after 72h and is near-dead after two weeks. |
| RISK_BLOCKED | ESCALATE only. **Never an automated retry** — that is the "compliant escalation" the track bar asks for. |

Attempt budget: **3–5 attempts inside a 10–14 day window.** `max_attempts=3` is the default
and is inside that band.

### 10.4 — Where the LLM is allowed to exist

The track's first judging criterion is **AI Judgment**: forcing an LLM into a problem a rule
solves better is explicitly marked down. So the architecture is:

> **The LLM is sandboxed and stripped of execution authority. Its only job is to read
> unstructured context and return a typed diagnostic proposal. It never chooses an action,
> never touches money, and never produces evidence.**

Concretely: 21 of the 23 reasons in 10.1 are a deterministic lookup — `classify_rules`
settles them with no model call. The model is reached only for `card_declined` (genuinely
ambiguous: could be funds, risk, or issuer), for an empty/unrecognised reason, and for free-text
merchant notes. It returns a `RootCause`; `policy.decide()` — pure Python — chooses the action;
`execute()` — stepproof-gated — moves the money. The rationale it writes is prose and is
**never** evidence (§5.3).

Report `n_rules_classified` vs `n_llm_classified` prominently. "The model was invoked on 11% of
the batch, because the other 89% was a lookup" is a better answer to *AI Judgment* than any
architecture diagram.
