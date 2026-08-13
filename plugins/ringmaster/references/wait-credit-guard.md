# Wait Credit Guard

**Why:** Every `get_command_or_subagent_output` / `wait_commands_or_subagents` call that comes back "still running" is another parent-agent turn. That turn re-sends the whole conversation. Tight 30s (or 10m) polls on a job that runs for hours will drain credits once the session is fat. Human attention does not work on a 10-minute metronome. It works as **instant / cup of coffee / lunch / overnight**. Overnight, checking every hour is enough.

Enforcement lives in `hooks/bin/wait-credit-guard.py` (trusted plugin hook). This note is the playbook the Ringmaster follows even if the hook is off.

## Rule

Pick the human rung you actually believe, then let elapsed time walk you up. Do not climb a 2x ladder that caps at 10 minutes.

| Rung | When | `timeout_ms` |
|---|---|---|
| **Instant** | First glance, or you think it is seconds to a few minutes | Command estimate (table below), often 1–5 min |
| **Coffee** | Still running after the instant wait, or you would go get coffee | 900000 (15 min) |
| **Lunch / overnight** | Still running after ~20 min on the clock, or you already know it is hours | 3600000 (1 hour) |

1. **If you know it is hours or overnight, start at lunch.** First wait is `timeout_ms=3600000`. Do not open with a 1-minute guess and "see."
2. **If you are unsure, start at the estimate table** (instant). First collect may be a snapshot.
3. **The hook steps you up by wall-clock elapsed**, not by doubling forever. After ~2 min you are on coffee (15m). After ~20 min you are on lunch/overnight (1h) and you stay there. A job that has already been running for hours skips straight to hourly.
4. **Never snapshot-poll a running task.** Omit `timeout_ms` only for the first glance or after a completion/kill. If a completion notification already has the output, do not poll at all.
5. **Prefer one long wait.** Finished tasks return immediately even when `timeout_ms` is 1 hour. You are not sitting out the full interval if the job already ended.
6. **Monitors / `/loop`:** terminal lines only (`DONE` / `FAILED` / `CANCELLED`). Completion `/loop` is 1h for overnight work, never 60s.

## Instant estimates (only when you do not already know it is long)

| Kind | `timeout_ms` |
|---|---|
| `sleep N` | `N * 1000` |
| `pytest`, `npm test`, `go test` | 120000 (2m) |
| `cargo build/test/check`, `npm run build`, `npm install` / `ci`, `mvn`, `gradle` | 180000 (3m) |
| `docker build` | 300000 (5m) |
| other shell | 60000 (1m) |
| background subagent | 180000 (3m) |

These are the **instant** rung. They are not a cap. A `docker build` that is still going at 5 minutes becomes coffee, then hourly. A training run you already know is overnight never uses this table.

## What the hook does

- **Start** (`run_terminal_command` / `spawn_subagent` with a task id): store start time + estimate. First collect is allowed immediately.
- **Poll while running:** if now is still inside the current rung's window and `timeout_ms` is missing or too small, **deny** and tell you the required `timeout_ms`. Retry with that value.
- **Elapsed wins:** a task whose start is already 20+ minutes ago requires a 1 hour wait, even on the first denied short poll.
- **Completed / failed / cancelled / killed:** drop state. Further collects are allowed.
- Fail-open: a hook crash never blocks the tool.

## Do not

- `get_command_or_subagent_output` with no timeout in a loop.
- Default 30s waits, or a 10-minute cap, on something that might run until morning.
- `monitor` or `/loop` as a substitute for one long wait on a one-shot job.
- Sleep-loops in the shell to poll; use one `timeout_ms` wait instead.
