#!/bin/bash
# ci-review-local.sh — run the same headless-mode logic as the GitHub
# Actions workflow, locally, so you can test/debug it before it's wired
# into CI (where failures are slower to iterate on).
#
# Usage: ./ci-review-local.sh
# Requires: ANTHROPIC_API_KEY set, jq installed

set -uo pipefail
# NOTE: deliberately NOT using `set -e` here. An earlier version of this
# script had `set -e`, which made bash terminate immediately the moment
# `claude` returned non-zero — killing the script before it ever reached
# the error-handling code below. `set -e` and "catch the exit code
# yourself" are mutually exclusive for the specific command you want to
# inspect; pick one. See NOTES.md for the real bug this caused.

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "ANTHROPIC_API_KEY not set — this script needs a real key to run"
  echo "against the actual API (mock mode doesn't apply to Claude Code CLI itself)."
  exit 1
fi

echo "Running headless review with --output-format json..."

claude -p "List 3 things to check before merging a checkout API change: security, error handling, testing" \
  --output-format json \
  --model claude-sonnet-4-6 \
  --max-turns 3 \
  > review.json 2> review-stderr.log

EXIT_CODE=$?

# VERIFIED (2.1.226): the exit code alone is NOT a reliable signal for
# *why* something failed — a bad API key returned exit code 1, not the
# documented 2, and stderr only carried an unrelated connectors-precedence
# warning. The real diagnostic is in the JSON body on stdout, written even
# on failure: `is_error`, `api_error_status` (real HTTP status), and
# `result` (human-readable message). Check that instead of trusting the
# exit code to tell you the failure category.
IS_ERROR=$(jq -r '.is_error // false' review.json 2>/dev/null || echo "unknown")

if [ "$EXIT_CODE" -ne 0 ] || [ "$IS_ERROR" = "true" ]; then
  echo "Claude Code call failed (exit code: $EXIT_CODE, is_error: $IS_ERROR)"
  if [ "$IS_ERROR" = "true" ]; then
    echo "API error status: $(jq -r '.api_error_status // "unknown"' review.json)"
    echo "Message: $(jq -r '.result // "no result field"' review.json)"
  else
    echo "--- stderr ---"
    cat review-stderr.log
  fi
  exit 0  # don't propagate failure to a CI pipeline exit — degrade to manual review
fi

echo "--- Parsed result ---"
jq -r '.result' review.json

echo "--- Cost/usage metrics ---"
jq '{cost_usd: .total_cost_usd, duration_ms: .duration_ms, turns: .num_turns}' review.json
