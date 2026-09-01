# Questions a reviewer will have

Answered directly, including the ones where the answer is a limitation.

---

## On the numbers

### "Your data is synthetic. You wrote the generator, the policy, and the scorer."

Correct, and it is the fairest criticism of this submission. Four things narrow it:

1. The failure taxonomy is **Razorpay's own** — all 23 documented `reason` codes with their
   real `source` values, not a taxonomy I invented.
2. The calibration comes from **published recovery benchmarks**, so the batch is tuned to a
   range the industry reports rather than one that flatters the agent.
3. The **rails are real.** [`LIVE-RUN.md`](LIVE-RUN.md) is the same pipeline against live
   Razorpay test mode: five real payment links, real state fetched back, real seals.
4. The engineered failure signature — `status=created, amount_paid=0` — turned out **not to
   be synthetic at all.** It is exactly what an unpaid Razorpay link returns.

What remains true: the *records* are generated. On real merchant traffic the recovery rate
would differ. **The gap between claimed and verified would not**, because it is a property of
how the two are measured, not of what the payments are.

### "How do I know 53% isn't cherry-picked?"

You do not have to take my word for it: it partly *is*, and I said so before you asked.
Seed 7 gives 53.0%; the mean across 20 independent batches is **44.1%** with sd 12.8pp.
That is in [`ROBUSTNESS.md`](ROBUSTNESS.md), reproducible with `python -m salvage sweep`.

The number that does not move: the naive agent overstated in **20 of 20** batches.

### "44% recovery isn't very good."

It is roughly where published benchmarks put reason-specific smart retries. A submission
reporting 90% on a batch like this is reporting its own bug — which is precisely what the
comparison in the README demonstrates, since the unverified scoring of *this same run*
reports 91.2%.

---

## On the AI

### "The model runs on 4.2% of records. Is this even an AI project?"

The first judging criterion says forcing an LLM where a rule works better is marked down. 21
of 23 Razorpay reason codes are a deterministic lookup — using a model there would be slower,
costlier, less accurate and non-reproducible.

The model is used exactly where rules fail, and it is measured there: **0/7 → 6/7** on the
ambiguous tail, lifting holdout root-cause accuracy from 95.8% to 100.0%.

The harder version of this question is *"could you have used AI for more?"* Yes — and I think
most of those uses would have been worse. The one I would genuinely add is free-text merchant
notes and customer support threads, which are unstructured in a way rules cannot touch. The
synthetic batch has no such field, so adding it would have meant inventing data to justify a
model call. That is the wrong order.

### "What if the model is wrong?"

Then a record gets the wrong *diagnosis*, and that is all. The model returns a typed
`RootCause`; `policy.decide()` is pure Python and chooses the action; `execute()` moves the
money; stepproof verifies the outcome. A wrong diagnosis produces a wrong-but-bounded action
that is still cost-capped, attempt-capped, time-gated, and verified afterwards.

Confidence below 0.5 is discarded for the rules verdict. An out-of-vocabulary answer fails
`FailureReason(...)` and is rejected. A model that is unreachable changes nothing: the rules
settle every record and the run completes.

### "Can someone prompt-inject it?"

