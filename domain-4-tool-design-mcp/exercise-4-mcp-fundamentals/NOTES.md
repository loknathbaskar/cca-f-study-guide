# Domain 4, Exercise 4: MCP Architecture Fundamentals — A Real Server and Client

## What this demonstrates

An actual, working MCP server (`order_server.py`) and a real MCP client
(`mcp_client_demo.py`) communicating over real stdio transport — not a
mock, not a simulation. This is the first Domain 4 exercise to build
against genuine MCP infrastructure rather than hand-rolled `tool_use`
schemas.

**The server exposes all three MCP primitives:**
- **Tool** — `get_order_status(order_id)`: an explicit action/query the
  client decides to invoke, takes parameters, returns a result
- **Resource** — `orders://all`: read-only, URI-addressable data the
  client can fetch directly, without "calling" anything the way a tool
  is called
- **Prompt** — `order_summary_prompt(order_id)`: a reusable, parameterized
  message template, meant to be surfaced by the HOST application (e.g.
  as a slash command), not invoked mid-conversation by the model itself
  the way a tool is

**The client** spawns the server as a subprocess, speaks MCP over stdio,
lists everything available (discovery), then invokes each primitive once
(tool call, resource read, prompt fetch) so the actual request/response
shape for each is visible directly, not just described.

## Rule of thumb for Tool vs. Resource vs. Prompt

- Has side effects, or is explicitly invoked for an action → **Tool**
- Read-only data pulled in as context → **Resource**
- A reusable, parameterized message template surfaced by the host,
  not invoked by the model mid-reasoning → **Prompt**

## Try it yourself

```bash
cd domain-4-tool-design-mcp/exercise-4-mcp-fundamentals
python3 -m venv venv
./venv/bin/pip install "mcp==1.9.4"
./venv/bin/python3 mcp_client_demo.py
```

You should see discovery output listing 1 tool, 1 resource, 1 prompt,
followed by the actual invocation of each — including the tool's text
result, the resource's raw content, and the prompt's generated message.

## Real bugs hit while building this — both genuinely instructive

### Bug 1: `mcp` 2.x renamed `FastMCP` to `MCPServer`

Installing the latest `mcp` package (`pip install mcp`) pulled version
2.1.1, where `from mcp.server.fastmcp import FastMCP` no longer exists —
it was renamed to `MCPServer` in a breaking v2 release, with an explicit
migration guide. Nearly every current tutorial and piece of documentation
(as of this writing) still references the `FastMCP` decorator API,
meaning following widely-available guides verbatim would break
immediately on a fresh install.

**Fix**: pinned to `mcp==1.9.4`, the last version using the `FastMCP`
class name. **Exam-relevant lesson**: MCP tooling is moving fast enough
that pinning a specific SDK version and verifying imports before relying
on tutorial code is not optional caution — it's necessary. This mirrors
Domain 2's Claude Code hooks findings: "moves fast" isn't a throwaway
disclaimer, it's a real, recurring category of gotcha across this entire
study guide.

### Bug 2: subprocess spawned the WRONG Python interpreter

Even after fixing Bug 1 inside a clean virtual environment, the client
still failed — because `StdioServerParameters(command="python3", ...)`
used a bare command name, which resolves via `PATH` and picked up the
**system** Python (with the broken `mcp` 2.1.1 install) instead of the
venv's Python actually running the client script.

**Fix**: use `sys.executable` instead of a bare `"python3"` string —
this guarantees the spawned server subprocess uses the exact same
interpreter (and therefore the same installed packages) as the client
process spawning it.

**Why this is a genuinely important, generalizable lesson, not just an
environment quirk**: any time a program spawns a subprocess by a bare
command name rather than an explicit path/interpreter reference, it's
implicitly trusting `PATH` resolution to pick the "right" version of
something — which silently breaks the moment more than one version
exists on a machine (exactly the situation any real developer's machine
tends to be in, with multiple Python installs, venvs, and system
packages coexisting). This is the MCP-specific instance of a very
common, very real class of bug.

## Design principle worth defending in an exam-style answer

**Why does MCP separate Resources from Tools at all, instead of just
making everything a tool the model decides to call?** A Resource is
meant to be something the HOST can proactively include as context
without requiring the model to decide, mid-conversation, "should I call
a tool to fetch this." For data that's cheap, safe, and likely relevant
regardless of the specific question (like a snapshot of all current
orders), pulling it in as a Resource avoids depending on the model
correctly deciding to fetch it via tool call in every scenario where it
would help.

**Why does a Prompt exist as a separate primitive from a Tool that
returns a string?** A Prompt is meant to be discoverable and
invocable by the HOST UI directly (e.g. as a slash command a human
picks), independent of the model's own reasoning loop — it's a
host-level affordance, not something the model decides to reach for
autonomously the way it decides to call a tool.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'mcp.server.fastmcp'` | `pip install mcp` installed 2.1.1, where FastMCP was renamed to MCPServer | Pinned `mcp==1.9.4` |
| `AttributeError: Meta` / `Connection closed` even after pinning the client's venv correctly | Server subprocess spawned via bare `"python3"`, which resolved to the system Python's broken `mcp` 2.1.1 install rather than the venv's correct 1.9.4 | Used `sys.executable` instead of a bare command string, guaranteeing the same interpreter/environment for both client and spawned server |

## Next step
Exercise 5 — MCP clients: discovery, invocation, and multi-server
routing (extending this same server/client pair to a multi-server
scenario).

## Cross-environment confirmation

Verified working identically on two separate environments: the sandbox
(Python 3.12) and a local MacBook (Python 3.13) — same output, same
successful discovery and invocation of all three primitives on both.
This confirms the two fixes (pinning `mcp==1.9.4`, using `sys.executable`
instead of a bare `"python3"`) are genuinely portable fixes, not
sandbox-specific workarounds.
