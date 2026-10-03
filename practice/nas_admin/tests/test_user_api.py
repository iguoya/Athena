"""全局学习者目录 API 测试（ADR 0074、0075）。

内存 SQLite 顶替后台库，自己搭一个最小 Flask 应用，不依赖路由器、不依赖 FAB：

    cd practice/nas_admin && .venv/Scripts/python -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))

from flask import Flask  # noqa: E402
from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from nas_admin import access  # noqa: E402
from nas_admin.user_api import directory, init_user_api  # noqa: E402

BASE = "/api/users/v1"


class UserApiCase(unittest.TestCase):
    def setUp(self) -> None:
        access.reset_rate_limits()
        self.engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        app = Flask(__name__)
        init_user_api(app, engine=self.engine)
        self.client = app.test_client()

    def call(self, method, path, body=None, acting=None):
        headers = {}
        if acting is not None:
            headers["X-Athena-User"] = str(acting)
        return self.client.open(BASE + path, method=method, json=body, headers=headers)

    def register(self, name):
        r = self.call("POST", "/users", {"name": name})
        self.assertEqual(r.status_code, 201, r.get_data(as_text=True))
        return r.get_json()["user"]


class AccessTests(UserApiCase):
    """应用里不认证（ADR 0077）：不需要令牌，只限流。"""

    def test_不需要令牌(self):
        self.assertEqual(self.call("POST", "/users", {"name": "小王"}).status_code, 201)
        self.assertEqual(self.client.post(BASE + "/login", json={"name": "小王"}, headers={"Authorization": "Bearer x"}).status_code, 200)

    def test_超过限流返回429(self):
        self.register("小王")
        access.reset_rate_limits()  # 登记那一下也算一次请求，重新计数
        with mock.patch.object(access, "RATE_LIMIT", 2):
            self.assertEqual(self.call("POST", "/login", {"name": "小王"}).status_code, 200)
            self.assertEqual(self.call("POST", "/login", {"name": "小王"}).status_code, 200)
            r = self.call("POST", "/login", {"name": "小王"})
        self.assertEqual((r.status_code, r.get_json()["error"]), (429, "rate_limited"))

    def test_响应不被缓存(self):
        self.assertEqual(self.call("POST", "/users", {"name": "小王"}).headers["Cache-Control"], "no-store")


class RegisterTests(UserApiCase):
    def test_编号从_1_顺序分配(self):
        self.assertEqual(self.register("tiger"), {"id": 1, "name": "tiger"})
        self.assertEqual(self.register("小王"), {"id": 2, "name": "小王"})

    def test_重名照样新建_编号不同(self):
        a, b = self.register("小王"), self.register("小王")
        self.assertNotEqual(a["id"], b["id"])

    def test_名字去首尾空白后保存(self):
        self.assertEqual(self.register("  小王  ")["name"], "小王")

    def test_编号用完后拒绝登记(self):
        directory.ensure_table(self.engine)
        with self.engine.begin() as conn:
            for n in range(directory.MAX_ID):
                directory.register(conn, f"u{n}")
        r = self.call("POST", "/users", {"name": "多余的人"})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.get_json()["error"], "directory_full")

    def test_校验(self):
        cases = [
            ({"name": ""}, "空名字"),
            ({"name": "   "}, "纯空白"),
            ({"name": "a/b"}, "斜杠"),
            ({"name": "a\\b"}, "反斜杠"),
            ({"name": "x" * 65}, "过长"),
            ({"name": 5}, "非字符串"),
            ({}, "缺名字"),
            ({"name": "ok", "role": "admin"}, "未知字段"),
        ]
        for body, label in cases:
            self.assertEqual(self.call("POST", "/users", body).status_code, 400, label)
        self.assertEqual(self.client.post(BASE + "/users", data="oops").status_code, 400)


class LoginTests(UserApiCase):
    def test_名字唯一直接登录(self):
        self.register("tiger")
        r = self.call("POST", "/login", {"name": "tiger"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["user"], {"id": 1, "name": "tiger"})

    def test_忽略大小写和首尾空白(self):
        self.register("Tiger")
        for typed in ("tiger", "TIGER", "  tiger "):
            r = self.call("POST", "/login", {"name": typed})
            self.assertEqual(r.status_code, 200, typed)
            self.assertEqual(r.get_json()["user"]["name"], "Tiger", "返回登记时的写法")

    def test_没有这个名字_404(self):
        r = self.call("POST", "/login", {"name": "没人"})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json()["error"], "not_found")

    def test_重名要再问编号_409(self):
        self.register("小王")
        self.register("小王")
        r = self.call("POST", "/login", {"name": "小王"})
        self.assertEqual(r.status_code, 409)
        body = r.get_json()
        self.assertEqual((body["error"], body["matches"]), ("ambiguous", 2))
        self.assertNotIn("user", body, "不泄露任何一个重名者的编号")

    def test_重名带上编号就能进(self):
        self.register("小王")
        second = self.register("小王")
        r = self.call("POST", "/login", {"name": "小王", "id": second["id"]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["user"]["id"], second["id"])

    def test_编号接受数字串(self):
        self.register("小王")
        r = self.call("POST", "/login", {"name": "小王", "id": "1"})
        self.assertEqual(r.status_code, 200)

    def test_编号和名字对不上_与不存在同一个答案(self):
        self.register("小王")
        self.register("小李")
        wrong = self.call("POST", "/login", {"name": "小王", "id": 2})
        unknown = self.call("POST", "/login", {"name": "没人"})
        self.assertEqual(wrong.status_code, 404)
        self.assertEqual(wrong.get_json(), unknown.get_json(), "不暗示名字存不存在")

    def test_编号校验(self):
        self.register("小王")
        for bad in (0, 1000, -1, "abc", True, 1.5):
            r = self.call("POST", "/login", {"name": "小王", "id": bad})
            self.assertEqual(r.status_code, 400, repr(bad))


class SelfOnlyTests(UserApiCase):
    def test_改自己的名字(self):
        me = self.register("tiger")
        r = self.call("PATCH", f"/users/{me['id']}", {"name": "老司机"}, acting=me["id"])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["user"], {"id": 1, "name": "老司机"})
        self.assertEqual(self.call("POST", "/login", {"name": "老司机"}).status_code, 200)
        self.assertEqual(self.call("POST", "/login", {"name": "tiger"}).status_code, 404, "旧名字不再能登录")

    def test_不能改别人的名字(self):
        mine, other = self.register("tiger"), self.register("小王")
        r = self.call("PATCH", f"/users/{other['id']}", {"name": "被改了"}, acting=mine["id"])
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.get_json()["error"], "forbidden")
        self.assertEqual(self.call("POST", "/login", {"name": "小王"}).get_json()["user"]["name"], "小王")

    def test_不带当前学习者头也不能改(self):
        me = self.register("tiger")
        self.assertEqual(self.call("PATCH", f"/users/{me['id']}", {"name": "x"}).status_code, 403)

    def test_改名后可以与别人重名_靠编号区分(self):
        a, b = self.register("小王"), self.register("小李")
        self.call("PATCH", f"/users/{b['id']}", {"name": "小王"}, acting=b["id"])
        self.assertEqual(self.call("POST", "/login", {"name": "小王"}).status_code, 409)
        self.assertEqual(self.call("POST", "/login", {"name": "小王", "id": a["id"]}).status_code, 200)

    def test_查自己_查别人被拒(self):
        mine, other = self.register("tiger"), self.register("小王")
        ok = self.call("GET", f"/users/{mine['id']}", acting=mine["id"])
        self.assertEqual(ok.get_json()["user"]["name"], "tiger")
        self.assertEqual(self.call("GET", f"/users/{other['id']}", acting=mine["id"]).status_code, 403)

    def test_自己的编号不存在_404(self):
        self.assertEqual(self.call("GET", "/users/7", acting=7).status_code, 404)
        self.assertEqual(self.call("PATCH", "/users/7", {"name": "x"}, acting=7).status_code, 404)

    def test_改名校验(self):
        me = self.register("tiger")
        for body in ({"name": ""}, {"name": "a/b"}, {}, {"name": "x", "id": 2}):
            r = self.call("PATCH", f"/users/{me['id']}", body, acting=me["id"])
            self.assertEqual(r.status_code, 400, str(body))


class StorageTests(UserApiCase):
    def test_库里存的是名字和折叠键(self):
        self.register("Tiger")
        with self.engine.connect() as conn:
            row = conn.execute(select(directory.users)).mappings().one()
        self.assertEqual((row["id"], row["name"], row["name_key"]), (1, "Tiger", "tiger"))
        self.assertTrue(row["created_at"] and row["updated_at"])


if __name__ == "__main__":
    unittest.main()
