# Domain 4, Exercise 1: Tool Descriptions as Routing Mechanisms

## What this demonstrates

Claude selects which tool to call based ONLY on each tool's name,
description, and schema — never the implementation. This makes tool
descriptions **the actual routing logic**, not documentation. Ambiguous
or overlapping descriptions between near-duplicate tools cause
misrouting — this is the real-tool version of Domain 1's
`search_agent`/`analyze_agent` mock-router bug, except this time it's
Claude's own tool selection being tested directly, with 5 real tools in
one API call.

**The setup**: 5 customer-service tools, including a deliberate
near-duplicate pair:
- `search_orders` — meant for system-wide order search
- `get_customer_orders` — meant for one specific customer's orders

Same 5 tools, same schemas, tested twice — once with vague, overlapping
descriptions for the pair ("Search for orders." / "Get orders for a
customer."), once with descriptions that explicitly state scope and
cross-reference each other ("...NOT scoped to a single customer... use
get_customer_orders instead if...").

**Mock-mode result**: AMBIGUOUS scored 3/5, missing exactly the two
queries that probe the near-duplicate pair. CLEAR scored 5/5. (Standard
caveat: this is a scripted simulation to sanity-check the exercise
mechanics — verify the real pattern holds against the actual API below.)

## Try it yourself

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 exercise1_tool_description_routing.py
```

Check specifically:
1. Does the AMBIGUOUS set actually misroute queries 1 and 2 (the pair
   probes), or does Claude disambiguate correctly from context even with
   weak descriptions?
2. Does the CLEAR set score higher, and specifically fix exactly those
   two queries — or does clarifying descriptions introduce some new,
   unexpected confusion elsewhere?
3. Do the 3 unambiguous queries (order status, customer lookup, update)
   stay correct in both conditions? If they don't, that's a different,
   more concerning finding — it would mean the tool set has broader
   problems beyond just the deliberate near-duplicate pair.

## Design principle worth defending in an exam-style answer

**Why is "add more tools" often worse than "write better descriptions of
fewer tools"?** Every tool added increases the chance of description
overlap with an existing tool. `search_orders` and `get_customer_orders`
solving genuinely different problems is fine — the bug isn't that they
exist, it's that nothing in their original descriptions told Claude how
to tell them apart. The fix cost nothing architecturally (same tools,
same schemas) — it was purely a documentation-quality fix, which is
exactly why is it easy to overlook in a real system: the code all
"works," the tools are all individually well-implemented, and the whole
system still routes incorrectly.

**Why cross-reference the other tool by name in each description
("use X instead if...")?** This directly tells Claude the boundary
between the two tools, rather than hoping two independently-good
descriptions happen to imply a clear boundary between each other. This
is the tool-description equivalent of Step 1's "explicit default for the
no-signal case" — don't leave the disambiguation implicit.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| First mock version scored the same (2/5) on both AMBIGUOUS and CLEAR conditions, showing no contrast at all | `_mock_response()`'s matching logic was too crude — it didn't actually match the specific test queries used in this script, so it fell through to generic defaults regardless of which description set was active | Rewrote the mock to match each of the 5 specific test queries explicitly, and to check the actual description text to decide ambiguous vs. clear behavior |
| **First real run: both AMBIGUOUS and CLEAR scored 5/5 — no contrast at all, meaning the test never actually isolated what it claimed to test** | Test queries 1 and 2 contained strong scope-disambiguating language of their own ("placed by customer #12345", "across the store") — the model could route correctly from the QUERY's wording alone, without needing the tool descriptions to do any disambiguating work. The test accidentally measured "can the model route correctly given an unambiguous query," not "do ambiguous tool descriptions cause misrouting." | Rewrote queries 1 and 2 to be genuinely neutral about scope ("Pull up orders for 12345", "I need to see orders with a delayed status") — removing the language that let query wording substitute for tool-description quality, so descriptions actually have to carry the routing decision |

**This mirrors Domain 3 Step 5's Test 1 exactly**: a test can look like it's
measuring one thing (tool description quality) while actually measuring
something else entirely (query clarity) if the query itself contains the
disambiguating information the test was supposed to isolate. Worth
treating any "both conditions scored the same" result as a signal to
check the test design before concluding the manipulation had no effect.

| **Second real run: STILL 5/5 on both conditions, even with neutral queries** | The schemas themselves were leaking the disambiguating signal, independent of description text: `get_customer_orders` required a field literally named `customer_id`, while `search_orders` required `status_filter`/`date_range`. Even with a terse description, the model could infer each tool's purpose from its parameter names alone — the test still had an uncontrolled variable (informative schema field names) that was doing the actual disambiguating work the description was supposed to be tested on. | Made schema field names equally generic in the AMBIGUOUS condition (`param1`, `param2` instead of `customer_id`, `status_filter`) — description text is now genuinely the only variable differing between conditions |

**This is a real, valuable finding, not a persistent test failure**:
Claude's tool routing draws on tool name + description + schema field
names collectively — a bad description alone may not cause misrouting if
the schema's own field names still carry clear intent. Two consecutive
null results, each traced to a different uncontrolled variable (query
wording, then schema field names), is stronger evidence for this
robustness than a single clean result would have been. It also means
real-world tool sets with reasonably named parameters may be more
resistant to bad descriptions than the exam's "descriptions matter"
framing might suggest in isolation — the practical risk is likely
highest when BOTH description AND parameter names are uninformative
together, not either alone.

## Third attempt: MISLEADING descriptions (swapped, not just vague)

With names and schemas both fully informative, descriptions were
deliberately swapped so each tool's description used language that
actually belongs to the OTHER tool (`search_orders` described as
"retrieve a specific customer's order records"; `get_customer_orders`
described as "search across the entire database"). This mirrors Domain
1's real keyword-collision bug more closely than mere vagueness did.

**Real result: still 5/5, both tools routed correctly despite actively
misleading description text.**

## Final conclusion, after four consecutive real-data attempts

Real Claude Sonnet 4.6's tool routing is **remarkably robust to
description-text manipulation alone** — vague, neutral, or actively
misleading — as long as the tool **name** itself stays semantically
informative. Across four rounds, each of which controlled for a
different confound (query wording, schema field names, then description
content itself), routing never broke. The only untested variable is the
tool name — and obscuring that too would mean testing something outside
real practice, since production tools are essentially never given
meaningless names.

**This forces an important, honest correction to Domain 1's original
finding.** The `search_agent`/`analyze_agent` misrouting bug documented
in Domain 1 occurred in a **hand-written mock router using naive Python
substring-matching on system prompt text** — it was never a
demonstration of real Claude's actual tool-selection behavior. Four
attempts to reproduce a comparable failure against the real model, using
real `tool_use`, could not do so without also degrading the tool name
itself. **A lesson about a simplistic custom router's fragility is not
the same claim as a lesson about Claude's real routing robustness** —
conflating the two would be a genuine mistake, and this exercise exists
specifically to catch that distinction before the exam does.

**What this means practically, and what's still worth taking seriously**:
this doesn't mean tool descriptions don't matter — it means the
practical failure mode is likely narrower than "any vague description is
dangerous." The real risk concentrates where: (a) tool **names**
themselves are also similar/generic (not tested here — genuinely worth
avoiding in practice regardless), (b) more tools are competing for the
same intent than the 2-way case tested here (routing among 5-10
similarly-scoped tools may behave differently than a clean pair), or
(c) the query itself is also genuinely ambiguous, removing the
compensating signal query context otherwise provides. None of those
were fully tested here — worth flagging as follow-up territory rather
than claiming this exercise closed the topic completely.

## Next step
Exercise 2 — structured error responses + idempotency/partial success
handling.
