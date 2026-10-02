"""Flask-AppBuilder 配置。

数据落在软路由的 PostgreSQL（17.5）：本机开发与路由器运行用同一条连接串，
同一套数据。**连接串不进仓库**（凭据规则见 AGENTS 与仓库 ADR 0068）：从环境
变量 `NAS_ADMIN_DATABASE_URL` 或本目录 `db-local.json`（已 gitignore，格式
`{"url": "postgresql://user:pass@host:port/db"}`）读取，两者都没有就拒绝启动。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _database_url() -> str:
    from_env = os.environ.get("NAS_ADMIN_DATABASE_URL")
    if from_env:
        return from_env
    local = BASE_DIR / "db-local.json"
    if local.is_file():
        try:
            return str(json.loads(local.read_text(encoding="utf-8"))["url"])
        except (json.JSONDecodeError, KeyError) as error:
            sys.exit(f"db-local.json 格式不对（需要 {{\"url\": ...}}）：{error}")
    sys.exit(
        "缺数据库连接串：设环境变量 NAS_ADMIN_DATABASE_URL，"
        f"或建 {local}（内容 {{\"url\": \"postgresql://用户:密码@主机:5432/nas_admin\"}}）。"
    )


def _normalize(url: str) -> str:
    # 常见写法是 postgresql://；SQLAlchemy 默认会去找没装的 psycopg2，这里用的是 psycopg 3。
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def _secret_key() -> str:
    """会话签名密钥。来源按序：环境变量 `NAS_ADMIN_SECRET_KEY`，本目录 `secret-key.txt`
    （已 gitignore，600；路由器上由 deploy 首次部署时随机生成），最后才是仅供本机开发的
    默认值——默认值是公开的，拿它能伪造登录会话，所以路由器上绝不能落到这一步。"""
    from_env = os.environ.get("NAS_ADMIN_SECRET_KEY")
    if from_env:
        return from_env
    local = BASE_DIR / "secret-key.txt"
    if local.is_file():
        key = local.read_text(encoding="utf-8").strip()
        if len(key) < 32:
            sys.exit("secret-key.txt 太短（至少 32 个字符）")
        return key
    return "athena-nas-admin-dev-key"


SQLALCHEMY_DATABASE_URI = _normalize(_database_url())
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = _secret_key()
