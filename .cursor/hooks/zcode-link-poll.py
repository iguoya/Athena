#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""常驻监听 comms 舱的文件事件，有变动才查未读。进程掉了由 zcode-link.py 在下次会话拉起。

依赖 watchdog（换机器先 `pip install watchdog`）；缺失时后台自动安装，期间降级低频
轮询，装好即切回事件监听，无需重启。

未读只由 <舱>/msgs、<舱>/chat、<舱>/read 三处的文件变动决定，watchdog 监听舱根目录、
按路径第一段过滤；事件只当「该查了」的信号，检查永远是全量的，丢事件无害。
监听模式另留兜底轮询，兜住内核缓冲溢出等丢事件的情况。
只追加「摘要发生变化」的行，避免同一条未读刷屏。不标记已读。
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
COMMS = ROOT / "comms" / "comms.py"
STATE = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Athena" / "zcode-link"
PID_FILE = STATE / "poll.pid"
LOG_FILE = STATE / "poll.log"
PROJECTS = ("driver", "comms-console")
# 未读相关的子目录；监听整个舱根，只对这些目录的事件做检查
LISTEN_DIRS = {"msgs", "chat", "read"}
NO_WINDOW = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW，子进程不闪控制台窗
MIN_INTERVAL = 2.0  # 两次检查的最小间隔，写一波文件（原子替换是多条事件）只查一次
FALLBACK = 60.0  # 监听模式下多久没有事件也强制查一轮
POLL_FALLBACK = 30.0  # 无 watchdog 时的降级轮询间隔

_LAST_CHECK = 0.0


def check(project: str) -> str:
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
        return ""
    return (done.stdout or "").strip()


def emit(text: str) -> None:
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(text + "\n")


def check_all(last: dict[str, str]) -> None:
    global _LAST_CHECK
    _LAST_CHECK = time.monotonic()
    for project in PROJECTS:
        text = check(project)
        if text == last.get(project, ""):
            continue
        last[project] = text
        if not text:
            continue
        emit(time.strftime("%Y-%m-%d %H:%M:%S") + f" [{project}]\n" + text)


def run_watchdog(last: dict[str, str]) -> None:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    wake = threading.Event()

    class InboxEvents(FileSystemEventHandler):
        def on_any_event(self, event):
            path = getattr(event, "dest_path", None) or getattr(event, "src_path", "")
            if not path:
                return
            try:
                top = Path(path).relative_to(ROOT / "comms").parts
            except ValueError:
                return
            if len(top) > 1 and top[0] in PROJECTS and top[1] in LISTEN_DIRS:
                wake.set()

    observer = Observer()
    for project in PROJECTS:
        home = ROOT / "comms" / project
        if home.is_dir():
            observer.schedule(InboxEvents(), str(home), recursive=True)
    observer.daemon = True
    observer.start()
    emit(f"—— poller 启动：watchdog 监听 {', '.join(PROJECTS)}（pid={os.getpid()}）——")

    check_all(last)
    while True:
        wake.wait(timeout=FALLBACK)  # 既是事件唤醒，也是兜底轮询的计时
        wake.clear()
        gap = MIN_INTERVAL - (time.monotonic() - _LAST_CHECK)
        if gap > 0:
            time.sleep(gap)
            wake.clear()  # 防抖窗口内积压的置位丢掉，这轮全量检查会看到全部变化
        check_all(last)


def install_watchdog_bg() -> threading.Event:
    """后台安装 watchdog，装好且可导入后置位返回的 Event。

    离线或安装失败就留在低频轮询，不重试——下次进程被拉起时再试。
    """
    ok = threading.Event()

    def work():
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet", "watchdog"],
                capture_output=True, timeout=300, creationflags=NO_WINDOW,
            )
            importlib.invalidate_caches()
            import watchdog  # noqa: F401
            ok.set()
        except Exception:
            pass

    threading.Thread(target=work, daemon=True).start()
    return ok


def run_polling(last: dict[str, str], upgraded: threading.Event) -> None:
    emit(f"—— poller 启动：无 watchdog，先降级 {POLL_FALLBACK:.0f}s 轮询，"
         f"后台安装后自动切换（pid={os.getpid()}）——")
    while not upgraded.wait(POLL_FALLBACK):
        check_all(last)
    emit("—— watchdog 就绪，切换事件监听——")


def main() -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    last: dict[str, str] = {}
    try:
        import watchdog  # noqa: F401

        run_watchdog(last)
        return 0
    except ImportError:
        pass
    run_polling(last, install_watchdog_bg())
    run_watchdog(last)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
