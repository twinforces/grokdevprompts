# CHANGELOG

Long-term history. What / Why / How + git hash. Successes and failures.

## 2026-08-13 — brochure is the whole pack; pack files only

- **What:** `docs/brochure.md` now sells Ringmaster (roles, hygiene, subagent policy, credit guard). Playbooks and skills point at this pack only.
- **Why:** The bill is the hook. The product is the circus boss. Old external-note wording was leftover.
- **How:** README is plugin-only install. Master prompt / skills / role routing use pack `references/`. Plain filenames, not wiki links.
- **Hash:** pending this change

## 2026-08-13 — wait-credit-guard human rungs (plugin 0.2.1)

- **What:** Replaced the 2x / 10-minute cap with instant / coffee (15m) / lunch-overnight (1h). Phase follows elapsed wall time. Prompt: if you know it is hours, first wait is 1h.
- **Why:** Multi-hour and overnight jobs were still getting a wake every 10 minutes. Human interest is coffee / lunch / morning, not a 10-minute metronome.
- **How:** `next_interval()` uses started_ms + elapsed. Cap is `LUNCH_MS` (1h). Playbooks, master prompt, coding-bootstrap, and `docs/brochure.md` (X-ready) updated to match.
- **Hash:** `c496008`

## 2026-08-13 — wait-credit-guard (plugin 0.2.0)

- **What:** Added estimate-then-backoff waits for background commands and subagents. Hook denies snapshot or short polls during the backoff window; playbook + master prompt / coding-bootstrap tell the Ringmaster to prefer one long `timeout_ms`.
- **Why:** Polling a long job with the default 30s wait (or no timeout) re-sends the whole conversation each time. That is what was eating credits.
- **How:** `hooks/bin/wait-credit-guard.py` (selftest) + `hooks/hooks.json`. Duration table: sleep N, tests 2m, cargo/npm install/build 3m, docker build 5m, other shell 1m, background subagent 3m. Cap 600000ms. Fail-open on hook errors. Completed/killed tasks drop state so a completion collect is not blocked.
- **Hash:** `282fa98`
- **Tried / not this change:** Prompt-only advice was not enough; agents still tight-poll under time pressure, so enforcement is a PreToolUse deny with the required `timeout_ms`.
