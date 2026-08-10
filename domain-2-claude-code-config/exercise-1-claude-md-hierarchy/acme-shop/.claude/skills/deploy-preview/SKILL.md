---
name: deploy-preview
description: Deploy a preview build of the current branch to staging and report the URL. Use when the user asks to deploy a preview, ship to staging, or test a branch live.
context: fork
allowed-tools: Bash, Read
---

Deploy a preview build of the current branch:

1. Run `npm run build` in `frontend/` and confirm it succeeds
2. Run `npm run build` in `api/` and confirm it succeeds
3. Run the deploy script: `./scripts/deploy-staging.sh $(git branch --show-current)`
4. Parse the deploy script's output for the resulting preview URL
5. Report only the final preview URL and build status — do not include full
   build logs in your response

Note on `context: fork`: this skill runs in an isolated subagent context,
separate from the main conversation. That matters here specifically because
build output is long and mostly noise — you want the preview URL back in
your main session, not thousands of lines of webpack/tsc output polluting
the context you're actively working in.

Note on `allowed-tools: Bash, Read`: this skill is pre-approved to run
shell commands and read files, but NOT to edit or write files. A deploy
skill has no legitimate reason to modify source — restricting the tool
set is a deliberate safety boundary, not an oversight.
