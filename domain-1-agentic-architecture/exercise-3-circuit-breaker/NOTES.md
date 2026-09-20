# Domain 1, Exercise 3: Real Circuit Breaker

Fills another real gap: the Domain 1 quiz established WHERE a circuit
breaker belongs (one level above single-pipeline invocation, tracking
state across multiple runs) but we'd never actually built and tripped
one against real failures.

## What this demonstrates

A coordinator processes 8 tickets sequentially. Tickets containing
"POISON" are deliberately instructed to omit the required
`confirmation_code` field, giving a reliable, cheap, reproducible real
failure — no need for an actually-flaky external dependency. A
`CircuitBreaker` class sits **above** the per-ticket loop (the placement
the quiz established as correct) and trips after 3 **consecutive**
failures, at which point it stops making further real API calls
entirely, rather than continuing to hammer a broken pattern. Any success
resets the consecutive-failure count back to 0.

**Ticket sequence is deliberately arranged**: 2 normal (should succeed),
3 consecutive "poison" (should trip on the 3rd), then 3 more normal
tickets that should **never actually be sent** once tripped — directly
testing whether the breaker actually stops real API calls, not just logs
a warning while continuing anyway.

**Verified before spending any real API cost**: the `CircuitBreaker`
class's own logic was tested in isolation (no API calls) against the
exact success/fail sequence this exercise uses — confirmed to trip
precisely on the 3rd consecutive failure, not before or after.

## Try it yourself

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 exercise3_circuit_breaker.py
```

Check specifically:
1. Do tickets 1-2 succeed, and 3-5 (the POISON ones) fail?
2. Does the breaker report tripped after ticket 5, not before?
3. **Most important**: do tickets 6-8 show as `SKIPPED` with **no API
   call made**, or does the loop keep calling the API anyway despite the
   trip? The `real_api_calls_made` counter at the end should read 5, not
   8 — that's the concrete, checkable proof the breaker actually saved
   cost rather than just logging a warning.

## Design principle worth defending in an exam-style answer

**Why must the breaker track CONSECUTIVE failures, not total failures?**
Total failure count would trip on a system that's mostly healthy with
occasional unrelated errors scattered across a long run. Consecutive
failures specifically detect "something is currently, persistently
broken" — a genuinely different signal a total counter would miss
entirely, since one success anywhere would never reset a total count the
way it correctly resets a consecutive one here.

**Why does tripping need to actually skip the API call, not just log a
warning and continue?** A circuit breaker's entire value proposition is
protecting against wasted cost/time on a call that's very likely to keep
failing — a breaker that trips but keeps calling anyway provides
observability without the actual protection, which is the whole point of
implementing one instead of just alerting on a failure-rate dashboard.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| *(fill in once you run this against the real API)* | | |

## Next step
Given exam timing, this is the third Domain 1 exercise added — sequential
pipeline (Ex1), genuine parallel + hidden-dependency (Ex2), and now a
real circuit breaker (Ex3). Review real results alongside CONCEPTS.md
before the exam.
