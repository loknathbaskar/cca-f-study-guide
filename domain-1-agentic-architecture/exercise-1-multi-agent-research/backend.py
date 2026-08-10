"""
backend.py — LLM call abstraction for the Domain 1 hands-on exercise.

Real exam relevance:
  - The exam does NOT test whether you have an API key. It tests whether you
    understand the ARCHITECTURE: agentic loop, tool use, context passing,
    error handling, escalation.
  - This file isolates "how we talk to Claude" so the orchestration code
    (coordinator.py, subagents.py) is identical whether you're running with
    a real ANTHROPIC_API_KEY or not.

If you set ANTHROPIC_API_KEY, this makes real calls to claude-sonnet-4-6.
If not, it falls back to a mock that returns realistic, deterministic
responses so you can still exercise (and break) the control flow.
"""

import os
import time
import random

from dotenv import load_dotenv

load_dotenv()  # walks up from this file to find the repo-root .env

USE_REAL_API = bool(os.environ.get("ANTHROPIC_API_KEY"))

if USE_REAL_API:
    import anthropic
    _client = anthropic.Anthropic()


class TransientAPIError(Exception):
    """Simulated retryable error (rate limit, overload, timeout)."""
    pass


def call_claude(system: str, messages: list, tools: list = None, max_tokens: int = 1024,
                 simulate_failure_rate: float = 0.0, agent_name: str = None):
    """
    Single entry point every agent uses to talk to Claude.

    simulate_failure_rate: probability [0,1] of injecting a TransientAPIError.
    This exists ON PURPOSE — Domain 1 and Domain 5 both test whether you
    handle partial failures and retries correctly, not just the happy path.
    """
    if simulate_failure_rate and random.random() < simulate_failure_rate:
        raise TransientAPIError("simulated 529 overloaded_error")

    if USE_REAL_API:
        kwargs = dict(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        if tools:
            kwargs["tools"] = tools
        resp = _client.messages.create(**kwargs)
        return resp

    # ---- Mock mode ----
    time.sleep(0.2)  # simulate latency
    return _mock_response(agent_name or system, messages)


class _MockContentBlock:
    def __init__(self, type_, text=None, name=None, input_=None, id_=None):
        self.type = type_
        self.text = text
        self.name = name
        self.input = input_
        self.id = id_


class _MockResponse:
    def __init__(self, content, stop_reason="end_turn"):
        self.content = content
        self.stop_reason = stop_reason


_MOCK_TEXT_BY_AGENT = {
    "search_agent": (
        "Found 3 relevant sources on Claude agentic architecture: "
        "(1) Anthropic engineering blog on multi-agent orchestration, "
        "(2) MCP specification docs, (3) a case study on subagent context isolation."
    ),
    "analyze_agent": (
        "Key findings: subagents should receive minimal, task-scoped context "
        "(not the full conversation history), and the coordinator should "
        "own final synthesis to avoid conflicting conclusions."
    ),
    "synthesize_agent": (
        "Synthesis: a coordinator/subagent pattern reduces context pollution "
        "and lets you parallelize independent subtasks, at the cost of added "
        "orchestration and error-handling complexity."
    ),
    "report_agent": (
        "# Research Summary\n\nMulti-agent systems trade simplicity for "
        "parallelism and context isolation. Use them when subtasks are "
        "genuinely independent; use a single agent when they're not."
    ),
    "coordinator": (
        "Plan: 1) search_agent gathers sources 2) analyze_agent extracts findings "
        "3) synthesize_agent identifies tradeoffs 4) report_agent writes final doc."
    ),
}


def _mock_response(agent_key: str, messages: list):
    """Deterministic canned responses keyed off an explicit agent identifier
    (not a substring search of prompt text — that was a real bug: the
    analyze_agent's own instructions contain the word "search", which
    caused it to misfire into the search_agent's mock branch. Fixed by
    passing agent_name explicitly instead of sniffing prompt text.)"""
    last = messages[-1]["content"] if messages else ""
    last_str = last if isinstance(last, str) else str(last)

    text = _MOCK_TEXT_BY_AGENT.get(agent_key)
    if text is None:
        text = f"[mock] Processed: {last_str[:80]}"

    return _MockResponse(content=[_MockContentBlock("text", text=text)])
