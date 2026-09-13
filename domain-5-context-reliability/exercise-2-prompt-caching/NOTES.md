# Domain 5, Exercise 2: Prompt Caching — Write, Hit, and a Real Broken-Cache Test

## What this demonstrates

Three real API calls, same large static system prompt (a padded product
policy doc, well over the minimum cacheable token threshold):

- **Call 1**: first call with `cache_control: {"type": "ephemeral"}` on
  the system prompt — expect a **cache write**
  (`cache_creation_input_tokens > 0`), billed at a premium (~1.25x base
  input price)
- **Call 2**: identical system prompt, called shortly after — expect a
  **cache hit** (`cache_read_input_tokens > 0`), billed at a steep
  discount (~0.1x base input price) — this is the actual cost saving
  prompt caching exists for
- **Call 3 — the anti-pattern test**: the SAME policy doc, but with a
  live timestamp string injected at the top (something a real system
  might do without thinking about the consequence). Since a cached
  prefix must be byte-identical up to the cache breakpoint, this should
  break the cache entirely — expect a fresh cache write again, not a
  hit, proving directly (not just citing) that "don't put timestamps in
  cached content" is a real, measurable failure mode.

## Try it yourself

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 exercise2_prompt_caching.py
```

Check specifically:
1. Does Call 1 show `cache_creation_input_tokens > 0` and Call 2 show
   `cache_read_input_tokens > 0` for a comparable token count?
2. Does Call 3 show a fresh `cache_creation_input_tokens > 0` (cache
   miss/rewrite) rather than a hit — confirming the timestamp actually
   broke the cache?
3. Compute the real cost per call using the printed usage numbers — is
   Call 2 dramatically cheaper than Call 1? Is Call 3 roughly as
   expensive as Call 1 (no savings at all), rather than partially
   benefiting?

## Design principle worth defending in an exam-style answer

**Why does even a single injected timestamp break the ENTIRE cache,
rather than just that one changed line?** Caching works on a byte-exact
prefix match — everything before (and including) the cache breakpoint
must be identical to the previously cached version. A one-character
difference anywhere in that prefix means the system can't recognize it
as the same cached content at all, so it falls back to processing (and
writing to cache again) as if this were the first time. This is a hard,
binary requirement, not a "close enough" fuzzy match.

**Why does this matter specifically for agentic/production systems, not
just a one-off cost curiosity?** A system prompt that includes anything
that changes per-request — a timestamp, a request ID, a dynamically
computed "current user's name" inserted at the top rather than the
bottom — silently pays full price on every single call while looking
like it should be benefiting from caching. This is exactly the kind of
bug that's invisible unless you specifically check `cache_read_input_tokens`
per call, which most naive integrations never do.

**Why cache write costs MORE than base input (a premium), not the
same?** The premium compensates for the one-time cost of actually
computing and storing the cached representation. The economics only pay
off if the SAME prefix gets reused enough times afterward at the steep
read discount — caching a prefix you'll only ever send once is strictly
worse than not caching it at all.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| Script crashed with `ModuleNotFoundError: No module named 'anthropic'` even when meant to exit cleanly on a missing API key | `import anthropic` was placed at the top of the file, before the `ANTHROPIC_API_KEY` check — so the import ran (and failed, in an environment without the package installed) regardless of whether a key was present | Moved the key check above the `anthropic` import entirely, so the script can exit cleanly with a clear message even in an environment that doesn't have the `anthropic` package installed at all |
| **First real run: all three calls showed `cache_creation_input_tokens=0` AND `cache_read_input_tokens=0` — caching never engaged at all, not even a write** | Claude models (Sonnet/Opus) require a minimum of 1024 tokens in the cacheable prefix before caching activates at all. The original policy doc was only ~470 tokens (confirmed by `input_tokens=523` across all three calls, essentially unchanged) — I claimed it was "comfortably padded" without actually counting tokens, assuming instead of verifying, the same mistake made in Domain 3 Step 5 and Domain 4 Exercise 1 | Substantially expanded the policy doc (added several more detailed sections) to ~1356 tokens by rough estimate, well clear of the threshold. Also added an upfront rough token-count check that prints a warning BEFORE making any API calls if the document looks too short — catching this class of mistake before burning a real API call to discover it |

**Worth internalizing as its own lesson, again**: "I made this long
enough" is a claim, not a verification — the actual fix here wasn't
writing more words, it was checking an actual number (token count)
against an actual documented threshold (1024) before asserting the test
was set up correctly. This is the same discipline that caught Domain 3's
truncated-output bug and Domain 4's missing-required-field confound:
verify the mechanical setup before drawing conclusions from the results
it produces.

## Real results — fully confirmed, cleanly

**Call 1 (cache write)**: `cache_creation_input_tokens=1219`, cost
$0.004619.

**Call 2 (cache hit)**: `cache_read_input_tokens=1219` — the exact same
token count as what was written, confirming the cache stored and
returned the identical content. Cost **$0.000411 — about 11.2x cheaper
than Call 1** for a functionally equivalent request. This matches the
predicted ~1.25x write / ~0.1x read multiplier ratio closely (3.75/0.30
≈ 12.5x theoretical ratio; the observed 11.2x is close, with the
difference explained by the small non-cached portion of each request).

**Call 3 (timestamp anti-pattern)**: `cache_creation_input_tokens=1239`
— a **fresh cache write, not a hit**. The timestamp fully invalidated
the cache. Cost was **$0.004691 — slightly MORE than Call 1**, not
merely "no savings" as hedged in the original prediction. The small
excess (1239 vs. 1219 tokens) is the timestamp string itself adding a
few tokens of pure overhead, with zero caching benefit retained at all.

## Conclusion

Every part of the prediction held, with real, precise numbers: caching
requires clearing a real minimum token threshold (confirmed by the first
failed attempt), delivers a genuine ~11x cost reduction on a cache hit
for identical content, and a single dynamic element (a timestamp)
injected into an otherwise-static cached prefix doesn't degrade caching
gracefully — it eliminates the benefit completely and adds pure overhead
on top. This is a strong, fully evidence-backed answer to "why does my
production system's caching not seem to be saving money" — check
literally the exact byte-for-byte prefix for anything that changes
per-request, since even one such element anywhere in the cached portion
silently costs you the entire benefit.

## Next step
Exercise 3 — durable state vs. transient conversation: the scratchpad
pattern for long-running sessions.
