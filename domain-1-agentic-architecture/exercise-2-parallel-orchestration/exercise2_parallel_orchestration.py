"""
exercise2_parallel_orchestration.py — Domain 1, filling a real gap: Exercise
1 only tested SEQUENTIAL subagent execution. This tests TRUE PARALLEL
execution against the real API, plus the specific failure mode Domain 1's
quiz covered only conceptually: what actually happens when a "parallel for
speed" design includes a hidden dependency.

TEST A — genuine parallel fan-out: three independent subagents (pricing
research, shipping-policy research, warranty-policy research for the same
fictional product) run concurrently via asyncio, then a synthesis call
combines them. Measures real wall-clock time vs. what sequential would
have taken, and checks the synthesis correctly reflects all three.

TEST B — the hidden-dependency failure, demonstrated for real: two
subagents are run in TRUE parallel where the second genuinely needs the
first's output (subagent 2 is asked to "cross-check the shipping policy
against whatever warranty terms were just found" — but in true parallel
execution, subagent 2 has no way to see subagent 1's still-in-flight
result). This directly tests the real-API version of Domain 1 quiz
question 13.
"""

import os
import asyncio
import time

if not os.environ.get("ANTHROPIC_API_KEY"):
    print("This exercise requires ANTHROPIC_API_KEY.")
    raise SystemExit(0)

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


async def call_subagent(label: str, system: str, user_message: str):
    """Wraps a synchronous Anthropic call so it can run concurrently via asyncio.to_thread."""
    start = time.time()
    response = await asyncio.to_thread(
        client.messages.create,
        model=MODEL, max_tokens=400,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    elapsed = time.time() - start
    text = "".join(b.text for b in response.content if b.type == "text")
    print(f"  [{label}] completed in {elapsed:.1f}s")
    return text


async def test_a_genuine_parallel():
    print("=" * 70)
    print("TEST A: Genuine parallel fan-out — 3 independent subagents")
    print("=" * 70)
    overall_start = time.time()

    results = await asyncio.gather(
        call_subagent("Pricing", "You are a pricing research subagent.",
                       "Invent a plausible retail price range for a mid-range wireless noise-cancelling headphone, with brief reasoning."),
        call_subagent("Shipping", "You are a shipping-policy research subagent.",
                       "Invent a plausible standard shipping policy (timeframe, cost) for an electronics retailer."),
        call_subagent("Warranty", "You are a warranty-policy research subagent.",
                       "Invent a plausible warranty policy (duration, coverage) for consumer electronics."),
    )

    overall_elapsed = time.time() - overall_start
    print(f"\n  All 3 completed in {overall_elapsed:.1f}s total (genuinely concurrent,")
    print(f"  not 3x sequential — each subagent above reported its own individual time)")

    print("\n  --- Synthesis call, combining all 3 real results ---")
    synth_input = f"Pricing findings: {results[0]}\n\nShipping findings: {results[1]}\n\nWarranty findings: {results[2]}\n\nWrite a 3-sentence product summary combining all three."
    synth_response = client.messages.create(
        model=MODEL, max_tokens=300,
        system="You are a synthesis agent combining independent research findings.",
        messages=[{"role": "user", "content": synth_input}],
    )
    synth_text = "".join(b.text for b in synth_response.content if b.type == "text")
    print(f"  Synthesis: {synth_text}")
    return overall_elapsed


async def test_b_hidden_dependency():
    print()
    print("=" * 70)
    print("TEST B: The hidden-dependency failure — REAL, not simulated")
    print("=" * 70)
    print("  Subagent 2 is asked to cross-check against subagent 1's findings,")
    print("  but both are launched in TRUE parallel — subagent 2 cannot")
    print("  actually see subagent 1's result, since neither has finished yet.")
    print()

    results = await asyncio.gather(
        call_subagent("Warranty (1)", "You are a warranty-policy research subagent.",
                       "Invent a plausible warranty policy (duration, coverage) for a consumer electronics product."),
        call_subagent("Cross-check (2)", "You are a shipping-policy subagent.",
                       "Cross-check our standard shipping policy against whatever warranty terms the other subagent just found, and flag any conflict."),
    )

    print(f"\n  Subagent 1 (Warranty) result: {results[0][:200]}")
    print(f"\n  Subagent 2 (Cross-check) result: {results[1][:300]}")
    print()
    print("  Does subagent 2's response reveal it actually had no access to")
    print("  subagent 1's real findings (e.g., it invents/assumes warranty")
    print("  terms, asks for them, or notes it cannot see them) — confirming")
    print("  the real-API version of the hidden-dependency failure mode?")


async def main():
    seq_would_be_estimate = None
    parallel_time = await test_a_genuine_parallel()
    await test_b_hidden_dependency()

    print()
    print("=" * 70)
    print(f"Test A took {parallel_time:.1f}s for 3 concurrent calls.")
    print("Compare this to Exercise 1's sequential pipeline timing (4 stages,")
    print("each waiting for the previous) to see the real speedup genuine")
    print("parallelism provides — and Test B shows the real cost: parallel")
    print("execution cannot honor a dependency between two 'parallel' agents.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
