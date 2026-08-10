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
| *(fill in as you test locally and in a real Actions run)* | | |

## Follow-up exercises (not yet done)
- [ ] Add `--resume` to chain a second headless call (e.g. "now suggest a
      fix for the top finding") using the `session_id` from the first
- [ ] Test what happens when `ANTHROPIC_API_KEY` is missing/invalid in CI —
      confirm it's actually exit code 2 as documented
- [ ] Add a `stream-json` variant for a scenario needing real-time output
      (e.g. a long-running migration script with live progress)
