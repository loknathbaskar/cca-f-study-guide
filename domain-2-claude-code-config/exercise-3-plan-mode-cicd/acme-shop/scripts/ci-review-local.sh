#!/bin/bash
# ci-review-local.sh — run the same headless-mode logic as the GitHub
# Actions workflow, locally, so you can test/debug it before it's wired
# into CI (where failures are slower to iterate on).
#
# Usage: ./ci-review-local.sh
# Requires: ANTHROPIC_API_KEY set, jq installed

set -euo pipefail

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "ANTHROPIC_API_KEY not set — this script needs a real key to run"
  echo "against the actual API (mock mode doesn't apply to Claude Code CLI itself)."
  exit 1
fi

echo "Running headless review with --output-format json..."

claude -p "List 3 things to check before merging a checkout API change: security, error handling, testing" \
  --output-format json \
  --max-turns 3 \
  > review.json

EXIT_CODE=$?

# Exit code convention: 0 success, 1 generic error, 2 auth error
if [ $EXIT_CODE -ne 0 ]; then
  echo "Claude Code exited with code $EXIT_CODE"
  case $EXIT_CODE in
    1) echo "Generic error — check the prompt or network" ;;
    2) echo "Auth error — check ANTHROPIC_API_KEY" ;;
  esac
  exit 0  # don't propagate failure to a CI pipeline exit — degrade to manual review
fi

echo "--- Parsed result ---"
jq -r '.result' review.json

echo "--- Cost/usage metrics ---"
jq '{cost: .cost_usd, duration_ms: .duration_ms, turns: .num_turns}' review.json
