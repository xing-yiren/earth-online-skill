"""Smoke test for cross-session task scanner."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    tmpdir = Path(tempfile.mkdtemp())
    data_root = tmpdir / "data"
    _copy_seed_data(data_root)

    sessions_root = tmpdir / "sessions" / "test-project"
    sessions_root.mkdir(parents=True)
    _write_session(sessions_root / "session_01.jsonl", [
        {"type": "user", "isMeta": False, "message": {"role": "user", "content": "我需要整理项目开发计划，包括里程碑和时间节点"}},
        {"type": "user", "isMeta": True, "message": {"role": "user", "content": "/clear"}},
        {"type": "user", "isMeta": False, "message": {"role": "user", "content": "每天阅读30分钟技术文章"}},
    ])
    _write_session(sessions_root / "session_02.jsonl", [
        {"type": "user", "isMeta": False, "message": {"role": "user", "content": "今天要修复登录页面的样式bug"}},
        {"type": "user", "isMeta": False, "message": {"role": "user", "content": "好的"}},
        {"type": "user", "isMeta": False, "message": {"role": "user", "content": "行"}},
    ])

    env = dict(os.environ)
    env["EARTH_ONLINE_DATA_ROOT"] = str(data_root)
    env["PYTHONIOENCODING"] = "utf-8"
    env["_EO_SESSION_SCAN_ROOT_OVERRIDE"] = str(sessions_root.parent)

    tool_path = ROOT / "scripts" / "tools" / "scan_sessions.py"

    # Step 1: call without confirmation - should ask for permission
    no_confirm = _run_tool(tool_path, {"render": True}, env)
    _assert(no_confirm.get("error") == "confirmation_required", "must require confirmation")
    _assert("message" in no_confirm, "must include confirmation message")

    # Step 2: call with confirmation - should return candidates
    confirmed = _run_tool(tool_path, {"confirmed_by_user": True, "render": True}, env)
    _assert(confirmed.get("success"), f"scan should succeed, got: {confirmed}")
    _assert(confirmed.get("count", 0) >= 2, f"should find at least 2 candidates, got {confirmed.get('count')}")
    _assert("message" in confirmed, "must include rendered message")

    names = {c["name"] for c in confirmed.get("candidates", [])}
    _assert("整理项目开发计划" in names or any("整理项目开发计划" in c.get("raw_text", "") for c in confirmed.get("candidates", [])), f"should find plan task in candidates: {names}")
    _assert("每天阅读30分钟技术文章" in names or any("每天阅读30分钟" in c.get("raw_text", "") for c in confirmed.get("candidates", [])), f"should find reading habit: {names}")

    # Step 3: verify scan does not write any runtime data
    tasks_path = data_root / "tasks.json"
    if tasks_path.exists():
        tasks_state = json.loads(tasks_path.read_text(encoding="utf-8"))
        _assert(tasks_state.get("task_counter", 0) == 0, "scan must not create tasks")

    print(json.dumps({"success": True, "candidate_count": confirmed.get("count")}, ensure_ascii=False, indent=2))


def _run_tool(tool_path: Path, payload: dict, env: dict) -> dict:
    completed = subprocess.run(
        [sys.executable, str(tool_path), json.dumps(payload, ensure_ascii=False)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)


def _copy_seed_data(data_root: Path) -> None:
    seed = ROOT / "examples" / "seed-data"
    data_root.mkdir(parents=True, exist_ok=True)
    for path in seed.iterdir():
        if path.is_file():
            shutil.copy2(path, data_root / path.name)


def _write_session(path: Path, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    main()
