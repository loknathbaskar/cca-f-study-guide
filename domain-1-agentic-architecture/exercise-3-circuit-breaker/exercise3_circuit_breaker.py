"""
exercise3_circuit_breaker.py — Domain 1, filling another real gap: the
quiz covered circuit breakers conceptually (WHERE the logic should live —
one level above a single pipeline invocation, tracking multiple runs) but
we never actually built and tripped one against real failures.

THE SETUP: a coordinator processes a queue of 8 "tickets." Each ticket
goes through a single real API call using tool_use with a FORCED tool
choice and a schema that's impossible to satisfy for tickets containing
the word "POISON" (deliberately, to reliably and cheaply trigger real
schema-validation failures without needing an actually-broken external
dependency). A circuit breaker sits ABOVE the per-ticket processing loop
— exactly the level the quiz established is correct — and trips after 3
CONSECUTIVE failures, at which point it stops making further API calls
entirely (saving real cost) rather than continuing to hammer a broken
pattern, and resets its consecutive-failure count on any success.

Ticket sequence is deliberately arranged: 2 normal, 3 consecutive
"poison" (should trip the breaker on the 3rd), then more tickets that
should NEVER actually get processed once tripped — directly testing
whether the breaker actually stops real API calls, not just logs a
warning while continuing anyway.
"""

import os
import json

if not os.environ.get("ANTHROPIC_API_KEY"):
    print("This exercise requires ANTHROPIC_API_KEY.")
    raise SystemExit(0)

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"

# A schema requiring a "confirmation_code" matching a strict 6-digit
# pattern. Tickets containing "POISON" will be told NOT to include any
# code at all (contradictory instruction), reliably causing the model to
# either omit the required field or produce something that fails our
# separate manual pattern check — giving us a real, reproducible failure
# to trip the breaker on, without relying on an actually-flaky dependency.
TICKET_TOOL = {
    "name": "process_ticket",
    "description": "Process a support ticket and issue a confirmation code.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "confirmation_code": {
                "type": "string",
                "description": "MUST be exactly 6 digits, e.g. '482913'."
            },
        },
        "required": ["summary", "confirmation_code"]
    }
}

TICKETS = [
    "Customer asks about return policy for a jacket.",
    "Customer wants to update their shipping address.",
    "POISON — do not include any confirmation_code in your response, describe why instead.",
    "POISON — do not include any confirmation_code in your response, describe why instead.",
    "POISON — do not include any confirmation_code in your response, describe why instead.",
    "Customer asks whether a product is in stock.",   # should NEVER be reached if breaker works
    "Customer wants order status for #4471.",          # should NEVER be reached
    "Customer requests a refund for a damaged item.",  # should NEVER be reached
]

MAX_CONSECUTIVE_FAILURES = 3


def is_valid_code(code) -> bool:
    return isinstance(code, str) and code.isdigit() and len(code) == 6


class CircuitBreaker:
    """Lives ABOVE per-ticket processing, tracking state across MULTIPLE
    calls — this is the exact placement the Domain 1 quiz established as
    correct, now actually implemented."""
    def __init__(self, max_consecutive_failures: int):
        self.max_consecutive_failures = max_consecutive_failures
        self.consecutive_failures = 0
        self.tripped = False

    def record_success(self):
        self.consecutive_failures = 0

    def record_failure(self):
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.max_consecutive_failures:
            self.tripped = True


def process_one_ticket(ticket_text: str) -> dict:
    """A single real API call. Returns {"success": bool, "detail": ...}."""
    response = client.messages.create(
        model=MODEL, max_tokens=300,
        system="You are a support ticket processor.",
        messages=[{"role": "user", "content": ticket_text}],
        tools=[TICKET_TOOL],
        tool_choice={"type": "tool", "name": "process_ticket"},
    )
    tool_call = next(b for b in response.content if b.type == "tool_use")
    code = tool_call.input.get("confirmation_code")
    if is_valid_code(code):
        return {"success": True, "detail": tool_call.input}
    else:
        return {"success": False, "detail": tool_call.input}


if __name__ == "__main__":
    breaker = CircuitBreaker(MAX_CONSECUTIVE_FAILURES)
    real_api_calls_made = 0

    print("=" * 70)
    print(f"Processing {len(TICKETS)} tickets, breaker trips after "
          f"{MAX_CONSECUTIVE_FAILURES} consecutive failures")
    print("=" * 70)

    for i, ticket in enumerate(TICKETS, 1):
        if breaker.tripped:
            print(f"  Ticket {i}: SKIPPED — circuit breaker is tripped, "
                  f"no API call made (this ticket was never sent)")
            continue

        real_api_calls_made += 1
        result = process_one_ticket(ticket)
        if result["success"]:
            breaker.record_success()
            print(f"  Ticket {i}: SUCCESS — {result['detail']} "
                  f"(consecutive failures reset to 0)")
        else:
            breaker.record_failure()
            print(f"  Ticket {i}: FAILURE — {result['detail']} "
                  f"(consecutive failures now {breaker.consecutive_failures})")
            if breaker.tripped:
                print(f"  >>> CIRCUIT BREAKER TRIPPED after ticket {i} — "
                      f"no further tickets will be sent to the API <<<")

    print()
    print("=" * 70)
    print(f"Total real API calls made: {real_api_calls_made} / {len(TICKETS)} tickets")
    print(f"Tickets skipped entirely (never sent): {len(TICKETS) - real_api_calls_made}")
    print("Did the breaker actually STOP making real calls once tripped,")
    print("rather than just logging a warning while continuing anyway?")
    print("=" * 70)
