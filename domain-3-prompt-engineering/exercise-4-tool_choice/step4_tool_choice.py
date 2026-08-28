"""
step4_tool_choice.py — Domain 3, Concept 4: tool_choice — auto vs. any vs.
forced (a specific named tool).

THE THREE MODES:
  - {"type": "auto"}: model decides whether to use a tool at all, or just
    respond in text. Flexible, but breaks the guarantee of structured
    output — sometimes you'll get text back instead of a tool call.
  - {"type": "any"}: model MUST call one of the provided tools, but can
    choose WHICH one. Guarantees structure, while still allowing the
    model to pick the right tool for the input.
  - {"type": "tool", "name": "X"}: model MUST call exactly tool X.
    Strongest guarantee (always get that exact structure), but zero
    flexibility — even garbage input gets forced through the same schema.

THE POINT OF THIS EXERCISE: give the model an "escape valve" tool
(request_human_clarification) alongside the extraction tool, then feed it
BOTH a normal ticket and a genuinely un-triageable one (spam/garbage), to
see concretely what each tool_choice mode does with input that doesn't
actually fit the intended schema.

Prediction to test: does FORCED tool_choice on extract_ticket_data hallucinate
a plausible-looking classification for garbage input, since it has no
other option? Does ANY (with the clarification tool available) correctly
route garbage to the escape valve instead?
"""

from backend import call_claude, USE_REAL_API

EXTRACT_TOOL = {
    "name": "extract_ticket_data",
    "description": "Extract structured triage data from a genuine, legible support ticket.",
    "input_schema": {
        "type": "object",
        "properties": {
            "customer_sentiment": {
                "type": "string",
                "enum": ["very_negative", "negative", "neutral", "positive"],
            },
            "issue_category": {
                "type": "string",
                "enum": [
                    "shipping_delay", "billing_error", "product_defect",
                    "product_question", "app_bug", "other"
                ],
            },
            "issue_category_detail": {
                "type": ["string", "null"],
                "description": "Required if issue_category is 'other'. Null otherwise."
            },
            "urgency": {"type": "string", "enum": ["low", "medium", "high"]},
            "refund_requested": {"type": ["boolean", "null"]},
            "requires_escalation": {"type": "boolean"},
        },
        "required": [
            "customer_sentiment", "issue_category", "issue_category_detail",
            "urgency", "refund_requested", "requires_escalation"
        ]
    }
}

CLARIFICATION_TOOL = {
    "name": "request_human_clarification",
    "description": "Use this when the input is too ambiguous, incomplete, spam, or nonsensical to meaningfully classify as a real support ticket — do NOT force garbage input through extract_ticket_data.",
    "input_schema": {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Brief explanation of why this can't be classified as a genuine ticket."
            }
        },
        "required": ["reason"]
    }
}

SYSTEM = """You are a support ticket triager. For each input, either
extract structured data from it (if it's a genuine support ticket) or
flag that it needs human review (if it's not legible as a real ticket)."""

NORMAL_TICKET = "My order #4471 hasn't arrived in 3 weeks. I've emailed twice with no response. This is unacceptable, I want a full refund immediately."
GARBAGE_TICKET = "asdkfj ASDKFJ buy crypto NOW!!! click here www.definitely-not-a-scam.biz for 1000x gains guaranteed"


def run_and_report(label, system, message, tools, tool_choice):
    result = call_claude(system, message, tools=tools, tool_choice=tool_choice)
    if result.stop_reason == "tool_use" or any(b.type == "tool_use" for b in result.content):
        tool_call = next(b for b in result.content if b.type == "tool_use")
        print(f"  {label}: called `{tool_call.name}` with {tool_call.input}")
    else:
        text = "".join(b.text for b in result.content if b.type == "text")
        print(f"  {label}: NO tool called, returned text instead: {text[:150]}")


if __name__ == "__main__":
    print(f"Running in {'REAL API' if USE_REAL_API else 'MOCK'} mode\n")

    print("=" * 70)
    print("NORMAL TICKET — a genuine, clearly-triageable ticket")
    print("=" * 70)
    run_and_report("A) AUTO (extract_tool only)", SYSTEM, NORMAL_TICKET,
                    [EXTRACT_TOOL], {"type": "auto"})
    run_and_report("B) ANY (both tools available)", SYSTEM, NORMAL_TICKET,
                    [EXTRACT_TOOL, CLARIFICATION_TOOL], {"type": "any"})
    run_and_report("C) FORCED extract_ticket_data", SYSTEM, NORMAL_TICKET,
                    [EXTRACT_TOOL], {"type": "tool", "name": "extract_ticket_data"})

    print()
    print("=" * 70)
    print("GARBAGE TICKET — spam, not a real support request")
    print("=" * 70)
    run_and_report("A) AUTO (extract_tool only)", SYSTEM, GARBAGE_TICKET,
                    [EXTRACT_TOOL], {"type": "auto"})
    run_and_report("B) ANY (both tools available)", SYSTEM, GARBAGE_TICKET,
                    [EXTRACT_TOOL, CLARIFICATION_TOOL], {"type": "any"})
    run_and_report("C) FORCED extract_ticket_data", SYSTEM, GARBAGE_TICKET,
                    [EXTRACT_TOOL], {"type": "tool", "name": "extract_ticket_data"})

    print()
    print("=" * 70)
    print("Key question: on GARBAGE input, does C) hallucinate a plausible-")
    print("looking classification (since it has no other option), while")
    print("B) correctly routes to request_human_clarification instead?")
    print("=" * 70)
