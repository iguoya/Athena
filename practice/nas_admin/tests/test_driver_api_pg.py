"""驾考 API 对真实 PostgreSQL 的集成测试。

SQLite 测试盖住逻辑，这里盖住 PG 才有的东西：`INSERT … SELECT` 的参数类型、咨询锁
（并发写不重复）、identity 列、以及**只有增删改查权限的低权限角色**确实够用且不能改表。

没配环境变量就整体跳过（日常 check 不依赖路由器）。要跑：

    DRIVER_API_TEST_PG_OWNER_URL=postgresql://属主:密码@主机/测试库   # 建表、清表用
    DRIVER_API_TEST_PG_URL=postgresql://API角色:密码@主机/测试库       # 被测的低权限角色

测试库里的表由属主按 driver 客户端的 DDL 建好（与 `subjects/driver/lib/progress.dart`
的 `_ensureSchema` 同构）；本文件会对照 `schema.py` 核对列名，漂移了立刻报错。
"""

from __future__ import annotations

import os
import sys
import threading
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from flask import Flask  # noqa: E402
from sqlalchemy import create_engine, inspect, text  # noqa: E402
from sqlalchemy.exc import DBAPIError  # noqa: E402

from nas_admin.driver_api import auth, init_driver_api, schema, store  # noqa: E402
from test_driver_api import BASE, T0, T1, attempt, memory_engine  # noqa: E402

OWNER_URL = os.environ.get("DRIVER_API_TEST_PG_OWNER_URL")
API_URL = os.environ.get("DRIVER_API_TEST_PG_URL")


