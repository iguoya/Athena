"""驾考仪表盘测试（ADR 0069）。

和 REST API 测试同一套路：内存 SQLite 顶替 PG，最小 Flask 应用，不依赖路由器。
重点锁三件事：

1. 聚合口径——尤其连续练习天数，必须等于客户端 `DailyActivityChart.dayStreak`
   （look.dart：从今天往前数，今天没练就是 0）；
2. 只读——请求页面与数据端点前后，各表行数不变；
3. 降级——未配置连接串时给 503 + error 代码，不白屏、不带细节。
"""

from __future__ import annotations

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))

from flask import Flask  # noqa: E402
from sqlalchemy import create_engine, insert, select, func  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from nas_admin.driver_api import schema, store  # noqa: E402
from nas_admin.driver_dashboard import aggregates, init_driver_dashboard  # noqa: E402

TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
BEFORE_YESTERDAY = (date.today() - timedelta(days=2)).isoformat()


class DashboardCase(unittest.TestCase):
    def setUp(self) -> None:
        self.driver = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        schema.metadata.create_all(self.driver)
        # import_name 用 nas_admin 包，让最小应用与生产一样从包目录找 templates/ 与 static/。
        app = Flask("nas_admin")
        app.extensions[store.ENGINE_KEY] = self.driver
        init_driver_dashboard(app)
        self.client = app.test_client()

    def seed(self) -> None:
        """今天 2 答对 1、昨天 1 答对、前天 2 错 1（三天连着，但前天断了正确率）；
        科目一有模拟考，科目四只有作答；成就与练车各一点。"""
        with self.driver.begin() as conn:
            conn.execute(
                insert(schema.attempts),
                [
                    {"question_id": "q1", "topic_id": "t1", "subject_id": "subject1", "correct": 1, "duration_ms": 4000, "at": f"{TODAY}T10:00:00.000"},
                    {"question_id": "q2", "topic_id": "t1", "subject_id": "subject1", "correct": 0, "duration_ms": 6000, "at": f"{TODAY}T10:01:00.000"},
                    {"question_id": "q3", "topic_id": "t2", "subject_id": "subject4", "correct": 1, "duration_ms": 5000, "at": f"{YESTERDAY}T09:00:00.000"},
                    {"question_id": "q1", "topic_id": "t1", "subject_id": "subject1", "correct": 0, "duration_ms": 3000, "at": f"{BEFORE_YESTERDAY}T08:00:00.000"},
                    {"question_id": "q2", "topic_id": "t1", "subject_id": "subject1", "correct": 0, "duration_ms": 0, "at": f"{BEFORE_YESTERDAY}T08:01:00.000"},
                ],
            )
            conn.execute(
                insert(schema.exams),
                [
                    {"subject_id": "subject1", "score": 88, "passed": 0, "at": f"{YESTERDAY}T11:00:00.000"},
                    {"subject_id": "subject1", "score": 95, "passed": 1, "at": f"{TODAY}T12:00:00.000"},
                ],
            )
            conn.execute(insert(schema.achievements), [{"key": "streak.5", "at": f"{YESTERDAY}T09:05:00.000"}])
            conn.execute(insert(schema.drill_runs), [{"item_id": "s2.start", "mistakes": "", "at": f"{YESTERDAY}T15:00:00.000"}])

    def table_counts(self) -> dict[str, int]:
        out = {}
        with self.driver.connect() as conn:
            for name, table in schema.metadata.tables.items():
                out[name] = int(conn.execute(select(func.count()).select_from(table)).scalar_one())
        return out


