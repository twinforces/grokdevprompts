#!/usr/bin/env python3
"""Ask before creating a git repo. Never runs git init.

SessionStart shows the question to the user. The first write in that session
also tells the model to ask once. A crash fails open.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def is_work_tree(path: str) -> bool:
    try:
        completed = subprocess.run(
            ["git", "-C", path, "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return False
    return completed.returncode == 0 and (completed.stdout or "").strip() == "true"


def too_broad(path: str) -> bool:
    """Home, filesystem root, and temp dirs are the wrong place for git init."""
    try:
        resolved = Path(path).expanduser().resolve()
    except Exception:
        return True
    if not resolved.is_dir():
        return True
    home = Path.home().resolve()
    if resolved == home or resolved == Path(resolved.anchor):
        return True
    temps = []
    for raw in ("/tmp", "/var/tmp", "/private/tmp", tempfile.gettempdir()):
        try:
            temps.append(Path(raw).resolve())
        except Exception:
            continue
    return resolved in temps


def workspace(event: dict[str, Any]) -> str:
    for key in ("workspaceRoot", "workspace_root", "cwd"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def event_kind(event: dict[str, Any]) -> str:
    raw = str(event.get("hook_event_name") or event.get("hookEventName") or "")
    compact = raw.replace("_", "").replace("-", "").lower()
    if "sessionstart" in compact:
        return "session"
    if "pretooluse" in compact:
        return "pre"
    return ""


def session_id(event: dict[str, Any]) -> str:
    for key in ("sessionId", "session_id"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def state_file() -> Path | None:
    root = os.environ.get("GROK_PLUGIN_DATA")
    if not root:
        return None
    return Path(root) / "ensure-git-repo.json"


def load_state() -> dict[str, list[str]]:
    path = state_file()
    if path is None or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    clean: dict[str, list[str]] = {}
    for key, value in list(data.items())[-20:]:
        if isinstance(key, str) and isinstance(value, list):
            clean[key] = [item for item in value if isinstance(item, str)]
    return clean


def already_asked(session: str, path: str) -> bool:
    if not session:
        return False
    return path in load_state().get(session, [])


def mark_asked(session: str, path: str) -> None:
    if not session:
        return
    target = state_file()
    if target is None:
        return
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        state = load_state()
        paths = state.setdefault(session, [])
        if path not in paths:
            paths.append(path)
        # Keep the file to recent sessions so it cannot grow without bound.
        trimmed = dict(list(state.items())[-20:])
        target.write_text(json.dumps(trimmed), encoding="utf-8")
    except Exception:
        return


def question(path: str) -> str:
    return (
        f"{path} is not a git repository. "
        "Do you want to make it one with `git init`? "
        "Ringmaster will not run git init unless you say yes."
    )


def reply(
    kind: str,
    path: str,
    *,
    is_repo: bool,
    broad: bool,
    asked: bool,
) -> dict[str, Any] | None:
    if kind == "session":
        if not path or is_repo or broad:
            return None
        return {"systemMessage": question(path)}
    if kind == "pre":
        if not path or is_repo or broad or asked:
            return {"decision": "allow"}
        return {
            "decision": "allow",
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": (
                    f"{question(path)} "
                    "Ask that once if they have not already answered. "
                    "Then continue the edit either way."
                ),
            },
        }
    return None


def handle(event: dict[str, Any]) -> dict[str, Any] | None:
    kind = event_kind(event)
    if not kind:
        return None
    path = workspace(event)
    if not path:
        return {"decision": "allow"} if kind == "pre" else None
    repo = is_work_tree(path)
    broad = too_broad(path)
    session = session_id(event)
    asked = already_asked(session, path)
    result = reply(kind, path, is_repo=repo, broad=broad, asked=asked)
    if (
        kind == "pre"
        and result is not None
        and "additionalContext" in result.get("hookSpecificOutput", {})
    ):
        mark_asked(session, path)
    return result


def selftest() -> int:
    failures: list[str] = []

    def check(label: str, cond: bool, detail: str = "") -> None:
        if not cond:
            failures.append(f"{label}: {detail}" if detail else label)

    home = str(Path.home())
    scratch = tempfile.mkdtemp(prefix="ensure-git-repo-")
    try:
        check("scratch is not a repo", not is_work_tree(scratch), scratch)
        check("home is too broad", too_broad(home))
        check("scratch is not too broad", not too_broad(scratch), scratch)
        check("root is too broad", too_broad("/"))

        quiet = reply("session", scratch, is_repo=True, broad=False, asked=False)
        check("session in repo is quiet", quiet is None, str(quiet))
        home_msg = reply("session", home, is_repo=False, broad=True, asked=False)
        check("session at home is quiet", home_msg is None, str(home_msg))
        asked_msg = reply("session", scratch, is_repo=False, broad=False, asked=False)
        check(
            "session asks",
            isinstance(asked_msg, dict) and "git init" in asked_msg.get("systemMessage", ""),
            str(asked_msg),
        )

        edit = reply("pre", scratch, is_repo=False, broad=False, asked=False)
        context = (edit or {}).get("hookSpecificOutput", {}).get("additionalContext", "")
        check("edit allows", (edit or {}).get("decision") == "allow", str(edit))
        check("edit asks once", "git init" in context and "once" in context, context)
        again = reply("pre", scratch, is_repo=False, broad=False, asked=True)
        check(
            "second edit stays quiet",
            again == {"decision": "allow"},
            str(again),
        )

        data = tempfile.mkdtemp(prefix="ensure-git-repo-state-")
        os.environ["GROK_PLUGIN_DATA"] = data
        event = {
            "hook_event_name": "PreToolUse",
            "sessionId": "s1",
            "workspaceRoot": scratch,
        }
        first = handle(event)
        second = handle(event)
        check("live first asks", "git init" in json.dumps(first))
        check("live second is quiet", second == {"decision": "allow"}, str(second))
    finally:
        os.environ.pop("GROK_PLUGIN_DATA", None)

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("ensure-git-repo selftest ok")
    return 0


def main(argv: list[str]) -> int:
    if argv and argv[0] in {"--selftest", "selftest"}:
        return selftest()
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(event, dict):
        return 0
    try:
        result = handle(event)
    except Exception:
        return 0
    if result is not None:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
