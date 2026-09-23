#!/usr/bin/env python3
"""按当前平台调用 flutter。找不到 PATH 里的 SDK 时，再试 ~/flutter。

无参数：一律 `flutter run`（改 Dart 热重载，改 JSON 热重启）。启动器拉起时
stdin 不是 TTY，而且编排器返回后会关掉继承来的 stdin——必须自己拿伪终端，
否则 resident runner 收到 EOF 就退出，看起来像「每次都要冷启动」。
有参数：原样转给 flutter，例如 pub get / analyze。
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import threading
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
MACOS_XCODE_DEVELOPER = Path("/Applications/Xcode.app/Contents/Developer")


def flutter_bin() -> str:
    found = shutil.which("flutter")
    if found:
        return found
    name = "flutter.bat" if os.name == "nt" else "flutter"
    candidate = Path.home() / "flutter" / "bin" / name
    if candidate.is_file():
        return str(candidate)
    raise SystemExit("找不到 flutter。把 SDK 放进 PATH，或安装到 ~/flutter。")


def flutter_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("ATHENA_DRIVER_ROOT", str(APP_ROOT))
    apply_macos_xcode(env)
    return env


def apply_macos_xcode(env: dict[str, str]) -> None:
    """本机常把 xcode-select 指到 Command Line Tools；Flutter 编 macOS 窗口要完整 Xcode。

    不改系统默认（那需要 sudo），只给这一次启动设 DEVELOPER_DIR。
    """
    if sys.platform != "darwin":
        return
    developer = Path(env["DEVELOPER_DIR"]) if env.get("DEVELOPER_DIR") else MACOS_XCODE_DEVELOPER
    xcodebuild = developer / "usr/bin/xcodebuild"
    if not xcodebuild.is_file():
        return
    env.setdefault("DEVELOPER_DIR", str(developer))
    xcode_bin = str(developer / "usr/bin")
    path = env.get("PATH", "")
    parts = path.split(os.pathsep) if path else []
    if xcode_bin not in parts:
        env["PATH"] = os.pathsep.join([xcode_bin, *parts])


def desktop_device() -> str:
    mapping = {"Darwin": "macos", "Windows": "windows", "Linux": "linux"}
    system = platform.system()
    if system not in mapping:
        raise SystemExit(f"没有为 {system} 配置桌面设备")
    return mapping[system]


def run_resident(flutter: str, device: str, env: dict[str, str]) -> int:
    args = [flutter, "run", "-d", device]
    print(f"[启动] flutter run -d {device}（热重载）", flush=True)
    if sys.platform == "win32":
        return subprocess.call(
            args,
            cwd=APP_ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )

    import pty

    master, slave = pty.openpty()
    try:
        proc = subprocess.Popen(
            args,
            cwd=APP_ROOT,
            env=env,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            close_fds=True,
            start_new_session=True,
        )
    finally:
        os.close(slave)

    def drain() -> None:
        try:
            while True:
                chunk = os.read(master, 4096)
                if not chunk:
                    break
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()
        except OSError:
            pass

    threading.Thread(target=drain, daemon=True).start()
    try:
        return proc.wait()
    finally:
        try:
            os.close(master)
        except OSError:
            pass


def main(argv: list[str]) -> int:
    flutter = flutter_bin()
    env = flutter_env()
    if sys.platform == "darwin" and env.get("DEVELOPER_DIR"):
        print(f"[工具链] DEVELOPER_DIR={env['DEVELOPER_DIR']}", flush=True)
    if argv:
        return subprocess.call([flutter, *argv], cwd=APP_ROOT, env=env)
    return run_resident(flutter, desktop_device(), env)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
