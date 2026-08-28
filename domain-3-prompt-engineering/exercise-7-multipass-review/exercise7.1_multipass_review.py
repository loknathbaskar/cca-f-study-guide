"""
exercise2_multipass_review.py — Domain 3, Concept 6: Multi-pass review
architectures (draft pass + critique pass) for reducing false positives.

THE SETUP: `requires_escalation` has NEVER had explicit criteria in any
prompt across this whole exercise (a gap we flagged honestly back in
Step 3/4) — every escalation flag so far has been an ungrounded guess.
That makes it the perfect real candidate for a two-pass architecture:

  PASS 1 (draft): extract ticket data as usual, including a
  requires_escalation guess with no explicit criteria — this is exactly
  what we've been doing all along, unchanged.

  PASS 2 (critique): a SEPARATE call, given the original ticket + the
  draft's escalation verdict, specifically asked to challenge it: is
  there an actual concrete signal (dispute threat, repeated unresolved
  contact, safety issue, explicit request for a manager) — or was the
  draft reacting to emotional intensity/tone with no real substance
  behind it? The critique pass can only CONFIRM or DOWNGRADE (never
  invent a new escalation the draft didn't flag) — this specifically
  targets FALSE POSITIVES, which is the stated exam concept.

A NEW ticket (7) is added, deliberately designed to bait a false-positive
escalation: high emotional intensity, zero concrete signal. This is the
real test of whether critique catches what a draft pass alone misses.
"""

from backend import call_claude, USE_REAL_API

EXTRACT_TOOL = {
    "name": "extract_ticket_data",
    "description": "Extract structured triage data from a support ticket.",
    "input_schema": {
        "type": "object",
        "properties": {
            "customer_sentiment": {
                "type": "string",
                "enum": ["very_negative", "negative", "neutral", "positive"],
            },
            "issue_category": {
                "type": "string",
                "enum": ["shipping_delay", "billing_error", "product_defect",
                          "product_question", "app_bug", "other"],
            },
            "issue_category_detail": {"type": ["string", "null"]},
            "urgency": {"type": "string", "enum": ["low", "medium", "high"]},
            "refund_requested": {"type": ["boolean", "null"]},
            "requires_escalation": {
                "type": "boolean",
                "description": "Whether this needs a human supervisor, not just a standard agent."
            },
        },
        "required": ["customer_sentiment", "issue_category", "issue_category_detail",
                      "urgency", "refund_requested", "requires_escalation"]
    }
}

CRITIQUE_TOOL = {
    "name": "critique_escalation",
    "description": "Review a draft escalation decision and confirm or downgrade it based on whether a concrete signal actually justifies it.",
    "input_schema": {
        "type": "object",
        "properties": {
            "concrete_signal_found": {
                "type": ["string", "null"],
                "description": "The specific concrete signal justifying escalation (dispute threat, repeated unresolved contact, safety issue, explicit request for a manager), or null if none exists."
            },
            "final_verdict": {
                "type": "boolean",
                "description": "true only if concrete_signal_found is non-null. Can only CONFIRM or DOWNGRADE the draft — never upgrade a draft 'false' to 'true'."
            },
            "reasoning": {"type": "string"},
        },
        "required": ["concrete_signal_found", "final_verdict", "reasoning"]
    }
}

DRAFT_SYSTEM = """You are a support ticket triager. Extract structured
data from each ticket. Flag requires_escalation=true if the customer
seems very upset, angry, or dissatisfied — we want to make sure no
frustrated customer falls through the cracks."""

CRITIQUE_SYSTEM = """You are a senior reviewer auditing escalation
decisions made by a junior triager, specifically to catch FALSE
POSITIVES — escalations flagged from emotional intensity or negative tone
alone, with no concrete actionable signal behind them.

A concrete signal is one of: an explicit dispute/chargeback threat,
repeated unresolved contact attempts (2+), an explicit safety issue, or
an explicit request to speak to a manager/supervisor. Strong language,
ALL CAPS, exclamation points, or general anger are NOT concrete signals
on their own.

You may only CONFIRM the draft's escalation flag (if a concrete signal
truly exists) or DOWNGRADE it to false (if it doesn't). You may never
upgrade a draft's "false" to "true" — this pass exists only to catch
over-escalation, not to find new escalations the draft missed."""

TICKETS = [
    "My order #4471 hasn't arrived in 3 weeks. I've emailed twice with no response. This is unacceptable, I want a full refund immediately.",
    "not sure if this is the right place but my package arrived damaged, box was crushed. not a huge deal, item still works, just wanted you to know",
    "URGENT: I was charged twice for order #8821. Please fix this today or I'm disputing the charge with my bank.",
    # Ticket 7 — the false-positive bait: maximum emotional intensity,
    # zero concrete signal. A draft pass reacting to tone alone should
    # over-flag this; critique should catch it.
    "This is the WORST experience of my life. I am ABSOLUTELY FURIOUS. I have never in my life been so disrespected by a company. My package box had a small dent in the corner. Fix your packaging!!!",
]


def draft_pass(ticket: str) -> dict:
    result = call_claude(
        DRAFT_SYSTEM, ticket,
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "extract_ticket_data"},
    )
    tool_call = next(b for b in result.content if b.type == "tool_use")
    return tool_call.input


def critique_pass(ticket: str, draft: dict) -> dict:
    if draft["requires_escalation"] is False:
        # Nothing to critique — the whole point is catching false
        # positives, not second-guessing a draft that already said no
        return {"concrete_signal_found": None, "final_verdict": False,
                "reasoning": "Draft did not flag escalation — critique pass only reviews positive flags."}

    critique_input = (
        f"Original ticket: {ticket}\n\n"
        f"Draft triager flagged requires_escalation=true for this ticket. "
        f"Review whether a concrete signal actually justifies that."
    )
    result = call_claude(
        CRITIQUE_SYSTEM, critique_input,
        tools=[CRITIQUE_TOOL],
        tool_choice={"type": "tool", "name": "critique_escalation"},
    )
    tool_call = next(b for b in result.content if b.type == "tool_use")
    return tool_call.input


if __name__ == "__main__":
    print(f"Running in {'REAL API' if USE_REAL_API else 'MOCK'} mode\n")

    for i, ticket in enumerate(TICKETS, 1):
        print("=" * 70)
        print(f"TICKET {i}: {ticket[:80]}{'...' if len(ticket) > 80 else ''}")
        print("=" * 70)

        draft = draft_pass(ticket)
        print(f"  DRAFT:    requires_escalation={draft['requires_escalation']}")

        critique = critique_pass(ticket, draft)
        if draft["requires_escalation"]:
            print(f"  CRITIQUE: concrete_signal={critique['concrete_signal_found']}")
            print(f"            final_verdict={critique['final_verdict']}")
            print(f"            reasoning: {critique['reasoning']}")

            if draft["requires_escalation"] != critique["final_verdict"]:
                print(f"  >>> DOWNGRADED: draft said escalate, critique overrode to false <<<")
            else:
                print(f"  >>> CONFIRMED: critique agrees escalation is justified <<<")
        print()

    print("=" * 70)
    print("Key question: did the critique pass correctly downgrade ticket 7")
    print("(maximum emotional intensity, zero concrete signal), while")
    print("CONFIRMING tickets 1 and 3 (which have real concrete signals)?")
    print("=" * 70)
