#!/usr/bin/env python3
"""nas-admin 的验证入口：依赖就绪 + smoke 测试。

    python3 scripts/check.py            # 仓库根或本目录执行均可

首次运行自动建 .venv 装依赖；之后用 .venv 里的 Python 重入自身，
用 Flask test_client 打 /api/health 与 /login/ 两个端点。

用 Python 而不是 shell：验证三平台都要能跑（ADR 0047）。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))


def _force_utf8_output() -> None:
    """Windows 控制台默认不是 UTF-8，打印中文会抛 UnicodeEncodeError（ADR 0047）。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def _in_venv() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def _venv_python() -> Path:
    import os

    candidate = APP_ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return candidate


def main() -> int:
    _force_utf8_output()
    if not _in_venv():
        venv = _venv_python()
        if not venv.is_file():
            print("== 首次运行：创建虚拟环境并安装依赖 ==", flush=True)
            code = subprocess.run([sys.executable, "scripts/run_dev.py", "bootstrap"], cwd=APP_ROOT).returncode
            if code != 0:
                return code
        print("== 用 .venv 重入运行 smoke ==", flush=True)
        return subprocess.run([str(venv), Path(__file__).resolve()], cwd=APP_ROOT).returncode

    print("== smoke：导入应用并用 test_client 打端点 ==", flush=True)
    from app import app as flask_app

    client = flask_app.test_client()

    health = client.get("/api/health")
    assert health.status_code == 200, f"/api/health 状态码 {health.status_code}"
    payload = health.get_json()
    assert payload.get("ok") is True, f"/api/health 返回 {payload}"

    login = client.get("/login/")
    assert login.status_code == 200, f"/login/ 状态码 {login.status_code}"

    index = client.get("/")
    assert index.status_code == 200, f"/ 状态码 {index.status_code}"

    # 仪表盘页面是纯壳（ADR 0069）：不查库也必须能出，数据端点降级由测试覆盖。
    driver_page = client.get("/driver/")
    assert driver_page.status_code == 200, f"/driver/ 状态码 {driver_page.status_code}"

    print(f"smoke OK：/api/health ok=true，/login/、/ 与 /driver/ 均 200，database={payload['database']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
