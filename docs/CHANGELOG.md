# CHANGELOG

Long-term history. What / Why / How + git hash. Successes and failures.

## 2026-08-13 — wait-credit-guard (plugin 0.2.0)

- **What:** Added estimate-then-backoff waits for background commands and subagents. Hook denies snapshot or short polls during the backoff window; playbook + master prompt / coding-bootstrap tell the Ringmaster to prefer one long `timeout_ms`.
- **Why:** Polling a long job with the default 30s wait (or no timeout) re-sends the whole conversation each time. That is what was eating credits.
- **How:** `hooks/bin/wait-credit-guard.py` (selftest) + `hooks/hooks.json`. Duration table: sleep N, tests 2m, cargo/npm install/build 3m, docker build 5m, other shell 1m, background subagent 3m. Cap 600000ms. Fail-open on hook errors. Completed/killed tasks drop state so a completion collect is not blocked.
- **Hash:** pending this commit
- **Tried / not this change:** Prompt-only advice was not enough; agents still tight-poll under time pressure, so enforcement is a PreToolUse deny with the required `timeout_ms`.
