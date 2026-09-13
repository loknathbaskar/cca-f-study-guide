# Domain 5, Exercise 3: Durable State vs. Transient Conversation — The Scratchpad Pattern

## What this demonstrates

Direct extension of two earlier findings: Domain 1's session-state-vs-
subagent-context distinction, and Exercise 1's finding that structured
records guarantee retrievability where prose doesn't. This exercise
tests the exam's own claim — *"reliable systems separate durable state
from transient conversation"* — against a realistic failure mode: a
long-running, multi-step task where an early decision needs to survive
context loss.

**The setup**: a simulated 6-step data migration. Step 2 establishes a
critical rule ("skip any record with a null email field") that must be
applied consistently for the rest of the task.

**Two conditions, same underlying task:**
- **TRANSIENT ONLY**: simulated context loss truncates the conversation
  to only the last 2 steps — Step 2 (the rule) is gone. Claude resumes
  with only this truncated context.
- **DURABLE SCRATCHPAD**: the rule was written to an actual file on disk
  the moment it was established (simulating a real system writing
  scratchpad state incrementally, not just at the end). After the same
  context loss, Claude resumes using ONLY the scratchpad file's content
  — no conversation history at all.

**The test**: present a new record with a null email in both conditions
and see whether the Step 2 rule is still correctly applied.

## Try it yourself

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 exercise3_durable_state.py
```

Check specifically:
1. Does TRANSIENT actually lose the rule — does it guess, ask for
   clarification, or (worse) make up a plausible-sounding but
   unfounded answer about what to do with the null-email record?
2. Does DURABLE SCRATCHPAD correctly apply the exact rule, since it's
   explicitly present in the (much shorter) context it was given?
3. If TRANSIENT actually gets it right anyway (e.g., by reasonably
   inferring a sensible default), that's a real and worth-documenting
   result too — it wouldn't mean durable state is pointless, but it
   would show the risk is probabilistic, not guaranteed, which is
   itself useful to know precisely.

## Design principle worth defending in an exam-style answer

**Why is this a different (and arguably more realistic) failure mode
than Exercise 1's compaction test?** Exercise 1 tested a single
compaction event applied to a whole conversation. This tests something
more specific to long-running agentic tasks: a decision made mid-task
that must survive an unpredictable AMOUNT of subsequent context churn —
you don't know in advance how many more steps will come before context
runs out, so you can't just "summarize well once." A scratchpad written
incrementally, as decisions happen, doesn't depend on guessing what a
future compaction event will and won't preserve.

**Why write to the scratchpad AT THE MOMENT the decision is made, rather
than at the end of the task or during a compaction pass?** If the write
only happens later, there's a window where the decision exists only in
transient context — and if something goes wrong (a crash, a context
overflow, an unplanned session end) before that later write happens, the
decision is lost anyway. Writing durable state incrementally, as close
to the moment of decision as possible, minimizes the window where
critical state is single-point-of-failure.

**How does this connect to Domain 1's coordinator/subagent pattern?**
The same principle, one level up: Domain 1 established that subagents
should get scoped context, not full history, and that session state
(`run_log`) is tracked separately from any single call's context. A
scratchpad file is the natural persistence layer for that broader
session state — surviving not just across subagent calls within one
run, but across entire session boundaries (restarts, compaction,
context limits).

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| None — ran correctly on the first attempt. The real finding is more subtle than a simple pass/fail, documented below. | — | — |

## Real results — same final answer, categorically different reliability

**Both conditions recommended skipping record #847.** On the surface,
this looks like a null result — but examining *how* each one reached
that conclusion reveals a much more important and more dangerous
finding than a simple pass/fail would.

**TRANSIENT reached the correct action through INFERENCE, not recall.**
Its stated reasoning: *"Previous batches already have a skipped
category... skipping invalid/incomplete records is clearly the existing
convention... a null email field typically indicates incomplete or
corrupt source data."* **It never once references the actual
established rule** (email required as a primary key in the new system)
— because that rule wasn't in its context at all. It reverse-engineered
a plausible-sounding equivalent policy from the coincidental existence
of a "skipped" counter, not from the real business decision made in
Step 2.

**DURABLE SCRATCHPAD reached the same action, grounded in the actual
rule.** It explicitly cited *"the established rule documented in the
scratchpad"* and the real rationale (email as primary key requirement),
and correctly incremented the count (42→43) — fully traceable back to
the genuine documented decision, not an inference.

**Why this matters more than a simple "transient failed" result would**:
TRANSIENT didn't fail here — it got *lucky*. The real rule happened to
align closely with an intuitive default ("null fields in required-ish
columns get skipped") that generic pattern-matching could stumble into
without ever knowing the actual rule existed. **If the real established
rule had been less obvious or counterintuitive** — e.g., "skip null
email UNLESS the customer is VIP tier, in which case migrate with a
placeholder" — TRANSIENT would have had no path to recovering that
correctly, since nothing about generic inference could produce a
business-specific exception like that. DURABLE would still get it right
regardless, because it's reading the actual rule rather than
reconstructing one.

**The genuinely alarming part**: a monitoring system checking only "did
it choose skip or migrate" would see **zero difference** between these
two conditions in this specific test. The risk is completely invisible
unless you check *why* an answer was reached, not just *what* the answer
was — this is a much harder failure mode to catch in production than an
outright wrong answer, precisely because it doesn't look wrong.

## Natural follow-up worth doing

Re-run this with a genuinely non-obvious, arbitrary business rule (like
the VIP-tier exception above) instead of the null-email rule, which
turned out to overlap heavily with generic common sense. That would be a
stronger test of the actual claim, since it would remove the possibility
of TRANSIENT succeeding via lucky inference — a rule with no intuitive
default forces a real test of recall vs. fabrication.

## Next step
Exercise 4 — escalation, confidence handling, and human-in-the-loop
design.
