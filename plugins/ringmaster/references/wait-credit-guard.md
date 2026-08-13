# Wait Credit Guard

**Why:** Every `get_command_or_subagent_output` / `wait_commands_or_subagents` call that comes back "still running" is another parent-agent turn. That turn re-sends the whole conversation. On a long job, tight 30s polls (the tool default) will drain credits once the session is fat. The notification on completion is free enough; the poll loop is not.

Enforcement lives in `hooks/bin/wait-credit-guard.py` (trusted plugin hook). This note is the playbook the Ringmaster follows even if the hook is off.

## Rule

1. **Estimate first.** When you background a command or subagent, pick a duration from the table below (or `sleep N` when the command literally sleeps). First collect may be a snapshot.
2. **Then geometric backoff.** If it is still running, the next wait is `timeout_ms = last_interval * 2`, capped at **10 minutes** (`600000`). Sequence from a 60s default: 60s, 120s, 240s, 480s, 600s, 600s...
3. **Never snapshot-poll a running task.** Omit `timeout_ms` only for the first glance or after a completion/kill. If a completion notification already has the output, do not poll at all.
4. **Prefer one long wait over N short ones.** If you have no other work, call once with `timeout_ms` set to the estimate (or the remaining backoff). A finished task returns immediately even when `timeout_ms` is large.
5. **Do other work inside the wait only if it is real work.** Do not busy-loop "check again" turns. Monitors must emit only terminal lines (`DONE` / `FAILED` / `CANCELLED`), never progress. `/loop` for completion checks should be 5m+ , not 60s.

## Duration estimates (first wait)

| Kind | `timeout_ms` |
|---|---|
| `sleep N` | `N * 1000` |
| `pytest`, `npm test`, `go test` | 120000 (2m) |
| `cargo build/test/check`, `npm run build`, `npm install` / `ci`, `mvn`, `gradle` | 180000 (3m) |
| `docker build` | 300000 (5m) |
| other shell | 60000 (1m) |
| background subagent | 180000 (3m) |

The hook uses this same table. If you know the job is longer (full CI, huge compile), start higher. Backoff still caps at 10 minutes per wait.

## What the hook does

- **Start** (`run_terminal_command` / `spawn_subagent` with a task id): store the estimate. First collect is allowed immediately.
- **Poll while running:** if now is still inside the backoff window and `timeout_ms` is missing or too small, **deny** and tell you the required `timeout_ms`. Retry with that value.
- **Completed / failed / cancelled / killed:** drop state. Further collects are allowed.
- Fail-open: a hook crash never blocks the tool.

If a completion notification arrives during backoff and you still need the output, retry with the required `timeout_ms`. Finished work returns at once; you are not sitting on the full interval.

## Do not

- `get_command_or_subagent_output` with no timeout in a loop.
- Default 30s waits repeated "just to see".
- `monitor` or `/loop` as a substitute for a single long wait on a one-shot job.
- Sleep-loops in the shell to poll; use one `timeout_ms` wait instead.
