"""math-tools 应用级验证:app.json 合法性 + 前端类型检查 + 前端构建。

依赖未安装(node_modules 缺失)时明确跳过并提示,不静默失败。
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check_app_json() -> None:
    app = json.loads((ROOT / "app.json").read_text(encoding="utf-8"))
    expected_id = "math-tools"
    if app.get("id") != expected_id:
        raise SystemExit(f"app.json id 应为 {expected_id},实际 {app.get('id')}")
    dev = app.get("dev", {})
    if dev.get("binary") != f"athena-{expected_id}":
        raise SystemExit("app.json dev.binary 应为 athena-math-tools")
    port = dev.get("ready", {}).get("http", "")
    if ":1451" not in port:
        raise SystemExit(f"app.json dev.ready.http 应指向 1451 端口,实际 {port}")
    print("ok: app.json")


def run_npm(args: list[str]) -> None:
    npm = shutil.which("npm")
    if npm is None:
        raise SystemExit("找不到 npm,请先安装 Node.js")
    proc = subprocess.run([npm, *args], cwd=ROOT)
    if proc.returncode != 0:
        raise SystemExit(f"npm {args[0]} 失败")


def main() -> int:
    check_app_json()

    if not (ROOT / "node_modules").exists():
        print("skip: 前端依赖未安装(node_modules 缺失),先运行 npm install")
        return 0

    run_npm(["run", "typecheck"])
    print("ok: vue-tsc 类型检查")
    run_npm(["run", "build"])
    print("ok: vite build")
    return 0


if __name__ == "__main__":
    sys.exit(main())
