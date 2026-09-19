import os

USE_REAL_API = bool(os.environ.get("ANTHROPIC_API_KEY"))

if USE_REAL_API:
    import anthropic
    _client = anthropic.Anthropic()


def call_claude(system: str, user_message: str, tools: list = None,
                 tool_choice: dict = None, max_tokens: int = 1500):
    if USE_REAL_API:
        kwargs = dict(
            model="claude-sonnet-4-6", max_tokens=max_tokens,
            system=system, messages=[{"role": "user", "content": user_message}],
        )
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
        return _client.messages.create(**kwargs)
    raise RuntimeError("This exercise needs a real ANTHROPIC_API_KEY — "
                       "compaction quality is exactly what's being tested, "
                       "and a mock would just script the expected answer.")
