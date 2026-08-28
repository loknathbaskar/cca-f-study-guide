This is a nuanced result that complicates the simple story — worth documenting precisely rather than forcing it into "forced=bad, any=good."

Normal ticket — all three modes agreed, as expected (baseline confirmed)
Garbage ticket — FORCED was smarter than predicted, but not fully honest
A) AUTO: opted out, returned plain text explaining it's spam — correctly avoided the tool, but this breaks the structured-output guarantee (your pipeline now has to handle "sometimes I get text instead of JSON")
B) ANY: correctly routed to request_human_clarification with a clear reason — the clean, intended result
C) FORCED: did not blindly hallucinate a fake-but-plausible ticket the way the mock predicted. It used issue_category: "other" with an explicit, honest issue_category_detail: "NOT A GENUINE SUPPORT TICKET — Flagged for human review... Does not contain a legitimate customer issue." It even correctly set requires_escalation: True.

This is a genuinely interesting finding: FORCED tool_choice used the "other" + detail escape hatch we built in Step 3 as a workaround for not having a dedicated escape-valve tool. Good schema design in one step partially compensated for a limitation introduced in a later step — that's worth remembering as a real interaction between these concepts, not something either step's exercise called out in isolation.

But it wasn't perfectly honest: refund_requested came back False, not null — the same "unstated collapsed into a guessed value" pattern from Step 3's ticket 5. Even with the honest "other" disclosure, one field still asserted something the input never stated.

The architectural point that still favors ANY over FORCED, even given this result: FORCED still produces a database record representing something that isn't a real ticket at all — it just happens to contain an honest disclaimer inside that record. Downstream, anything counting tickets, aggregating by category, or computing sentiment metrics now has a phantom "other" entry to filter out. ANY's approach — no extraction record produced, a distinct clarification-request object instead — doesn't require that downstream cleanup at all. Honest hallucination is still hallucination; it's just labeled.

Edited a file, read a file
bash
cd ~/projects/cca-f-study-guide/domain-3-prompt-engineering/exercise-1-structured-extraction
# replace NOTES.md
git add NOTES.md
git commit -m "Domain 3 Step 4: document real result — FORCED used Step 3's escape hatch honestly, but still flawed on refund_requested"
git push

This is one of the better findings in the repo precisely because it resists a clean narrative — "FORCED tool_choice hallucinates on bad input" is the textbook warning, but what actually happened is more interesting: a well-designed schema partially defused that risk, while a different field still slipped. That's a genuinely useful, hard-won lesson: schema design decisions from one step can interact with tool_choice decisions made later, in ways worth testing explicitly rather than assuming independently.