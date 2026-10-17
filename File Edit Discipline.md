# File Edit Discipline

**Why:** A full-file write from a stale copy clobbers concurrent edits. The smallest exact replace, after a fresh read of the target, is the write that survives.

## Rules

- Never overwrite a file with a full write unless you have just re-read it in the same turn and the content is small. Prefer the smallest surgical edit (exact string replace or patch) that achieves the goal.
- Before any write or edit tool call, re-read the target file. If the content differs from what you last saw, stop and report the difference instead of writing.
- Never edit a file larger than ~2k lines with a single full-file write. Break the change into smaller targeted edits or work in a worktree.
- If a write fails or returns "file modified," re-read and retry at most once. On the second failure, stop and report the current file state plus the intended change.
- After every successful edit, run the relevant tests, typecheck, or linter if one exists. Do not declare done until they pass or you have explained why they cannot.
- Prefer working in a git worktree (`-w` or subagent isolation) for any change that touches more than one file or is non-trivial. Land via ordinary git when finished.
- Default to Plan mode for any change that touches more than two files, modifies auth/payment/data paths, or is ambiguous. Wait for explicit approval before writing.

## Enforcement

The rules above are what you follow. The plugin hook is the part that can actually stop a write. It does not know whether you re-read the file. A crash fails open.

- `hooks/bin/guard-write.py` runs on `PreToolUse` for `Write|Edit` (Grok's `write` and `search_replace` included). It denies obvious secret paths (`.env`, `.pem`, `.key`, `id_rsa`, `secrets`, `.grok/hooks`) and a body over 150k characters, or a payload Grok had to truncate. A deny means pick a smaller edit or a worktree.
- `hooks/bin/post-edit-check.py` runs on `PostToolUse`. It feeds `git diff --check` back to you. The write already happened. Outside a git repo it stays quiet.
- `hooks/bin/ensure-git-repo.py` runs on session start and on the first write. If the workspace is not a git repository, it asks whether to run `git init`. It never runs `git init` itself. Home, filesystem root, and the temp directory are skipped.
- Both are registered in `hooks/hooks.json` and trusted with the plugin. Reload plugins after an update.
- A stricter "must have re-read" check needs session state and gets fragile. This hook does not try.

Self-test: `python3 plugins/ringmaster/hooks/bin/guard-write.py --selftest`, `python3 plugins/ringmaster/hooks/bin/post-edit-check.py --selftest`, and `python3 plugins/ringmaster/hooks/bin/ensure-git-repo.py --selftest`.
