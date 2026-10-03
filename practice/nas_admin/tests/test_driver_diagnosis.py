"""驾考仪表盘「学习诊断」测试（主仓库 ADR 0076 决策 10）。

口径必须和客户端 `subjects/driver/lib/diagnosis.dart` 一致，所以这里的用例都是从
`test/diagnosis_test.dart` 的同名场景搬来的：同样的输入，同样的结论、同样的门槛。
"""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))

from flask import Flask  # noqa: E402
from sqlalchemy import create_engine, insert, select, func  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from nas_admin.driver_api import schema, store  # noqa: E402
from nas_admin.driver_dashboard import diagnosis, init_driver_dashboard  # noqa: E402
from nas_admin.user_api import directory  # noqa: E402

BASE = datetime(2026, 9, 1, 10, 0, 0)
TITLES = {"drive.s1.rules": "通行规则", "drive.s1.penalty": "违法记分与处罚"}


def row(qid, correct, *, day=0, minute=0, topic="drive.s1.rules", ms=5000, kind="practice", chosen=None, reason=None):
    at = BASE + timedelta(days=day, minutes=minute)
    return {
        "question_id": qid,
        "topic_id": topic,
        "correct": 1 if correct else 0,
        "duration_ms": ms,
        "at": at.isoformat(timespec="milliseconds"),
        "kind": kind,
        "chosen": chosen,
        "reason": reason,
    }


class RetentionTest(unittest.TestCase):
    def test_buckets_by_calendar_day_gap_after_a_correct_answer(self):
        rows = [
            row("a", True), row("a", True, minute=30),  # 同一天，保持
            row("b", True), row("b", False, day=1),  # 隔 1 天，忘了
            row("c", True), row("c", True, day=3),  # 隔 2～3 天
            row("d", True), row("d", True, day=20),  # 隔 15 天以上
        ]
        buckets = {b["label"]: b for b in diagnosis.forgetting_curve(rows)}
        self.assertEqual((buckets["同一天"]["n"], buckets["同一天"]["correct"]), (1, 1))
        self.assertEqual((buckets["隔 1 天"]["n"], buckets["隔 1 天"]["correct"]), (1, 0))
        self.assertEqual(buckets["隔 2～3 天"]["n"], 1)
        self.assertEqual(buckets["隔 15 天以上"]["n"], 1)
        self.assertEqual(buckets["隔 4～7 天"]["rate"], None)

    def test_previous_wrong_answers_do_not_count(self):
        """上一次答错的不算「记住了又忘」，客户端同样跳过。"""
        rows = [row("a", False), row("a", True, day=1)]
        self.assertTrue(all(b["n"] == 0 for b in diagnosis.forgetting_curve(rows)))

    def test_small_samples_are_marked_not_enough(self):
        rows = [r for i in range(diagnosis.RETENTION_MIN_SAMPLE) for r in (row(f"q{i}", True), row(f"q{i}", True, day=1))]
        bucket = next(b for b in diagnosis.forgetting_curve(rows) if b["label"] == "隔 1 天")
        self.assertEqual(bucket["n"], diagnosis.RETENTION_MIN_SAMPLE)
        self.assertTrue(bucket["enough"])
        self.assertFalse(diagnosis.forgetting_curve(rows[:4])[1]["enough"])

    def test_unparseable_time_rows_are_skipped(self):
        rows = [{**row("a", True), "at": "不是时间"}, row("a", True), row("a", True, day=1)]
        bucket = next(b for b in diagnosis.forgetting_curve(rows) if b["label"] == "隔 1 天")
        self.assertEqual(bucket["n"], 1)


def cause_rows():
    """20 次答对（中位数 5000ms）+ 各种各样的错。"""
    rows = [row(f"ok{i}", True, minute=i, ms=5000) for i in range(20)]
    rows += [
        row("w1", False, minute=30, ms=2000, topic="drive.s1.penalty"),  # 快：粗心
        row("w2", False, minute=31, ms=9000, topic="drive.s1.penalty"),  # 慢：不会
        row("w3", False, minute=32, ms=5000),  # 一般错
        row("s1", True, minute=33, ms=9000),  # 答对但慢：不熟
    ]
    return rows


