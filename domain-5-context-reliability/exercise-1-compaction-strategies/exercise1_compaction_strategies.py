"""
exercise1_compaction_strategies.py — Domain 5, Concept 1: Context
compaction — does structured extraction actually preserve facts better
than prose summarization?

THE CLAIM BEING TESTED (from the exam guide's own language): "Structured
records, targeted retrieval, and explicit unresolved fields are often
safer than replacing an entire history with an unverified prose
summary." This is a specific, falsifiable claim — let's actually test it,
including its likely WEAKNESS, not just its strength.

THE SETUP: a fact-dense, 8-turn customer support conversation, with:
  - Multiple specific numbers (order IDs, dollar amounts, dates)
  - A mid-conversation PROMISE made by the agent (a fee waiver) — this is
    exactly the kind of "unresolved commitment" the exam language calls out
  - One INCIDENTAL detail unrelated to the main support issue (the
    customer mentions an upcoming address change) — deliberately NOT
    something an obvious support-ticket schema would think to capture

TWO COMPACTION METHODS, same conversation:
  A) PROSE SUMMARY — a free-text summary, no schema
  B) STRUCTURED EXTRACTION — a JSON record with explicit fields for the
     facts we anticipated mattering (order IDs, amounts, promises,
     unresolved items) — but NO field for the incidental address-change
     detail, since a real schema author might not have anticipated it

THEN: using ONLY the compacted representation (not the original
conversation) as context, ask two follow-up questions:
  Q1 (in-schema fact): "What exact fee amount was promised to be waived?"
  Q2 (out-of-schema, incidental fact): "Did the customer mention anything
      about their living situation changing?"

PREDICTION: structured extraction should win Q1 (the fact it was
designed to capture) but may LOSE Q2 (the fact no field existed for) —
testing both the claimed strength and a real, honest weakness of rigid
structure, not just confirming the exam's claim uncritically.
"""

from backend import call_claude, USE_REAL_API

CONVERSATION = """
Customer: Hi, I'm following up on order #55291. It was supposed to arrive last Tuesday and it's still not here.
Agent: I'm sorry to hear that. Let me look into order #55291 for you. I see it shipped on the 3rd but there's a carrier delay. It should arrive within 2 more business days.
Customer: This is the second time this has happened with your shipping. Last month order #48120 was also late.
Agent: I understand your frustration. For the inconvenience, I'd like to waive the $12.99 expedited shipping fee you paid on this order as a goodwill gesture.
Customer: That's appreciated but I really just need the package. Also, quick unrelated thing - I'm moving to a new apartment next month, does that affect any active orders if I update my address now?
Agent: Great question - if you update your shipping address before an order ships, it will use the new address. Order #55291 has already shipped though, so it will go to your current address on file.
Customer: Okay that makes sense. What about the $12.99 waiver - will that show up as a refund or account credit?
Agent: It'll be processed as a refund to your original payment method, typically within 3-5 business days.
Customer: Got it, thank you. One more thing - I never got a response about my order from 2 months ago, #41055, which I believe was never delivered at all. Can someone look into that too?
Agent: I don't see a resolution logged for #41055 in our system. I'm flagging this for our fulfillment team to investigate and will follow up within 48 hours.
"""

EXTRACT_TOOL = {
    "name": "extract_support_summary",
    "description": "Extract a structured summary of a customer support conversation.",
    "input_schema": {
        "type": "object",
        "properties": {
            "order_ids_mentioned": {"type": "array", "items": {"type": "string"}},
            "promises_made": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "promise": {"type": "string"},
                        "amount": {"type": ["number", "null"]},
                        "fulfillment_method": {"type": ["string", "null"]},
                        "timeline": {"type": ["string", "null"]},
                    },
                    "required": ["promise", "amount", "fulfillment_method", "timeline"]
                }
            },
            "unresolved_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "issue": {"type": "string"},
                        "related_order_id": {"type": ["string", "null"]},
                        "follow_up_committed": {"type": ["string", "null"]},
                    },
                    "required": ["issue", "related_order_id", "follow_up_committed"]
                }
            },
        },
        "required": ["order_ids_mentioned", "promises_made", "unresolved_items"]
    }
}


def get_prose_summary():
    result = call_claude(
        "Summarize the following customer support conversation concisely, preserving key facts.",
        CONVERSATION,
    )
    return "".join(b.text for b in result.content if b.type == "text")


def get_structured_summary():
    result = call_claude(
        "Extract a structured summary of this customer support conversation.",
        CONVERSATION,
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "extract_support_summary"},
    )
    tool_call = next(b for b in result.content if b.type == "tool_use")
    return tool_call.input


def ask_followup(compacted_context: str, question: str, label: str):
    result = call_claude(
        "Answer the user's question using ONLY the context provided below. "
        "If the context doesn't contain the answer, say so explicitly — do not guess.\n\n"
        f"CONTEXT:\n{compacted_context}",
        question,
    )
    answer = "".join(b.text for b in result.content if b.type == "text")
    print(f"  [{label}] Q: {question}")
    print(f"  [{label}] A: {answer}\n")


if __name__ == "__main__":
    if not USE_REAL_API:
        print("This exercise requires ANTHROPIC_API_KEY — compaction quality")
        print("is exactly what's being tested, no meaningful mock exists.")
        raise SystemExit(0)

    print("=" * 70)
    print("Generating both compacted representations from the same conversation")
    print("=" * 70)
    prose = get_prose_summary()
    print(f"\nPROSE SUMMARY:\n{prose}\n")

    structured = get_structured_summary()
    print(f"STRUCTURED EXTRACTION:\n{structured}\n")

    print("=" * 70)
    print("Q1 (IN-SCHEMA FACT): the exact fee waiver amount")
    print("=" * 70)
    ask_followup(prose, "What exact fee amount was promised to be waived, and how will it be returned to the customer?", "PROSE")
    ask_followup(str(structured), "What exact fee amount was promised to be waived, and how will it be returned to the customer?", "STRUCTURED")

    print("=" * 70)
    print("Q2 (OUT-OF-SCHEMA, INCIDENTAL FACT): the address change mention")
    print("(the extraction schema has NO field for this — testing whether")
    print(" that means it's lost entirely)")
    print("=" * 70)
    ask_followup(prose, "Did the customer mention anything about their living situation changing?", "PROSE")
    ask_followup(str(structured), "Did the customer mention anything about their living situation changing?", "STRUCTURED")

    print("=" * 70)
    print("Did structured extraction win Q1 but lose Q2 — confirming both the")
    print("claimed strength AND a real weakness of rigid structure, rather")
    print("than structured being unconditionally better?")
    print("=" * 70)
