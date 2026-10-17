# RECENTGOALS

Living scratchpad. Older items migrate to `CHANGELOG.md`.

## Current

### File Edit Discipline (plugin 0.2.2)
- **What:** Ruleset for writes: re-read first, surgical edit, one retry, then tests. Worktree for non-trivial or multi-file work. Plan mode above two files, or for auth/payment/data paths, or when the change is ambiguous. Plugin hooks deny secret paths and bodies over 150k, feed `git diff --check` back, and ask once before `git init` when the workspace is not a repository.
- **Why:** Full-file writes from a stale copy clobber concurrent edits. Prompt rules alone do not stop the tool call.
- **How:** `File Edit Discipline.md` and `references/file-edit-discipline.md`. Hooks: `hooks/bin/guard-write.py`, `hooks/bin/post-edit-check.py`, wired in `hooks/hooks.json`. Master prompt, coding-bootstrap, Implementer posture, and `/bootstrap-prompt` load the rules. Brochure lists them.
- **Hash:** uncommitted

### Wait-credit-guard for long-running Grok tasks
- **What:** Human-scale waits: instant (estimate) → coffee (15m) → lunch/overnight (1h). Hook denies short/missing `timeout_ms` while the task is still running. If you know it is hours, start at 1h.
- **Why:** Each still-running poll is a full parent turn. A 10-minute cap still wakes a fat session all night. Overnight, hourly is enough.
- **How:** Elapsed wall time since start picks the rung (not 2x forever). Playbook + master prompt / coding-bootstrap. Plugin 0.2.1. Brochure covers the whole pack. Playbooks point at this repo only.
- **Hash:** `c496008` (0.2.0 was `282fa98`); brochure `5964fc7`