Tested with six live attacks through `gateway_description`, including a forged system turn, a
direct action instruction, a schema escape and a credential-exfiltration attempt. All six
failed. Details in [`THREAT-MODEL.md`](THREAT-MODEL.md#t3--prompt-injection-through-gateway-text).

The important part is not that the model held. It is that **it would not have mattered if it
hadn't** — the model has no execution authority to hijack.

### "Why Mistral and not GPT or Claude?"

Because its free tier needs no credit card, which keeps the project reproducible by anyone.
The transport is OpenAI-compatible, so Gemini, Groq, Cerebras and OpenRouter are two
environment variables and zero code. The model is not the interesting part and the
architecture is deliberately built so it can be swapped.

---

## On the engineering

### "Did agents write this? Did you actually build it?"

Yes to both, and the repository does not hide it.

I wrote [`CONTRACT.md`](../.agents/CONTRACT.md) — the frozen interface, the shared types, the
ten stepproof rules, the Razorpay taxonomy, the metric formulas — and
[`PLAN.md`](../.agents/PLAN.md), the twelve tasks partitioned into file-disjoint lanes. Four
agents implemented those lanes in parallel worktrees. I integrated, verified and graded the
result in [`QA-REPORT.md`](../.agents/QA-REPORT.md).

What that got me was throughput. What it did **not** get me was correctness, and the record
shows exactly where:

- Every lane passed its own tests. **Three defects existed only where the lanes met** — a
  swallowed `AttributeError` hiding 20 failures, an amount gate the interface could not
  satisfy costing 78 false failures, and a demo cohort too thin to demonstrate anything.
  Finding those was integration work, not agent work.
- **The double-charge was caught by none of them.** Not by four agents, not by 441 tests, not
  by any lane review. It surfaced from asking the question a payments engineer asks first:
  *can this thing take money twice?* — and then writing the test that answers it.
- **CI caught that `pip install .` had never worked.** Every local check passed because my
  machine already had the missing piece.

If the takeaway you want is "can this person direct agents and still own the outcome," the
`.agents/` directory is the honest answer, including the contract clauses annotated where I
got them wrong and the lane that overruled me and was right.

### "Why no dashboard?"

Because the deliverable is a claim about correctness, and a chart is a weak way to make one.
`RESULTS.md`, the ledger, and a reproducible CLI can each be checked by a skeptic; a
dashboard mostly asks to be believed. If this went to a merchant, the UI would matter
enormously — but it would be built on top of numbers that had been made trustworthy first,
and that ordering is the argument.

### "Why not LangChain or CrewAI?"

Nothing here needs an agent framework. There is one loop, one decision point, and one model
call on 4.2% of records. A framework would have added a dependency, an abstraction layer, and
a place for the model to acquire execution authority — which is the exact property this
design removes on purpose. stepproof ships adapters for LangChain, CrewAI and the OpenAI
Agents SDK, so the verification layer works inside those stacks for anyone who does need one.

### "Isn't stepproof just logging?"

No. A log records what a component *said*. A seal records what the world *showed*, alongside
what was claimed, and refuses to accept prose in place of an observation. The difference is
load-bearing here: 108 seals in a run say `verified=False` on actions whose API calls all
returned success. A logger would have written "success" 108 times.

It is also hash-chained, so the record cannot be quietly edited after the fact —
demonstrated by forging one seal and watching `verify_chain()` name the record.

### "Why SQLite?"

Because the system of record needs to be durable, queryable and inspectable by a reviewer
with no setup. In production it is Postgres and the schema barely changes.
[`PRODUCTION.md`](PRODUCTION.md) covers what does.

---

## On scope

### "Does this scale?"

Not as written, and I measured where it stops rather than guessing.
`stepproof.Ledger.append()` re-reads the chain for the previous hash, so a single append
against a million-seal chain takes about two seconds. That is a wall, and the fix belongs in
stepproof — which is what having the audit layer as a separate library buys you.

The bigger structural change is that verification has to move from action time to webhook
time: recovery is asynchronous, and an agent that checks once, immediately, will under-report
on real traffic no matter how good its policy is. That is why the live run shows ₹0 recovered
and why that number is correct. All of it is in [`PRODUCTION.md`](PRODUCTION.md).

### "What would you do next?"

In order: webhook-driven verification, an idempotency key per `(payment_id, attempt_no)`,
settlement-report reconciliation instead of API status, and a timezone field so quiet hours
mean 22:00 IST rather than 22:00 wherever the server happens to live.

Then the part that is actually interesting — pointing the same verification layer at refunds,
payouts, mandates and disputes, because the failure it catches is not specific to recovery.
It is specific to agents.
