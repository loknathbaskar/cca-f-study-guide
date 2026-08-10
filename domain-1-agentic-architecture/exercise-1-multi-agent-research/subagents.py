"""
subagents.py — Specialized subagents for the Multi-Agent Research System
(this is Exam Scenario 3, Domain 1: Agentic Architecture & Orchestration).

EXAM-RELEVANT DESIGN DECISIONS baked into this file:

1. Each subagent gets a NARROW system prompt (single responsibility).
   -> Tests: "task decomposition" — don't build one mega-agent.

2. Each subagent receives only the SPECIFIC input it needs, not the full
   conversation history. This is "context passing" done right.
   -> Common wrong answer on the exam: passing the entire coordinator
      transcript to every subagent "just in case." That bloats context
      and lets subagents drift off-task.

3. Every subagent call is wrapped so a failure returns a structured
   result instead of raising — the coordinator decides what to do next
   (retry, skip, escalate). This is "partial failure handling."
"""

from dataclasses import dataclass
from backend import call_claude, TransientAPIError


@dataclass
class SubagentResult:
    agent: str
    success: bool
    output: str = None
    error: str = None
    retryable: bool = False


def _run_subagent(agent_name: str, system_prompt: str, task_input: str,
                   simulate_failure_rate: float = 0.0) -> SubagentResult:
    try:
        resp = call_claude(
            system=system_prompt,
            messages=[{"role": "user", "content": task_input}],
            simulate_failure_rate=simulate_failure_rate,
            agent_name=agent_name,
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        return SubagentResult(agent=agent_name, success=True, output=text)
    except TransientAPIError as e:
        return SubagentResult(agent=agent_name, success=False, error=str(e), retryable=True)
    except Exception as e:
        return SubagentResult(agent=agent_name, success=False, error=str(e), retryable=False)


def search_agent(topic: str, failure_rate=0.0) -> SubagentResult:
    return _run_subagent(
        "search_agent",
        system_prompt="You are a search subagent. Find and list relevant sources for the given topic. Do not analyze them, only find them.",
        task_input=f"Find sources on: {topic}",
        simulate_failure_rate=failure_rate,
    )


def analyze_agent(sources: str, failure_rate=0.0) -> SubagentResult:
    return _run_subagent(
        "analyze_agent",
        system_prompt="You are an analysis subagent. Extract key findings from the given sources. Do not search for new sources or write a final report.",
        task_input=f"Analyze these sources:\n{sources}",
        simulate_failure_rate=failure_rate,
    )


def synthesize_agent(findings: str, failure_rate=0.0) -> SubagentResult:
    return _run_subagent(
        "synthesize_agent",
        system_prompt="You are a synthesis subagent. Identify tradeoffs and higher-level conclusions from the given findings.",
        task_input=f"Synthesize these findings:\n{findings}",
        simulate_failure_rate=failure_rate,
    )


def report_agent(synthesis: str, failure_rate=0.0) -> SubagentResult:
    return _run_subagent(
        "report_agent",
        system_prompt="You are a report-writing subagent. Write a concise, well-structured markdown report from the given synthesis.",
        task_input=f"Write a report based on:\n{synthesis}",
        simulate_failure_rate=failure_rate,
    )
