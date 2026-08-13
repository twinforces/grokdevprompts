# RECENTGOALS

Living scratchpad. Older items migrate to `CHANGELOG.md`.

## Current

### Wait-credit-guard for long-running Grok tasks
- **What:** Estimate the first background wait, then geometric backoff (2x, cap 10 minutes) so snapshot-polling cannot re-send a fat parent context every few seconds. Trusted hook denies short/missing `timeout_ms` while the task is still running.
- **Why:** Each `get_command_or_subagent_output` that returns "still running" is a full parent turn. Tight 30s polls drain credits once the session is large.
- **How:** `plugins/ringmaster/hooks/` + `references/wait-credit-guard.md`, wired into master prompt / coding-bootstrap. Plugin bumped to 0.2.0. Installed copy updated with `grok plugin update ringmaster`.
- **Hash:** `282fa98`
