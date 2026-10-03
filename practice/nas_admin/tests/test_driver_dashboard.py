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
                    {"question_id": "q1", "topic_id": "drive.s1.rules", "subject_id": "subject1", "correct": 1, "duration_ms": 4000, "at": f"{TODAY}T10:00:00.000"},
                    {"question_id": "q2", "topic_id": "drive.s1.rules", "subject_id": "subject1", "correct": 0, "duration_ms": 6000, "at": f"{TODAY}T10:01:00.000"},
                    {"question_id": "q3", "topic_id": "drive.s4.civil", "subject_id": "subject4", "correct": 1, "duration_ms": 5000, "at": f"{YESTERDAY}T09:00:00.000"},
                    {"question_id": "q1", "topic_id": "drive.s1.rules", "subject_id": "subject1", "correct": 0, "duration_ms": 3000, "at": f"{BEFORE_YESTERDAY}T08:00:00.000"},
                    {"question_id": "q2", "topic_id": "drive.s1.rules", "subject_id": "subject1", "correct": 0, "duration_ms": 0, "at": f"{BEFORE_YESTERDAY}T08:01:00.000"},
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

        # 日历热力：全量按天的 [日期, 量] 对，只有练过的天出现
        calendar = {d[0]: d[1] for d in data["calendar"]}
        self.assertEqual(calendar[TODAY], 2)
        self.assertEqual(calendar[YESTERDAY], 1)
        self.assertEqual(calendar[BEFORE_YESTERDAY], 2)
        self.assertEqual(len(calendar), 3)

        # 旭日：一级按量降序（subject1=4 在前），叶子带章节展示名
        self.assertEqual(data["sunburst"][0]["name"], "科目一")
        self.assertEqual(data["sunburst"][0]["value"], 4)
        self.assertIn("通行、超车与让行", [c["name"] for c in data["sunburst"][0]["children"]])

        # 雷达：seed 里每章作答都不足 10 次，正确率噪声大，不进雷达
        self.assertEqual(data["radar"]["indicators"], [])

        self.assertEqual(len(data["exams"]), 2)
        self.assertEqual(data["exams"][0]["score"], 88)
        self.assertFalse(data["exams"][0]["passed"])

        self.assertEqual(data["achievements"][0]["label"], "连对 5 题")
        self.assertEqual(data["achievements"][0]["at"].startswith(YESTERDAY), True)

    def test_radar_picks_main_subject_with_threshold(self):
        """雷达取正式科目中作答量最大的；不足 10 次的章节不进。"""
        with self.driver.begin() as conn:
            rows = []
            # 科目一 rules 章 12 次答对 10、signals 章 12 次答对 6；alcohol 只有 5 次（门槛外）
            for i in range(12):
                rows.append({"question_id": f"q{i}", "topic_id": "drive.s1.rules", "subject_id": "subject1",
                             "correct": 1 if i < 10 else 0, "duration_ms": 0, "at": f"{TODAY}T1{i:02d}:00:00.000"})
                rows.append({"question_id": f"s{i}", "topic_id": "drive.s1.signals", "subject_id": "subject1",
                             "correct": 1 if i < 6 else 0, "duration_ms": 0, "at": f"{TODAY}T2{i:02d}:00:00.000"})
            for i in range(5):
                rows.append({"question_id": f"a{i}", "topic_id": "drive.s1.alcohol", "subject_id": "subject1",
                             "correct": 1, "duration_ms": 0, "at": f"{TODAY}T3{i:02d}:00:00.000"})
            # 错题本量再大也不抢主修科目（wrong 不是正式科目）
            for i in range(50):
                rows.append({"question_id": f"w{i}", "topic_id": "drive.s1.rules", "subject_id": "wrong",
                             "correct": 0, "duration_ms": 0, "at": f"{TODAY}T4{i:02d}:00:00.000"})
            conn.execute(insert(schema.attempts), rows)
        data = self.client.get("/driver/data.json").get_json()
        radar = data["radar"]
        self.assertEqual(radar["subject"], "科目一")
        names = [i["name"] for i in radar["indicators"]]
        self.assertEqual(names, ["通行、超车与让行", "交通信号与标志"])  # 按量降序，alcohol 被门槛滤掉
        self.assertEqual(radar["values"], [83.3, 50.0])

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


