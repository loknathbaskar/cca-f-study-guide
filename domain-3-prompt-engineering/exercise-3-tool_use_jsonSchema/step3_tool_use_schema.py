"""
step3_tool_use_schema.py — Domain 3, Concept 3: Structured output via
tool_use. Two separate lessons in one exercise:

LESSON A: "A JSON schema guarantees STRUCTURE, not SEMANTIC correctness."
We run the SAME vague-vs-explicit comparison from Step 1, but now forced
through a tool_use schema instead of free text. Prediction to test: does
wrapping the vague prompt in a schema fix its miscalibration on ticket 4
(the dispute-threat-discounting problem), or does the schema just force
a WRONG answer into a valid shape instead of a right answer into a valid
shape? Structure and correctness are independent properties — this
either confirms or challenges that claim with real data.

LESSON B: Schema design choices that matter —
  - refund_requested is NULLABLE (bool | null), not just bool. A ticket
    that never mentions a refund should produce null, not a guessed
    True/False. Forcing a non-nullable boolean forces a hallucinated
    guess on every single ticket that doesn't mention refunds at all.
  - issue_category has an "other" escape hatch + issue_category_detail
    free-text field, so a ticket that doesn't cleanly fit any enum value
    doesn't get force-fit into the closest wrong bucket.
"""

from backend import call_claude, SAMPLE_TICKETS, USE_REAL_API

EXTRACT_TOOL = {
    "name": "extract_ticket_data",
    "description": "Extract structured triage data from a support ticket.",
    "input_schema": {
        "type": "object",
        "properties": {
            "customer_sentiment": {
                "type": "string",
                "enum": ["very_negative", "negative", "neutral", "positive"],
                "description": "Overall emotional tone of the ticket."
            },
            "issue_category": {
                "type": "string",
                "enum": [
                    "shipping_delay", "billing_error", "product_defect",
                    "product_question", "app_bug", "other"
                ],
                "description": "Best-fit category. Use 'other' if none fit cleanly — do not force a mismatched category."
            },
            "issue_category_detail": {
                "type": ["string", "null"],
                "description": "Required, brief free-text description if issue_category is 'other'. Null otherwise."
            },
            "urgency": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Triage urgency level."
            },
            "refund_requested": {
                "type": ["boolean", "null"],
                "description": "true if a refund is explicitly requested, false if explicitly declined/not applicable, null if refunds are not mentioned at all. Do NOT guess — use null when genuinely unstated."
            },
            "requires_escalation": {
                "type": "boolean",
                "description": "true if this needs a human supervisor, not just a standard agent."
            }
        },
        "required": [
            "customer_sentiment", "issue_category", "issue_category_detail",
            "urgency", "refund_requested", "requires_escalation"
        ]
    }
}

VAGUE_SYSTEM = """You are a support ticket triager. Extract structured
data from each ticket. Be conservative about escalating things
unnecessarily."""

EXPLICIT_SYSTEM = """You are a support ticket triager. Extract structured
data from each ticket using these exact thresholds for urgency — apply
them mechanically:

- HIGH: any of — explicit dispute/chargeback threat, repeated unresolved
  contact (2+ prior attempts mentioned), same-day deadline stated by customer
- MEDIUM: a real product/service problem (damage, bug, defect) with none
  of the HIGH signals present
- LOW: questions, preferences, or issues the customer themselves frames
  as minor/non-blocking, OR no explicit signal for a category at all

For refund_requested: use null unless a refund is explicitly mentioned —
do not infer a refund request from general dissatisfaction alone."""


def run_condition(label, system_prompt):
    print(f"--- {label} ---")
    for i, ticket in enumerate(SAMPLE_TICKETS, 1):
        result = call_claude(
            system_prompt, ticket,
            tools=[EXTRACT_TOOL],
            tool_choice={"type": "tool", "name": "extract_ticket_data"},
        )
        tool_call = next(b for b in result.content if b.type == "tool_use")
        print(f"  Ticket {i}: {tool_call.input}")
    print()


if __name__ == "__main__":
    print(f"Running in {'REAL API' if USE_REAL_API else 'MOCK'} mode\n")
    run_condition("A) VAGUE + tool_use schema", VAGUE_SYSTEM)
    run_condition("B) EXPLICIT + tool_use schema", EXPLICIT_SYSTEM)

    print("=" * 70)
    print("Check: does the schema alone fix ticket 4's miscalibration,")
    print("or does VAGUE still under-rate urgency despite valid structure?")
    print("Also check: does refund_requested come back null for tickets")
    print("that never mention a refund, or does it guess true/false?")
    print("=" * 70)
