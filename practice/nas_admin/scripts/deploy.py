#!/usr/bin/env python3
"""把本目录部署到软路由的 /opt/webapp 并重启服务——两边由此「关联」：

    本机 practice/nas_admin（唯一源）
        └─ python3 scripts/deploy.py
              ├─ 打包（tarfile，排除 .venv/__pycache__/tests/db-local.json 等，
              │  文件模式与属主在包里统一，不带 Windows 的 666/777）
              ├─ ssh 标准输入写文件上传（dropbear 没有 sftp-server，
              │  scp -O 在 Windows OpenSSH 下行为不稳，管道最省心）
              ├─ 远程备份 /opt/webapp → /opt/webapp.bak-<时间戳>（700）
              ├─ 远程解包覆盖 + pip3 install -r requirements.txt
              ├─ 写 db-local.json；首次部署随机生成 secret-key.txt
              ├─ 统一权限：目录 755、文件 644、属主 root；三份密钥文件 600、属主 webapp
              ├─ 首次部署（PG 里还没有 ab_user 表）时建管理员
              ├─ /etc/init.d/webapp restart
              └─ 访问 /api/health 验证 ok:true

用法：
    python3 scripts/deploy.py [--host root@192.168.6.1]

凭据（ADR 0068）都不进仓库：数据库连接串从环境变量 NAS_ADMIN_DATABASE_URL 或本目录
db-local.json 读；后台管理员密码只从环境变量 NAS_ADMIN_ADMIN_PASSWORD 读（只有首次
建号才需要）。**凭据一律经 ssh 标准输入送过去，不拼进命令行参数**——参数会出现在两端
的进程列表里。

服务以低权限用户 `webapp` 运行，所以：代码归 root、别人不可写（被攻破的进程改不了自己的
代码），只有三份密钥文件交给 webapp 读。
"""

from __future__ import annotations

import argparse
import io
import json
import os
import shlex
import subprocess
import sys
import tarfile
import time
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
REMOTE_DIR = "/opt/webapp"
# 顶层不部署：开发环境、测试、运行数据、版本库元数据。scripts/ 只放行下面列出的几个。
EXCLUDED_TOP = {".venv", "data", "__pycache__", ".git", ".gitignore", "tests"}
EXCLUDED_ROOT_FILES = {"db-local.json", "secret-key.txt", "driver-db.json"}
EXCLUDED_SUFFIX = (".pyc", ".tar")
# 路由器上要用的脚本；目前没有（设备令牌已取消，ADR 0077）。run_dev/check/deploy 是开发脚本，不上路由。
DEPLOYED_SCRIPTS: set[str] = set()
SECRET_FILES = ("db-local.json", "secret-key.txt", "driver-db.json")


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def _normalize(info: tarfile.TarInfo) -> tarfile.TarInfo:
    """包里的模式与属主统一：Windows 打的包默认是 666/777，解包到路由器就成了所有人可写。"""
    info.mode = 0o755 if info.isdir() else 0o644
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    return info


def build_tar() -> bytes:
    """打进内存。data/ 是运行数据，部署永不触碰；连接串、密钥文件绝不进包。"""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for path in sorted(APP_ROOT.rglob("*")):
            rel = path.relative_to(APP_ROOT)
            posix = rel.as_posix()
            if rel.parts[0] in EXCLUDED_TOP:
                continue
            if rel.parts[0] == "scripts" and posix not in DEPLOYED_SCRIPTS and posix != "scripts":
                continue
            if len(rel.parts) == 1 and rel.name in EXCLUDED_ROOT_FILES:
                continue
            if any(part == "__pycache__" for part in rel.parts):
                continue
            if rel.suffix in EXCLUDED_SUFFIX:
                continue
            tar.add(path, arcname=posix, recursive=False, filter=_normalize)
    return buffer.getvalue()


def ssh(host: str, command: str, *, stdin: bytes | None = None, step: str) -> str:
    """执行远程命令；需要带凭据的内容走 stdin，不进 argv。"""
    print(f"[{step}] @{host}", flush=True)
    completed = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=10", host, command],
        input=stdin,
        capture_output=True,
    )
    out = completed.stdout.decode("utf-8", errors="replace")
    err = completed.stderr.decode("utf-8", errors="replace")
    if completed.returncode != 0:
        print(out, end="")
        print(err, end="", file=sys.stderr)
        raise SystemExit(f"[{step}] 失败（退出码 {completed.returncode}）")
    return out


