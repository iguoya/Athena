"""驾考 API 挂进真实的 FAB 应用（`create_app`）后的冒烟：不破坏原有端点，令牌走后台库。

用临时 SQLite 文件顶替后台的 PG 连接串，所以不依赖路由器：

    cd practice/nas_admin && .venv/Scripts/python -m unittest discover -s tests -v
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

BASE = "/api/driver/v1"


class RealAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ["NAS_ADMIN_DATABASE_URL"] = f"sqlite:///{Path(cls.tmp.name, 'admin.db').as_posix()}"
        from nas_admin import create_app, db
        from nas_admin.driver_api import auth, schema, store

        cls.app = create_app("config")
        cls.app.testing = True
        driver = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        schema.metadata.create_all(driver)
        cls.app.extensions[store.ENGINE_KEY] = driver
        with cls.app.app_context():
            _id, cls.token = auth.create_token(db.engine, "冒烟")
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls) -> None:
        from nas_admin import db

        with cls.app.app_context():
            db.engine.dispose()
        cls.tmp.cleanup()

    def test_原有端点不受影响(self):
        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        self.assertTrue(health.get_json()["ok"])
        self.assertEqual(self.client.get("/login/").status_code, 200)

    def test_仪表盘页面与数据端点(self):
        page = self.client.get("/driver/")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"echarts.min.js", page.data)
        data = self.client.get("/driver/data.json")
        self.assertEqual(data.status_code, 200)
        self.assertIn("overview", data.get_json())

    def test_API_要令牌_有令牌能读写(self):
        self.assertEqual(self.client.get(f"{BASE}/ping").status_code, 401)
        headers = {"Authorization": f"Bearer {self.token}"}
        self.assertEqual(self.client.get(f"{BASE}/ping", headers=headers).get_json()["device"], "冒烟")
        item = {"question_id": "q", "topic_id": "t", "subject_id": "s", "correct": 1, "at": "2026-10-02T14:11:10.123"}
        r = self.client.post(f"{BASE}/attempts", json={"items": [item]}, headers=headers)
        self.assertEqual(r.get_json(), {"inserted": 1, "skipped": 0})

    def test_API_不走_FAB_登录会话(self):
        # FAB 的登录 cookie 不该让 API 通过：API 只认设备令牌。
        r = self.client.post("/login/", data={"username": "x", "password": "y"})
        self.assertIn(r.status_code, (200, 302, 400))
        self.assertEqual(self.client.get(f"{BASE}/ping").status_code, 401)

    def test_路由表里_API_都在约定前缀下(self):
        rules = [r.rule for r in self.app.url_map.iter_rules() if r.endpoint.startswith("driver_api.")]
        self.assertTrue(rules)
        self.assertTrue(all(rule.startswith(BASE) for rule in rules), rules)


if __name__ == "__main__":
    unittest.main()
