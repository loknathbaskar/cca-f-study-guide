# Domain 4, Exercise 6: Transport Mechanisms — stdio vs. StreamableHTTP

## What this demonstrates

The two MCP transports, with a concrete, measurable proof of the real
architectural difference — not just a description of it.

- **stdio**: the client spawns the server as a subprocess it owns. Every
  client gets its OWN fresh server process, with its own memory. Zero
  network config, but strictly local, and no state can ever be shared
  across clients.
- **StreamableHTTP**: a single HTTP endpoint (POST for client→server,
  GET/SSE for server→client) that ONE running server process serves to
  MULTIPLE clients over the network simultaneously, sharing state across
  all of them. This is the modern, recommended transport for any
  network-based/production deployment (the older SSE-only transport is
  deprecated in favor of it).

## The concrete proof, not just the claim

`http_order_server.py` keeps a simple in-memory call counter,
incremented on every tool call. Three separate client connections were
made — Client A, Client B, then Client A again (a brand new session each
time, not a reused connection):

```
[Client A]         call #1
[Client B]          call #2
[Client A (again)]  call #3
```

**The counter kept incrementing across all three, rather than resetting
to #1 each time.** That's direct proof all three connected to the SAME
persistent server process — something categorically impossible with
stdio, where each client spawning its own subprocess would reset any
in-memory counter back to zero every time.

## Try it yourself

Two separate terminal windows (this genuinely needs two independent,
persistent processes — see the sandbox limitation note below for why):

**Terminal 1:**
```bash
cd domain-4-tool-design-mcp/exercise-6-transports
python3 -m venv venv
./venv/bin/pip install "mcp==1.9.4"
./venv/bin/python3 http_order_server.py
```
Leave this running.

**Terminal 2:**
```bash
cd domain-4-tool-design-mcp/exercise-6-transports
./venv/bin/python3 http_client_demo.py
```

Watch the call counter in the output — same proof described above.

## A real environment limitation worth documenting, not a code bug

The first attempt to verify this in the sandbox used `nohup ... &` to
background the server in one command, then a separate tool call to run
the client — the server process died between the two calls, because
this particular sandboxed tool environment doesn't persist background
processes across separate invocations. The fix wasn't a code change —
it was running the server and client within a single combined command
(or, on a real machine, two persistent terminal windows, which is the
natural way this would actually be run). Worth knowing this distinction
if you ever hit a similar "it worked a second ago" surprise in a
notebook-like or otherwise ephemeral execution environment — the
server's lifetime needs to genuinely outlive the process spawning it,
which some sandboxed tool environments don't guarantee across separate
calls.

## Design principle worth defending in an exam-style answer

**Why is StreamableHTTP "the recommended choice for network-based
deployments" specifically, not just "the newer one"?** It's not newer
for its own sake — it enables things stdio structurally cannot: multiple
concurrent clients against one running server (this exercise's proof),
remote/cross-machine access (a server on a different machine than the
client), and standard HTTP infrastructure (load balancers, horizontal
scaling, auth) applying to it like any other web service.

**Why would you ever still choose stdio, given StreamableHTTP's
capabilities?** Zero network configuration and zero exposed attack
surface — the server only ever talks to the process that spawned it,
over a channel with no network listener at all. For a personal, local
tool (a host application talking to a server on the same machine, like
Claude Desktop's default local MCP server configuration), that's a
meaningful security and simplicity advantage StreamableHTTP doesn't
have — StreamableHTTP means a real network listener that needs its own
access control.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| First verification attempt: client failed with `ConnectError: All connection attempts failed`, even though the server had been confirmed running seconds earlier via `curl` | The sandboxed tool environment doesn't persist a backgrounded process (`nohup ... &`) across separate tool invocations — the server process was killed when the first command's shell session ended | Ran server startup and client execution within a single combined command, so the backgrounded server process stayed alive for the duration of the client's run |

## Next step
Exercise 7 — MCP security: access scoping, authentication, tool
annotation trust, and production hardening.

## Cross-environment confirmation — and a stronger proof than planned

Verified locally, with an even more convincing result than the original
design called for: the client script was run **twice**, as two entirely
separate process invocations (not just multiple clients within one
script run). The counter continued seamlessly: 1, 2, 3 on the first run,
then 4, 5, 6 on the second — proving the shared state genuinely lives on
the server process itself, completely decoupled from any client's
process lifecycle, not just shared across clients within a single
script's execution window. This is a cleaner, stronger demonstration of
the same underlying point.
