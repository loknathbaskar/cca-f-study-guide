"""
backend.py — same real/mock abstraction pattern as Domain 1's exercise, so
this runs whether or not ANTHROPIC_API_KEY is set. Mock mode here is
LESS deterministic than Domain 1's on purpose — it simulates realistic
inconsistency for the vague-prompt demo (step 1), which is the actual
point being demonstrated.
"""

import os
import random

USE_REAL_API = bool(os.environ.get("ANTHROPIC_API_KEY"))

if USE_REAL_API:
    import anthropic
    _client = anthropic.Anthropic()


def call_claude(system: str, user_message: str, tools: list = None,
                 tool_choice: dict = None, max_tokens: int = 1024):
    if USE_REAL_API:
        kwargs = dict(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
        return _client.messages.create(**kwargs)

    return _mock_response(system, user_message, tools, tool_choice)


class _MockContentBlock:
    def __init__(self, type_, text=None, name=None, input_=None, id_=None):
        self.type = type_
        self.text = text
        self.name = name
        self.input = input_
        self.id = id_ or "mock_tool_use_id"


class _MockResponse:
    def __init__(self, content, stop_reason="end_turn"):
        self.content = content
        self.stop_reason = stop_reason


# Realistic support ticket bodies used across all steps — same inputs,
# different prompting techniques, so results are actually comparable.
SAMPLE_TICKETS = [
    "My order #4471 hasn't arrived in 3 weeks. I've emailed twice with no response. This is unacceptable, I want a full refund immediately.",
    "Hi, quick question — does the blue sweater run small? Thinking about sizing up.",
    "the app crashed again while I was checking out. lost my whole cart. kind of annoying but whatever, I'll just redo it",
    "URGENT: I was charged twice for order #8821. Please fix this today or I'm disputing the charge with my bank.",
    "not sure if this is the right place but my package arrived damaged, box was crushed. not a huge deal, item still works, just wanted you to know",
    # Ticket 6 — deliberately does NOT fit shipping_delay, billing_error,
    # product_defect, product_question, or app_bug. Tests whether the
    # schema's "other" + issue_category_detail escape hatch gets used
    # correctly, or whether this gets force-fit into the nearest wrong
    # category (most likely candidate for a wrong force-fit: product_question,
    # since it's at least vaguely "about the company").
    "I called your support line yesterday and the rep was incredibly rude and dismissive when I asked a simple question. I want someone to actually know this happened.",
]


def _mock_response(system, user_message, tools, tool_choice):
    """
    Mock behavior deliberately varies based on WHICH step's system prompt
    is used, to simulate the real phenomenon each step demonstrates:
    - vague prompt -> inconsistent, mood-based urgency judgments
    - explicit criteria -> consistent judgments matching stated thresholds
    - tool_use -> returns a proper tool_use block instead of text
    """
    text_lower = user_message.lower()

    # Step 2 mock: vague + few-shot -> should approximate explicit's
    # correctness on the two failure-mode tickets (3 and 4), since the
    # examples directly target those patterns
    if "example 1" in system.lower() and "example 2" in system.lower() and not tools:
        if "urgent" in text_lower or "dispute" in text_lower or "today" in text_lower:
            urgency = "high"
        elif "3 weeks" in text_lower or "twice" in text_lower:
            urgency = "high"
        elif "damaged" in text_lower:
            urgency = "low"  # matches Example 1's pattern: real issue + customer downplays -> low
        elif "crashed" in text_lower:
            urgency = "low"  # corrected to match fixed Example 3: customer's non-blocking framing determines category, recurrence alone isn't a listed signal
        else:
            urgency = "low"
        return _MockResponse([_MockContentBlock(
            "text", text=f"Signals found based on the examples. Urgency: {urgency}"
        )])

    # Step 1 mock: vague "be conservative about urgency" prompt ->
    # deliberately inconsistent, to simulate what actually happens with
    # underspecified criteria (a real vague prompt against a real model
    # doesn't literally randomize like this, but DOES produce inconsistent
    # boundary judgments across similar-but-not-identical inputs, which is
    # what this simulates for teaching purposes without needing dozens of
    # live API calls to observe empirically)
    if "conservative" in system.lower() and "urgency" in system.lower() and not tools:
        if "damaged" in text_lower and "not a huge deal" in text_lower:
            # Ambiguous case — mock simulates the real inconsistency risk
            urgency = random.choice(["low", "medium"])
        elif "urgent" in text_lower or "dispute" in text_lower:
            urgency = "high"
        elif "3 weeks" in text_lower or "unacceptable" in text_lower:
            urgency = random.choice(["medium", "high"])  # the actual boundary case
        elif "crashed" in text_lower and "whatever" in text_lower:
            urgency = random.choice(["low", "medium"])  # another real boundary case
        elif "rude" in text_lower and "rep" in text_lower:
            urgency = random.choice(["low", "medium"])  # ticket 6 — off-category, ambiguous under vague criteria too
        else:
            urgency = "low"
        return _MockResponse([_MockContentBlock("text", text=f"Urgency: {urgency}")])

    # Step 2 mock: explicit criteria -> consistent, rule-based
    if "threshold" in system.lower() and not tools:
        if "urgent" in text_lower or "dispute" in text_lower or "today" in text_lower:
            urgency = "high"
        elif "3 weeks" in text_lower or "twice" in text_lower:
            urgency = "high"  # explicit rule: unresolved + repeated contact = high
        elif "damaged" in text_lower:
            urgency = "medium"  # explicit rule: product issue, no financial/repeated-contact signal = medium
        elif "crashed" in text_lower:
            urgency = "medium"  # explicit rule: functional bug = medium regardless of tone
        else:
            urgency = "low"
        return _MockResponse([_MockContentBlock("text", text=f"Urgency: {urgency}")])

    # tool_use mock (step 3+) — differentiate VAGUE vs EXPLICIT so the
    # "schema doesn't fix miscalibration" demonstration works in mock mode
    if tools:
        tool_name = tools[0]["name"]
        is_explicit = "threshold" in system.lower() or "mechanically" in system.lower()

        # Step 4 mock: tool_choice auto/any/forced, with a garbage-input case
        is_garbage = "crypto" in text_lower or "guaranteed" in text_lower
        has_clarification_tool = any(t["name"] == "request_human_clarification" for t in tools)
        choice_type = (tool_choice or {}).get("type", "auto")

        if is_garbage:
            if choice_type == "auto":
                # AUTO with only extract_tool available: model recognizes
                # garbage isn't a real ticket and just responds in text
                # instead of forcing a tool call
                return _MockResponse([_MockContentBlock(
                    "text",
                    text="This doesn't appear to be a genuine support ticket — it looks like spam/promotional content, not something to extract triage data from."
                )])
            elif choice_type == "any" and has_clarification_tool:
                # ANY with the escape-valve tool available: correctly
                # routes to clarification instead of forcing extraction
                return _MockResponse(
                    [_MockContentBlock("tool_use", name="request_human_clarification",
                                        input_={"reason": "This appears to be spam/promotional content, not a genuine support ticket."})],
                    stop_reason="tool_use",
                )
            elif choice_type == "tool":
                # FORCED extract_ticket_data: no other option exists —
                # must hallucinate SOMETHING into the schema
                return _MockResponse(
                    [_MockContentBlock("tool_use", name="extract_ticket_data", input_={
                        "customer_sentiment": "neutral",
                        "issue_category": "other",
                        "issue_category_detail": "Unable to determine — input does not resemble a genuine support ticket",
                        "urgency": "low",
                        "refund_requested": None,
                        "requires_escalation": False,
                    })],
                    stop_reason="tool_use",
                )

        # normal (non-garbage) ticket under step 4's tool_choice modes —
        # all three modes should behave the same on legible input
        if "3 weeks" in text_lower and tool_name in ("extract_ticket_data",):
            if choice_type in ("auto", "any", "tool"):
                return _MockResponse(
                    [_MockContentBlock("tool_use", name="extract_ticket_data", input_={
                        "customer_sentiment": "very_negative",
                        "issue_category": "shipping_delay",
                        "issue_category_detail": None,
                        "urgency": "high",
                        "refund_requested": True,
                        "requires_escalation": True,
                    })],
                    stop_reason="tool_use",
                )

        if "damaged" in text_lower:
            mock_input = {
                "customer_sentiment": "negative",
                "issue_category": "shipping_delay",
                "issue_category_detail": None,
                "urgency": "low",  # customer frames as minor -> low under BOTH conditions
                "refund_requested": None,  # never mentioned -> null, correctly, under both
                "requires_escalation": False,
            }
        elif "urgent" in text_lower or "dispute" in text_lower:
            mock_input = {
                "customer_sentiment": "very_negative",
                "issue_category": "billing_error",
                "issue_category_detail": None,
                # THE KEY DEMONSTRATION: same schema, different urgency,
                # because the schema doesn't fix the underlying vague-prompt
                # miscalibration — it just forces whatever answer into a
                # valid shape
                "urgency": "high" if is_explicit else "medium",
                "refund_requested": None,  # no refund mentioned in this ticket, only a dispute threat
                "requires_escalation": is_explicit,
            }
        elif "sizing" in text_lower or "run small" in text_lower:
            mock_input = {
                "customer_sentiment": "neutral",
                "issue_category": "product_question",
                "issue_category_detail": None,
                "urgency": "low",
                "refund_requested": None,
                "requires_escalation": False,
            }
        elif "crashed" in text_lower:
            mock_input = {
                "customer_sentiment": "neutral",
                "issue_category": "app_bug",
                "issue_category_detail": None,
                "urgency": "low" if is_explicit else "medium",  # same pattern as ticket 4, mirrored
                "refund_requested": None,
                "requires_escalation": False,
            }
        elif "rude" in text_lower and "rep" in text_lower:
            # Ticket 6 — designed to not fit any of the 5 named categories.
            # Tests whether "other" + issue_category_detail gets used
            # correctly instead of a force-fit into the nearest wrong bucket.
            mock_input = {
                "customer_sentiment": "negative",
                "issue_category": "other",
                "issue_category_detail": "Complaint about a rude/dismissive support representative — a staff conduct issue, not a product, billing, shipping, or app problem.",
                "urgency": "low" if is_explicit else "medium",
                "refund_requested": None,
                "requires_escalation": False,
            }
        else:
            mock_input = {
                "customer_sentiment": "negative",
                "issue_category": "shipping_delay",
                "issue_category_detail": None,
                "urgency": "high",
                "refund_requested": True,  # explicitly requested in this ticket's text
                "requires_escalation": True,
            }
        return _MockResponse(
            [_MockContentBlock("tool_use", name=tool_name, input_=mock_input)],
            stop_reason="tool_use",
        )

    return _MockResponse([_MockContentBlock("text", text="[mock] unhandled case")])
