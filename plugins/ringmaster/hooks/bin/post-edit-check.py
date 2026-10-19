#!/usr/bin/env python3
"""PostToolUse feedback after a file edit.

Runs `git diff --check` and feeds problems back to the model. The write has
already happened. This does not undo it. Not a git repo, or git missing:
fail open.
"""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any


def interpret(returncode: int, stdout: str, stderr: str) -> dict[str, Any] | None:
    # PostToolUse honors only decision "block". Any other decision, including
    # "allow", is recorded as a failed hook. A clean check stays silent.
    # 128+ is git's fatal range (no repo, bad invocation). Do not nag on that.
    if returncode == 0 or returncode >= 128:
        return None
    text = (stdout or "").strip()
    if not text:
        return None
    return {
        "decision": "block",
        "reason": "git diff --check reported issues",
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": text[:2000],
        },
    }


def work_dir(event: dict[str, Any]) -> str | None:
    for key in ("workspaceRoot", "workspace_root", "cwd"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def run_check(cwd: str | None) -> dict[str, Any] | None:
    try:
        completed = subprocess.run(
            ["git", "diff", "--check"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd,
        )
    except Exception:
        return None
    return interpret(completed.returncode, completed.stdout or "", completed.stderr or "")


def selftest() -> int:
    failures: list[str] = []

    def check(label: str, got: dict[str, Any] | None, expect: str | None) -> None:
        decision = None if got is None else got.get("decision")
        if decision != expect:
            failures.append(f"{label}: {got}")

    check("clean", interpret(0, "", ""), None)
    check("fatal", interpret(129, "", "fatal: not a git repository"), None)
    check("whitespace", interpret(2, "src/app.py:1: trailing whitespace.\n", ""), "block")
    check("empty nonzero", interpret(2, "", ""), None)
    note = interpret(2, "src/app.py:1: trailing whitespace.\n", "") or {}
    context = note.get("hookSpecificOutput", {}).get("additionalContext", "")
    if "trailing whitespace" not in context:
        failures.append(f"context missing: {note}")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("post-edit-check selftest ok")
    return 0


def main(argv: list[str]) -> int:
    if argv and argv[0] in {"--selftest", "selftest"}:
        return selftest()
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(event, dict):
        event = {}
    try:
        result = run_check(work_dir(event))
    except Exception:
        return 0
    if result is not None:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
