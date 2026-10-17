#!/usr/bin/env python3
"""PreToolUse gate for file writes.

Denies obvious secret paths and very large full overwrites. Does not try to
prove the file was re-read. A crash or bad payload fails open (allow).

Matcher: Write|Edit, which Grok also maps onto write / search_replace.
"""

from __future__ import annotations

import json
import sys
from typing import Any

# Substrings, compared against the lowercased path.
SENSITIVE = (".env", ".pem", ".key", "id_rsa", "secrets", ".grok/hooks")

# Bodies larger than this are not surgical. ~150k chars is a ~2k-line file.
MAX_BODY = 150_000

FULL_WRITE_TOOLS = {"write", "write_file"}
EDIT_TOOLS = {
    "search_replace",
    "hashline_edit",
    "strreplace",
    "edit",
    "multiedit",
}


def allow() -> dict[str, str]:
    return {"decision": "allow"}


def deny(reason: str) -> dict[str, str]:
    return {"decision": "deny", "reason": reason}


def tool_name(event: dict[str, Any]) -> str:
    return str(event.get("toolName") or event.get("tool_name") or "")


def tool_input(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("toolInput")
    if raw is None:
        raw = event.get("tool_input")
    return raw if isinstance(raw, dict) else {}


def target_path(inp: dict[str, Any]) -> str:
    for key in ("path", "file_path", "target_file", "target_notebook"):
        value = inp.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def is_sensitive(path: str) -> bool:
    lowered = path.replace("\\", "/").lower()
    return any(token in lowered for token in SENSITIVE)


def text_field(inp: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = inp.get(key)
        if isinstance(value, str):
            return value
    return ""


def truncated(event: dict[str, Any]) -> bool:
    flag = event.get("toolInputTruncated")
    if flag is None:
        flag = event.get("tool_input_truncated")
    return flag is True


def decide(event: dict[str, Any]) -> dict[str, str]:
    name = tool_name(event).strip()
    lowered = name.lower()
    inp = tool_input(event)
    path = target_path(inp)

    if path and is_sensitive(path):
        return deny(f"Blocked write to sensitive path: {path}")

    # A truncated hook payload means the body was large enough to be cut.
    # The size check below cannot see the real length in that case.
    huge_payload = truncated(event)

    if lowered in FULL_WRITE_TOOLS or name in {"Write", "write_file"}:
        content = text_field(inp, "content", "contents")
        if huge_payload or len(content) > MAX_BODY:
            return deny(
                "Full-file content is very large. Prefer a smaller surgical edit or worktree."
            )
        return allow()

    if lowered in EDIT_TOOLS or name in {"Edit", "MultiEdit", "StrReplace"}:
        # A full overwrite can also arrive as search_replace with `content`.
        # Truncation means some string in the call was large (often a whole-file
        # old_string / new_string). A normal small edit is not truncated.
        content = text_field(inp, "content", "contents")
        new_string = text_field(inp, "new_string")
        if huge_payload or len(content) > MAX_BODY or len(new_string) > MAX_BODY:
            return deny(
                "Full-file content is very large. Prefer a smaller surgical edit or worktree."
            )
        return allow()

    return allow()


def selftest() -> int:
    failures: list[str] = []

    def check(label: str, event: dict[str, Any], expect: str) -> None:
        got = decide(event).get("decision")
        if got != expect:
            failures.append(f"{label}: expected {expect}, got {got} ({decide(event)})")

    check("plain edit", {"toolName": "search_replace", "toolInput": {"file_path": "src/app.py", "old_string": "a", "new_string": "b"}}, "allow")
    check("write small", {"toolName": "write", "toolInput": {"file_path": "src/app.py", "content": "hello"}}, "allow")
    check("env", {"toolName": "write", "toolInput": {"file_path": "config/.env", "content": "X=1"}}, "deny")
    check("pem", {"toolName": "Write", "toolInput": {"path": "certs/server.pem", "contents": "x"}}, "deny")
    check("id_rsa", {"toolName": "search_replace", "toolInput": {"file_path": "id_rsa", "old_string": "a", "new_string": "b"}}, "deny")
    check("secrets dir", {"toolName": "write", "toolInput": {"target_file": "deploy/secrets/token", "content": "x"}}, "deny")
    check("hooks dir", {"toolName": "search_replace", "toolInput": {"file_path": ".grok/hooks/file-safety.json", "old_string": "a", "new_string": "b"}}, "deny")
    check("large write", {"toolName": "write", "toolInput": {"file_path": "big.py", "content": "x" * (MAX_BODY + 1)}}, "deny")
    check("large replace", {"toolName": "search_replace", "toolInput": {"file_path": "big.py", "old_string": "a", "new_string": "y" * (MAX_BODY + 1)}}, "deny")
    check("truncated write", {"toolName": "write", "toolInputTruncated": True, "toolInput": {"file_path": "big.py", "content": "cut"}}, "deny")
    check("truncated replace", {"toolName": "search_replace", "toolInputTruncated": True, "toolInput": {"file_path": "big.py", "old_string": "cut", "new_string": "b"}}, "deny")
    check("small under cap", {"toolName": "search_replace", "toolInput": {"file_path": "src/app.py", "new_string": "z" * 1000}}, "allow")
    check("empty payload", {}, "allow")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("guard-write selftest ok")
    return 0


def main(argv: list[str]) -> int:
    if argv and argv[0] in {"--selftest", "selftest"}:
        return selftest()
    try:
        event = json.load(sys.stdin)
    except Exception:
        print(json.dumps(allow()))
        return 0
    if not isinstance(event, dict):
        print(json.dumps(allow()))
        return 0
    try:
        print(json.dumps(decide(event)))
    except Exception:
        print(json.dumps(allow()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
