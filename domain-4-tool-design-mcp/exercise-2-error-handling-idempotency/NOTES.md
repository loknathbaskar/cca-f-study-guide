# Domain 4, Exercise 2: Structured Errors, Partial Success, and Idempotency

## What this demonstrates

Three separate real multi-turn tests — Claude calls a tool, we return a
crafted structured result, Claude reacts, we observe what happens next.
No mock mode: simulating realistic multi-turn model reasoning by hand
would just mean scripting the expected answer, which defeats the purpose
of testing it. Requires a real `ANTHROPIC_API_KEY`.

**Test A — structured errors change behavior appropriately.** A single
`cancel_order` tool returns one of three structured error shapes:
- `not_found`, `isRetryable: false`
- `rate_limited`, `isRetryable: true`
- `permission_denied`, `isRetryable: false`

Does Claude's next action differ correctly per error — does it actually
attempt a retry ONLY for the rate-limited case, and correctly stop/report
for the two non-retryable ones, rather than treating all three failures
identically?

**Test B — partial success is preserved, not flattened.** A batch
`cancel_orders` call for 5 orders returns 3 successes and 2 failures,
each failure with a DIFFERENT reason (`already shipped` vs. `order not
found`). Does Claude's final summary to the user name the specific
orders and specific reasons, or does it round up ("all cancelled") or
round down ("failed") into an inaccurate single verdict?

**Test C — idempotency key reuse on retry.** A `charge_customer` call
times out on the first attempt (a structured, retryable error). Claude is
explicitly told retrying is safe IF it reuses the same `idempotency_key`.
Does it actually reuse the same key, or generate a new one? A new key on
retry defeats the entire purpose of idempotency — the payment processor
would see two different keys and could process two real charges.

## Try it yourself

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 exercise2_error_idempotency.py
```

## Design principle worth defending in an exam-style answer

**Why does a structured `isRetryable` field matter more than just an
error message string?** A message like "Rate limit exceeded" is
information a human reads; `isRetryable: true` is a **decision the tool
author already made available** for the calling model to act on directly,
without needing to infer retry-appropriateness from message text (which
is fragile — message wording can change, and inferring intent from prose
is exactly the kind of judgment call Domain 3 showed models can get
wrong under vague instructions).

**Why must partial success return per-item results instead of one
overall boolean?** A single `success: false` for a 5-item batch where 3
actually succeeded would cause the caller to believe (and report) that
NOTHING happened — potentially causing a retry of the whole batch,
double-cancelling the 3 that already succeeded. Precision here isn't
cosmetic; it's what makes retry-safety possible at the batch level.

**Why is idempotency key reuse specifically a retry-safety mechanism, not
just a formality?** Without a stable key, a network timeout (where the
first charge may have actually succeeded despite the client never
learning that) followed by a client-initiated retry becomes
indistinguishable from two separate legitimate charge requests, from the
payment processor's point of view. The key is what lets the processor
say "I've already seen this exact logical request" and refuse to double
process it — but only if the same key is presented both times.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| None — all three tests passed cleanly on the real API. One behavioral nuance worth documenting precisely, not a bug. | — | — |

## Real results

**Test A — all three error types produced correctly differentiated
behavior:**
- `not_found`: reported as failed, no retry attempted, asked for the
  correct order ID
- `rate_limited` (retryable): correctly identified as temporary — but
  **asked permission to retry rather than autonomously retrying**
- `permission_denied`: reported as non-retryable, suggested escalation
  to a supervisor, no retry attempted

**The nuance worth being precise about**: `isRetryable: true` told Claude
the retry is *safe*, but nothing told it whether it's *authorized* to
retry autonomously versus asking first. It defaulted to asking — a
reasonable, conservative choice for a side-effecting action, but this
means the structured error field alone doesn't determine autonomous
retry behavior; that's a separate policy decision. If autonomous retry
is actually wanted (e.g. in an automated backend pipeline with no human
to ask), the system prompt needs to grant that explicitly — mirroring
Domain 1's `MAX_RETRIES` being explicit orchestration code, never an
assumption about default model behavior.

**Test B — fully precise, not flattened, and went beyond the ask:**
Correctly reported exactly 3 successes and 2 failures with their
specific, DIFFERENT reasons (already shipped vs. not found) in both
table and prose form — no rounding up or down. It additionally supplied
contextually appropriate next steps per failure type (suggesting a
return process for the shipped order, suggesting an ID recheck for the
not-found order) — genuinely useful differentiated guidance beyond just
preserving the raw data accurately.

**Test C — clean, and verifiably correct, not just narratively
confident:** the exact same idempotency key
(`CUST-999-2500-20250610-001`) was reused on the retry attempt after the
simulated timeout, confirmed by the script's own programmatic check
comparing the two logged keys — not just Claude's own claim that it
avoided double-charging.

## Conclusion

Structured error fields (`category`, `isRetryable`) and explicit
idempotency-key instructions worked exactly as designed — Claude
differentiated retryable from non-retryable correctly, preserved partial
success with full precision, and correctly reused an idempotency key
across a retry. The one thing worth carrying forward: a retryable flag
communicates safety, not authorization — decide and state explicitly
whether autonomous retry is wanted, don't assume it follows automatically
from `isRetryable: true`.

## Next step
Exercise 3 — tool distribution across agents.