class CauseTest(unittest.TestCase):
    def test_classifies_against_own_median(self):
        report = diagnosis.error_causes(cause_rows(), TITLES)
        self.assertEqual(report["median_ms"], 5000)
        self.assertEqual(report["counts"], {"careless": 1, "unknown": 1, "ordinary": 1, "shaky": 1})
        self.assertEqual(report["by_cause"]["careless"], [{"title": "违法记分与处罚", "n": 1}])

    def test_needs_enough_correct_answers_for_a_median(self):
        rows = [row(f"ok{i}", True, ms=5000) for i in range(diagnosis.CAUSE_MIN_CORRECT_FOR_MEDIAN - 1)]
        rows.append(row("w", False, ms=1000))
        report = diagnosis.error_causes(rows, TITLES)
        self.assertIsNone(report["median_ms"])
        self.assertEqual(sum(report["counts"].values()), 0)

    def test_invalid_durations_are_ignored(self):
        rows = cause_rows() + [row("z", False, ms=0), row("y", False, ms=diagnosis.DURATION_CAP_MS + 1)]
        self.assertEqual(sum(diagnosis.error_causes(rows, TITLES)["counts"].values()), 4)

    def test_boundaries_match_client(self):
        """恰好 0.6 倍算快、恰好 1.6 倍算慢（客户端用 <= 与 >=）。"""
        rows = [row(f"ok{i}", True, minute=i, ms=5000) for i in range(20)]
        rows += [row("f", False, minute=40, ms=3000), row("s", False, minute=41, ms=8000)]
        counts = diagnosis.error_causes(rows, TITLES)["counts"]
        self.assertEqual((counts["careless"], counts["unknown"]), (1, 1))


class ConfusionTest(unittest.TestCase):
    def test_repeated_wrong_pick_and_multi_count(self):
        rows = [
            row("drive.s1.rules.1", False, chosen="B"),
            row("drive.s1.rules.1", False, minute=1, chosen="B"),
            row("drive.s1.rules.2", False, chosen="A"),
            row("drive.s1.rules.2", False, minute=1, chosen="C"),  # 两次选的不一样，不算反复
            row("drive.s1.rules.3", False, chosen="A,B"),
            row("drive.s1.rules.4", False),  # 没记所选选项
            row("drive.s1.rules.5", True, chosen="A"),
        ]
        report = diagnosis.confusion(rows, TITLES)
        self.assertEqual((report["wrong_total"], report["with_chosen"], report["multi_wrong"]), (6, 5, 1))
        self.assertEqual(len(report["repeated"]), 1)
        self.assertEqual(report["repeated"][0]["serial"], "s1.rules.1")
        self.assertEqual((report["repeated"][0]["chosen"], report["repeated"][0]["times"]), ("B", 2))

    def test_no_data_is_empty(self):
        report = diagnosis.confusion([], TITLES)
        self.assertEqual((report["wrong_total"], report["repeated"]), (0, []))


class OutcomeTest(unittest.TestCase):
    def test_variant_gap_matches_client_scenario(self):
        rows = [row(f"r{i}", i < 8, kind="reinforce", reason="retest", minute=i) for i in range(10)]
        rows += [row(f"v{i}", i < 4, kind="reinforce", reason="variant", minute=20 + i) for i in range(10)]
        gap = diagnosis.variant_gap(diagnosis.reason_outcomes(rows))
        self.assertAlmostEqual(gap["gap"], 0.4)
        self.assertTrue(gap["enough"])

    def test_gap_needs_both_sides_and_samples(self):
        self.assertIsNone(diagnosis.variant_gap(diagnosis.reason_outcomes([row("r", True, kind="reinforce", reason="retest")])))
        self.assertIsNone(diagnosis.variant_gap([]))
        small = diagnosis.variant_gap(diagnosis.reason_outcomes([
            row("r", True, kind="reinforce", reason="retest"),
            row("v", False, kind="reinforce", reason="variant", minute=1),
        ]))
        self.assertFalse(small["enough"])

    def test_only_reinforce_rows_with_reason_count_and_order_is_fixed(self):
        rows = [
            row("a", True, kind="reinforce", reason="due"),
            row("b", True, kind="reinforce", reason="variant", minute=1),
            row("c", True, kind="reinforce", reason="retest", minute=2),
            row("d", True, kind="practice", reason="retest", minute=3),  # 不是强化练习
            row("e", True, kind="reinforce", minute=4),  # 旧数据没有理由
        ]
        outcomes = diagnosis.reason_outcomes(rows)
        self.assertEqual([o["reason"] for o in outcomes], ["retest", "variant", "due"])
        self.assertEqual(outcomes[0]["n"], 1)


