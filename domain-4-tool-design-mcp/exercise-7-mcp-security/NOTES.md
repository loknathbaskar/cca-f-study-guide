# Domain 4, Exercise 7: MCP Security — Annotation Trust and Access Scoping

## What this demonstrates

Two separate, concrete security tests — both actually exploited, then
actually fixed, not just described.

## Test A: Tool annotations are advisory, not verified

`annotation_trust_server.py` declares `check_order_status` with
`readOnlyHint=True` (the standard MCP annotation meaning "this tool does
not modify its environment") — but the actual implementation ALSO
deletes the order as an undisclosed side effect.

**This directly mirrors Domain 2's `allowed-tools` finding**: metadata a
component says about ITSELF is not something a security-conscious caller
should trust unconditionally. `readOnlyHint` is server-supplied; a
malicious or simply buggy server can declare whatever it wants about its
own tools.

**Real result, confirmed:**
- **NAIVE HOST** (trusts the annotation, skips confirmation/logging for
  "read-only" tools): called the tool, then a follow-up check showed
  *"No orders remain"* — the order was silently deleted despite the
  read-only claim, and the naive host had no way to notice.
- **HARDENED HOST** (never trusts the annotation; snapshots actual state
  before and after every call, regardless of what the tool claims):
  detected the mismatch directly — *"State BEFORE call: 4471"* vs.
  *"State AFTER call: No orders remain"* — and flagged the tool for not
  being trustworthy going forward.

## Test B: Access scoping — a real path traversal exploit

`access_scoping_server.py` has two versions of the same tool: one
(`read_file_naive`) using naive `os.path.join()` with no containment
check, one (`read_file_hardened`) that resolves the real final path and
verifies it's still inside the sandbox directory before opening anything.

**Real result, confirmed — an actual live exploit, not a description of
one:**
```
read_file_naive('../secret.txt')    -> TOP SECRET: admin password is hunter2
read_file_hardened('../secret.txt') -> BLOCKED: '../secret.txt' resolves outside the sandboxed directory.
```

`os.path.join()` does NOT sanitize `..` path components — it happily
concatenates them, and the resulting path resolves outside the intended
directory. `os.path.realpath()` followed by an explicit "is this still
under the sandbox root" check is what actually enforces containment.

## Try it yourself

```bash
cd domain-4-tool-design-mcp/exercise-7-mcp-security
python3 -m venv venv
./venv/bin/pip install "mcp==1.9.4"
mkdir -p sandbox
echo "innocent sandboxed content" > sandbox/order-notes.txt
echo "TOP SECRET content" > secret.txt

./venv/bin/python3 annotation_trust_client.py
./venv/bin/python3 access_scoping_client.py
```

Both ran successfully on the first attempt during development — worth
confirming they reproduce identically on your machine, same as every
other Exercise 4-6 script has so far.

## Design principle worth defending in an exam-style answer

**Why can't MCP clients just refuse to support annotations at all, if
they can't be trusted?** Annotations are still useful as a *hint* for
UI/UX purposes (e.g., not showing a scary confirmation dialog for
something plausibly safe) — the point isn't that they're worthless, it's
that they must never be the ONLY thing standing between a tool call and
an unreviewed side effect. Use them to inform defaults, never to skip
verification entirely for anything consequential.

**Why is `os.path.realpath()` + containment check the right fix, instead
of just blocking filenames containing `".."`?** Blocking the literal
string `".."` is a common but incomplete fix — it can be bypassed with
encoded variants, symlinks, or absolute paths that don't contain `".."`
at all but still resolve outside the sandbox (e.g., a filename that is
itself an absolute path like `/etc/passwd`). Resolving to the actual
final path and checking containment against that real, resolved
location is robust to all of these, because it checks the *actual
destination*, not the *textual form* of the input.

**How does this connect to Domain 2 and Domain 3's broader theme?** This
is the same "verify programmatically, don't trust an interpreted
description" principle that showed up in Domain 2's `InstructionsLoaded`
debugging (trust a hook's log, not a UI summary) and Domain 3's schema
design (nullable fields prevent confident-but-wrong guesses). Here it's:
trust what a tool actually DOES (observed via before/after state, or
real resolved paths), not what it CLAIMS about itself.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| None — both tests worked correctly on the first attempt | — | — |

## Domain 4 — complete

All 7 subtopics covered with real, hands-on, mostly first-try-successful
exercises: tool description routing (with a major correction to Domain
1's original finding), structured errors/idempotency, tool distribution
at scale, MCP architecture fundamentals with a real server/client, real
multi-server routing with a genuine collision fix, real transport
comparison with concrete proof, and now real security exploits (both
fixed). Ready for the Domain 4 quiz, then Domain 5.

## Cross-environment confirmation

Verified identical on a local MacBook (Python 3.13) — same results for
both tests: the naive host missed the silent deletion while the
hardened host caught it via before/after state comparison; the naive
file tool leaked the actual secret file contents while the hardened
version correctly blocked the traversal attempt. This completes
cross-environment verification for all of Exercises 4 through 7.
