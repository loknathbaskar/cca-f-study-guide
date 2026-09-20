# Domain 1, Exercise 2: Genuine Parallel Orchestration

Fills a real gap noticed while reviewing repo coverage before the exam:
Exercise 1 only tested a **sequential** pipeline (search → analyze →
synthesize → report). Domain 1 is 27% of the exam — the largest single
domain — but had only one exercise. This adds a second, genuinely
different real-API test rather than another pass over the same pattern.

## What this demonstrates

**Test A — genuine parallel fan-out (real, not simulated):** three
independent subagents (pricing, shipping-policy, warranty-policy research
for a fictional product) launched concurrently via `asyncio`, then
combined in a synthesis call. Measures real wall-clock time — actual
proof that concurrent execution is faster than 3 sequential calls would
be, not just a conceptual claim.

**Test B — the hidden-dependency failure, verified empirically:** two
subagents launched in TRUE parallel, where the second is asked to
"cross-check against whatever the other subagent just found." Since both
are genuinely concurrent, subagent 2 cannot actually see subagent 1's
result when it runs. This is the real-API version of a failure mode we'd
previously only tested via multiple-choice quiz — here it's directly
observable in what subagent 2 actually says when asked to reference
information it doesn't have.

## Try it yourself

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 exercise2_parallel_orchestration.py
```

Check specifically:
1. **Test A**: does the total concurrent time come in well under what 3
   sequential calls would take (compare against each subagent's
   individually-reported time)? Does the synthesis correctly reflect all
   three real findings?
2. **Test B**: how does subagent 2 actually handle being asked to
   reference information from a call that hasn't finished yet — does it
   invent plausible warranty terms, explicitly note it has no access to
   the other subagent's findings, or something else? Any of these is a
   real, informative result — the point is observing what actually
   happens, not confirming a predicted answer.

## Design principle worth defending in an exam-style answer

**Why does true parallel execution provide no mechanism for one subagent
to see another's in-flight result?** `asyncio.gather` (or equivalent
concurrent execution) launches all calls at once — there's no shared
state or message-passing between them during execution, only after each
individually completes. A dependency between "parallel" agents has to be
resolved by *not* actually running them in parallel for that portion, or
by restructuring the task so the dependent step only starts after the
one it needs.

**Why measure real wall-clock time instead of just asserting parallelism
is faster?** Domain 1's claims throughout this repo have consistently
been verified empirically rather than assumed — this is the same
discipline applied to task decomposition specifically. A predicted
speedup that doesn't materialize in a real timed test would itself be an
important finding, not just a confirmation to skip.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| *(fill in once you run this against the real API)* | | |

## Next step

Given exam timing, this closes out the pre-exam Domain 1 gap-filling —
review the real results here alongside Exercise 1's sequential pipeline
findings and the CONCEPTS.md refresher for a complete picture of Domain
1 going into the exam.
