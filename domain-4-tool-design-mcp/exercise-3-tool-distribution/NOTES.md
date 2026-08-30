# Domain 4, Exercise 3: Tool Distribution — Monolithic vs. Distributed

## What this demonstrates

Direct follow-up to Exercise 1's finding: tool NAME was a remarkably
robust routing signal in a clean 2-tool comparison. This exercise asks
whether that robustness holds at **scale** — 15 tools across 3 unrelated
domains (e-commerce, HR, IT support), 5 per domain, with a deliberate
cross-domain near-collision: `update_payment_method` (e-commerce, a
customer's card) and `update_direct_deposit` (HR, an employee's bank
account for payroll) — both fundamentally "update where money goes,"
capable of colliding on a genuinely ambiguous query.

**Two approaches, same 6 test queries** (4 unambiguous, 2 deliberately
probing the cross-domain collision):
- **A) MONOLITHIC**: one agent, all 15 tools available in a single call
- **B) DISTRIBUTED**: a lightweight router first picks one of 3 domains
  (forced choice among 3 router-only tools), THEN only that domain's 5
  tools are available for the actual call — the colliding tool from the
  other domain is never even a candidate at the second stage

**Mock-mode result**: MONOLITHIC 4/6 (missed the payment-collision query
and one unrelated device-report query), DISTRIBUTED 5/6. (Standard
caveat: scripted simulation for a sanity check, not evidence — verify
against the real API below.)

## Try it yourself

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 exercise3_tool_distribution.py
```

Check specifically:
1. Does MONOLITHIC actually misroute either of the two payment/deposit
   collision queries, given 15 candidates to choose from instead of 2?
2. Does the router in DISTRIBUTED correctly classify domain for all 6
   queries — a router failure would sink the whole downstream call
   regardless of how good the domain-specific tools are?
3. If DISTRIBUTED scores higher, is the cost (2 API calls instead of 1
   per query) actually justified by the accuracy gain here, or is this a
   case where the extra architecture isn't earning its cost — worth a
   genuinely honest verdict, not an assumed one, especially given
   Exercise 1 found routing more robust than expected at a smaller scale.

## Design principle worth defending in an exam-style answer

**Why would scale change routing accuracy, if Exercise 1 found name
alone often robust?** Exercise 1 tested exactly 2 competing tools. As
tool count grows, so does the number of names the model must
discriminate between simultaneously — even if each individual name is
clear, more candidates increase the chance that *some* pair collides
semantically (here, "payment" and "deposit" both meaning "where money
goes"). Robustness demonstrated at n=2 doesn't automatically extrapolate
to n=15 — that's exactly why this needs its own test rather than
assuming Exercise 1's finding generalizes.

**Why does the router approach specifically fix the collision, if it
fixes anything?** Not because routing is inherently smarter — because it
**physically removes the colliding tool from consideration** at the
second stage. `update_direct_deposit` isn't a candidate at all when the
e-commerce specialist is invoked; there's nothing to collide with. This
is the same principle as Domain 1's context scoping — reducing what's in
front of the model at decision time, rather than trusting it to
correctly ignore irrelevant options from a larger set.

**What's the real cost, worth being honest about?** Two API calls per
request instead of one — added latency and cost on every single query,
including the 4 unambiguous ones that didn't need disambiguating help at
all. This is only worth it if the collision risk in your actual tool set
is real and consequential (e.g., an HR tool and a payments tool
attached to real money movement) — not a default architecture to reach
for out of caution alone.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| First mock version crashed on the distributed test (`KeyError`) | `_mock_response()` didn't recognize when it was being called for the router phase (with `ROUTER_TOOLS`) versus the domain-tool phase — it tried to look up a domain tool name in `DOMAIN_TOOLS` using whatever it guessed, which isn't a valid key | Added explicit router-phase detection (checking for `route_to_ecommerce` in the tool list) before falling through to domain-tool logic |
| **First real run: both approaches scored 1/6, with "NO TOOL" on nearly everything — including queries with only one plausible tool available** | Every tool's schema marks an ID field (`employee_id`, `user_id`, `customer_id`) as REQUIRED, but most test queries never supplied one. Claude very likely correctly withheld the tool call (it can't fill a required field it wasn't given) and asked a clarifying question in plain text instead — which the script was mislabeling as a routing failure, when it was actually reasonable behavior given genuinely incomplete queries. This confounded the entire test: it was measuring "does the model call a tool with missing required data" (it correctly doesn't), not "does the model pick the right tool." | Two-part fix: (1) script now prints the actual text response whenever no tool is called, so this can be confirmed directly rather than assumed; (2) every test query now includes a plausible ID, so schemas can actually be satisfied and the test isolates routing specifically |

**This is the same category of mistake as Exercise 1's first two attempts
and Domain 3 Step 5's Test 1**: a test can look like it's measuring one
thing while actually measuring something else, if a variable that should
have been held constant (here, parameter completeness) was accidentally
left uncontrolled. Worth treating any suspiciously uniform bad result
(1/6 across BOTH conditions, not just one) as a signal to check the test
mechanics before concluding anything about the actual concept.

## Real results — corrected hypothesis, and a clean final comparison

The diagnostic print revealed the actual cause was narrower than
guessed: it wasn't a missing ID (the ID was present in every query) — it
was the `dates` field on `request_pto` needing a concrete value, and
"next Friday" being a relative expression the model correctly declined
to silently resolve into a guessed specific date rather than
hallucinating one. Good behavior, just not the exact mechanism
hypothesized.

**With that isolated, both approaches scored identically: 5/6, missing
the exact same PTO query for the exact same date-ambiguity reason.**

**The headline finding**: the deliberate cross-domain collision this
exercise was built to test — `update_payment_method` vs.
`update_direct_deposit`, both semantically "update where money goes" —
was resolved **correctly by both approaches**. Distribution didn't fix
anything here, because there was nothing left to fix: the monolithic
15-tool agent already routed both collision queries correctly using
context (the query's own "customer"/"paycheck" framing plus tool name
clarity), matching Exercise 1's finding that name+context is a robust
signal, now confirmed to hold at 3x the tool count with a real
adversarial pair present.

**Cost/benefit, stated plainly**: DISTRIBUTED cost exactly double the API
calls (a router call plus a specialist call, per query) for an outcome
identical to MONOLITHIC's single call. In this specific test, that
architecture wasn't earning its cost — a finding worth taking as
seriously as a positive result would have been. This doesn't mean
distribution is never worth it (a genuinely larger or more collision-prone
tool set might behave differently), but it does mean the decision should
be based on demonstrated need in your actual tool set, not applied
preemptively as a default "safer" architecture.

## Next step
Exercise 4 — MCP architecture fundamentals (servers, clients, the three
primitives) and building a real MCP server.
