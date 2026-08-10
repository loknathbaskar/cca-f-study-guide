import json
from coordinator import run_research_pipeline
from backend import USE_REAL_API

print(f"Running in {'REAL API' if USE_REAL_API else 'MOCK'} mode\n")

print("=" * 60)
print("RUN 1: Happy path (no injected failures)")
print("=" * 60)
result1 = run_research_pipeline("Claude multi-agent orchestration patterns", failure_rate=0.0)
print(json.dumps(result1, indent=2)[:1200])

print("\n" + "=" * 60)
print("RUN 2: With a 60% chance of transient failure per stage")
print("=" * 60)
result2 = run_research_pipeline("MCP tool design best practices", failure_rate=0.6)
print(json.dumps(result2, indent=2)[:1200])

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Run 1 status: {result1['status']}")
print(f"Run 2 status: {result2['status']}")
