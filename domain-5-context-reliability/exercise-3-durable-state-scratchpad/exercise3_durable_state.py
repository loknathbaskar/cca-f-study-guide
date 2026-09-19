"""
exercise3_durable_state.py — Domain 5, Concept 3: Durable state vs.
transient conversation — the scratchpad pattern.

THE CLAIM: "Reliable systems separate durable state from transient
conversation." In a long-running, multi-step task, decisions made early
on (business rules, exceptions, running counts) need to survive context
loss — compaction, session restart, or simply the conversation growing
too long to keep everything in view. If that state lives ONLY in
conversation history, losing access to early turns means losing the
decision itself, not just the wording of it.

THE SETUP: a simulated 6-step data migration task. Step 2 establishes a
RULE ("skip any record with a null email field") that must be applied
consistently for the rest of the task — this is exactly the kind of
early decision a long session risks losing track of.

TWO CONDITIONS, same underlying task:

  A) TRANSIENT ONLY — after "context loss" (simulated by truncating the
     conversation to only the most recent 2 steps), Claude is asked to
     resume and make a decision about a new record. It only has the
     TRUNCATED conversation — the turn establishing the null-email rule
     is gone.

  B) DURABLE SCRATCHPAD — the same rule was written to an actual
     scratchpad file on disk at the moment it was established. After the
     same simulated context loss, Claude is given ONLY the scratchpad
     file's content (not the truncated conversation) to resume from.

THE TEST: present a new record with a null email in both conditions, and
see whether the rule from Step 2 is still correctly applied.
"""

import os

if not os.environ.get("ANTHROPIC_API_KEY"):
    print("This exercise requires ANTHROPIC_API_KEY.")
    raise SystemExit(0)

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"

# The full 6-step task, as it originally happened — Step 2 establishes
# the critical rule. In condition A, only steps 5-6 survive "context
# loss." In condition B, nothing from this transcript survives at all —
# only the scratchpad file does.
FULL_STEPS = [
    ("Step 1", "Beginning data migration. 1,000 customer records to process. Starting with record batch 1-200."),
    ("Step 2", "Record #47 has a null email field. DECISION: any record with a null email field will be SKIPPED and logged separately, not migrated, since our new system requires a valid email as a primary key. This rule applies for the rest of this migration."),
    ("Step 3", "Batch 1-200 complete. 189 migrated, 11 skipped (null email). Starting batch 201-400."),
    ("Step 4", "Batch 201-400 complete. 384 migrated, 16 skipped (null email). Starting batch 401-600."),
    ("Step 5", "Batch 401-600 complete. 591 migrated so far total, 34 skipped so far total. Starting batch 601-800."),
    ("Step 6", "Batch 601-800 complete. 782 migrated so far total, 42 skipped so far total. Starting final batch 801-1000."),
]

NEW_RECORD_QUESTION = "Record #847 in the current batch has a null email field. What should be done with it, and why?"

SCRATCHPAD_PATH = "migration_scratchpad.md"


def condition_a_transient():
    print("=" * 70)
    print("CONDITION A: TRANSIENT ONLY — context loss truncates to last 2 steps")
    print("=" * 70)

    # Simulate context loss: only steps 5-6 "survive." Step 2 (the rule)
    # is gone — this is the realistic failure mode of naive truncation
    # or a compaction that doesn't specifically preserve early decisions.
    surviving_context = "\n".join(f"{label}: {text}" for label, text in FULL_STEPS[-2:])
    print(f"  Surviving context (steps 5-6 only):\n{surviving_context}\n")

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
    print("CONDITION B: DURABLE SCRATCHPAD — written to disk when established")
    print("=" * 70)

    # Simulate the scratchpad being written INCREMENTALLY as the task
    # progressed (this write would have happened back at Step 2, in a
    # real system) — by the time of "context loss," this file already
    # exists on disk, independent of conversation history entirely.
    with open(SCRATCHPAD_PATH, "w") as f:
        f.write("# Migration Scratchpad\n\n")
        f.write("## Rules established\n")
        f.write("- Any record with a null email field is SKIPPED and logged separately, "
                 "not migrated, since the new system requires a valid email as a primary key. "
                 "This rule applies for the entire migration.\n\n")
        f.write("## Progress\n")
        f.write("- 782 migrated so far total, 42 skipped so far total (through batch 601-800)\n")
        f.write("- Currently processing final batch 801-1000\n")

    with open(SCRATCHPAD_PATH) as f:
        scratchpad_content = f.read()
    print(f"  Scratchpad file content (the ONLY context provided):\n{scratchpad_content}\n")

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
    print("Did TRANSIENT lose the null-email skip rule (Step 2), while")
    print("DURABLE SCRATCHPAD correctly applied it, having preserved it")
    print("independent of conversation history entirely?")
    print("=" * 70)

    if os.path.exists(SCRATCHPAD_PATH):
        os.remove(SCRATCHPAD_PATH)
