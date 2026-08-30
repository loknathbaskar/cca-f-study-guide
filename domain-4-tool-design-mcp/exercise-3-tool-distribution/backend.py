import os

USE_REAL_API = bool(os.environ.get("ANTHROPIC_API_KEY"))

if USE_REAL_API:
    import anthropic
    _client = anthropic.Anthropic()


def call_claude(system: str, user_message: str, tools: list, max_tokens: int = 1024):
    if USE_REAL_API:
        return _client.messages.create(
            model="claude-sonnet-4-6", max_tokens=max_tokens,
            system=system, messages=[{"role": "user", "content": user_message}],
            tools=tools, tool_choice={"type": "auto"},
        )
    return _mock_response(user_message, tools)


class _MockContentBlock:
    def __init__(self, type_, text=None, name=None, input_=None):
        self.type = type_
        self.text = text
        self.name = name
        self.input = input_


class _MockResponse:
    def __init__(self, content):
        self.content = content


def _mock_response(user_message, tools):
    """Mock simulates the full 15-tool monolithic set having a real
    chance of misrouting on the ambiguous 'payment' queries specifically
    (since more similarly-named candidates exist to confuse), while the
    distributed 5-tool specialist set routes correctly since the
    ambiguous alternative isn't even present in that agent's tool list.
    This is a scripted simulation for a sanity check — verify against
    the real API, same as every prior exercise."""
    text_lower = user_message.lower()
    tool_names = [t["name"] for t in tools]
    is_router_call = "route_to_ecommerce" in tool_names
    is_monolithic = len(tools) > 6

    # ROUTER PHASE — must return one of the 3 route_to_X tools
    if is_router_call:
        if "paycheck" in text_lower or "deposit" in text_lower or "pto" in text_lower or "time off" in text_lower:
            return _MockResponse([_MockContentBlock("tool_use", name="route_to_hr", input_={})])
        if "password" in text_lower or "vpn" in text_lower or "laptop" in text_lower or "locked out" in text_lower or "account" in text_lower:
            return _MockResponse([_MockContentBlock("tool_use", name="route_to_it", input_={})])
        return _MockResponse([_MockContentBlock("tool_use", name="route_to_ecommerce", input_={})])

    # DOMAIN TOOL PHASE (either the 15-tool monolithic set, or a 5-tool
    # distributed specialist set)
    if "update my payment" in text_lower or "payment information" in text_lower:
        if is_monolithic and "update_direct_deposit" in tool_names:
            return _MockResponse([_MockContentBlock("tool_use", name="update_direct_deposit", input_={"employee_id": "unknown"})])
        elif "update_payment_method" in tool_names:
            return _MockResponse([_MockContentBlock("tool_use", name="update_payment_method", input_={"customer_id": "unknown"})])

    if "paycheck" in text_lower or "deposit" in text_lower:
        if "update_direct_deposit" in tool_names:
            return _MockResponse([_MockContentBlock("tool_use", name="update_direct_deposit", input_={"employee_id": "unknown"})])

    if "reset" in text_lower and "password" in text_lower and "reset_password" in tool_names:
        return _MockResponse([_MockContentBlock("tool_use", name="reset_password", input_={"user_id": "unknown"})])
    if "order" in text_lower and "status" in text_lower and "get_order_status" in tool_names:
        return _MockResponse([_MockContentBlock("tool_use", name="get_order_status", input_={"order_id": "unknown"})])
    if ("pto" in text_lower or "time off" in text_lower) and "request_pto" in tool_names:
        return _MockResponse([_MockContentBlock("tool_use", name="request_pto", input_={"employee_id": "unknown"})])
    if ("laptop" in text_lower or "stolen" in text_lower) and "report_device_lost" in tool_names:
        return _MockResponse([_MockContentBlock("tool_use", name="report_device_lost", input_={"user_id": "unknown", "device_type": "laptop"})])
    if ("locked out" in text_lower or "unlock" in text_lower) and "unlock_account" in tool_names:
        return _MockResponse([_MockContentBlock("tool_use", name="unlock_account", input_={"user_id": "unknown"})])

    # simulate monolithic-set confusion for anything not explicitly
    # handled above: pick a plausible-but-possibly-wrong tool from
    # whatever's available, to reflect a large tool set's higher chance
    # of a near-miss rather than a clean "no tool" outcome
    return _MockResponse([_MockContentBlock("tool_use", name=tool_names[0], input_={})])
