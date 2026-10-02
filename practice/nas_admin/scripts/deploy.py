#!/usr/bin/env python3
"""把本目录部署到软路由的 /opt/webapp 并重启服务——两边由此「关联」：

    本机 practice/nas_admin（唯一源）
        └─ python3 scripts/deploy.py
              ├─ 打包（tarfile，排除 .venv/__pycache__/db-local.json，
              │  连接串由部署脚本在路由器上单独写，凭据不进 tar）
              ├─ ssh 标准输入写文件上传（dropbear 没有 sftp-server，
              │  scp -O 在 Windows OpenSSH 下行为不稳，管道最省心）
              ├─ 远程备份 /opt/webapp → /opt/webapp.bak-<时间戳>
              ├─ 远程解包覆盖 + pip3 install -r requirements.txt
              ├─ 首次部署（PG 里还没有 ab_user 表）时 flask fab create-admin
              ├─ /etc/init.d/webapp restart
              └─ curl /api/health 验证 ok:true

用法：
    python3 scripts/deploy.py [--host root@192.168.6.1]

凭据（ADR 0068）都不进仓库：数据库连接串从环境变量 NAS_ADMIN_DATABASE_URL
或本目录 db-local.json 读，部署时写到路由器 /opt/webapp/db-local.json（600）；
后台管理员密码只从环境变量 NAS_ADMIN_ADMIN_PASSWORD 读（首次建号用）。
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import tarfile
import time
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
REMOTE_DIR = "/opt/webapp"
EXCLUDED_TOP = {".venv", "data", "__pycache__", ".git", ".gitignore", "scripts"}
EXCLUDED_ROOT_FILES = {"db-local.json"}
EXCLUDED_SUFFIX = (".pyc", ".tar")


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def build_tar() -> bytes:
    """打进内存。EXCLUDED_TOP 里的 scripts/ 不部署——路由器上不需要开发脚本；
    data/ 是运行数据，部署永不触碰；db-local.json 含连接串，绝不进包。"""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for path in sorted(APP_ROOT.rglob("*")):
            rel = path.relative_to(APP_ROOT)
            if rel.parts[0] in EXCLUDED_TOP:
                continue
            if rel.parts[0] in EXCLUDED_ROOT_FILES:
                continue
            if any(part == "__pycache__" for part in rel.parts):
                continue
            if rel.suffix in EXCLUDED_SUFFIX:
                continue
            tar.add(path, arcname=str(rel))
    return buffer.getvalue()


def run(command: list[str], step: str, remote: str | None = None) -> str:
    print(f"[{step}] {'@' + remote if remote else ''} {' '.join(command[:4])}…", flush=True)
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.returncode != 0:
        print(completed.stdout, end="")
        print(completed.stderr, end="", file=sys.stderr)
        raise SystemExit(f"[{step}] 失败（退出码 {completed.returncode}）")
    return completed.stdout


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="部署 nas-admin 到软路由 /opt/webapp")
    parser.add_argument("--host", default="root@192.168.6.1", help="SSH 目标（默认 root@192.168.6.1）")
    args = parser.parse_args()
    host = args.host

    payload = build_tar()
    print(f"[打包] {len(payload) / 1024:.1f} KiB", flush=True)
    try:
        # 不走 scp（dropbear 没有 sftp-server，scp -O 在 Windows OpenSSH 下行为
        # 不稳）：直接用 ssh 标准输入把 tar 写过去，跨平台一致。
        print(f"[上传] @{host} ssh cat > /tmp/nas-admin-deploy.tar.gz", flush=True)
        upload = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", host, "cat > /tmp/nas-admin-deploy.tar.gz"],
            input=payload,
            capture_output=True,
        )
        if upload.returncode != 0:
            print(upload.stderr.decode(errors="replace"), file=sys.stderr)
            raise SystemExit(f"[上传] 失败（退出码 {upload.returncode}）")

        stamp = time.strftime("%Y%m%d-%H%M%S")
        # 凭据不进仓库：数据库连接串从 db-local.json（或环境变量）来，
        # 后台管理员密码只从环境变量来，都没有就拒绝部署（ADR 0068）。
        db_url = os.environ.get("NAS_ADMIN_DATABASE_URL")
        if not db_url:
            local_config = APP_ROOT / "db-local.json"
            if local_config.is_file():
                db_url = str(json.loads(local_config.read_text(encoding="utf-8"))["url"])
        if not db_url:
            raise SystemExit("缺数据库连接串：设 NAS_ADMIN_DATABASE_URL 或建 db-local.json")
        admin_password = os.environ.get("NAS_ADMIN_ADMIN_PASSWORD")
        if not admin_password:
            raise SystemExit("缺后台管理员密码：部署时设 NAS_ADMIN_ADMIN_PASSWORD（首次建号用，之后可省）")
        remote_script = f"""set -e
[ -d {REMOTE_DIR} ] && cp -a {REMOTE_DIR} {REMOTE_DIR}.bak-{stamp} || true
mkdir -p {REMOTE_DIR}
tar -xzf /tmp/nas-admin-deploy.tar.gz -C {REMOTE_DIR}
pip3 install --no-cache-dir -r {REMOTE_DIR}/requirements.txt
printf '%s' '{db_url}' > {REMOTE_DIR}/db-local.json
chmod 600 {REMOTE_DIR}/db-local.json
HAS_USERS=$(psql '{db_url}' -tAc \\
  "SELECT 1 FROM information_schema.tables WHERE table_name='ab_user'" || true)
if [ "$HAS_USERS" != "1" ]; then
  cd {REMOTE_DIR} && python3 -m flask --app app fab create-admin \\
    --username admin --firstname Admin --lastname NAS --email admin@nas.local \\
    --password '{admin_password}'
fi
/etc/init.d/webapp restart
sleep 3
curl -s -m 10 http://127.0.0.1:5000/api/health
"""
        output = run(
            ["ssh", "-o", "ConnectTimeout=10", host, remote_script],
            "远程部署",
            remote=host,
        )
        print(output.strip(), flush=True)
        if '"ok":true' not in output.replace(" ", ""):
            raise SystemExit("部署后 /api/health 未返回 ok:true，请上路由器查日志：logread | grep webapp")
        print("部署完成，备份在路由器 " + f"{REMOTE_DIR}.bak-{stamp}")
    finally:
        run(["ssh", host, "rm -f /tmp/nas-admin-deploy.tar.gz"], "清理", remote=host)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
