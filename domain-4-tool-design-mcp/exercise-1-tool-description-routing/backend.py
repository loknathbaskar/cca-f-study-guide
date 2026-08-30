"""
backend.py — same real/mock abstraction pattern used throughout Domains 1
and 3, so exercises run whether or not ANTHROPIC_API_KEY is set.
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
    """
    Mock intentionally simulates realistic misrouting between the
    near-duplicate pair (search_orders / get_customer_orders) when
    descriptions are ambiguous, and correct routing once disambiguated —
    a simulation for a quick sanity check, NOT a stand-in for real
    evidence. Verify against the real API, same as every prior domain.
    """
    text_lower = user_message.lower()
    tool_names = [t["name"] for t in (tools or [])]
    has_pair = "search_orders" in tool_names and "get_customer_orders" in tool_names
    # detect ambiguous vs clear by checking description length/content
    is_ambiguous_set = has_pair and any(
        t["name"] == "search_orders" and t["description"] == "Search for orders."
        for t in tools
    )

    def pick(name, **input_kwargs):
        return _MockResponse(
            [_MockContentBlock("tool_use", name=name, input_=input_kwargs)],
            stop_reason="tool_use",
        )

    # Query 1: "Pull up orders for 12345" — should be get_customer_orders,
    # but query no longer contains strong scope language
    if "pull up orders for" in text_lower:
        if is_ambiguous_set:
            return pick("search_orders", status_filter=None, date_range=None)  # misrouted
        else:
            return pick("get_customer_orders", customer_id="12345")

    # Query 2: "I need to see orders with a delayed status" — should be
    # search_orders, query no longer says "across the store"
    if "delayed status" in text_lower:
        if is_ambiguous_set:
            return pick("get_customer_orders", customer_id="unknown")  # misrouted — no customer given at all!
        else:
            return pick("search_orders", status_filter="delayed", date_range=None)

    # Query 3: unambiguous single-order status lookup
    if "status of order" in text_lower:
        return pick("get_order_status", order_id="9981")

    # Query 4: unambiguous customer lookup
    if "look up the customer" in text_lower:
        return pick("search_customer", query="Maria Lopez")

    # Query 5: unambiguous update
    if "shipping address" in text_lower:
        return pick("update_order", order_id="4471", field="shipping_address", new_value="123 Main St")

    return pick("search_customer", query=user_message[:30])
