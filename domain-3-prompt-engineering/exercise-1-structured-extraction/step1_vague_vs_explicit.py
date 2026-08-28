"""
step1_vague_vs_explicit.py — Domain 3, Concept 1: Explicit criteria vs. vague instructions.

THE CLAIM THIS DEMONSTRATES: "be conservative" or "flag if urgent" style
instructions don't fail because the model is bad at the task — they fail
because they leave the actual decision boundary undefined. Two people
(or two calls) can both be "being conservative" and land on different
answers for the same boundary-case input.

We run the SAME 5 support tickets through two prompts:
  A) vague: "Rate urgency. Be conservative about escalating."
  B) explicit: concrete rules mapping specific signals to specific levels

Run this multiple times — with the vague prompt, watch the boundary cases
(the damaged-but-shrugged-off ticket, the "3 weeks unacceptable" ticket)
potentially flip between runs. With the explicit prompt, they shouldn't.
"""

from backend import call_claude, SAMPLE_TICKETS, USE_REAL_API

VAGUE_SYSTEM = """You are a support ticket triager. Rate each ticket's
urgency. Be conservative about escalating things unnecessarily."""

EXPLICIT_SYSTEM = """You are a support ticket triager. Rate urgency using
these exact thresholds — apply them mechanically, don't use general
judgment beyond what's stated:

- HIGH: any of — explicit dispute/chargeback threat, repeated unresolved
  contact (2+ prior attempts mentioned), same-day deadline stated by customer
- MEDIUM: a real product/service problem (damage, bug, defect) with none
  of the HIGH signals present
- LOW: questions, preferences, or issues the customer themselves frames
  as minor/non-blocking

If a ticket has no explicit signal for a category, default to LOW."""


def run_comparison():
    print(f"Running in {'REAL API' if USE_REAL_API else 'MOCK'} mode\n")

    for i, ticket in enumerate(SAMPLE_TICKETS, 1):
        print(f"--- Ticket {i} ---")
        print(f"  {ticket[:80]}{'...' if len(ticket) > 80 else ''}")

        vague_result = call_claude(VAGUE_SYSTEM, ticket)
        vague_text = "".join(b.text for b in vague_result.content if b.type == "text")
        print(f"  [VAGUE]    {vague_text}")

        explicit_result = call_claude(EXPLICIT_SYSTEM, ticket)
        explicit_text = "".join(b.text for b in explicit_result.content if b.type == "text")
        print(f"  [EXPLICIT] {explicit_text}")
        print()


if __name__ == "__main__":
    print("=" * 70)
    print("RUN 1")
    print("=" * 70)
    run_comparison()

    print("=" * 70)
    print("RUN 2 (run again — compare VAGUE results between Run 1 and Run 2)")
    print("=" * 70)
    run_comparison()
