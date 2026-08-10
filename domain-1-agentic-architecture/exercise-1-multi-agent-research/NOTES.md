# Exercise 1: Multi-Agent Research System

Maps to **Exam Scenario 3** and **Domain 1** (also touches Domain 5).

## Files
- `backend.py` — LLM call abstraction; real API if `ANTHROPIC_API_KEY` set, else deterministic mock
- `subagents.py` — 4 narrow-purpose subagents, each wrapped to return a `SubagentResult` instead of raising
- `coordinator.py` — sequences the pipeline, retries transient failures (capped), escalates on exhaustion/non-retryable errors
- `demo.py` — runs a happy-path scenario and a high-failure-rate scenario side by side

## Setup
```bash
cd domain-1-agentic-architecture/exercise-1-multi-agent-research
pip install anthropic   # only needed for real API mode
python3 demo.py
```

Optional — use real Claude instead of mock:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 demo.py
```

## What to observe

1. **Run 1 (0% failure rate)**: all 4 stages complete; each subagent's output
   is distinct and only depends on the *previous stage's output*, not the
   original topic or full history.
2. **Run 2 (60% failure rate)**: watch the retry log lines, then the
   escalation record — note it captures *which* agent failed and *why*,
   not just "something went wrong."

## Design decisions worth defending in an exam-style answer

- Why retry only on `retryable=True` errors, not all errors? (Non-retryable
  errors — e.g. a malformed request — will fail identically on retry; retrying
  them just wastes time/cost before escalating anyway.)
- Why does the coordinator own synthesis instead of having subagents merge
  their own outputs? (Avoids subagents needing visibility into each other's
  context; keeps responsibility boundaries clean.)
- Why cap retries at 2 instead of retrying forever? (Bounded latency/cost;
  a human should be looped in rather than an agent looping silently.)

## Bugs / gotchas log

| Bug | Cause | Fix |
|---|---|---|
| `analyze_agent` mock returned `search_agent`'s canned text | Mock router used substring match on system prompt (`"search" in system.lower()`), and analyze_agent's own prompt contained the word "search" | Pass explicit `agent_name` to `call_claude()` instead of inferring identity from prompt text |

## Follow-up exercises (not yet done)
- [ ] Add a `critique_agent` stage
- [ ] Parallelize search + an independent second data-gathering subagent using `asyncio`
- [ ] Add a hard cap on total pipeline wall-clock time, separate from per-stage retries
