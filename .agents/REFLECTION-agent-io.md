# REFLECTION — lane agent-io (A1, A2, A3)

## What was hard, and what it changed

**Making the engineered failure honest.** The first shape I considered put the stuck cohort
in per-record fixture files. That is a lie a judge can see: the fixture would be the reason
the record fails, so the demo would prove nothing about the agent. Moving it into
`rzp.py` — a cohort chosen by hashing the payment id, with a create response that is
byte-for-byte indistinguishable from a healthy one — makes the point properly. Nothing in
the `201` says which records are doomed. Only the second call, the one a naive agent never
makes, tells you.

The same reasoning forced a third link fate. If ordinary non-recovering links also sat at
`created`, the cohort would be invisible: "stuck" would just mean "not paid". Ordinary links
now lapse to `expired`, so the engineered eight are the only ones whose evidence reads
`status=created amount_paid=0` — legible in `RESULTS.md` with no human narrating it.

**Statelessness cost more than it was worth.** I wanted `fetch_payment_link` to answer from
the link id alone, so a fresh client would replay identically. It cannot: the amount is not
recoverable from an id, and encoding it into one would have been a clever lie. The client
now replays links it issued, and raises a named error for a link it never saw, rather than
inventing a plausible body. `fetch_payment` still has the unsolvable version of that problem
and it is written down in BLOCKERS rather than papered over.

**The LLM question was a contract conflict, not a coding problem.** Reading §10.4 literally
would have pushed model use past the cap the same document sets. Resolving it took reading
§10.1, §10.4, A3 and the QA checklist together and choosing the reading that survives all
four — rules settle 22 of 23 reasons, the model gets `card_declined` and genuine unknowns.
That is written up as BLOCKERS #1 instead of being absorbed silently.

## What I would change with more time

`detect()` cannot see the store, so "no settlement, attempts under cap" is only half
enforceable there; the store half lives in `policy.decide`, which does have the store. It
works, but the concern is split across two modules and the contract signature is the reason.

## What I would not change

Refusing to guess. With no `ANTHROPIC_API_KEY` on the machine, an unsettleable
`card_declined` comes back `UNKNOWN` rather than wearing a fabricated cause at a made-up
confidence. In a project whose entire claim is that it cannot book a recovery that did not
happen, a classifier that invents diagnoses would have undercut the thesis in the same repo.
