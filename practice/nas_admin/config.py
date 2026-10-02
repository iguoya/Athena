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


SQLALCHEMY_DATABASE_URI = _database_url()
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 生产部署时应通过环境变量换掉默认密钥（见 AGENTS.md 待办）。
SECRET_KEY = os.environ.get("NAS_ADMIN_SECRET_KEY", "athena-nas-admin-dev-key")
