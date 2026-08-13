#!/usr/bin/env python3
"""Credit guard for Grok background-task polling.

Each get_command_or_subagent_output / wait_commands_or_subagents call that
returns "still running" becomes another model turn. As the parent context
grows, those turns get expensive. This hook:

1. Records a duration estimate when a background command or subagent starts.
2. Enforces geometric backoff on subsequent polls (estimate, 2x, 4x, ... cap).
3. Denies snapshot / short polls during the backoff window. Finished tasks
   return immediately when retried with timeout_ms set to the required wait.

State lives in $GROK_PLUGIN_DATA/wait-credit-guard.json (or a temp dir in tests).
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import sys
import tempfile
import time
from typing import Any

FACTOR = 2
CAP_MS = 10 * 60 * 1000
DEFAULT_ESTIMATE_MS = 60 * 1000
DEFAULT_SUBAGENT_MS = 3 * 60 * 1000
STALE_MS = 24 * 60 * 60 * 1000

# Order matters: first match wins.
ESTIMATE_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"\bsleep\s+(\d+(?:\.\d+)?)\b"), -1),  # special: parsed below
    (re.compile(r"\bdocker\s+build\b"), 5 * 60 * 1000),
    (re.compile(r"\bnpm\s+(?:ci|install)\b"), 3 * 60 * 1000),
    (re.compile(r"\byarn\s+install\b"), 3 * 60 * 1000),
    (re.compile(r"\bpnpm\s+(?:i|install)\b"), 3 * 60 * 1000),
    (re.compile(r"\bpip(?:3)?\s+install\b"), 3 * 60 * 1000),
    (re.compile(r"\bcargo\s+(?:build|test|check)\b"), 3 * 60 * 1000),
    (re.compile(r"\bnpm\s+run\s+build\b"), 3 * 60 * 1000),
    (re.compile(r"\bnpm\s+(?:test|run\s+test)\b"), 2 * 60 * 1000),
    (re.compile(r"\bpytest\b"), 2 * 60 * 1000),
    (re.compile(r"\bgo\s+test\b"), 2 * 60 * 1000),
    (re.compile(r"\bmvn\b"), 3 * 60 * 1000),
    (re.compile(r"\bgradlew?\b"), 3 * 60 * 1000),
    (re.compile(r"\bmake\b"), 2 * 60 * 1000),
]

WAIT_TOOLS = {
    "get_command_or_subagent_output",
    "wait_commands_or_subagents",
    "gettaskoutput",
    "waittasks",
    "wait_commands",
}
START_TOOLS = {
    "run_terminal_command",
    "bash",
    "spawn_subagent",
    "task",
}
KILL_TOOLS = {
    "kill_command_or_subagent",
}

DONE_STATUSES = {"completed", "complete", "failed", "cancelled", "canceled", "exited", "success", "error"}
RUNNING_STATUSES = {"running", "in_progress", "pending", "started", "waiting"}


def now_ms() -> int:
    return int(time.time() * 1000)


def state_path() -> str:
    override = os.environ.get("WAIT_CREDIT_GUARD_STATE")
    if override:
        return override
    data_dir = os.environ.get("GROK_PLUGIN_DATA")
    if not data_dir:
        data_dir = os.path.join(tempfile.gettempdir(), "ringmaster-wait-credit-guard")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "wait-credit-guard.json")


def load_state(path: str) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    tasks = data.get("tasks")
    if not isinstance(tasks, dict):
        tasks = {}
        data["tasks"] = tasks
    cutoff = now_ms() - STALE_MS
    stale = [tid for tid, rec in tasks.items() if not isinstance(rec, dict) or rec.get("updated_ms", 0) < cutoff]
    for tid in stale:
        tasks.pop(tid, None)
    return data


def save_state(path: str, data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def with_state(mutator):
    path = state_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    lock_path = path + ".lock"
    with open(lock_path, "a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        state = load_state(path)
        result = mutator(state)
        save_state(path, state)
        return result


def parse_jsonish(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return value
        return value


def as_int(value: Any) -> int | None:
    if value is None or value is False:
        return None
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def estimate_from_command(command: str) -> int:
    text = command or ""
    sleep = re.search(r"\bsleep\s+(\d+(?:\.\d+)?)\b", text)
    if sleep:
        return max(1000, int(float(sleep.group(1)) * 1000))
    for pattern, ms in ESTIMATE_PATTERNS:
        if pattern.search(text):
            if ms < 0:
                continue
            return ms
    return DEFAULT_ESTIMATE_MS


def estimate_for_start(tool_name: str, tool_input: dict[str, Any]) -> int:
    lowered = tool_name.lower()
    if "spawn" in lowered or lowered == "task":
        return DEFAULT_SUBAGENT_MS
    command = ""
    if isinstance(tool_input, dict):
        command = str(tool_input.get("command") or "")
    return estimate_from_command(command)


def extract_ids(blob: Any) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()

    def add(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, (list, tuple)):
            for item in value:
                add(item)
            return
        text = str(value).strip()
        if not text or text in seen:
            return
        seen.add(text)
        found.append(text)

    data = parse_jsonish(blob)
    if isinstance(data, dict):
        for key in ("task_id", "taskId", "subagent_id", "subagentId"):
            if key in data:
                add(data.get(key))
        for key in ("task_ids", "taskIds"):
            if key in data:
                add(data.get(key))
        # Nested spawn / background result envelopes.
        for key in ("result", "output", "data"):
            if key in data:
                for item in extract_ids(data.get(key)):
                    add(item)
    elif isinstance(data, list):
        for item in data:
            for tid in extract_ids(item):
                add(tid)
    elif isinstance(blob, str):
        for match in re.finditer(
            r'"(?:task_id|taskId|subagent_id|subagentId)"\s*:\s*"([^"]+)"',
            blob,
        ):
            add(match.group(1))
    return found


def extract_timeout_ms(tool_input: dict[str, Any]) -> int | None:
    if not isinstance(tool_input, dict):
        return None
    raw = tool_input.get("timeout_ms", tool_input.get("timeoutMs"))
    parsed = as_int(raw)
    if parsed is None or parsed <= 0:
        return None
    return parsed


def infer_status(tool_result: Any) -> str | None:
    data = parse_jsonish(tool_result)
    texts: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            status = node.get("status") or node.get("state")
            if isinstance(status, str):
                texts.append(status.lower())
            if node.get("completed") is True:
                texts.append("completed")
            if "exit_code" in node or "exitCode" in node:
                texts.append("completed")
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            texts.append(node.lower())

    walk(data)
    if isinstance(tool_result, str):
        texts.append(tool_result.lower())

    joined = " ".join(texts)
    if any(s in RUNNING_STATUSES for s in texts) or "still running" in joined:
        if not any(s in DONE_STATUSES for s in texts) or "still running" in joined:
            return "running"
    if any(s in DONE_STATUSES for s in texts):
        return "completed"
    if "still running" in joined or re.search(r"\brunning\b", joined):
        return "running"
    return None


def normalize_tool_name(name: str) -> str:
    return (name or "").strip()


def is_wait_tool(name: str) -> bool:
    lowered = name.lower()
    return lowered in WAIT_TOOLS or "get_command_or_subagent_output" in lowered or "wait_command" in lowered


def is_start_tool(name: str) -> bool:
    return name.lower() in START_TOOLS


def is_kill_tool(name: str) -> bool:
    return name.lower() in KILL_TOOLS


def allow() -> dict[str, str]:
    return {"decision": "allow"}


def deny(reason: str) -> dict[str, str]:
    return {"decision": "deny", "reason": reason}


def next_interval(record: dict[str, Any]) -> int:
    current = as_int(record.get("interval_ms")) or as_int(record.get("estimate_ms")) or DEFAULT_ESTIMATE_MS
    polls = as_int(record.get("polls")) or 0
    if polls <= 1:
        return min(current, CAP_MS)
    return min(max(current, 1000) * FACTOR, CAP_MS)


def pre_wait(state: dict[str, Any], tool_input: dict[str, Any]) -> dict[str, str]:
    ids = extract_ids(tool_input)
    if not ids:
        return allow()
    timeout = extract_timeout_ms(tool_input)
    tasks = state.setdefault("tasks", {})
    now = now_ms()
    required = 0
    blocking_id = None
    for tid in ids:
        rec = tasks.get(tid)
        if not isinstance(rec, dict):
            continue
        if rec.get("last_status") in DONE_STATUSES:
            continue
        next_at = as_int(rec.get("next_allowed_ms")) or 0
        if now >= next_at:
            continue
        remaining = next_at - now
        if timeout is not None and timeout >= remaining:
            continue
        if remaining > required:
            required = remaining
            blocking_id = tid
    if not required or not blocking_id:
        return allow()
    rec = tasks[blocking_id]
    polls = as_int(rec.get("polls")) or 0
    interval = as_int(rec.get("interval_ms")) or DEFAULT_ESTIMATE_MS
    return deny(
        "Credit guard: task {tid} still running (poll #{polls}, interval {interval}ms). "
        "Snapshot/short polls re-send the whole parent context and burn credits. "
        "Retry with timeout_ms={required} (geometric backoff, cap {cap}ms). "
        "A finished task returns immediately.".format(
            tid=blocking_id,
            polls=polls,
            interval=interval,
            required=required,
            cap=CAP_MS,
        )
    )


def touch_running(record: dict[str, Any], estimate_ms: int | None = None) -> None:
    now = now_ms()
    if estimate_ms:
        record["estimate_ms"] = estimate_ms
    record.setdefault("estimate_ms", DEFAULT_ESTIMATE_MS)
    record.setdefault("interval_ms", record["estimate_ms"])
    record.setdefault("polls", 0)
    record["polls"] = int(record.get("polls") or 0) + 1
    record["interval_ms"] = next_interval(record)
    record["next_allowed_ms"] = now + int(record["interval_ms"])
    record["last_status"] = "running"
    record["updated_ms"] = now
    record["last_check_ms"] = now


def post_start(state: dict[str, Any], tool_name: str, tool_input: dict[str, Any], tool_result: Any) -> None:
    if isinstance(tool_input, dict) and tool_input.get("background") is False:
        return
    ids = extract_ids(tool_result) or extract_ids(tool_input)
    if not ids:
        return
    estimate = estimate_for_start(tool_name, tool_input if isinstance(tool_input, dict) else {})
    tasks = state.setdefault("tasks", {})
    now = now_ms()
    for tid in ids:
        rec = tasks.get(tid) if isinstance(tasks.get(tid), dict) else {}
        rec["estimate_ms"] = estimate
        rec["interval_ms"] = estimate
        rec["polls"] = 0
        rec["next_allowed_ms"] = now  # first collect is free
        rec["last_status"] = "running"
        rec["updated_ms"] = now
        rec["source"] = tool_name
        tasks[tid] = rec


def post_wait(state: dict[str, Any], tool_input: dict[str, Any], tool_result: Any) -> None:
    ids = extract_ids(tool_input) or extract_ids(tool_result)
    if not ids:
        return
    status = infer_status(tool_result)
    tasks = state.setdefault("tasks", {})
    if status in DONE_STATUSES:
        for tid in ids:
            tasks.pop(tid, None)
        return
    for tid in ids:
        rec = tasks.get(tid) if isinstance(tasks.get(tid), dict) else {}
        touch_running(rec, estimate_ms=rec.get("estimate_ms") or DEFAULT_ESTIMATE_MS)
        tasks[tid] = rec


def post_kill(state: dict[str, Any], tool_input: dict[str, Any], tool_result: Any) -> None:
    ids = extract_ids(tool_input) or extract_ids(tool_result)
    tasks = state.setdefault("tasks", {})
    for tid in ids:
        tasks.pop(tid, None)


def handle_event(event: dict[str, Any]) -> dict[str, str] | None:
    event_name = str(
        event.get("hookEventName")
        or os.environ.get("GROK_HOOK_EVENT")
        or ""
    ).lower()
    tool_name = normalize_tool_name(str(event.get("toolName") or event.get("tool_name") or ""))
    tool_input = parse_jsonish(event.get("toolInput") or event.get("tool_input") or {})
    if not isinstance(tool_input, dict):
        tool_input = {}
    tool_result = event.get("toolResult", event.get("tool_result"))

    if event_name in {"pre_tool_use", "pretooluse"}:
        if is_wait_tool(tool_name):
            return with_state(lambda state: pre_wait(state, tool_input))
        return allow()

    if event_name in {"post_tool_use", "posttooluse"}:

        def mutate(state: dict[str, Any]) -> None:
            if is_start_tool(tool_name):
                post_start(state, tool_name, tool_input, tool_result)
            elif is_wait_tool(tool_name):
                post_wait(state, tool_input, tool_result)
            elif is_kill_tool(tool_name):
                post_kill(state, tool_input, tool_result)

        with_state(mutate)
        return None

    return allow() if event_name.startswith("pre") else None


def emit(payload: dict[str, str] | None) -> None:
    if payload is None:
        return
    sys.stdout.write(json.dumps(payload))
    sys.stdout.write("\n")


def selftest() -> int:
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if not cond:
            failures.append(f"{name}: {detail}" if detail else name)

    check("sleep estimate", estimate_from_command("sleep 12 && echo done") == 12000)
    check("docker estimate", estimate_from_command("docker build -t app .") == 5 * 60 * 1000)
    check("pytest estimate", estimate_from_command("pytest -q") == 2 * 60 * 1000)
    check("default estimate", estimate_from_command("echo hi") == DEFAULT_ESTIMATE_MS)
    check("subagent estimate", estimate_for_start("spawn_subagent", {"prompt": "review"}) == DEFAULT_SUBAGENT_MS)

    fd, path = tempfile.mkstemp(prefix="wait-credit-guard-", suffix=".json")
    os.close(fd)
    os.environ["WAIT_CREDIT_GUARD_STATE"] = path
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"tasks": {}}, fh)

        start_event = {
            "hookEventName": "post_tool_use",
            "toolName": "run_terminal_command",
            "toolInput": {"command": "pytest -q", "background": True},
            "toolResult": {"task_id": "t1"},
        }
        handle_event(start_event)

        first = handle_event(
            {
                "hookEventName": "pre_tool_use",
                "toolName": "get_command_or_subagent_output",
                "toolInput": {"task_ids": ["t1"]},
            }
        )
        check("first snapshot allowed", first == allow(), str(first))

        handle_event(
            {
                "hookEventName": "post_tool_use",
                "toolName": "get_command_or_subagent_output",
                "toolInput": {"task_ids": ["t1"]},
                "toolResult": {"status": "running", "output": "still running"},
            }
        )

        second = handle_event(
            {
                "hookEventName": "pre_tool_use",
                "toolName": "get_command_or_subagent_output",
                "toolInput": {"task_ids": ["t1"]},
            }
        )
        check("tight snapshot denied", second is not None and second.get("decision") == "deny", str(second))
        check("deny mentions timeout", second is not None and "timeout_ms=" in second.get("reason", ""), str(second))

        required = 0
        if second and second.get("reason"):
            match = re.search(r"timeout_ms=(\d+)", second["reason"])
            if match:
                required = int(match.group(1))
        short_wait = handle_event(
            {
                "hookEventName": "pre_tool_use",
                "toolName": "get_command_or_subagent_output",
                "toolInput": {"task_ids": ["t1"], "timeout_ms": max(1, required // 4)},
            }
        )
        check("short wait denied", short_wait is not None and short_wait.get("decision") == "deny", str(short_wait))

        long_wait = handle_event(
            {
                "hookEventName": "pre_tool_use",
                "toolName": "get_command_or_subagent_output",
                "toolInput": {"task_ids": ["t1"], "timeout_ms": max(required, 1)},
            }
        )
        check("backoff wait allowed", long_wait == allow(), str(long_wait))

        handle_event(
            {
                "hookEventName": "post_tool_use",
                "toolName": "get_command_or_subagent_output",
                "toolInput": {"task_ids": ["t1"], "timeout_ms": max(required, 1)},
                "toolResult": {"status": "completed", "exit_code": 0},
            }
        )
        after_done = handle_event(
            {
                "hookEventName": "pre_tool_use",
                "toolName": "get_command_or_subagent_output",
                "toolInput": {"task_ids": ["t1"]},
            }
        )
        check("completed snapshot allowed", after_done == allow(), str(after_done))

        handle_event(
            {
                "hookEventName": "post_tool_use",
                "toolName": "spawn_subagent",
                "toolInput": {"prompt": "review", "background": True},
                "toolResult": {"subagent_id": "s1"},
            }
        )
        handle_event(
            {
                "hookEventName": "post_tool_use",
                "toolName": "get_command_or_subagent_output",
                "toolInput": {"task_id": "s1"},
                "toolResult": "still running",
            }
        )
        denied_sub = handle_event(
            {
                "hookEventName": "pre_tool_use",
                "toolName": "get_command_or_subagent_output",
                "toolInput": {"task_id": "s1"},
            }
        )
        check("subagent backoff", denied_sub is not None and denied_sub.get("decision") == "deny", str(denied_sub))

        handle_event(
            {
                "hookEventName": "post_tool_use",
                "toolName": "kill_command_or_subagent",
                "toolInput": {"task_id": "s1"},
                "toolResult": {"success": True},
            }
        )
        after_kill = handle_event(
            {
                "hookEventName": "pre_tool_use",
                "toolName": "get_command_or_subagent_output",
                "toolInput": {"task_id": "s1"},
            }
        )
        check("killed task allowed", after_kill == allow(), str(after_kill))

        # Geometric growth of stored interval across successive running polls.
        handle_event(
            {
                "hookEventName": "post_tool_use",
                "toolName": "run_terminal_command",
                "toolInput": {"command": "sleep 90", "background": True},
                "toolResult": {"task_id": "geom"},
            }
        )
        intervals = []
        for _ in range(5):
            handle_event(
                {
                    "hookEventName": "post_tool_use",
                    "toolName": "get_command_or_subagent_output",
                    "toolInput": {"task_id": "geom"},
                    "toolResult": {"status": "running"},
                }
            )
            with open(path, encoding="utf-8") as fh:
                intervals.append(json.load(fh)["tasks"]["geom"]["interval_ms"])
        check("geom start", intervals[0] == 90_000, str(intervals))
        check("geom second", intervals[1] == 180_000, str(intervals))
        check("geom third", intervals[2] == 360_000, str(intervals))
        check("geom fourth", intervals[3] == 720_000 if False else intervals[3] == CAP_MS, str(intervals))
        check("geom cap", intervals[4] == CAP_MS, str(intervals))
    finally:
        for suffix in ("", ".tmp", ".lock"):
            try:
                os.remove(path + suffix if suffix else path)
            except OSError:
                pass
        os.environ.pop("WAIT_CREDIT_GUARD_STATE", None)

    if failures:
        sys.stderr.write("SELFTEST FAILED\n")
        for item in failures:
            sys.stderr.write(f"  - {item}\n")
        return 1
    sys.stdout.write("SELFTEST OK\n")
    return 0


def main(argv: list[str]) -> int:
    if argv and argv[0] in {"--selftest", "selftest"}:
        return selftest()
    raw = sys.stdin.read()
    if not raw.strip():
        emit(allow())
        return 0
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        emit(allow())
        return 0
    if not isinstance(event, dict):
        emit(allow())
        return 0
    try:
        emit(handle_event(event))
    except Exception as exc:  # fail-open: never brick tool use
        sys.stderr.write(f"wait-credit-guard error: {exc}\n")
        emit(allow())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
