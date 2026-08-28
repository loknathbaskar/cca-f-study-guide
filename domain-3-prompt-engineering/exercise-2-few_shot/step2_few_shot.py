"""
step2_few_shot.py — Domain 3, Concept 2: Few-shot prompting with boundary
cases, not happy-path examples.

THE POINT: Step 1 found two distinct failure modes in the VAGUE prompt:
  1. Ticket 3 (recurring bug, customer downplays it) -> indecisive,
     invented an undefined "Low-Medium" label
  2. Ticket 4 (explicit dispute threat, stated casually/angrily) -> the
     model's own judgment overrode a clear policy signal ("don't let the
     threatening tone inflate the urgency")

A good few-shot set targets THESE failure modes directly — not random
examples, not easy cases the model would get right anyway. The 3 examples
below are deliberately constructed to be near-misses of tickets 3 and 4,
so if few-shot works, we should see it specifically fix these two
failure patterns, not just "improve results in general."

We compare THREE conditions on the same 5 tickets from Step 1:
  A) VAGUE (from step 1, for reference)
  B) VAGUE + FEW-SHOT (same vague instruction, examples added)
  C) EXPLICIT (from step 1, for reference)

If B performs close to C, few-shot examples can substitute for explicit
rule-writing. If B still shows ticket 3/4-style failures, that tells you
something real about the limits of few-shot vs. explicit criteria.
"""

from backend import call_claude, SAMPLE_TICKETS, USE_REAL_API

VAGUE_SYSTEM = """You are a support ticket triager. Rate each ticket's
urgency. Be conservative about escalating things unnecessarily."""

# Few-shot examples deliberately targeting the TWO failure modes from
# Step 1 — not generic examples, near-misses of tickets 3 and 4:
FEW_SHOT_SYSTEM = """You are a support ticket triager. Rate each ticket's
urgency as LOW, MEDIUM, or HIGH. Be conservative about escalating things
unnecessarily.

Here are examples of how to reason through tricky cases:

Example 1:
Ticket: "the payment page timed out twice, so annoying, but I eventually
got it to work"
Reasoning: There's a real bug (payment timeout), but the customer resolved
it themselves and explicitly frames it as merely annoying, not blocking.
No dispute mention, no deadline.
Urgency: LOW

Example 2:
Ticket: "hey no big deal but my card got charged the wrong amount, if it's
not fixed by end of week I might just dispute it lol"
Reasoning: The tone is casual and joking ("lol", "no big deal"), but the
ticket explicitly contains a dispute threat. Tone does not override an
explicit dispute/chargeback signal — the signal itself is what matters,
regardless of how it's phrased.
Urgency: HIGH

Example 3:
Ticket: "app keeps freezing when I add items to wishlist, happened 3 times
this week, still able to shop around it, not a big deal"
Reasoning: A real, recurring functional bug — but the customer explicitly
frames it as not blocking and not a big deal, with no dispute threat and
no deadline. Per policy, the customer's own minor/non-blocking framing
determines the category here, even though the underlying bug is real and
recurring. Recurrence alone isn't a listed HIGH or MEDIUM signal — only
dispute threats, repeated *unresolved contact attempts* (not repeated bug
occurrences), and deadlines are.
Urgency: LOW

Now rate the following ticket the same way — briefly state which signals
you found, then give the urgency level."""

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


def run_condition(label, system_prompt):
    print(f"--- {label} ---")
    for i, ticket in enumerate(SAMPLE_TICKETS, 1):
        result = call_claude(system_prompt, ticket)
        text = "".join(b.text for b in result.content if b.type == "text")
        print(f"  Ticket {i}:\n{text}\n")
    print()


if __name__ == "__main__":
    print(f"Running in {'REAL API' if USE_REAL_API else 'MOCK'} mode\n")
    run_condition("A) VAGUE", VAGUE_SYSTEM)
    run_condition("B) VAGUE + FEW-SHOT", FEW_SHOT_SYSTEM)
    run_condition("C) EXPLICIT", EXPLICIT_SYSTEM)

    print("=" * 70)
    print("Compare ticket 3 and ticket 4 specifically across A, B, C —")
    print("did few-shot (B) fix the two failure modes Step 1 found in A?")
    print("=" * 70)