class PageTest(DashboardCase):
    def test_page_renders_without_login(self):
        response = self.client.get("/driver/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"echarts.min.js", response.data)
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_data_json_aggregates(self):
        self.seed()
        response = self.client.get("/driver/data.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        data = response.get_json()

        self.assertEqual(data["overview"]["attempts"], 5)
        self.assertEqual(data["overview"]["correct"], 2)
        self.assertEqual(data["overview"]["rate"], 0.4)
        # 平均用时只算 duration_ms > 0 的（对齐客户端 averageDurationMs）
        self.assertEqual(data["overview"]["avg_duration_ms"], 4500)
        self.assertEqual(data["overview"]["exams"], 2)
        self.assertEqual(data["overview"]["achievements"], 1)
        self.assertEqual(data["overview"]["drills"], 1)
        self.assertEqual(data["overview"]["rehearsals"], 0)
        self.assertEqual(data["overview"]["last_day"], TODAY)
        # 连续练习：今天、昨天都有，前天也有——3 天
        self.assertEqual(data["overview"]["streak"], 3)

        # 每日窗口固定 30 天、补齐空白天、时间正序
        daily = data["daily"]
        self.assertEqual(len(daily), 30)
        self.assertEqual(daily[-1]["date"], TODAY)
        self.assertEqual(daily[-1]["attempts"], 2)
        self.assertEqual(daily[-2]["attempts"], 1)
        self.assertEqual(daily[0]["attempts"], 0)

        # 科目合并 attempts 与 exams 两路
        by_id = {s["id"]: s for s in data["subjects"]}
        self.assertEqual(by_id["subject1"]["attempts"], 4)
        self.assertEqual(by_id["subject1"]["rate"], 0.25)
        self.assertEqual(by_id["subject1"]["exams"], 2)
        self.assertEqual(by_id["subject1"]["exam_avg"], 91.5)
        self.assertEqual(by_id["subject4"]["attempts"], 1)
        self.assertEqual(by_id["subject4"]["title"], "科目四")

        self.assertEqual(len(data["exams"]), 2)
        self.assertEqual(data["exams"][0]["score"], 88)
        self.assertFalse(data["exams"][0]["passed"])

        self.assertEqual(data["achievements"][0]["label"], "连对 5 题")
        self.assertEqual(data["achievements"][0]["at"].startswith(YESTERDAY), True)

    def test_readonly_no_rows_change(self):
        self.seed()
        before = self.table_counts()
        self.client.get("/driver/")
        self.client.get("/driver/data.json")
        self.assertEqual(self.table_counts(), before)

    def test_empty_database(self):
        response = self.client.get("/driver/data.json")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["overview"]["attempts"], 0)
        self.assertIsNone(data["overview"]["rate"])
        self.assertIsNone(data["overview"]["avg_duration_ms"])
        self.assertEqual(data["overview"]["streak"], 0)
        # 空库时每日窗口也完整（30 天全 0），前端不画空图
        self.assertEqual(len(data["daily"]), 30)
        self.assertTrue(all(d["attempts"] == 0 for d in data["daily"]))
        self.assertEqual(data["subjects"], [])


class StreakTest(unittest.TestCase):
    """dayStreak 口径与客户端（look.dart）一致：从今天往前数，今天没练就是 0。"""

    @staticmethod
    def window(attempts_per_day: list[int]) -> list[dict]:
        n = len(attempts_per_day)
        today = date.today()
        return [
            {"date": (today - timedelta(days=n - 1 - i)).isoformat(), "attempts": a, "correct": 0}
            for i, a in enumerate(attempts_per_day)
        ]

    def test_today_empty_means_zero(self):
        # 昨天之前天天练，但今天还没练：0（客户端就是这么算的）
        self.assertEqual(aggregates.day_streak(self.window([3, 2, 0])), 0)

    def test_consecutive_days(self):
        self.assertEqual(aggregates.day_streak(self.window([0, 2, 3, 4])), 3)

    def test_gap_breaks(self):
        self.assertEqual(aggregates.day_streak(self.window([5, 0, 2, 3])), 2)

    def test_all_empty(self):
        self.assertEqual(aggregates.day_streak(self.window([0, 0])), 0)


class DegradationTest(unittest.TestCase):
    def setUp(self) -> None:
        app = Flask("nas_admin")
        init_driver_dashboard(app)
        self.client = app.test_client()

    def test_not_configured_is_503_json(self):
        # 不注入 engine、清掉可能被别的测试留下的全局缓存，让 engine() 走配置读取
        with mock.patch.object(store, "_engine", None), mock.patch.object(
            store, "_database_url", side_effect=store.NotConfigured("未配置")
        ):
            response = self.client.get("/driver/data.json")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["error"], "not_configured")
        self.assertNotIn(b"Traceback", response.data)

    def test_page_still_renders_when_data_fails(self):
        # 页面是纯壳，数据端点挂了页面照样出，前端自会显示降级提示
        with mock.patch.object(store, "_engine", None), mock.patch.object(
            store, "_database_url", side_effect=store.NotConfigured("未配置")
        ):
            response = self.client.get("/driver/")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