class EndpointTest(unittest.TestCase):
    def setUp(self) -> None:
        kw = dict(poolclass=StaticPool, connect_args={"check_same_thread": False})
        self.driver = create_engine("sqlite://", **kw)
        self.names = create_engine("sqlite://", **kw)
        schema.metadata.create_all(self.driver)
        app = Flask("nas_admin")
        app.extensions[store.ENGINE_KEY] = self.driver
        app.extensions[directory.ENGINE_KEY] = self.names
        init_driver_dashboard(app)
        self.client = app.test_client()

    def add(self, user, rows):
        with self.driver.begin() as conn:
            conn.execute(
                insert(schema.attempts),
                [{**r, "user": user, "subject_id": "subject1", "hesitant": 0} for r in rows],
            )

    def test_no_attempts_is_an_empty_answer_not_an_error(self):
        data = self.client.get("/driver/diagnosis.json").get_json()
        self.assertEqual((data["learners"], data["selected"], data["diagnosis"]), ([], None, None))

    def test_defaults_to_the_busiest_learner_and_names_come_from_directory(self):
        with self.names.begin() as conn:
            directory.ensure_table(self.names)
            conn.execute(insert(directory.users), [
                {"id": 1, "name": "tiger", "name_key": "tiger", "created_at": "x", "updated_at": "x"},
            ])
        self.add("1", cause_rows())
        self.add("2", [row("a", True)])
        response = self.client.get("/driver/diagnosis.json")
        data = response.get_json()
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual([(p["id"], p["name"]) for p in data["learners"]], [("1", "tiger"), ("2", "学习者 2")])
        self.assertEqual(data["selected"], "1")
        self.assertEqual(data["diagnosis"]["causes"]["counts"]["careless"], 1)

    def test_only_the_selected_learners_rows_are_used(self):
        self.add("1", cause_rows())
        self.add("2", [row("a", True), row("a", False, day=1)])
        data = self.client.get("/driver/diagnosis.json?user=2").get_json()
        self.assertEqual(data["selected"], "2")
        self.assertEqual(data["diagnosis"]["attempts"], 2)
        self.assertIsNone(data["diagnosis"]["causes"]["median_ms"])

    def test_unknown_learner_is_404_without_details(self):
        self.add("1", [row("a", True)])
        response = self.client.get("/driver/diagnosis.json?user=99")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"], "unknown_learner")

    def test_directory_failure_degrades_to_ids(self):
        """目录库不可用时，诊断照出，只是名字退回编号。"""
        self.names.dispose()
        self.names = None
        broken = create_engine("sqlite:///file:/nonexistent/x.db?mode=ro&uri=true")
        self.client.application.extensions[directory.ENGINE_KEY] = broken
        self.add("1", [row("a", True)])
        data = self.client.get("/driver/diagnosis.json").get_json()
        self.assertEqual(data["learners"][0]["name"], "学习者 1")

    def test_read_only(self):
        self.add("1", cause_rows())
        with self.driver.connect() as conn:
            before = conn.execute(select(func.count()).select_from(schema.attempts)).scalar_one()
        self.client.get("/driver/diagnosis.json")
        with self.driver.connect() as conn:
            after = conn.execute(select(func.count()).select_from(schema.attempts)).scalar_one()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
