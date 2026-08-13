---
name: hygiene
description: Run Ringmaster project hygiene — RECENTGOALS/CHANGELOG, docs pairing for runnable code, early commits, and transition checkpoints. Use when the user says "hygiene", "project hygiene", "/hygiene", "docs hygiene", "commit hygiene", or asks for a hygiene checkpoint.
---

# Project Hygiene (Ringmaster pack)

Execute the Ringmaster project hygiene playbook. The playbook is vendored in this plugin.

## Playbook location

Prefer, in order:

1. `${GROK_PLUGIN_ROOT}/references/documentation-and-commit-hygiene.md`
2. Relative to this skill: `../../references/documentation-and-commit-hygiene.md`
3. Marketplace repo checkout: `plugins/ringmaster/references/documentation-and-commit-hygiene.md`

**Scope:** Apply only to **serious work**. Skip throwaway spikes unless the user asks.

## Steps

### 1. Load the playbook
Read the full documentation-and-commit-hygiene reference. Internalize Core Rules (RECENTGOALS, CHANGELOG, runnable→docs, early commits, transitions, nagging, Why-first docs).

### 2. Orient to the current repo

```bash
git status
git log -5 --oneline
```

Read if present: `docs/RECENTGOALS.md`, `docs/CHANGELOG.md` (or root `CHANGELOG.md` / `RECENTGOALS.md`).

### 3. Audit first

| Check | Status | Notes |
|---|---|---|
| RECENTGOALS current? | | What/Why/How + hashes |
| CHANGELOG needs update/migration? | | successes + failures |
| Runnable code without docs/*.md? | | list gaps |
| Uncommitted meaningful work? | | suggest commit units |

### 4. Act (unless user said report-only)

1. Update **RECENTGOALS** (short; migrate old items to CHANGELOG).
2. Append **CHANGELOG** for durable history (What/Why/How + hash when available).
3. Create/update **docs/** for new or significantly changed runnable entrypoints (Why-first).
4. **Commits:** propose a plan; only run `git commit` if the user explicitly wants commits. No force-push; no amend of published history unless asked.
5. Keep changelog ↔ commit message flow bidirectional.

### 5. Transition checkpoint mode
If invoked at a role switch or after a sub-agent returns: treat as Ringmaster hygiene checkpoint; consider a small commit boundary (ask first); surface nags when warranted.

### 6. Report
What changed, what needs a user decision, open nags.

## Do not

- Heavy hygiene on throwaway experiments unless asked.
- Docs that only restate code without **why**.
- Commit secrets or skip the audit when the user only wanted status.
