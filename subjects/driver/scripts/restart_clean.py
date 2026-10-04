#!/usr/bin/env python3
"""一键清理重启驾考：停掉旧实例 → flutter clean → 经启动器重新打开 → 轮询到就绪。

热重载只替换已加载的 Dart 代码，改了原生插件、资源清单或 pubspec 之后想确认
「跑的是最新的」，就用这个。用 Python 而不是 shell（ADR 0047），三个平台同一份。

用法：
    python3 scripts/restart_clean.py
    python3 scripts/restart_clean.py --no-clean   # 只重启，不清构建缓存
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from run_dev import flutter_bin

APP_ID = "driver"
APP_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = APP_ROOT.parent.parent
LAUNCHER_DIR = REPO_ROOT / "launcher"

# Windows 的 Debug 全量构建实测约 76 秒，留足余量；超时多半是构建失败，看日志尾部。
READY_TIMEOUT_S = 600
STOP_TIMEOUT_S = 30
POLL_S = 3


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def launcher_bin() -> Path:
    """优先已编好的 release，其次 debug；都没有就现编一份（机器是完整开发机，ADR 0057）。

    不用 PATH 里的 `launcher`：JetBrains 的 IDE 会带一个同名程序。
    """
    exe = "launcher.exe" if sys.platform == "win32" else "launcher"
    for profile in ("release", "debug"):
        candidate = LAUNCHER_DIR / "target" / profile / exe
        if candidate.is_file():
            return candidate
    print("[准备] 还没有编好的启动器，先 cargo build --release", flush=True)
    subprocess.run(
        ["cargo", "build", "--release", "-p", "launcher-core"],
        cwd=LAUNCHER_DIR,
        check=True,
    )
    return LAUNCHER_DIR / "target" / "release" / exe


def app_row(launcher: Path) -> dict:
    """从 `list --json` 取驾考这一行。状态认稳定的 key，不解析中文 label（ADR 0048）。"""
    out = subprocess.run(
        [str(launcher), "list", "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout
    for row in json.loads(out):
        if row["id"] == APP_ID:
            return row
    raise SystemExit(f"启动器清单里没有 {APP_ID}")


def state(launcher: Path) -> str:
    return app_row(launcher)["state"]


def stop(launcher: Path) -> None:
    subprocess.run([str(launcher), "stop", APP_ID], cwd=REPO_ROOT)
    # 窗口进程退出前，Windows 会锁住 build/ 里的 exe 和 dll，flutter clean 删不掉。
    deadline = time.monotonic() + STOP_TIMEOUT_S
    while state(launcher) != "stopped":
        if time.monotonic() > deadline:
            raise SystemExit(f"{STOP_TIMEOUT_S} 秒内没停下来，请手动关闭驾考窗口后重试")
        time.sleep(1)


def clean() -> None:
    subprocess.run([flutter_bin(), "clean"], cwd=APP_ROOT, check=True)


def log_tail(log: str, lines: int = 40) -> str:
    try:
        text = Path(log).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "（读不到日志）"
    return "\n".join(text.splitlines()[-lines:])


def open_and_wait(launcher: Path) -> int:
    # 启动器拉起的应用会继承我们的 stdout；如果那是管道（`| tee`、CI、被别的程序调用），
    # 应用不退出管道就收不到 EOF，调用方会一直等。输出落到临时文件，再自己打印。
    with tempfile.TemporaryFile() as sink:
        subprocess.run(
            [str(launcher), "open", APP_ID],
            cwd=REPO_ROOT,
            stdin=subprocess.DEVNULL,
            stdout=sink,
            stderr=subprocess.STDOUT,
            check=True,
        )
        sink.seek(0)
        print(sink.read().decode("utf-8", errors="replace"), end="", flush=True)
    deadline = time.monotonic() + READY_TIMEOUT_S
    seen_starting = False
    while time.monotonic() < deadline:
        row = app_row(launcher)
        print(f"{time.strftime('%H:%M:%S')} state={row['state']}", flush=True)
        if row["state"] == "ready":
            print("READY", flush=True)
            return 0
        if row["state"] == "starting":
            seen_starting = True
        elif seen_starting:
            # 构建过程中曾是「启动中」，现在又回到「未运行」：构建或启动失败了。
            print(f"启动失败，日志 {row['log']} 末尾：\n{log_tail(row['log'])}", flush=True)
            return 1
        time.sleep(POLL_S)
    row = app_row(launcher)
    print(f"TIMEOUT，日志 {row['log']} 末尾：\n{log_tail(row['log'])}", flush=True)
    return 1


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-clean", action="store_true", help="只重启，不 flutter clean")
    args = parser.parse_args()

    print(f"===== {time.strftime('%c')} 重启驾考 =====", flush=True)
    launcher = launcher_bin()
    stop(launcher)
    if args.no_clean:
        print("[跳过] flutter clean", flush=True)
    else:
        clean()
        print("CLEAN_OK", flush=True)
    return open_and_wait(launcher)


if __name__ == "__main__":
    raise SystemExit(main())
