# Domain 4, Exercise 5: MCP Clients — Discovery, Invocation, and Multi-Server Routing

## What this demonstrates

Extends Exercise 4's working server/client pair to a real multi-server
scenario — exactly what a host application (Claude Desktop, Claude Code
with multiple `.mcp.json` entries) does when more than one MCP server is
configured. Two independent servers:

- `order_server.py` (from Exercise 4, now with an added `get_status` tool)
- `hr_server.py` (new) — also exposes a tool literally named
  `get_status`, scoped to employee PTO instead of orders

**This is a deliberate, realistic collision**: two independently-developed
servers, neither aware of the other, happening to choose the same
generic tool name. This is a genuine, common real-world MCP integration
problem, not a contrived edge case.

## The two-step real demonstration

**Step 1 — the collision happening**: a naive registry that aggregates
tools from both servers keyed only by tool name. The `hr` server's
`get_status` silently overwrites the `orders` server's `get_status` in
this registry — with no error, no warning, nothing crashing. The
`orders` server's `get_status` becomes completely unreachable through
this registry, and nothing about the program's behavior would tell you
that happened unless you specifically checked for it.

**Real output, confirmed on first run:**
```
!! COLLISION: 'get_status' from 'hr' silently OVERWRITES the existing entry from 'orders'
Naive registry ended up with: ['get_order_status', 'get_status', 'get_pto_balance']
```

**Step 2 — the standard fix**: namespace every tool with its server's
key (`orders__get_status`, `hr__get_status`). Both tools become
independently reachable, and invoking both through the namespaced
registry correctly calls each server's own version:
```
orders__get_status(order_id=4471) -> [ORDER STATUS] 4471: delayed
hr__get_status(employee_id=EMP-1001) -> [HR STATUS] EMP-1001: pending approval
```

## Try it yourself

```bash
cd domain-4-tool-design-mcp/exercise-5-mcp-clients-multiserver
python3 -m venv venv
./venv/bin/pip install "mcp==1.9.4"
./venv/bin/python3 multi_server_client.py
```

This ran successfully on the first attempt in this exercise's
development — worth verifying it also works cleanly on your machine, but
there's no known outstanding gotcha to hunt for here, unlike several
earlier exercises.

## Design principle worth defending in an exam-style answer

**Why does this collision risk grow specifically with multi-server
setups, when Domain 4 Exercise 1 found tool NAME to be a robust routing
signal?** Exercise 1's finding was about semantic disambiguation WITHIN
one flat tool list — Claude correctly picking among differently-purposed
tools based on their names. This exercise is a different problem
entirely: two tools with the IDENTICAL name, at the aggregation/registry
level, before the model ever gets to reason about anything. No amount of
routing intelligence fixes a registry that already dropped one of the
two tools before the model saw the list at all. This is an
infrastructure-level problem, not a reasoning-level one — hence a
structural fix (namespacing), not a prompting fix.

**Why prefix with the SERVER key specifically, rather than some other
disambiguator?** The server is the natural unit of "who owns this tool"
— namespacing by server both resolves the collision AND preserves useful
information for the calling model (or a human debugging the aggregated
tool list): which underlying system will actually execute this call. A
random or arbitrary disambiguator (e.g., appending `_2`) would resolve
the technical collision but destroy that provenance information.

**What would happen in production if you DIDN'T fix this?** Exactly what
Step 1 showed: not a crash, not an error message, not a warning in logs
by default — a silent, hard-to-diagnose bug where one entire tool from
one server becomes permanently unreachable, discovered only when someone
notices a feature "isn't working" and traces it back to a naming
collision that could have existed for a long time before being caught.
This is precisely the kind of bug that's cheap to prevent upfront
(namespace everything by default) and expensive to diagnose after the
fact.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| None — worked correctly on the first run, reusing the `sys.executable` fix and `mcp==1.9.4` pin already established in Exercise 4 | — | — |

## Next step
Exercise 6 — transport mechanisms: stdio vs. StreamableHTTP.

## Cross-environment confirmation

Verified working identically on two separate environments: the sandbox
(Python 3.12) and a local MacBook (Python 3.13) — same collision
detected, same namespaced fix, same correct invocation of both servers'
`get_status` tools on both machines.
