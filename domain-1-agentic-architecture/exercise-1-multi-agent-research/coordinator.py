"""
coordinator.py — The orchestrator for the Multi-Agent Research System.

EXAM-RELEVANT CONCEPTS EXERCISED HERE (Domain 1, 27% of exam):

  * Task decomposition — the pipeline is explicit: search -> analyze ->
    synthesize -> report. The coordinator never does the work itself,
    it only sequences and passes context.

  * Session state management — `run_log` accumulates what happened at
    each stage so you could resume, audit, or debug later.

  * Handling partial failures gracefully — if a subagent fails:
      - retryable failure -> retry with backoff, up to a cap
      - non-retryable failure -> escalate (stop and surface to a human)
    This maps directly to Domain 5 (Context Management & Reliability)
    too — the two domains overlap heavily in real exam scenarios.
"""

import time
from subagents import search_agent, analyze_agent, synthesize_agent, report_agent, SubagentResult


MAX_RETRIES = 2


def run_stage(agent_fn, *args, failure_rate=0.0, **kwargs) -> SubagentResult:
    """Run one pipeline stage with retry-on-retryable-error logic."""
    attempt = 0
    while True:
        result = agent_fn(*args, failure_rate=failure_rate, **kwargs)
        if result.success:
            return result
        if result.retryable and attempt < MAX_RETRIES:
            attempt += 1
            wait = 0.5 * attempt
            print(f"  [retry] {result.agent} failed ({result.error}) — "
                  f"retrying attempt {attempt}/{MAX_RETRIES} after {wait}s")
            time.sleep(wait)
            continue
        return result  # exhausted retries or non-retryable


def run_research_pipeline(topic: str, failure_rate: float = 0.0) -> dict:
    """
    Runs the full coordinator/subagent pipeline for one research topic.

    Returns a dict with the final report OR an escalation record if the
    pipeline could not complete. Never raises — a coordinator that crashes
    on subagent failure is exactly the anti-pattern the exam probes for.
    """
    run_log = {"topic": topic, "stages": []}

    # Stage 1: search
    search_result = run_stage(search_agent, topic, failure_rate=failure_rate)
    run_log["stages"].append(vars(search_result))
    if not search_result.success:
        return _escalate(run_log, "search_agent", search_result.error)

    # Stage 2: analyze (only gets the search output, not the original topic
    # or any coordinator-level context — narrow, scoped input)
    analyze_result = run_stage(analyze_agent, search_result.output, failure_rate=failure_rate)
    run_log["stages"].append(vars(analyze_result))
    if not analyze_result.success:
        return _escalate(run_log, "analyze_agent", analyze_result.error)

    # Stage 3: synthesize
    synth_result = run_stage(synthesize_agent, analyze_result.output, failure_rate=failure_rate)
    run_log["stages"].append(vars(synth_result))
    if not synth_result.success:
        return _escalate(run_log, "synthesize_agent", synth_result.error)

    # Stage 4: report
    report_result = run_stage(report_agent, synth_result.output, failure_rate=failure_rate)
    run_log["stages"].append(vars(report_result))
    if not report_result.success:
        return _escalate(run_log, "report_agent", report_result.error)

    run_log["status"] = "completed"
    run_log["final_report"] = report_result.output
    return run_log


def _escalate(run_log: dict, failed_agent: str, error: str) -> dict:
    """
    Escalation path: when a subagent fails non-retryably (or exhausts
    retries), the coordinator stops and hands off to a human rather than
    guessing or silently producing a degraded result.

    This is the #1 tested judgment call in Domain 1 & Domain 5: knowing
    WHEN to escalate vs. when to push through with a partial result.
    """
    run_log["status"] = "escalated"
    run_log["escalation"] = {
        "failed_at": failed_agent,
        "error": error,
        "reason": "Non-retryable failure or retries exhausted — human review required.",
    }
    return run_log
