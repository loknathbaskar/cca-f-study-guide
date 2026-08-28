"""
backend.py — same real/mock abstraction pattern used throughout this
exercise, so this runs whether or not ANTHROPIC_API_KEY is set.
"""

import os

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
    def __init__(self, type_, text=None, name=None, input_=None):
        self.type = type_
        self.text = text
        self.name = name
        self.input = input_


class _MockResponse:
    def __init__(self, content, stop_reason="end_turn"):
        self.content = content
        self.stop_reason = stop_reason


def _mock_response(system, user_message, tools, tool_choice):
    text_lower = user_message.lower()

    if tools and tools[0]["name"] == "extract_ticket_data":
        if "worst experience" in text_lower or "furious" in text_lower:
            # Ticket 7 mock: draft over-reacts to emotional intensity,
            # flags escalation despite no concrete signal — this is what
            # we're testing whether critique catches
            mock_input = {
                "customer_sentiment": "very_negative",
                "issue_category": "product_defect",
                "issue_category_detail": None,
                "urgency": "medium",
                "refund_requested": None,
                "requires_escalation": True,  # the false positive to catch
            }
        elif "dispute" in text_lower or "urgent" in text_lower:
            mock_input = {
                "customer_sentiment": "very_negative",
                "issue_category": "billing_error",
                "issue_category_detail": None,
                "urgency": "high",
                "refund_requested": None,
                "requires_escalation": True,  # real signal: dispute threat
            }
        elif "3 weeks" in text_lower:
            mock_input = {
                "customer_sentiment": "very_negative",
                "issue_category": "shipping_delay",
                "issue_category_detail": None,
                "urgency": "high",
                "refund_requested": True,
                "requires_escalation": True,  # real signal: repeated unresolved contact
            }
        else:
            mock_input = {
                "customer_sentiment": "neutral",
                "issue_category": "product_defect",
                "issue_category_detail": None,
                "urgency": "low",
                "refund_requested": None,
                "requires_escalation": False,
            }
        return _MockResponse(
            [_MockContentBlock("tool_use", name="extract_ticket_data", input_=mock_input)],
            stop_reason="tool_use",
        )

    if tools and tools[0]["name"] == "critique_escalation":
        if "worst experience" in text_lower or "furious" in text_lower:
            mock_input = {
                "concrete_signal_found": None,
                "final_verdict": False,
                "reasoning": "Strong emotional language (ALL CAPS, 'furious', 'worst experience') but no concrete signal — no dispute threat, no repeated contact, no safety issue, no request for a manager. The underlying issue is a small cosmetic dent. Downgrading."
            }
        else:
            mock_input = {
                "concrete_signal_found": "explicit dispute/chargeback threat or repeated unresolved contact",
                "final_verdict": True,
                "reasoning": "Confirmed — ticket contains an explicit concrete signal justifying escalation."
            }
        return _MockResponse(
            [_MockContentBlock("tool_use", name="critique_escalation", input_=mock_input)],
            stop_reason="tool_use",
        )

    return _MockResponse([_MockContentBlock("text", text="[mock] unhandled case")])
