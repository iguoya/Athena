#!/usr/bin/env python3
"""管理驾考 API 的设备令牌。

    python3 scripts/driver_token.py create "笔记本"   # 新建；令牌明文只显示这一次
    python3 scripts/driver_token.py list              # 列出（不含令牌）
    python3 scripts/driver_token.py revoke 3          # 撤销第 3 号

用后台自己的数据库连接串（环境变量 NAS_ADMIN_DATABASE_URL 或 db-local.json），
在路由器上和本机都能跑。令牌库里只存哈希，丢了只能撤销重发。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))


def _engine():
    from sqlalchemy import create_engine

    import config  # 取后台库连接串；没配会直接退出并说明

    url = config.SQLALCHEMY_DATABASE_URI
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return create_engine(url)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):  # Windows 控制台默认不是 UTF-8（ADR 0047）
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create", help="新建设备令牌")
    create.add_argument("name", help="设备名，如「笔记本」「台式机」")
    sub.add_parser("list", help="列出全部令牌（不含令牌本身）")
    revoke = sub.add_parser("revoke", help="撤销令牌")
    revoke.add_argument("id", type=int)
    args = parser.parse_args()

    from nas_admin.driver_api import auth

    engine = _engine()
    if args.command == "create":
        name = args.name.strip()
        if not name or len(name) > 100:
            print("设备名不能为空，且不超过 100 个字符", file=sys.stderr)
            return 2
        token_id, token = auth.create_token(engine, name)
        print(f"已创建 #{token_id}「{name}」。令牌只显示这一次，请立刻保存到该设备的本地配置：")
        print(token)
        return 0
    if args.command == "list":
        rows = auth.list_tokens(engine)
        if not rows:
            print("（还没有令牌）")
        for row in rows:
            state = f"已撤销 {row['revoked_at']}" if row["revoked_at"] else "有效"
            print(f"#{row['id']}  {row['name']}  创建 {row['created_at']}  最近使用 {row['last_used_at'] or '从未'}  {state}")
        return 0
    if auth.revoke_token(engine, args.id):
        print(f"已撤销 #{args.id}")
        return 0
    print(f"没有找到有效的 #{args.id}（不存在或早已撤销）", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
