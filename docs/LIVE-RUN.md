# Live run — real Razorpay test mode

The demo in the README runs offline against recorded fixtures, which invites a fair
question: *are the rails real, or only the recording?*

So here is the same pipeline, unmodified, with `offline=False`, talking to
`api.razorpay.com` with test-mode credentials. Real HTTP. Real payment links. Real state
fetched back. Real seals.

**No real money can move.** Test-mode keys (`rzp_test_…`) operate on Razorpay's sandbox;
no live-mode transaction was made at any point in this project.

---

## Transcript

```
key: rzp_test_TWd...   TEST MODE - no real money can move

slice: 10 holdout records, Rs15,872.88 at risk

RzpClient(offline=False) constructed -> live api.razorpay.com

payment_id            action        outcome               evidence
--------------------------------------------------------------------------------------
pay_I9M2BNfvUhzDt3    payment_link  failed_verification   rzp plink_TWiPOzX5UoHPsJ status=created amount_paid=0 ex
pay_PGJgq6sovciCwO    payment_link  failed_verification   rzp plink_TWiPQLFrNOoMUC status=created amount_paid=0 ex
pay_undIxoSUQV5Dv4    retry         failed_verification   rzp fetch_payment pay_undIxoSUQV5Dv4 raised RuntimeError
pay_kOLHaQr3PYsJ0d    payment_link  failed_verification   rzp plink_TWiPRUQMvOiwP0 status=created amount_paid=0 ex
pay_zwiPSaTan5DjCH    retry         failed_verification   rzp fetch_payment pay_zwiPSaTan5DjCH raised RuntimeError
pay_Fmrc5P7sAAoyET    payment_link  failed_verification   rzp plink_TWiPSeRBkpYdy5 status=created amount_paid=0 ex
pay_a3Xql3yRAQaky3    retry         failed_verification   rzp fetch_payment pay_a3Xql3yRAQaky3 raised RuntimeError
pay_DlYH7Pin7pYbJ7    payment_link  failed_verification   rzp plink_TWiPTtgEQMecUx status=created amount_paid=0 ex
pay_KXkAgbfHsy1TsX    none          suppressed            no rail used for pay_KXkAgbfHsy1TsX: timing_window (insu
pay_CpcAEOZfo5JLaY    payment_link  unresolved            payment_link for pay_CpcAEOZfo5JLaY raised RuntimeError:
--------------------------------------------------------------------------------------

10 records in 5.4s against LIVE test mode
  at risk                       Rs   15,872.88
  a naive agent would report    Rs   10,807.55   (every create returned 2xx)
  salvage verifies ARRIVED      Rs        0.00   (nobody paid these links)
  seals 9, chain INTACT, failed 9
```

---

## What this shows

**Five real payment links were created** — `plink_TWiPOzX5UoHPsJ`, `plink_TWiPQLFrNOoMUC`,
`plink_TWiPRUQMvOiwP0`, `plink_TWiPSeRBkpYdy5`, `plink_TWiPTtgEQMecUx`. Every one returned a
clean `201`. Every one was then re-fetched and found at `status=created, amount_paid=0`,
because nobody paid them — there is no customer on the other end of a sandbox link.

**An agent that trusted those `201`s would report ₹10,807.55 recovered. salvage reports
₹0.00, and can show you why for each record.** That is the project's whole claim, executed
against live infrastructure rather than a recording.

Note that `status=created, amount_paid=0` is exactly the signature of the engineered failure
cohort in the offline demo. It was never a synthetic shape. It is simply what an unpaid
Razorpay link looks like.

---

## Two failures, neither of them planned

### 1. `GET /payments/{id}` — "The id provided does not exist"

Three RETRY records failed this way:

```
razorpay GET /payments/pay_undIxoSUQV5Dv4 returned 400:
{"error":{"code":"BAD_REQUEST_ERROR","description":"The id provided does not exist",
"source":"internal","step":"payment_initiation","reason":"input_validation_failed"}}
```

**This is a real limitation and it is worth stating plainly.** salvage's `payment_id`s are
generated for the synthetic batch; they are not Razorpay payment ids, so re-presenting one
against the live API cannot work. RETRY can be exercised end to end only against payments
that actually exist in the account.

What matters is what salvage *did* about it: the verifier could not confirm a capture, so
the record was sealed `verified=False` and reported as `FAILED_VERIFICATION`. It did not
assume, did not retry blindly, and did not quietly count the record as recovered. **An
absence of evidence was treated as an absence of recovery**, which is the behaviour the
whole design exists to produce.

### 2. HTTP 429 — Razorpay rate-limited us mid-run

```
razorpay POST /payment_links returned 429:
{"error":{"code":"BAD_REQUEST_ERROR","description":"Too many requests"}}
```

Five links in roughly four seconds was enough to trip Razorpay's rate limiter. **This was
not planned, not simulated, and not something I knew about before running it.**

The batch did not stop. The record became a single `UNRESOLVED` row carrying the verbatim
provider error, the remaining records ran, the ledger stayed intact, and the run exited
cleanly. That is the `run_one` isolation contract holding on live infrastructure against a
failure mode nobody wrote a test for.

If this were going to production the fix is unremarkable — a token-bucket limiter and
retry-with-backoff on `429` specifically, since it is the one error class where the right
answer really is to try again. It is deliberately not in the submission: adding an untested
rate limiter the night before a deadline is how a working system becomes a broken one.

---

## Reproduce it

```bash
export RAZORPAY_KEY_ID=rzp_test_...
export RAZORPAY_KEY_SECRET=...
python -m salvage run --record        # refreshes fixtures from real test-mode traffic
```

The committed fixtures under `fixtures/` were restored after this run, so the offline demo
stays byte-for-byte deterministic. A live run writes its own.