def remote_script(*, stamp: str, db_url: str, admin_password: str | None) -> str:
    """在路由器上执行的完整流程。密钥内容都用 shlex.quote / json.dumps 处理，不手拼引号。"""
    db_json = json.dumps({"url": db_url})
    admin_env = f"export NAS_ADMIN_ADMIN_PASSWORD={shlex.quote(admin_password)}" if admin_password else "NAS_ADMIN_ADMIN_PASSWORD="
    return f"""set -e
R={REMOTE_DIR}
id webapp >/dev/null 2>&1 || {{ echo "路由器上没有 webapp 用户（服务应以它运行）" >&2; exit 4; }}
{admin_env}

if [ -d "$R" ]; then
  cp -a "$R" "$R.bak-{stamp}"
  chmod 700 "$R.bak-{stamp}"       # 备份里可能带着旧的密钥文件，不让别人读
fi
mkdir -p "$R"
tar -xzf /tmp/nas-admin-deploy.tar.gz -C "$R" -o
pip3 install --no-cache-dir -r "$R/requirements.txt" >/dev/null

# --- 密钥文件：连接串每次覆盖；会话密钥只在不存在时生成（换它会让所有人重新登录）
umask 077
cat > "$R/db-local.json" <<'JSON'
{db_json}
JSON
[ -f "$R/secret-key.txt" ] || tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 64 > "$R/secret-key.txt"
umask 022

# --- 权限：代码归 root、别人不可写；只有密钥文件交给运行用户 webapp 读
chown -R root:root "$R"
find "$R" -type d -exec chmod 755 {{}} +
find "$R" -type f -exec chmod 644 {{}} +
for f in {" ".join(SECRET_FILES)}; do
  if [ -f "$R/$f" ]; then chown webapp:webapp "$R/$f"; chmod 600 "$R/$f"; fi
done

# --- 首次部署建管理员（ab_user 表还不存在）
cd "$R"
if python3 - <<'PY'
import json, sys
import psycopg
url = json.load(open("db-local.json"))["url"].replace("postgresql+psycopg://", "postgresql://")
with psycopg.connect(url, connect_timeout=5) as conn:
    found = conn.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'ab_user'").fetchone()
sys.exit(0 if found else 1)
PY
then
  echo "已有后台账号表，跳过建管理员"
else
  [ -n "$NAS_ADMIN_ADMIN_PASSWORD" ] || {{ echo "首次部署需要管理员密码：设环境变量 NAS_ADMIN_ADMIN_PASSWORD" >&2; exit 3; }}
  python3 - <<'PY'
import os
from nas_admin import appbuilder, create_app

app = create_app()
with app.app_context():
    sm = appbuilder.sm
    sm.add_user("admin", "Admin", "NAS", "admin@nas.local", sm.find_role(sm.auth_role_admin), os.environ["NAS_ADMIN_ADMIN_PASSWORD"])
print("已创建管理员 admin")
PY
fi
# 上面以 root 跑 python 会留下 root 的 __pycache__：权限再统一一次
find "$R" -type d -exec chmod 755 {{}} +
find "$R" -type f -name '*.pyc' -exec chmod 644 {{}} +

/etc/init.d/webapp restart
sleep 4
wget -qO- http://127.0.0.1:5000/api/health
"""


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="部署 nas-admin 到软路由 /opt/webapp")
    parser.add_argument("--host", default="root@192.168.6.1", help="SSH 目标（默认 root@192.168.6.1）")
    args = parser.parse_args()
    host = args.host

    # 凭据不进仓库：连接串从环境变量或 db-local.json 来；没有就拒绝部署（ADR 0068）。
    db_url = os.environ.get("NAS_ADMIN_DATABASE_URL")
    if not db_url:
        local_config = APP_ROOT / "db-local.json"
        if local_config.is_file():
            db_url = str(json.loads(local_config.read_text(encoding="utf-8"))["url"])
    if not db_url:
        raise SystemExit("缺数据库连接串：设 NAS_ADMIN_DATABASE_URL 或建 db-local.json")
    admin_password = os.environ.get("NAS_ADMIN_ADMIN_PASSWORD") or None  # 只有首次建号才需要

    payload = build_tar()
    print(f"[打包] {len(payload) / 1024:.1f} KiB", flush=True)
    try:
        ssh(host, "cat > /tmp/nas-admin-deploy.tar.gz", stdin=payload, step="上传")
        stamp = time.strftime("%Y%m%d-%H%M%S")
        script = remote_script(stamp=stamp, db_url=db_url, admin_password=admin_password)
        output = ssh(host, "sh -s", stdin=script.encode("utf-8"), step="远程部署")
        print(output.strip(), flush=True)
        if '"ok":true' not in output.replace(" ", ""):
            raise SystemExit("部署后 /api/health 未返回 ok:true，请上路由器查日志：logread | grep webapp")
        print(f"部署完成，备份在路由器 {REMOTE_DIR}.bak-{stamp}（含旧的密钥文件，确认无误后请删除）")
    finally:
        ssh(host, "rm -f /tmp/nas-admin-deploy.tar.gz", step="清理")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
