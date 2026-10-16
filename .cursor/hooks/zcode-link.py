#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨会话长效通道：driver 与 comms-console 上跟 zcode 的未读。

- sessionStart / beforeSubmitPrompt：注入未读，并保证常驻监听在跑。
- stop：若这两舱仍有未读，用 followup_message 把当前会话拉回来回复。
  九州舱不在此列，避免每个会话都被拉去做别的舱的事。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
COMMS = ROOT / "comms" / "comms.py"
POLLER = Path(__file__).with_name("zcode-link-poll.py")
STATE = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Athena" / "zcode-link"
PID_FILE = STATE / "poll.pid"
LOG_FILE = STATE / "poll.log"
PROJECTS = ("driver", "comms-console")
NO_WINDOW = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW，comms.py 子进程不闪控制台窗


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not h:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return code.value == 259
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def ensure_poller() -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    if PID_FILE.is_file():
        try:
            pid = int(PID_FILE.read_text(encoding="utf-8").strip())
        except ValueError:
            pid = 0
        if pid_alive(pid):
            return
    flags = 0
    if os.name == "nt":
        flags = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED | NEW_GROUP | NO_WINDOW
    log = LOG_FILE.open("a", encoding="utf-8")
    subprocess.Popen(
        [sys.executable, str(POLLER)],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        close_fds=True,
        creationflags=flags,
    )


def notify_all() -> str:
    parts = []
    for project in PROJECTS:
        try:
            done = subprocess.run(
                [sys.executable, str(COMMS), "notify", "cursor", "--project", project],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=8,
                creationflags=NO_WINDOW,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        text = (done.stdout or "").strip()
        if text:
            parts.append(f"『{project}』\n{text}")
    return "\n".join(parts)


def main() -> int:
    raw = sys.stdin.read()
    event = ""
    try:
        payload = json.loads(raw) if raw.strip() else {}
        event = str(payload.get("hook_event_name") or payload.get("event") or "")
    except json.JSONDecodeError:
        payload = {}
    try:
        ensure_poller()
    except OSError:
        pass
    text = notify_all()
    out: dict = {}
    low = event.lower()
    if "submit" in low or event == "beforeSubmitPrompt":
        out["continue"] = True
    if text and event == "stop":
        out["followup_message"] = (
            "【zcode 长效通道】driver 或 comms-console 有未读。先读再回，不要结束联系。\n"
            f"{text}\n"
            "短回：python comms/comms.py say --from cursor --to zcode \"…\" --project <舱>\n"
            "正式：python comms/comms.py inbox cursor --project <舱>，读完 ack。"
        )
    elif text:
        out["additional_context"] = (
            "【zcode 长效通道】跨会话有效：换聊天、监听超时都不等于断线。"
            "这两舱的未读要读完并回复。标题带「紧急」才打断手头的活。\n"
            f"{text}\n"
            "短回：python comms/comms.py say --from cursor --to zcode \"…\" --project <舱>\n"
            "正式：python comms/comms.py inbox cursor --project <舱>"
        )
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
