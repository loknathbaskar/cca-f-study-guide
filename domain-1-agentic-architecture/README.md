# Domain 1: Agentic Architecture & Orchestration (27% — largest domain)

## Core concepts

- **Agentic loop**: the cycle of Claude receiving input → deciding to use a tool →
  getting the tool result → deciding again → ... → final answer. Not a single call.
- **Task decomposition**: splitting a big job into subtasks, each handled by a
  focused agent/subagent with a single responsibility.
- **Multi-agent coordination**: a coordinator agent delegates to subagents and
  owns final synthesis — subagents should NOT talk to each other directly.
- **Session state management**: tracking what's happened across a long-running
  or multi-step task so you can resume, audit, or debug.
- **Context passing**: subagents should get *scoped, minimal* input — not the
  full coordinator transcript. Passing everything "just in case" pollutes
  context and causes drift.

## Common exam traps

- Building one mega-agent instead of decomposing into subagents when subtasks
  are genuinely independent and parallelizable.
- Passing full conversation history to every subagent instead of a scoped task input.
- Coordinator crashing / propagating an exception instead of catching a subagent
  failure and deciding: retry (if transient/retryable) vs. escalate (if not).
- Retrying indefinitely instead of capping retries and escalating to a human
  after a threshold.
- Confusing "escalate" (stop, need human review) with "degrade gracefully"
  (return a partial but still useful result) — the exam expects you to know
  which is appropriate per scenario.

## Exercises

### Exercise 1 — Multi-Agent Research System
Coordinator delegates to `search_agent → analyze_agent → synthesize_agent → report_agent`.
Demonstrates: task decomposition, scoped context passing, retry-with-backoff on
transient failures, and escalation when retries are exhausted.

**Bug encountered while building this**: the mock LLM backend originally routed
responses by keyword-matching the *system prompt text*. Since `analyze_agent`'s
own instructions contained the word "search" (as in "do not search for new
sources"), it silently matched into the `search_agent`'s mock response branch.
Fixed by passing an explicit `agent_name` key instead of sniffing prompt text.

**Why this matters for the exam**: this is the exact failure mode Domain 2 tests
for with *real* tool/agent descriptions — ambiguous or overlapping language
causes Claude (or, here, my mock) to pick the wrong tool/agent silently, with
no error thrown. Precise, non-overlapping naming and descriptions matter.

**Try it yourself:**
1. Change `MAX_RETRIES` and `failure_rate` in `demo.py` — observe how the
   retry/escalate threshold shifts.
2. Add a `critique_agent` stage between synthesize and report that reviews
   the report before returning it. Decide: does it need the full synthesis,
   or just a summary? What happens to context size as you add more stages?