@unittest.skipUnless(OWNER_URL and API_URL, "未设 DRIVER_API_TEST_PG_OWNER_URL / DRIVER_API_TEST_PG_URL，跳过 PG 集成测试")
class PostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.owner = create_engine(store._normalize(OWNER_URL), pool_size=8, max_overflow=8)
        cls.api = create_engine(store._normalize(API_URL), pool_size=8, max_overflow=8)
        # 生产里令牌表在后台自己的 PG 库；测试也用 PG 存令牌（内存 SQLite 单连接扛不住多线程）。
        auth.ensure_table(cls.owner)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.owner.dispose()
        cls.api.dispose()

    def setUp(self) -> None:
        auth.reset_rate_limits()
        names = ", ".join([t.name for t in schema.metadata.sorted_tables] + [auth.tokens.name])
        with self.owner.begin() as conn:
            conn.execute(text(f"TRUNCATE {names} RESTART IDENTITY"))
        tokens = self.owner
        app = Flask(__name__)
        init_driver_api(app, driver_engine=self.api, token_engine=tokens)
        self.client = app.test_client()
        _id, token = auth.create_token(tokens, "pg-test")
        self.headers = {"Authorization": f"Bearer {token}"}

    def post(self, path, body):
        return self.client.post(BASE + path, json=body, headers=self.headers)

    def count(self, table: str) -> int:
        with self.owner.connect() as conn:
            return conn.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()

    # ------------------------------------------------------------ 结构一致

    def test_镜像的列与真实表一致(self):
        inspector = inspect(self.owner)
        for table in schema.metadata.sorted_tables:
            with self.subTest(table.name):
                real = {c["name"] for c in inspector.get_columns(table.name)}
                self.assertEqual(real, {c.name for c in table.columns}, "schema.py 与 driver 客户端建的表列不一致")

    # ------------------------------------------------------------ 基本读写

    def test_上传_幂等_拉取(self):
        r = self.post("/attempts", {"items": [attempt(at=T0, duration_ms=1500), attempt(at=T1)]})
        self.assertEqual(r.get_json(), {"inserted": 2, "skipped": 0})
        r = self.post("/attempts", {"items": [attempt(at=T0), attempt(at="2026-10-02T15:00:00.000")]})
        self.assertEqual(r.get_json(), {"inserted": 1, "skipped": 1})
        items = self.client.get(BASE + "/attempts", headers=self.headers).get_json()["items"]
        self.assertEqual([i["at"] for i in items], [T0, T1, "2026-10-02T15:00:00.000"])
        self.assertEqual(items[0]["duration_ms"], 1500)
        self.assertEqual([i["id"] for i in items], sorted(i["id"] for i in items))

    def test_中文与特殊字符原样保存(self):
        text_value = "右后视镜 'x' \"y\" \\ % _ 😀"
        self.post("/drill-notes", {"items": [{"item_id": "a", "text": text_value, "at": T0}]})
        got = self.client.get(BASE + "/drill-notes", headers=self.headers).get_json()["items"][0]
        self.assertEqual(got["text"], text_value)

    def test_通知_read_列(self):
        self.post("/notices", {"items": [{"kind": "k", "title": "t", "body": "", "at": T0}]})
        self.assertEqual(self.post("/notices/read-all", {}).get_json(), {"updated": 1})
        self.assertEqual(self.client.get(BASE + "/notices", headers=self.headers).get_json()["items"][0]["read"], 1)

    def test_成就与草稿(self):
        put = lambda path, body: self.client.put(BASE + path, json=body, headers=self.headers)  # noqa: E731
        put("/achievements/k", {"at": T1})
        self.assertEqual(put("/achievements/k", {"at": T0}).get_json()["at"], T0)
        draft = {
            "subject_id": "s", "title": "t", "question_ids": "[]", "question_count": 1, "minutes": 1, "pass_score": 1,
            "points_per_question": 1, "mix": "{}", "full_bank": 0, "picked": "[]", "started_at": T0, "saved_at": T1,
        }
        self.assertTrue(put("/exam-drafts/k", draft).get_json()["applied"])
        self.assertFalse(put("/exam-drafts/k", {**draft, "saved_at": T0}).get_json()["applied"])
        self.assertTrue(put("/exam-drafts/k", {**draft, "saved_at": "2026-10-02T16:00:00.000", "title": "新"}).get_json()["applied"])
        self.assertEqual(self.client.get(BASE + "/exam-drafts/k", headers=self.headers).get_json()["title"], "新")

    # ------------------------------------------------------------ 并发

    def test_并发上传同一批_不产生重复行(self):
        batch = [attempt(question=f"q{i}", at=f"2026-10-02T14:00:{i:02d}.000") for i in range(20)]
        results: list[int] = []
        errors: list[str] = []

        def worker() -> None:
            try:
                # 每个线程自己的 test_client，模拟多台设备同时同步。
                app = Flask(__name__)
                init_driver_api(app, driver_engine=self.api, token_engine=self.tokens_engine())
                r = app.test_client().post(BASE + "/attempts", json={"items": batch}, headers=self.headers)
                if r.status_code != 200:
                    errors.append(f"{r.status_code} {r.get_json()}")
                else:
                    results.append(r.get_json()["inserted"])
            except Exception as error:  # noqa: BLE001
                errors.append(repr(error))

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        self.assertEqual(self.count("attempts"), 20, "并发下不能有重复行")
        self.assertEqual(sum(results), 20, "每条恰好被某一个请求插入")

    def tokens_engine(self):
        return self.client.application.extensions[auth.TOKEN_ENGINE_KEY]

    # ------------------------------------------------------------ 权限

    def test_API_角色不能改表结构(self):
        for sql in ("CREATE TABLE evil (x int)", "DROP TABLE attempts", "ALTER TABLE attempts ADD COLUMN x int", "TRUNCATE attempts"):
            with self.subTest(sql):
                with self.assertRaises(DBAPIError):
                    with self.api.begin() as conn:
                        conn.execute(text(sql))
        self.assertEqual(self.count("attempts"), 0)

    def test_API_角色不能连别的库(self):
        other = create_engine(store._normalize(API_URL).rsplit("/", 1)[0] + "/postgres")
        try:
            with self.assertRaises(DBAPIError):
                with other.connect() as conn:
                    conn.execute(text("SELECT 1"))
        finally:
            other.dispose()


if __name__ == "__main__":
    unittest.main()
