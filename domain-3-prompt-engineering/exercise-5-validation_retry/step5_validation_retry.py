"""
step5_validation_retry.py — Domain 3, Concept 5: Validation-retry loops.

THE CLAIM: validation-retry (send back the original request + the specific
validation error + ask for a corrected response) works well for FORMAT
errors — wrong type, invalid pattern, malformed JSON — because there's a
mechanical, checkable definition of "correct" to validate against and
report back.

It's largely INEFFECTIVE for semantic/judgment errors — like the urgency
miscalibration from Steps 1-2 — because there's no mechanical check for
"is this urgency rating correct." A validator would need to re-implement
the entire policy logic to know the model got it wrong, at which point
you don't need the model for that field at all. Retrying with a generic
"please reconsider" doesn't give the model any NEW information — it's
just re-asking an underspecified question a second time.

TEST 1 DESIGN — TWICE CORRECTED, worth understanding why:
  v1: asked for "#NNNN" with no padding rule at all -> model complied
      immediately, no violation ever occurred, retry never exercised.
  v2: put the zero-padding rule directly in the ORIGINAL system prompt
      -> model complied immediately AGAIN, because it already had the
      rule before attempt 1. This wasn't testing retry either — it was
      just re-confirming "explicit instructions work" a third time.
  v3 (this version): the ORIGINAL prompt does NOT mention zero-padding at
      all — it only asks for "the order_id in a clean format." The model
      will naturally produce "#4471" (matching how it appears in the
      ticket), which FAILS our validator's zero-padding requirement. Only
      on retry does the specific rule get introduced, for the first time,
      via the validation error message. THIS is what actually tests
      whether retry feedback can supply missing information the original
      prompt never provided — the real thing this concept is about.

TEST 2 (semantic error, retry should NOT reliably converge): the exact
VAGUE prompt + ticket 4 from Steps 1-2, which we already know produces a
policy-inconsistent urgency rating. The retry is deliberately generic —
"please reconsider" — with the actual policy withheld throughout,
mirroring Test 1's ORIGINAL prompt withholding the padding rule. The
difference: Test 1's retry MESSAGE reveals the missing rule; Test 2's
retry message deliberately does NOT (since revealing it would just be
Step 1's fix again). This is the real controlled comparison — both start
underspecified, only one gets the missing information supplied via retry.
"""

import json
import re
from backend import call_claude, USE_REAL_API

# ---------- Test 1: format error, retry should work ----------

FORMAT_TEST_TICKET = "My order 4471 hasn't arrived in 3 weeks."

# Deliberately does NOT mention zero-padding — this constraint only gets
# revealed via the retry's validation error message, not upfront.
FORMAT_SYSTEM = """Extract the order ID and a one-word urgency rating from
the ticket as JSON: {"order_id": "...", "urgency": "..."}."""


def validate_format(parsed: dict) -> str | None:
    """Returns an error message if invalid, None if valid.
    Requires zero-padding to 6 digits — a rule NEVER stated in
    FORMAT_SYSTEM, so satisfying it on attempt 1 would be coincidental,
    not something the model was told to do."""
    order_id = parsed.get("order_id", "")
    if not re.match(r"^#\d{6}$", order_id):
        return f'order_id "{order_id}" is invalid — it must be exactly "#" followed by 6 digits, zero-padded (e.g. "#004471"), not the number as it naturally appears in the ticket.'
    return None


def run_format_retry_test(max_retries=2):
    print("=" * 70)
    print("TEST 1: Format error — does validation-retry converge?")
    print("(Original prompt does NOT mention zero-padding — only the")
    print(" retry's error message reveals that rule, for the first time)")
    print("=" * 70)

    messages_context = FORMAT_TEST_TICKET
    for attempt in range(max_retries + 1):
        result = call_claude(FORMAT_SYSTEM, messages_context)
        text = "".join(b.text for b in result.content if b.type == "text")
        print(f"  Attempt {attempt + 1} raw output: {text.strip()}")

        try:
            clean = re.sub(r"```json|```", "", text).strip()
            parsed = json.loads(clean)
        except json.JSONDecodeError as e:
            print(f"    -> JSON parse failed: {e}")
            messages_context = f"{FORMAT_TEST_TICKET}\n\nYour previous response was not valid JSON: {text}\nError: {e}\nPlease resend as valid JSON."
            continue

        error = validate_format(parsed)
        if error is None:
            print(f"    -> VALID after {attempt + 1} attempt(s): {parsed}")
            if attempt == 0:
                print("    -> NOTE: valid on attempt 1 despite the rule never")
                print("       being stated — the model coincidentally chose a")
                print("       padded format unprompted. Worth re-running a few")
                print("       times; this may not reproduce every time.")
            return
        else:
            print(f"    -> Validation error: {error}")
            messages_context = f"{FORMAT_TEST_TICKET}\n\nYour previous response was: {json.dumps(parsed)}\nValidation error: {error}\nPlease resend corrected JSON."

    print(f"    -> FAILED to converge after {max_retries + 1} attempts")


# ---------- Test 2: semantic error, retry should NOT reliably converge ----------

VAGUE_SYSTEM = """You are a support ticket triager. Rate each ticket's
urgency. Be conservative about escalating things unnecessarily."""

TICKET_4 = "URGENT: I was charged twice for order #8821. Please fix this today or I'm disputing the charge with my bank."


def run_semantic_retry_test(max_retries=2):
    print()
    print("=" * 70)
    print("TEST 2: Semantic/judgment error — does a GENERIC retry converge")
    print("to the policy-correct answer (HIGH, per Steps 1-2's rules)?")
    print("(Original prompt is vague, same as Test 1 v3's original prompt")
    print(" lacks the padding rule — but UNLIKE Test 1, the retry message")
    print(" here deliberately does NOT supply the missing rule either.)")
    print("=" * 70)

    conversation = TICKET_4
    for attempt in range(max_retries + 1):
        result = call_claude(VAGUE_SYSTEM, conversation)
        text = "".join(b.text for b in result.content if b.type == "text")
        print(f"  Attempt {attempt + 1}: {text[:200]}")

        conversation = f"{TICKET_4}\n\nYour previous rating was: {text[:200]}\nPlease reconsider whether this rating is appropriate and provide your final answer."

    print("    -> Compare final attempt to the EXPLICIT-prompt answer from")
    print("       Steps 1-2 (HIGH). Did generic re-asking get there on its own?")


if __name__ == "__main__":
    print(f"Running in {'REAL API' if USE_REAL_API else 'MOCK'} mode\n")
    run_format_retry_test()
    run_semantic_retry_test()