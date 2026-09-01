# What would have to change to run this for real

This repository is a batch script that proves an idea. It is not a system, and pretending
otherwise would be the least useful thing it could do. This document is the honest gap
between the two, with numbers where I measured them.

It is also the answer to the question I would ask a candidate who showed me salvage:
*"fine — now run it on a Tuesday at Razorpay volume."*

---

## 1. Polling must become webhooks

**Today.** After acting, salvage re-fetches provider state immediately and seals the answer.
A payment link created ten seconds ago is `status=created` because nobody has paid it yet —
which is correct, and also means the recovery verdict is *premature* rather than wrong.

**Why it matters.** Recovery is not synchronous. A payment link is paid hours or days later.
An agent that verifies once, immediately, will report near-zero recovery on live traffic no
matter how good its policy is — which is exactly what the [live run](LIVE-RUN.md) shows.

**The change.** The seal moves from *action time* to *outcome time*. `payment_link.paid` and
`payment.captured` webhooks drive verification; the action itself is sealed as *dispatched*,
and a second seal — chained to the first by `payment_id` — records what actually arrived.
The verdict becomes a state machine over the payment's lifetime rather than a single check.

This is the single biggest structural difference between the demo and a product, and it is
why the offline batch is honest about being a batch.

---

## 2. The ledger cannot stay a JSONL file

`stepproof.Ledger.append()` re-reads the entire chain to find the previous hash
(`ledger.py:56-60`), so appending is O(n) and a run is O(n²). I measured it:

| chain length | per-append |
|---|---|
| 500 | 8.98 ms |
| 1,000 | 9.84 ms |
| 2,000 | 11.75 ms |
| 4,000 | 15.74 ms |

Slope ≈ **0.0019 ms per existing seal**. Extrapolated, **a single append against a
1,000,000-seal chain takes roughly two seconds.** At Razorpay volume that is not a
performance problem, it is a wall.

**The change, and it is small:** keep the tip hash in memory (or in a single-row table) and
stop re-reading. Chaining is unaffected — `verify_chain()` still recomputes from disk, which
is the operation that has to be trustworthy, and it can stay O(n) because it runs on demand
rather than on every write. Storage becomes an append-only table partitioned by day, with
periodic checkpoint hashes so verification does not need the whole history.

That is a change to **stepproof**, not to salvage — which is the point of the layer being a
separate library with its own tests.

---

## 3. Idempotency has to be real

Today the rerun path is closed: `already_settled` is the first stopping rule and a settled
payment gets no money rail ([threat model T1](THREAT-MODEL.md)). What is *not* closed is the
crash window — a create request that succeeded while the client never saw the response.

**The change.** A deterministic `Idempotency-Key` per `(payment_id, attempt_no)` on every
mutating call, and an `attempts` row written *before* the call rather than after, so a
replay after a crash finds the intent already recorded.

---

## 4. Reconciliation is the real ground truth

The demo treats "the provider says `paid`" as final. A payments company does not. Money is
real when it settles, and settlement is T+1 or T+2 with reversals, chargebacks and
partial refunds arriving afterwards.

**The change.** `settlements` stops being written from an API status and starts being written
from the settlement report. The verifier gains a third state beyond confirmed and refuted:
*pending settlement*. `Seal.verified` already models this — it is `bool | None`, and `None`
means nobody has checked yet, which is exactly the right shape for "authorised but not yet
settled." salvage currently never emits `None`. A production version would, constantly.

---

## 5. What breaks first, in order

1. **Verification timing** — immediate re-fetch reports failure for recoveries that are
   simply not finished. Fixed by webhooks (§1).
2. **Ledger append** — quadratic, measured above. Fixed in stepproof (§2).
3. **Rate limits** — Razorpay returned `429` at five links in four seconds during the live
   run. A token bucket with backoff on `429` specifically, since it is the one error class
   where retrying is the correct response.
4. **Concurrency** — one SQLite file, one process. Becomes a queue with per-payment ordering
   so two workers can never act on one payment at once.
5. **Timezone** — quiet hours and payday logic read the server's local time, so a UTC host
   nudges Indian customers at 03:30 IST. A `timezone` field and `zoneinfo`.

---

## 6. Where the verification layer goes next

salvage is one loop. **stepproof is not about recovery at all** — it is about any agent
action whose success is asserted rather than observed, and a payments company has those
everywhere:

| Agent action | The claim | What real state would have to say |
|---|---|---|
| Recovery (this repo) | "I recovered the payment" | link `paid`, or payment `captured` |
| Refunds | "I refunded the customer" | a refund object exists, `processed`, correct amount |
| Payouts | "I paid the vendor" | payout `processed`, and the bank reference resolves |
| Subscriptions | "I fixed the mandate" | a live mandate with a next-charge date |
| Disputes | "I submitted evidence" | the dispute shows evidence `submitted` before the deadline |
| KYC / onboarding | "I verified the merchant" | the document check returned a decision, not a queue position |

Every row has the same shape: a tool returns success, an agent relays it, and nobody looks.
The rule that makes an agent deployable on any of them is the same one — **the claim and the
evidence are different objects, and only the evidence counts.**

That generality is why the verification layer is a separate library with its own tests and
its own CI, and why salvage consumes it as a dependency and never edits it. An auditor that
ships inside the thing it audits is not an auditor.
