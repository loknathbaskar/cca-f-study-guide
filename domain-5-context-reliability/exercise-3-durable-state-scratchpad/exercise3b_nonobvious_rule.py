"""
exercise3b_nonobvious_rule.py — Follow-up to Exercise 3: same durable vs.
transient test, but with a deliberately NON-OBVIOUS, arbitrary business
rule that generic inference has no way to reconstruct. The original
test's rule (skip null email) overlapped with an intuitive default
("null in a key field -> skip it"), letting TRANSIENT succeed via lucky
inference rather than real recall. This version removes that overlap.

THE NEW RULE (established at Step 2, same as before): "Any record with a
null email field is normally skipped — EXCEPT if the customer's loyalty
tier is 'VIP', in which case it should be migrated anyway using a
placeholder email in the format vip-{customer_id}@pending-migration.internal,
because VIP accounts cannot be dropped from the new system regardless of
data completeness."

This is specifically NOT something a generic "null fields get skipped"
heuristic could produce — the VIP exception is an arbitrary business
decision with no intuitive default. If TRANSIENT still gets this right
without the rule in context, that's a much stronger case for lucky
pattern-matching being more capable than expected. If TRANSIENT fails
this one (unlike the original null-email test), that confirms the
original test's success was specifically due to rule/inference overlap,
not general robustness.
"""

import os

if not os.environ.get("ANTHROPIC_API_KEY"):
    print("This exercise requires ANTHROPIC_API_KEY.")
    raise SystemExit(0)

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"

FULL_STEPS = [
    ("Step 1", "Beginning data migration. 1,000 customer records to process. Starting with record batch 1-200."),
    ("Step 2", "Record #47 has a null email field. DECISION: any record with a null email field is normally SKIPPED and logged separately, since our new system requires a valid email as a primary key. EXCEPTION: if the customer's loyalty tier is 'VIP', migrate the record anyway using a placeholder email in the format vip-{customer_id}@pending-migration.internal, because VIP accounts cannot be dropped from the new system regardless of data completeness. This rule (including the VIP exception) applies for the rest of this migration."),
    ("Step 3", "Batch 1-200 complete. 187 migrated, 2 migrated via VIP exception, 11 skipped (null email, non-VIP). Starting batch 201-400."),
    ("Step 4", "Batch 201-400 complete. 380 migrated, 4 migrated via VIP exception, 16 skipped. Starting batch 401-600."),
    ("Step 5", "Batch 401-600 complete. 585 migrated so far total (6 via VIP exception), 34 skipped so far total. Starting batch 601-800."),
    ("Step 6", "Batch 601-800 complete. 774 migrated so far total (8 via VIP exception), 42 skipped so far total. Starting final batch 801-1000."),
]

NEW_RECORD_QUESTION = ("Record #847 in the current batch has a null email field. "
                       "This customer's loyalty tier is VIP, customer_id is CUST-9931. "
                       "What should be done with it, and why?")

SCRATCHPAD_PATH = "migration_scratchpad_v2.md"


def condition_a_transient():
    print("=" * 70)
    print("CONDITION A: TRANSIENT ONLY — context loss truncates to last 2 steps")
    print("(the VIP exception rule from Step 2 is gone)")
    print("=" * 70)
    surviving_context = "\n".join(f"{label}: {text}" for label, text in FULL_STEPS[-2:])
    print(f"  Surviving context:\n{surviving_context}\n")

    response = client.messages.create(
        model=MODEL, max_tokens=300,
        system="You are assisting with a data migration task. Continue based on the context provided.",
        messages=[{
            "role": "user",
            "content": f"Migration progress so far:\n{surviving_context}\n\n{NEW_RECORD_QUESTION}"
        }],
    )
    answer = "".join(b.text for b in response.content if b.type == "text")
    print(f"  ANSWER: {answer}\n")
    return answer


def condition_b_durable_scratchpad():
    print("=" * 70)
    print("CONDITION B: DURABLE SCRATCHPAD — VIP exception preserved on disk")
    print("=" * 70)

    with open(SCRATCHPAD_PATH, "w") as f:
        f.write("# Migration Scratchpad v2\n\n")
        f.write("## Rules established\n")
        f.write("- Default: any record with a null email field is SKIPPED and logged "
                 "separately, since the new system requires a valid email as a primary key.\n")
        f.write("- EXCEPTION: if the customer's loyalty tier is 'VIP', migrate the record "
                 "anyway using a placeholder email in the format "
                 "vip-{customer_id}@pending-migration.internal, because VIP accounts cannot "
                 "be dropped from the new system regardless of data completeness.\n\n")
        f.write("## Progress\n")
        f.write("- 774 migrated so far total (8 via VIP exception), 42 skipped so far total\n")
        f.write("- Currently processing final batch 801-1000\n")

    with open(SCRATCHPAD_PATH) as f:
        scratchpad_content = f.read()
    print(f"  Scratchpad file content:\n{scratchpad_content}\n")

    response = client.messages.create(
        model=MODEL, max_tokens=300,
        system="You are assisting with a data migration task. Continue based on the scratchpad file content provided.",
        messages=[{
            "role": "user",
            "content": f"Scratchpad file contents:\n{scratchpad_content}\n\n{NEW_RECORD_QUESTION}"
        }],
    )
    answer = "".join(b.text for b in response.content if b.type == "text")
    print(f"  ANSWER: {answer}\n")
    return answer


if __name__ == "__main__":
    answer_a = condition_a_transient()
    answer_b = condition_b_durable_scratchpad()

    print("=" * 70)
    print("Did TRANSIENT fail to apply the VIP exception (since generic")
    print("inference has no way to reconstruct an arbitrary business rule),")
    print("while DURABLE SCRATCHPAD correctly migrated with the placeholder")
    print("email format?")
    print("=" * 70)

    if os.path.exists(SCRATCHPAD_PATH):
        os.remove(SCRATCHPAD_PATH)
