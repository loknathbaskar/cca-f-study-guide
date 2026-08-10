# Domain 1: Agentic Architecture & Orchestration — Concept Notes

*(27% of the CCA-F exam — the largest single domain)*

---

## 1. The Agentic Loop

An agentic system isn't one API call — it's a **loop**:

```
input → Claude decides → (maybe) use a tool → tool result fed back → Claude decides again → ... → final answer
```

**Key idea:** Claude can take multiple turns *on its own*, using tool results to decide
its next action, until it reaches a final answer. A single request/response pair is not
"agentic" — the loop, and Claude's autonomy within it, is what makes it agentic.

---

## 2. Task Decomposition

Breaking one large job into smaller, independently handleable subtasks.

**When to decompose:**
- Subtasks are genuinely independent (don't need each other's intermediate state)
- Subtasks benefit from different, focused instructions
- Subtasks could run in parallel

**When NOT to decompose:**
- The task is simple enough that one agent handles it cleanly
- Subtasks are tightly coupled and splitting them adds coordination overhead without benefit

**Exam trap:** Building one "mega-agent" with a giant system prompt covering every
responsibility, when the task clearly has independent parts that would benefit from
separate, focused agents.

---

## 3. Multi-Agent Coordination

**Pattern:** A **coordinator** agent delegates to **subagents**, each with a single,
narrow responsibility. The coordinator:
- Sequences the subagents (or runs them in parallel where independent)
- Owns final synthesis of results
- Handles failures (retry / escalate — see below)

**Subagents should NOT talk to each other directly.** Bypassing the coordinator breaks:
- Centralized error handling
- Consistent context scoping
- A single source of truth for the final synthesized answer

---

## 4. Context Passing Between Agents

Each subagent should receive **only the scoped input it needs** — not the full
conversation history of the coordinator.

**Why it matters:**
- Full history bloats token usage for no benefit
- Irrelevant context can cause a subagent to drift off its narrow task
- Scoped input keeps each subagent's behavior predictable and testable in isolation

**Rule of thumb:** if a subagent doesn't need a piece of context to do its specific job,
don't pass it.

---

## 5. Session State vs. Subagent Context

These are two different things, easy to conflate:

| | Session state | Subagent context |
|---|---|---|
| Scope | The whole run/session | One subagent call |
| Purpose | Auditing, debugging, resuming | Doing one scoped job |
| Size | Grows as the session progresses | Deliberately minimal |

**Risk:** even with perfectly scoped subagent context, session state itself can grow
unbounded over a long-lived process. If stale state is later reused or inspected without
pruning, it can leak irrelevant or outdated information into decisions.

---

## 6. Handling Partial Failures: Retry vs. Escalate

Not all failures deserve the same response.

**Retry when:**
- The error is genuinely transient (rate limit, overload, network timeout)
- You cap the number of retries (unbounded retry loops hide problems and waste cost/latency)

**Escalate (stop, hand off to a human) when:**
- Retries are exhausted
- The error is non-retryable by nature (e.g. malformed request/schema — it will fail
  identically every time, so retrying just wastes time before you escalate anyway)

**Escalate vs. degrade gracefully:**
- **Escalate**: stop, this needs human judgment (e.g. a payment can't be verified)
- **Degrade gracefully**: return a partial-but-still-useful result (e.g. a report built
  from 2 of 5 expected sources is still directionally useful)

Knowing *which* response fits a given failure — not just "retry or don't" — is the
core judgment call this domain tests.

---

## 7. Ambiguous Naming Causes Silent Misrouting

If two tools or subagents have overlapping or ambiguous descriptions, Claude (or any
router) can pick the wrong one — **silently, with no error thrown.**

**Principle:** identify tools/agents by explicit, unambiguous names/descriptions. Don't
rely on loose keyword overlap between what different components do — near-duplicate
purposes or descriptions are a direct cause of misrouting in production.

---

## 8. System-Level Reliability Patterns

Individual retry/escalate logic operates **per call**. Some reliability concerns only
make sense **above** that — at the level that invokes the pipeline repeatedly:

- **Circuit breakers**: if N consecutive full pipeline runs all escalate, stop calling
  the pipeline entirely until a human intervenes — this requires visibility across
  multiple runs, not just one call.
- This is a bridge concept into **Domain 5 (Context Management & Reliability)**.

---

## Quick self-check questions
1. Can you explain why a coordinator, not subagents, should own final synthesis?
2. Can you name a failure that should escalate immediately without any retry?
3. Can you explain why a circuit breaker can't live inside a single subagent call?

If you can answer all three without looking back at this file, you're ready to move to
Domain 2.