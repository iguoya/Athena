#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Athena 多舱未读提醒钩子（ADR 0165）。

接线（以 Cursor 为例，.cursor/hooks.json）：
    {"version": 1, "hooks": {"sessionStart": [
        {"command": "python comms/hooks/agent-notify.py --agent cursor", "timeout": 15}]}}

行为：
- 扫描 comms/*/config.json 的所有舱，逐舱调用 comms.py notify；
- 无未读：静默（beforeSubmitPrompt 只回 continue）；
- 有未读：把摘要注入 additional_context，不打断、不自动 ack。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Windows 控制台默认 GBK，钩子 JSON 必须 UTF-8
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOOL = Path(__file__).resolve().parents[1] / "comms.py"
COMMS_ROOT = TOOL.parents[1] / "comms"


def notify_for(project: str, agent: str) -> str:
    try:
        done = __import__("subprocess").run(
            [sys.executable, str(TOOL), "--project", project, "notify", agent],
            cwd=str(TOOL.parents[1]),
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=8,
        )
    except (OSError, __import__("subprocess").TimeoutExpired):
        return ""
    out = (done.stdout or "").strip()
    return f"『{project}』{out}" if out else ""


def main() -> int:
    raw = sys.stdin.read()  # 读掉 stdin，避免管道堵塞
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    event = str(payload.get("hook_event_name") or payload.get("event") or "")

    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default=os.environ.get("ATHENA_COMMS_AGENT", "cursor"))
    args, _ = ap.parse_known_args()

    parts = []
    if COMMS_ROOT.is_dir():
        for cfg in sorted(COMMS_ROOT.glob("*/config.json")):
            text = notify_for(cfg.parent.name, args.agent)
            if text:
                parts.append(text)

    out: dict = {}
    if "submit" in event.lower() or event == "beforeSubmitPrompt":
        out["continue"] = True
    if parts:
        out["additional_context"] = (
            "【Athena 协作通讯·未读提醒】正式收件箱与即时 chat 并行；"
            "手头告一段落再处理，标题带「紧急」的才打断。\n" + "\n".join(parts) + "\n"
            f"查看：python comms/comms.py inbox {args.agent} --project <舱名>"
        )
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
