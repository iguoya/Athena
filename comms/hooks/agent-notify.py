#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Athena 协作通讯钩子（ADR 0181）：会话注册 + 按订阅投递。

行为（ZCode / Claude Code 的 payload 带 session_id）：
- SessionStart / UserPromptSubmit：`session touch`（登记与心跳）→ `deliver`（本会话
  订阅内的未读**全文**注入，自动标记已投递，无需 ack）。operator / mute 会话零注入。
- 拿不到 session_id（如 Cursor 的 beforeSubmitPrompt）时降级为旧的逐舱摘要提醒，
  行为与 ADR 0165 时代一致，不影响使用。

接线（命令行签名与 0165 时代完全一致，升级无需改任何接线文件）：
    python comms/hooks/agent-notify.py --agent zcode        # ZCode   .zcode/config.json
    python comms/hooks/agent-notify.py --agent claude-code  # Claude  .claude/settings.json
    python comms/hooks/agent-notify.py --agent cursor       # Cursor  .cursor/hooks.json

会话的订阅与静音由代理或使用者用 session 命令声明：
    python comms/comms.py session touch --agent zcode --sid <session_id> --role operator
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Windows 控制台默认 GBK，钩子 JSON 必须 UTF-8
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOOL = Path(__file__).resolve().parents[1] / "comms.py"
COMMS_ROOT = TOOL.parents[1] / "comms"
NO_WINDOW = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW，子进程不闪控制台窗


def comms(args: list[str], timeout: int = 10) -> str:
    try:
        done = subprocess.run(
            [sys.executable, str(TOOL), *args],
            cwd=str(TOOL.parents[1]), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, creationflags=NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return (done.stdout or "").strip()


def legacy_notify(project: str, agent: str) -> str:
    out = comms(["--project", project, "notify", agent])
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
    agent = args.agent
    sid = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("session_id") or ""))[:8]

    parts: list[str] = []
    if len(sid) >= 4 and COMMS_ROOT.is_dir():
        # 会话路径：登记/心跳 + 按订阅投递全文。touch 或 deliver 失败（输出为空且非静音）
        # 时不阻塞会话——静默即可，代理随时可用 triage 主动查收。
        comms(["session", "touch", "--agent", agent, "--sid", sid], timeout=15)
        delivered = comms(["deliver", "--agent", agent, "--sid", sid], timeout=15)
        if delivered:
            parts.append(delivered)
    elif COMMS_ROOT.is_dir():
        # 降级路径（无会话标识）：逐舱摘要提醒，ADR 0165 行为。
        for cfg in sorted(COMMS_ROOT.glob("*/config.json")):
            text = legacy_notify(cfg.parent.name, agent)
            if text:
                parts.append(text)

    out: dict = {}
    if parts:
        text = "\n".join(parts)
        if not parts[0].startswith("【Athena 协作·会话投递】"):
            text = ("【Athena 协作通讯·未读提醒】正式收件箱与即时 chat 并行；"
                    "手头告一段落再处理，标题带「紧急」的才打断。\n" + text +
                    f"\n查看：python comms/comms.py triage {agent}")
    # 注意：Claude / ZCode 的 UserPromptSubmit 小写后同样含 submit，不能拿子串判断；
    # Cursor 的事件名就是 beforeSubmitPrompt，精确比对。
    cursor_submit = event == "beforeSubmitPrompt"
    if cursor_submit:
        out["continue"] = True
        if parts:
            out["additional_context"] = text  # Cursor 协议（下划线键）
    elif parts:
        # Claude Code / ZCode（UserPromptSubmit、SessionStart）：驼峰键注入上下文。
        # 两家的输出 schema 都很严（多余键会丢掉整个输出），所以这个分支不带 continue。
        out["additionalContext"] = text
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
