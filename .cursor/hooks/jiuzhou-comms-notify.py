#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""九州双通道提醒钩子：正式收件箱 + 即时 chat 并行。

Cursor hooks（sessionStart / beforeSubmitPrompt）调用本脚本。
- 无未读：静默（beforeSubmitPrompt 只回 continue）
- 有未读：把 ≤3 行摘要注入 additional_context，不打断、不自动 ack
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# Windows 控制台默认 GBK，钩子 JSON 必须 UTF-8
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
COMMS = ROOT / "comms" / "comms.py"
AGENT = "cursor"
PROJECT = "jiuzhou"
NO_WINDOW = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW，comms.py 子进程不闪控制台窗


def notify_text() -> str:
    if not COMMS.is_file():
        return ""
    try:
        completed = subprocess.run(
            [sys.executable, str(COMMS), "notify", AGENT, "--project", PROJECT],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
            creationflags=NO_WINDOW,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return (completed.stdout or "").strip()


def main() -> int:
    # 读掉 stdin，避免管道堵塞；事件类型不影响静默策略
    raw = sys.stdin.read()
    event = ""
    try:
        payload = json.loads(raw) if raw.strip() else {}
        event = str(payload.get("hook_event_name") or payload.get("event") or "")
    except json.JSONDecodeError:
        payload = {}

    text = notify_text()
    out: dict = {}

    # beforeSubmitPrompt 需要 continue
    if "submit" in event.lower() or event == "beforeSubmitPrompt":
        out["continue"] = True

    if text:
        urgent = "紧急" in text
        when = (
            "标题或正文带「紧急」：请打断当前手头优先处理。"
            if urgent
            else "手头告一段落再处理；标题带「紧急」的才打断。"
        )
        out["additional_context"] = (
            "【九州双通道·未读提醒】正式收件箱与即时 chat 并行。"
            f"{when}\n"
            f"{text}\n"
            "即时：python comms/comms.py chat cursor --project jiuzhou\n"
            "正式：python comms/comms.py inbox cursor --project jiuzhou\n"
            "快回：python comms/comms.py say --from cursor --to claude-code \"…\" --project jiuzhou\n"
            "线程：python comms/comms.py reply <消息片段> --from cursor --body \"…\" --project jiuzhou"
        )

    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
