---

# Step 6: The Message Batches API — Cost, Latency, and the Multi-Turn Limitation

## What this demonstrates

All 6 tickets from Steps 1-5, submitted as ONE batch using the EXPLICIT
prompt + `EXTRACT_TOOL` schema from Step 3, instead of 6 separate
synchronous calls. Three things to understand, not just recite:

1. **Cost**: batch requests run at 50% of standard synchronous pricing —
   same model, same tokens, half the price. The trade is turnaround time,
   not quality or capability.

2. **Latency**: asynchronous, with up to a 24-hour processing window
   (often much faster in practice, but never guaranteed). Wrong for
   anything user-facing/real-time; right for volume work nobody's waiting
   on synchronously — end-of-day reprocessing, backfilling historical
   data, bulk classification.

3. **The multi-turn limitation — the one people miss**: a batch request
   is ONE complete, single-shot message exchange. If the model responds
   with a `tool_use` block, that's the end of that batch item — there's
   no mechanism to submit the tool result and continue the same
   conversation inside the batch. Domain 1's coordinator/retry pattern,
   or any multi-turn agentic loop, cannot happen inside a single batch
   item. Continuing a conversation started in a batch requires either a
   synchronous follow-up call or a new batch entirely.

## No mock mode — deliberately

Unlike every other step, this one has no simulated version. Batch status,
polling, and a genuinely asynchronous processing window aren't things
that can be honestly faked — a mock would just be lying about timing in
a way that defeats the entire point of understanding what batch actually
costs you in turnaround. Requires a real `ANTHROPIC_API_KEY`.

## Try it yourself

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 step6_batch_api.py
```

It submits the batch, polls for up to 10 minutes (batches often complete
faster than the 24-hour max in practice, but don't assume — if it doesn't
finish in the demo window, that's normal, not a bug; the batch ID is
printed so you can check back later).

**Once you have results, compare directly against Step 3's synchronous
run of the same tickets:**
1. Do the actual `total_cost_usd`-equivalent numbers show roughly 50%
   savings for identical token counts? Verify the real discount rather
   than trusting the documented rate blindly.
2. How long did it actually take to complete, versus the ~12 real seconds
   per ticket we saw in Domain 2's synchronous CI script?
3. Do the extracted values match Step 3's EXPLICIT+schema results for the
   same tickets? They should — batch uses the identical underlying model
   and request, just queued differently.

## Design principle worth defending in an exam-style answer

**When would you choose batch over synchronous, concretely, for THIS
support-ticket pipeline?** Real-time customer-facing triage (a ticket
needs a category the moment it's submitted) must stay synchronous —
users aren't waiting 24 hours for a response. But re-classifying a
year of historical tickets to backfill a new `issue_category` taxonomy,
or running a nightly batch to compute aggregate sentiment trends, are
exactly the volume-not-time-sensitive workloads batch is built for — half
the cost, and nobody's blocked waiting on it.

**Why can't a multi-turn agentic pipeline (like Domain 1's coordinator)
run inside a single batch item?** Batch requests are resolved
independently and asynchronously — there's no live connection to send a
tool result back into mid-conversation the way a synchronous session
keeps state open. Each batch item is a complete, closed transaction.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| None — ran cleanly on the first try. Two real findings worth documenting below aren't bugs, they're confirmed behavior. | — | — |

## Real results

**Completion time**: 135 seconds for 6 tickets — nowhere near the 24-hour
ceiling. Confirms "batches often complete much faster in practice" with
an actual number, not just the documented worst case.

**Result ordering — a real, concrete confirmation of a documented
gotcha**: results returned in the order `ticket-4, ticket-3, ticket-1,
ticket-6, ticket-5, ticket-2` — NOT submission order. This is exactly
what the docs warn about ("results are not guaranteed to be in the same
order as requests"), now confirmed directly rather than taken on faith.
**Any consumer of batch results must map by `custom_id`, never by
position** — code that assumes result index 0 corresponds to request
index 0 will silently mismatch every single result.

**Correctness matches Step 3's synchronous run exactly**: ticket 4
(`urgency: high`, `refund_requested: null`), ticket 5 (`low`, `null`),
ticket 6 (`other`, `low`, `requires_escalation: true`) all match Step 3's
real EXPLICIT+schema results precisely. Batch mode doesn't change model
behavior — same model, same reasoning, purely a difference in
cost/delivery mechanism, confirmed with real matching data rather than
assumed.

**Cost — computed from real token counts, not assumed**: batch results
return raw `input_tokens`/`output_tokens` per request but no inline
`total_cost_usd` the way Domain 2's synchronous CLI JSON output did — cost
had to be computed manually against published per-token rates. Using
this run's actual totals (6,089 input tokens, 879 output tokens) against
Sonnet 4.6's confirmed current pricing ($3/$15 per M standard, $1.50/$7.50
per M batch):

| | Input cost | Output cost | Total |
|---|---|---|---|
| Synchronous | $0.018267 | $0.013185 | $0.031452 |
| Batch | $0.009134 | $0.006593 | $0.015726 |
| **Savings** | | | **$0.015726 (exactly 50%)** |

**The absolute savings here (under 2 cents) is irrelevant — that's the
actual lesson.** The same 50% ratio, extrapolated to this run's average
tokens/ticket at 100,000 tickets/month, is **~$262/month saved**. Batch
is a volume lever: meaningless for a 6-item demo, real money at
production scale. Don't evaluate whether batch is "worth it" by looking
at a small test run's dollar figure — look at the percentage, applied to
your actual volume.

## Exercise 1 — complete

All 6 concepts covered: vague vs. explicit criteria, targeted few-shot,
`tool_use` schema design, `tool_choice` modes, validation-retry loops,
and the Batches API. Every step has real, verified data — including
several honest corrections where the first attempt tested the wrong
thing or a mock's assumption didn't hold. Ready for the Domain 3 quiz.
