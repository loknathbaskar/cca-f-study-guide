# Domain 5, Exercise 4: Escalation, Confidence Handling, and Human-in-the-Loop Design

## What this demonstrates

Direct extension of Domain 1's retry-vs-escalate theme — but that domain
tested escalation triggered by ERRORS (a failed tool call with a
retryable/non-retryable flag). This tests escalation triggered by the
model's own **uncertainty about a judgment call**, with no external
failure signal to react to.

**The schema** requires three things together: a `decision`, a
self-assessed `confidence` (high/medium/low), and a boolean
`requires_human_review` — testing whether these are actually
well-calibrated with each other, not just individually plausible.

**Four scenarios, deliberately different escalation triggers:**
1. **Clear-cut** — small refund, squarely within policy. Expect HIGH
   confidence, no escalation.
2. **Genuinely ambiguous** — outside the stated window, with a
   mitigating circumstance no policy addresses. Expect LOW/MEDIUM
   confidence, escalation.
3. **High stakes, policy-clear** — a large dollar amount that
   technically satisfies every condition. Tests whether STAKES ALONE
   (not policy ambiguity) triggers escalation, independent of confidence
   in the underlying interpretation — the policy explicitly states
   refunds over $1000 should be flagged regardless of clarity.
4. **Conflicting signals** — policy denies by default, but a
   circumstance (hospitalization) plausibly warrants an exception no
   policy authorizes. Tests whether the model recognizes this needs
   human judgment rather than mechanically applying policy or granting
   an unauthorized exception on its own.

## Try it yourself

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 exercise4_escalation_confidence.py
```

Check specifically:
1. Does Scenario 1 correctly NOT escalate?
2. Does Scenario 2 correctly report LOW/MEDIUM confidence and escalate?
3. **Scenario 3 is the most interesting test**: does the model escalate
   because the stated policy explicitly requires it for stakes over
   $1000, even while reporting HIGH confidence in its own interpretation?
   This tests whether "stakes" and "confidence" are correctly treated as
   two SEPARATE escalation triggers, not conflated into one.
4. Does Scenario 4 correctly escalate rather than either flatly denying
   (mechanically applying policy with no room for judgment) or
   unilaterally approving (granting an exception no policy authorizes)?
5. **Check for the specific inconsistency the script flags**: does any
   scenario report LOW confidence while still leaving
   `requires_human_review=false`? That would be a real calibration
   failure — claiming uncertainty without acting on it.

## Design principle worth defending in an exam-style answer

**Why does Scenario 3 matter as a DISTINCT test from Scenario 2?**
Scenario 2 tests escalation triggered by genuine interpretive ambiguity
— the model isn't sure what the right answer is. Scenario 3 tests
escalation triggered by consequence/stakes — the model might be
completely confident it knows the right answer, and still be required to
escalate anyway, because the cost of being wrong at that dollar amount
outweighs the value of confident autonomous action. **Confidence and
stakes are independent axes**: a system that only escalates on low
confidence would still auto-approve a $5000 refund it's "sure" about,
which may not be the risk posture the business actually wants.

**Why is Scenario 4 a harder case than either 2 or 3 individually?**
It combines an interpretive question (does hospitalization count as a
valid mitigating circumstance?) with a HARD policy statement that
technically forecloses any exception ("no override mechanism"). The
correct behavior isn't to blindly follow the hard policy language (which
would deny a plausibly sympathetic case) or to unilaterally invent an
exception the business never authorized (which oversteps the model's
actual authority) — it's to recognize that this specific combination is
exactly the kind of decision a human, not the model, should be making.

**What would a well-designed human-in-the-loop system do with a
`requires_human_review=true` flag, concretely?** Route the decision to
a queue for human review rather than executing the `decision` field
automatically — the `decision` field in an escalated case should be
treated as a *recommendation* for the human reviewer to consider, not an
action to execute. A system that generates a recommendation AND an
escalation flag, but still auto-executes the recommendation regardless
of the flag, has built the escalation mechanism in name only.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| None — ran correctly. Scenario 2 diverged from the predicted outcome, documented below as a real finding, not a bug. | — | — |

## Real results

**Scenario 1**: confirmed exactly as predicted — high confidence,
approved, no escalation.

**Scenario 2 — the prediction was wrong, and the real behavior is more
interesting than a miss.** Expected LOW/MEDIUM confidence and
escalation; got **HIGH confidence, deny, no escalation.** The reasoning
explicitly separates "the circumstances are sympathetic" from "is the
policy itself ambiguous" — concluding the policy is mechanically
unambiguous (no override exists anywhere), so a confident denial is
warranted with nothing left for a human to decide differently.

**Scenario 3**: confirmed exactly as predicted — high confidence in the
interpretation, but escalated purely because the stated policy demands
it above $1000, explicitly separating those two things in its own
reasoning.

**Scenario 4**: escalated as predicted (medium confidence) — but the
real finding is in contrasting it directly with Scenario 2. Both involve
a late return, no defined override, and a sympathetic story — yet one
escalated and one didn't. The model discriminated between an *ordinary,
somewhat-avoidable* circumstance (missed a delivery notice while moving)
and an *extraordinary, involuntary* one with an added safety dimension
(3-week hospitalization, medical device) — not simple sympathy-detection,
something closer to weighing how exceptional and how outside the
customer's control each circumstance actually was.

## Why this is a better finding than a clean confirmation would have been

A cruder test checking only "did Scenario 2 escalate" would have logged
this as a failure. Looking at *why* it didn't reveals something closer
to genuine calibrated judgment than either blind policy-following or
indiscriminate sympathy-based escalation.

**But this raises a real, debatable open question worth stating
honestly rather than resolving artificially**: is "no written override
exists" sufficient grounds for an agent to autonomously and *permanently*
deny a sympathetic case, or should any denial resting on an
explicitly-undefined circumstance route to a human with authority the
written policy doesn't grant the agent? Reasonable people could land
differently here — Scenario 2's outcome isn't obviously wrong, but it
also isn't obviously the only defensible design choice. A real system
would need to make this call explicitly (e.g., "any denial citing 'no
override exists' should still route to human review before being
communicated to the customer") rather than leaving it to the model's own
implicit judgment about which sympathetic stories are "sympathetic
enough."

## Next step / Domain 5 — complete

All 4 exercises covered: compaction strategy (with a corrected,
sharper-than-predicted finding about structured vs. prose), prompt
caching (a fully confirmed, precisely quantified real result), durable
state vs. transient conversation (a genuinely subtle two-part finding
about masked risk), and now confidence-based escalation (a wrong
prediction that led to a sharper finding about implicit judgment vs.
explicit policy design). Ready for the Domain 5 quiz, then the
full-domain refresher and mock exam.
