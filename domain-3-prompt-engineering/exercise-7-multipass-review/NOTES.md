# Exercise 7: Multi-Pass Review — Draft Pass + Critique Pass for Reducing False Positives

Maps to Domain 3's final subtopic: evaluation and multi-pass review
architectures, reducing false positives in classification/review tasks.

## What this demonstrates

`requires_escalation` has never had explicit criteria anywhere in this
whole exercise (a gap flagged honestly back in Step 3/4) — every
escalation flag so far has been an ungrounded guess. This exercise uses
exactly that gap as the real test case for a two-pass architecture:

- **Pass 1 (draft)**: extract ticket data as usual, guessing
  `requires_escalation` with no explicit criteria — unchanged from every
  prior step.
- **Pass 2 (critique)**: a SEPARATE call, given the original ticket + the
  draft's escalation verdict, specifically instructed to distinguish
  genuine concrete signals (dispute threat, repeated unresolved contact,
  safety issue, explicit request for a manager) from emotional
  intensity/tone alone. The critique pass can only **confirm** or
  **downgrade** — never invent a new escalation the draft didn't flag,
  since the entire point is catching false positives, not finding more
  positives.

A new ticket (ticket 4 in this script) is added specifically as
false-positive bait: maximum emotional intensity (ALL CAPS, "worst
experience of my life," "absolutely furious"), describing an objectively
minor issue (a small cosmetic dent) with zero concrete signal behind it.

## Try it yourself

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 exercise2_multipass_review.py
```

Check specifically:
1. Does the **draft** pass over-flag the emotional-intensity ticket for
   escalation, reacting to tone rather than substance?
2. Does the **critique** pass correctly downgrade it, while confirming
   the two tickets that have genuine concrete signals (repeated
   unresolved contact, explicit dispute threat)?
3. Does critique ever incorrectly downgrade a ticket that SHOULD stay
   escalated — a false negative introduced by the fix itself? Worth
   checking, since a critique pass that's too aggressive about
   downgrading trades one class of error for another.

## Design principle worth defending in an exam-style answer

**Why must the critique pass only be allowed to confirm or downgrade,
never upgrade?** This exercise is specifically about reducing FALSE
POSITIVES — cases where escalation was flagged without justification. If
critique could also upgrade a draft's "false" to "true," you'd be solving
a different problem (false negatives) with the same mechanism, and
conflating two distinct failure modes that need to be measured and fixed
separately. A single pass trying to do both jobs at once is harder to
reason about than two passes each with one narrow job.

**Why is this a genuinely different technique from Steps 1-2's fix
(explicit criteria)?** Explicit criteria injects the missing rule
*before* the model ever answers — the ideal fix, when you can articulate
the rule in advance. Multi-pass review is valuable specifically when the
judgment is too holistic or context-dependent to reduce to a clean
upfront rule (or when you haven't figured out the rule yet) — instead of
specifying the answer in advance, you specify a *narrower, more
answerable question* for a second pass to check ("is there a concrete
signal, yes or no") rather than the original, harder question ("does
this deserve escalation").

**What's the real cost of this approach, worth being honest about?**
Double the API calls (and cost) for every ticket that gets flagged in
the draft pass. This is a legitimate trade-off, not a free win — worth
it specifically for judgment calls with real consequences for getting
wrong (unnecessary supervisor time, or worse, a customer issue that
doesn't get proper attention), not for every field in every pipeline.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| *(fill in once you run this against the real API)* | | |

## Domain 3 — complete

All subtopics covered: explicit vs. vague criteria, targeted few-shot,
`tool_use` schema design (nullable fields, enum escape hatches),
`tool_choice` modes, validation-retry (format vs. semantic), the Message
Batches API, and multi-pass review for reducing false positives. Ready
to move to Domain 4 (Tool Design & MCP Integration).
