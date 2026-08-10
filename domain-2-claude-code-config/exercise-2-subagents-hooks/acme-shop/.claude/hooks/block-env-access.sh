#!/bin/bash
# block-env-access.sh
#
# PreToolUse hook — reads JSON on stdin, decides whether to block.
# Exit code 2 blocks the tool call before it runs and sends stderr back to
# Claude as feedback. Exit code 0/1 lets it through (1 = non-blocking error).
#
# This is the ENFORCED version of the "never read/write .env" rule in
# .claude/rules/secrets-handling.md. Unlike that file, this cannot be argued
# with, reasoned around, or skipped under an insistent instruction — it runs
# regardless of what the model decides.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ "$FILE_PATH" == *.env ]] || [[ "$FILE_PATH" == *.env.* ]]; then
  echo "BLOCKED: $FILE_PATH matches .env pattern. Secrets files cannot be read or written by Claude Code in this project, no exceptions." >&2
  exit 2
fi

exit 0