class SubjectDetailTest(DashboardCase):
    """科目深挖与错题口径：跨场景作答序列、连对攻克、顽固榜、章节错题维度。"""

    def seed_subject(self) -> None:
        """q1 错→对→对（+错题本再对一次）= 已攻克；q2 错→错 = 仍错着；
        q3 全对 = 从未错过；q4 只在考前复习里出现过（也算答过的题）。"""
        rows = [
            # 正式场景 subject1
            {"question_id": "drive.s1.rules.001", "topic_id": "drive.s1.rules", "subject_id": "subject1", "correct": 0, "duration_ms": 0, "at": f"{BEFORE_YESTERDAY}T08:00:00.000"},
            {"question_id": "drive.s1.rules.001", "topic_id": "drive.s1.rules", "subject_id": "subject1", "correct": 1, "duration_ms": 0, "at": f"{BEFORE_YESTERDAY}T09:00:00.000"},
            {"question_id": "drive.s1.rules.001", "topic_id": "drive.s1.rules", "subject_id": "subject1", "correct": 1, "duration_ms": 0, "at": f"{YESTERDAY}T08:00:00.000"},
            {"question_id": "drive.s1.rules.002", "topic_id": "drive.s1.rules", "subject_id": "subject1", "correct": 0, "duration_ms": 0, "at": f"{BEFORE_YESTERDAY}T10:00:00.000"},
            {"question_id": "drive.s1.rules.002", "topic_id": "drive.s1.rules", "subject_id": "subject1", "correct": 0, "duration_ms": 0, "at": f"{YESTERDAY}T10:00:00.000"},
            {"question_id": "drive.s1.signals.003", "topic_id": "drive.s1.signals", "subject_id": "subject1", "correct": 1, "duration_ms": 0, "at": f"{TODAY}T08:00:00.000"},
            # 错题本：q1 又对了一次（算第 4 次作答）；q5 是 s1 的题但只有错题本记录
            {"question_id": "drive.s1.rules.001", "topic_id": "drive.s1.rules", "subject_id": "wrong", "correct": 1, "duration_ms": 0, "at": f"{TODAY}T09:00:00.000"},
            {"question_id": "drive.s1.alcohol.005", "topic_id": "drive.s1.alcohol", "subject_id": "wrong", "correct": 0, "duration_ms": 0, "at": f"{TODAY}T10:00:00.000"},
            # 考前复习：q4 只在这里出现
            {"question_id": "drive.s1.penalty.004", "topic_id": "drive.s1.penalty", "subject_id": "review", "correct": 1, "duration_ms": 0, "at": f"{TODAY}T11:00:00.000"},
            # 科目四一条：不得混进科目一
            {"question_id": "drive.s4.civil.001", "topic_id": "drive.s4.civil", "subject_id": "subject4", "correct": 1, "duration_ms": 0, "at": f"{TODAY}T12:00:00.000"},
        ]
        with self.driver.begin() as conn:
            conn.execute(insert(schema.attempts), rows)

    def test_wrong_analysis(self):
        self.seed_subject()
        detail = self.client.get("/driver/data.json").get_json()["details"]["subject1"]
        w = detail["wrong"]
        # 答过的题：q1-q5（q5 只有错题本记录也算）；错过的：q1、q2、q5；攻克：q1；仍错：q2、q5
        self.assertEqual(w["questions"], 5)
        self.assertEqual(w["ever_wrong"], 3)
        self.assertEqual(w["fixed"], 1)
        self.assertEqual(w["still"], 2)
        # 消化曲线：第 1 次对的只有 q3、q4（0.4）；第 2 次 1/2；第 3、4 次全对
        curve = {c["n"]: c for c in w["repeat_curve"]}
        self.assertEqual(curve[1]["count"], 5)
        self.assertEqual(curve[1]["rate"], 0.4)
        self.assertEqual(curve[2]["rate"], 0.5)
        self.assertEqual(curve[3]["rate"], 1.0)
        self.assertEqual(curve[4]["count"], 1)
        # 顽固榜：q2 错 2 次居首，带题号与状态
        self.assertEqual(w["stubborn"][0]["no"], "002")
        self.assertEqual(w["stubborn"][0]["wrongs"], 2)
        self.assertFalse(w["stubborn"][0]["fixed"])

    def test_chapters_carry_wrong_dimensions(self):
        self.seed_subject()
        detail = self.client.get("/driver/data.json").get_json()["details"]["subject1"]
        by_id = {c["id"]: c for c in detail["chapters"]}
        rules = by_id["drive.s1.rules"]
        self.assertEqual(rules["attempts"], 5)      # 正式场景 5 次
        self.assertEqual(rules["questions"], 2)     # q1、q2
        self.assertEqual(rules["wrong_questions"], 2)
        # alcohol 章只在错题本出现：正式作答 0，但错题统计里有它
        self.assertEqual(by_id["drive.s1.alcohol"]["questions"], 1)
        # 复习场景的重练量归入 wrong_drill，不进正式章节作答
        drill = {x["id"]: x for x in detail["wrong_drill"]}
        self.assertEqual(drill["drive.s1.penalty"]["attempts"], 1)

    def test_subject_separation_and_empty(self):
        self.seed_subject()
        details = self.client.get("/driver/data.json").get_json()["details"]
        self.assertEqual(details["subject1"]["title"], "科目一")
        self.assertEqual(details["subject4"]["title"], "科目四")
        self.assertEqual(len(details["subject4"]["chapters"]), 1)
        # 只做理论科目（科目一/四）的分科页；科目二即使有练习也不出标签页（ADR 0069）
        self.assertNotIn("subject2", details)


    def test_exam_chapter_dimensions(self):
        """kind='exam' 的章节维度（driver ADR 0057）：考试作答、正确率、丢分题数。"""
        with self.driver.begin() as conn:
            conn.execute(insert(schema.attempts), [
                # rules 章考试作答：3 题对 2、丢 1 题
                {"question_id": "drive.s1.rules.101", "topic_id": "drive.s1.rules", "subject_id": "subject1", "correct": 1, "duration_ms": 0, "at": f"{TODAY}T13:00:00.000", "kind": "exam"},
                {"question_id": "drive.s1.rules.102", "topic_id": "drive.s1.rules", "subject_id": "subject1", "correct": 1, "duration_ms": 0, "at": f"{TODAY}T13:01:00.000", "kind": "exam"},
                {"question_id": "drive.s1.rules.103", "topic_id": "drive.s1.rules", "subject_id": "subject1", "correct": 0, "duration_ms": 0, "at": f"{TODAY}T13:02:00.000", "kind": "exam"},
                # 同章平时练习：不计入考试维度
                {"question_id": "drive.s1.rules.104", "topic_id": "drive.s1.rules", "subject_id": "subject1", "correct": 0, "duration_ms": 0, "at": f"{TODAY}T14:00:00.000", "kind": "practice"},
                # 另一章只有平时练习：考试维度应为零值
                {"question_id": "drive.s1.signals.105", "topic_id": "drive.s1.signals", "subject_id": "subject1", "correct": 1, "duration_ms": 0, "at": f"{TODAY}T14:01:00.000", "kind": "practice"},
            ])
        detail = self.client.get("/driver/data.json").get_json()["details"]["subject1"]
        by_id = {c["id"]: c for c in detail["chapters"]}
        rules = by_id["drive.s1.rules"]
        self.assertEqual(rules["exam_attempts"], 3)
        self.assertEqual(rules["exam_rate"], 0.6667)
        self.assertEqual(rules["exam_wrong_questions"], 1)
        signals = by_id["drive.s1.signals"]
        self.assertEqual(signals["exam_attempts"], 0)
        self.assertIsNone(signals["exam_rate"])
        self.assertEqual(signals["exam_wrong_questions"], 0)

    def test_avg_duration_ignores_idle_outliers(self):
        """挂机产生的天文时长不拉偏平均用时（与客户端封顶一致的统计上限）。"""
        with self.driver.begin() as conn:
            conn.execute(insert(schema.attempts), [
                {"question_id": "drive.s1.rules.201", "topic_id": "drive.s1.rules", "subject_id": "subject1", "correct": 1, "duration_ms": 4000, "at": f"{TODAY}T15:00:00.000"},
                {"question_id": "drive.s1.rules.202", "topic_id": "drive.s1.rules", "subject_id": "subject1", "correct": 1, "duration_ms": 36947433, "at": f"{TODAY}T15:01:00.000"},
            ])
        data = self.client.get("/driver/data.json").get_json()
        self.assertEqual(data["overview"]["avg_duration_ms"], 4000)


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


class LabelTest(unittest.TestCase):
    def test_练习场景与科目的展示名(self):
        self.assertEqual(aggregates.SUBJECT_TITLES["wrong"][0], "错题本")
        self.assertEqual(aggregates.SUBJECT_TITLES["review"][0], "复习")

    def test_成就可读名(self):
        self.assertEqual(aggregates._achievement_label("streak.5"), "连对 5 题")
        self.assertEqual(aggregates._achievement_label("topic.t1"), "章节过关")
        self.assertEqual(aggregates._achievement_label("exam.pass.subject1"), "科目一模拟考首次及格")


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
