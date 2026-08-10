# Exercise 3: Plan Mode vs. Direct Execution + CI/CD Integration

Maps to **Domain 2** subtopics: plan mode vs. direct execution, CI/CD flags.

## What this exercise builds

1. `plan-mode-decision-guide.md` — the decision framework for when to use
   plan mode vs. direct execution, plus a hands-on test to actually feel
   the friction/value tradeoff rather than just read about it
2. `.github/workflows/claude-pr-review.yml` — a real GitHub Actions
   workflow using `-p` (headless/print mode), `--output-format json`,
   restricted `--allowedTools`, exit-code handling, and cost/usage logging
3. `scripts/ci-review-local.sh` — the same headless-mode logic runnable
   locally, to debug before wiring into actual CI

## Key exam-relevant facts baked into the CI workflow

- **`-p` / `--print`**: runs a single prompt non-interactively, prints to
  stdout, exits. This is the foundation of any CI usage.
- **`--output-format json`**: wraps the response in structured metadata
  (`result`, `session_id`, `cost_usd`, `duration_ms`, `num_turns`) instead
  of raw text — necessary for parsing with `jq` in a pipeline, not just
  nice-to-have.
- **`--allowedTools`**: restricted to `Read,Grep,Glob` in the CI workflow —
  a CI review job should never have write access to the repo it's
  reviewing. This is the CI-specific version of the least-privilege
  principle from Exercise 1's `allowed-tools` skill frontmatter.
- **Exit code convention**: 0 = success, 1 = generic error, 2 = auth error.
  The workflow explicitly does NOT propagate a Claude failure into a
  blocked pipeline — it falls back to manual review instead. This is a
  direct application of Domain 1's "degrade gracefully vs. escalate"
  judgment, applied to CI infrastructure rather than an agent pipeline.
- **`--max-turns`**: caps how many agentic turns a headless call can take —
  the CI equivalent of Domain 1's `MAX_RETRIES`, bounding cost/time rather
  than letting a call run unbounded.

## Try it yourself

**Local test first** (faster iteration than pushing to GitHub Actions):
```bash
cd acme-shop
export ANTHROPIC_API_KEY=sk-ant-...
chmod +x scripts/ci-review-local.sh
./scripts/ci-review-local.sh
```

**Then wire it into a real repo:**
1. Push `acme-shop/` (or your own project) to GitHub
2. Add `ANTHROPIC_API_KEY` as a repository secret
3. Open a PR and watch the workflow run — check the Actions tab for the
   posted review comment and the uploaded `claude-review-metrics` artifact

## Design decisions worth defending in an exam-style answer

- **Why `--allowedTools "Read,Grep,Glob"` and not the full default tool
  set?** Same least-privilege principle as Exercise 1's skill — a review
  job reading a diff has no legitimate reason to write files or run
  arbitrary bash. Restricting the tool set here is a security boundary
  for an untrusted-input scenario (a PR from an external contributor could
  contain adversarial content in file names or diffs).

- **Why catch a non-zero exit code and `exit 0` anyway instead of failing
  the pipeline?** A transient Claude Code failure (network blip, rate
  limit) shouldn't block every PR in the repo from merging. Degrading to
  "no automated review, proceed to manual review" is the right failure
  mode for this specific job — contrast with a job where failure SHOULD
  block the pipeline (e.g. a test suite).

- **Why log `cost_usd` and `duration_ms` per run?** Without per-run cost
  visibility, headless CI usage can silently scale into a real budget
  problem as PR volume grows — this is an observability practice, not
  just nice-to-have logging.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| `jq` filter returned `"cost": null` despite the review succeeding | My script used `.cost_usd` — the actual field is `.total_cost_usd`. Documentation examples found via search also used `.cost_usd`, so this is a real, current schema mismatch worth verifying yourself rather than trusting either me or third-party docs blindly. | Changed the filter to `.total_cost_usd` in both `ci-review-local.sh` and the GitHub Actions workflow |
| No model pinned — defaulted to `claude-opus-5` | `-p` with no `--model` flag uses whatever the CLI's current default is, which is not necessarily Sonnet and can change between versions | Added `--model claude-sonnet-4-6` explicitly to both scripts — CI cost/latency should be deliberate, not whatever the current default happens to be |
| Bad-key test produced no error-handling output at all — script just stopped silently after the connectors warning | The script had `set -euo pipefail` at the top. `set -e` terminates the script immediately on ANY non-zero exit — including the `claude` call itself — which meant it died right there, before ever reaching the script's own `EXIT_CODE=$?` / error-handling logic below it. The error handling was unreachable dead code. | Removed `-e` from the `set` flags (kept `-u` and `pipefail`). Also added `2> review-stderr.log` to capture and print the real stderr message instead of trusting a hardcoded exit-code-to-meaning table. |
| Documented exit-code convention (0 success / 1 generic error / 2 auth error) does not match observed behavior | A bad `ANTHROPIC_API_KEY` produced exit code **1**, not the documented **2**. Multiple third-party docs describe 2 as the auth-error code; this run contradicts that on 2.1.226. Possibly version-specific, possibly the convention was never accurate, possibly "invalid-but-present" key behaves differently than "missing" key. Not fully root-caused — flagging as a verified discrepancy rather than guessing further. | Script no longer branches logic on the specific exit code number — treats any non-zero as "something went wrong," prints real stderr, and degrades to manual review either way. Don't build CI logic that depends on a specific auth-error exit code without verifying it on your own version first. |

## Actual JSON schema returned by `--output-format json` (verified, 2.1.226)

Worth keeping this verified list rather than trusting any single doc source
— confirmed fields from a real run:

```
is_error, duration_api_ms, num_turns, stop_reason, session_id,
total_cost_usd, usage: {input_tokens, cache_creation_input_tokens,
  cache_read_input_tokens, output_tokens, server_tool_use, service_tier,
  cache_creation, inference_geo, iterations, speed},
modelUsage: {<model-name>: {inputTokens, outputTokens,
  cacheReadInputTokens, cacheCreationInputTokens, webSearchRequests,
  costUSD, contextWindow, maxOutputTokens, canonicalModel, provider}},
permission_denials, terminal_reason, fast_mode_state,
fast_mode_disabled_reason, subtype, api_error_status, result,
ttft_ms, ttft_stream_ms, time_to_request_ms, type, duration_ms, uuid
```

Notably richer than the `result`/`session_id`/`cost_usd`/`duration_ms` most
tutorials describe — `modelUsage` breaks cost down per-model (useful if a
session uses more than one model), `permission_denials` would show any
tool calls a hook or permission rule blocked (useful for the same kind of
audit `InstructionsLoaded` provides, but for tool denials specifically),
and cache token fields matter a lot for real cost accounting since
`cache_read_input_tokens` is billed differently than fresh input tokens.

## Follow-up exercises (not yet done)
- [ ] Add `--resume` to chain a second headless call (e.g. "now suggest a
      fix for the top finding") using the `session_id` from the first
- [ ] Test what happens when `ANTHROPIC_API_KEY` is missing/invalid in CI —
      confirm it's actually exit code 2 as documented
- [ ] Add a `stream-json` variant for a scenario needing real-time output
      (e.g. a long-running migration script with live progress)
