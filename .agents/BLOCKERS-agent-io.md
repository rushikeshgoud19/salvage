# BLOCKERS — lane agent-io (A1, A2, A3)

Nothing here stopped the lane. These are contract tensions I resolved deliberately rather
than diverging from silently, plus two limits the integrator has to know about.

## 1. §10.4 vs §10.1 on an empty gateway reason — resolved toward the rules

§10.1 gives `""` (abandoned, no gateway reason) a deterministic mapping to
`CHECKOUT_DROPOFF`. §10.4 says the model is reached for "an empty/unrecognised reason".
Following §10.4 literally would send every checkout-dropoff record to the model — one of
seven failure families, roughly 14% of a batch on its own, and `card_declined` on top of
it. That breaches the ≤15% cap in A3 and the QA line `n_llm_classified / n_at_risk ≤ 0.15`,
and it is precisely the reflex judging criterion #1 marks down: an LLM re-deriving a lookup
the gateway already published.

`classify_rules` therefore settles 22 of the 23 rows, including `""`. The model is reached
only for `card_declined` and for a `reason` string absent from the table. Measured on a
batch biased to 8% `card_declined` + 2% unrecognised, model share is ~10%.

Free-text merchant notes, the third case §10.4 names, are not implemented: no field in
`FailedPayment` carries merchant free text, so there is nothing to read. Sniffing
`gateway_description` for "free text" would have sent the whole dropoff family to the model
by accident.

## 2. Fixtures are hand-seeded from Razorpay's documented response schema, not recorded

§6 requires fixtures recorded from real test-mode responses and says a hand-invented fixture
verified against itself is circular. `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` do not exist,
so the six files in `fixtures/` were shaped by hand from Razorpay's published payment-link
and payment response bodies. This is a real limitation and the video should say so plainly.

It is mitigated, not hidden: `offline=False` **is** record mode — every response body the
online client receives is written straight back over `fixtures/<endpoint>__<status>.json`,
so one authenticated run replaces the entire seeded set with real traffic. And the
settlement check the verifiers rely on reads SQLite, which is real state either way.

## 3. `fetch_payment` cannot know the record's amount offline

The frozen signature passes only `rzp_payment_id`, so offline the client has no way to know
what the record was worth and echoes the recorded `amount`. **Verify a RETRY on
`status == "captured"`** (as A5's done-when says); do not gate it on that echoed amount, or
retries will pass or fail by fixture accident. `fetch_payment_link` has no such problem — it
replays the link this client issued and knows its amount exactly.

## 4. The engineered cohort is a share of issued links, not a fixed count of records

`_STUCK_PCT = 6` percent of the links `RzpClient` issues never leave `created`. The number of
*records* in the cohort therefore depends on how many the policy routes to `PAYMENT_LINK`:
measured 9 when half of a 240-record batch earns a link, 17 if every record does. If the
merged run lands far from 8, `_STUCK_PCT` in `salvage/rzp.py` is the single knob — cohort
membership stays deterministic at any value.

## 5. `tests/test_rzp.py` is not in the PLAN ownership table

A2's tests live in `tests/test_store.py` alongside A1's, with a docstring saying why. This
lane may not create a file outside its ownership row. Rename or split post-merge if wanted.
