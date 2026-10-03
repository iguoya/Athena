"""驾考 REST API 测试。

用内存 SQLite 顶替 PG（表结构镜像在 nas_admin.driver_api.schema），自己搭一个最小
Flask 应用，不依赖路由器、不依赖 FAB 初始化——本机和 CI 都能跑：

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
from nas_admin.driver_api import init_driver_api, schema, store  # noqa: E402

BASE = "/api/driver/v1"
T0 = "2026-10-02T14:11:10.123"
T1 = "2026-10-02T14:11:11.456"


def memory_engine():
    # StaticPool + check_same_thread=False：内存库在各线程共用同一条连接，数据才不会「消失」。
    return create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})


class ApiCase(unittest.TestCase):
    """每个用例一套全新的内存库和应用。应用里不认证（ADR 0077），只靠 X-Athena-User 分用户。"""

    def setUp(self) -> None:
        access.reset_rate_limits()
        self.driver = memory_engine()
        schema.metadata.create_all(self.driver)
        app = Flask(__name__)
        init_driver_api(app, driver_engine=self.driver)
        self.app = app
        self.client = app.test_client()
        # 默认以首用户 tiger 走（ADR 0071）：不带用户头的请求一律 400，
        # 个别用例换人时在 headers 里覆盖。
        self.headers = {"X-Athena-User": "tiger"}

    # 简写；user 用来临时换人（多用户用例）
    def get(self, path, user=None, **kw):
        headers = {**self.headers, **({"X-Athena-User": user} if user else {})}
        return self.client.get(BASE + path, headers=headers, **kw)

    def post(self, path, body, user=None):
        headers = {**self.headers, **({"X-Athena-User": user} if user else {})}
        return self.client.post(BASE + path, json=body, headers=headers)

    def put(self, path, body, user=None):
        headers = {**self.headers, **({"X-Athena-User": user} if user else {})}
        return self.client.put(BASE + path, json=body, headers=headers)

    def rows(self, table):
        with self.driver.connect() as conn:
            return [dict(r) for r in conn.execute(select(table).order_by(table.c.id)).mappings()]


def attempt(question="s1.signals.207", at=T0, **extra):
    return {"question_id": question, "topic_id": "t", "subject_id": "subject1", "correct": 1, "at": at, **extra}


class AccessTests(ApiCase):
    """应用里不认证（ADR 0077）：不需要令牌；用户靠请求头；只做限流。"""

    def test_不需要令牌_带了也不看(self):
        self.assertEqual(self.client.get(BASE + "/stats", headers={"X-Athena-User": "tiger"}).status_code, 200)
        r = self.client.get(BASE + "/stats", headers={"X-Athena-User": "tiger", "Authorization": "Bearer whatever"})
        self.assertEqual(r.status_code, 200, "旧客户端还带着令牌也能用，服务端直接忽略")

    def test_连通自检不要求学习者头(self):
        r = self.client.get(BASE + "/ping")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])
        self.assertNotIn("device", r.get_json())

    def test_其他接口缺学习者头是400(self):
        for method, path in (("get", "/stats"), ("post", "/attempts"), ("put", "/achievements/k"), ("post", "/notices/read-all")):
            r = getattr(self.client, method)(BASE + path, json={})
            self.assertEqual(r.status_code, 400, f"{method} {path}")

    def test_限流按来源地址_互不影响(self):
        self.assertTrue(all(access.allow("1.1.1.1", limit=3) for _ in range(3)))
        self.assertFalse(access.allow("1.1.1.1", limit=3))
        self.assertTrue(access.allow("2.2.2.2", limit=3), "别的来源不受影响")

    def test_超过限流返回429(self):
        with mock.patch.object(access, "RATE_LIMIT", 2):
            self.assertEqual(self.get("/stats").status_code, 200)
            self.assertEqual(self.get("/stats").status_code, 200)
            r = self.get("/stats")
        self.assertEqual((r.status_code, r.get_json()["error"]), (429, "rate_limited"))

    def test_经_Cloudflare_的请求按_Cf_Connecting_Ip_限流(self):
        with mock.patch.object(access, "RATE_LIMIT", 1):
            a = {**self.headers, "Cf-Connecting-Ip": "9.9.9.9"}
            b = {**self.headers, "Cf-Connecting-Ip": "8.8.8.8"}
            self.assertEqual(self.client.get(BASE + "/stats", headers=a).status_code, 200)
            self.assertEqual(self.client.get(BASE + "/stats", headers=a).status_code, 429)
            self.assertEqual(self.client.get(BASE + "/stats", headers=b).status_code, 200)

    def test_响应不被缓存(self):
        self.assertEqual(self.get("/ping").headers["Cache-Control"], "no-store")


class AppendOnlyTests(ApiCase):
    def test_上传后可拉取(self):
        r = self.post("/attempts", {"items": [attempt(at=T0), attempt(at=T1)]})
        self.assertEqual(r.get_json(), {"inserted": 2, "skipped": 0})
        body = self.get("/attempts").get_json()
        self.assertEqual([i["at"] for i in body["items"]], [T0, T1])
        self.assertFalse(body["has_more"])
        self.assertEqual(body["next_after_id"], body["items"][-1]["id"])

    def test_重复上传幂等(self):
        self.post("/attempts", {"items": [attempt()]})
        r = self.post("/attempts", {"items": [attempt(), attempt(at=T1)]})
        self.assertEqual(r.get_json(), {"inserted": 1, "skipped": 1})
        self.assertEqual(len(self.rows(schema.attempts)), 2)

    def test_同一批里的重复也只入一条(self):
        r = self.post("/attempts", {"items": [attempt(), attempt()]})
        self.assertEqual(r.get_json(), {"inserted": 1, "skipped": 1})

    def test_可选字段有默认值(self):
        self.post("/attempts", {"items": [attempt()]})
        row = self.rows(schema.attempts)[0]
        self.assertEqual((row["duration_ms"], row["hesitant"]), (0, 0))

    def test_布尔旗标接受_true_false(self):
        self.post("/attempts", {"items": [attempt(correct=True, hesitant=False)]})
        row = self.rows(schema.attempts)[0]
        self.assertEqual((row["correct"], row["hesitant"]), (1, 0))

    def test_分页与_has_more(self):
        self.post("/attempts", {"items": [attempt(at=f"2026-10-02T14:11:{s:02d}.000") for s in range(5)]})
        first = self.get("/attempts?limit=2").get_json()
        self.assertEqual(len(first["items"]), 2)
        self.assertTrue(first["has_more"])
        second = self.get(f"/attempts?limit=2&after_id={first['next_after_id']}").get_json()
        self.assertEqual(len(second["items"]), 2)
        third = self.get(f"/attempts?limit=2&after_id={second['next_after_id']}").get_json()
        self.assertEqual(len(third["items"]), 1)
        self.assertFalse(third["has_more"])
        ids = [i["id"] for page in (first, second, third) for i in page["items"]]
        self.assertEqual(ids, sorted(set(ids)), "按 id 升序且无重复")

    def test_空页游标不后退(self):
        body = self.get("/attempts?after_id=42").get_json()
        self.assertEqual((body["items"], body["next_after_id"]), ([], 42))

    def test_其余追加型资源都能写能读(self):
        samples = {
            "exams": {"subject_id": "subject1", "score": 96, "passed": 1, "at": T0},
            "drill-runs": {"item_id": "c2.park", "mistakes": "[1,2]", "at": T0},
            "rehearsals": {"item_id": "c2.park", "missed": "[]", "total": 4, "at": T0},
            "drill-notes": {"item_id": "c2.park", "text": "看右后视镜", "at": T0},
            "point-notes": {"item_id": "c2.park", "step": 2, "text": "打死方向", "at": T0},
            "notices": {"kind": "unlock", "title": "解锁科目二", "body": "", "at": T0},
        }
        for path, item in samples.items():
            with self.subTest(path):
                self.assertEqual(self.post(f"/{path}", {"items": [item]}).get_json()["inserted"], 1)
                self.assertEqual(self.post(f"/{path}", {"items": [item]}).get_json()["skipped"], 1)
                got = self.get(f"/{path}").get_json()["items"]
                self.assertEqual(len(got), 1)
                for key, value in item.items():
                    self.assertEqual(got[0][key], value)

    def test_通知默认未读_read_all_只改未读(self):
        self.post("/notices", {"items": [{"kind": "k", "title": "a", "body": "", "at": T0}, {"kind": "k", "title": "b", "body": "", "at": T1, "read": 1}]})
        self.assertEqual([n["read"] for n in self.get("/notices").get_json()["items"]], [0, 1])
        self.assertEqual(self.post("/notices/read-all", {}).get_json(), {"updated": 1})
        self.assertEqual([n["read"] for n in self.get("/notices").get_json()["items"]], [1, 1])
        self.assertEqual(self.post("/notices/read-all", {}).get_json(), {"updated": 0})

    def test_不同键的记录互不影响(self):
        self.post("/point-notes", {"items": [{"item_id": "a", "step": 1, "text": "x", "at": T0}]})
        r = self.post("/point-notes", {"items": [{"item_id": "a", "step": 2, "text": "x", "at": T0}]})
        self.assertEqual(r.get_json()["inserted"], 1, "同点位不同步骤是两条")

    def test_统计(self):
        self.post("/attempts", {"items": [attempt(), attempt(at=T1)]})
        stats = self.get("/stats").get_json()["stats"]
        self.assertEqual(stats["attempts"]["count"], 2)
        self.assertEqual(stats["attempts"]["max_id"], 2)
        self.assertEqual(stats["exams"], {"count": 0, "max_id": 0})


class ValidationTests(ApiCase):
    def assert_invalid(self, response, fragment=""):
        self.assertEqual(response.status_code, 400, response.get_data(as_text=True))
        body = response.get_json()
        self.assertEqual(body["error"], "invalid")
        self.assertIn(fragment, body["message"])

    def test_未知字段被拒(self):
        self.assert_invalid(self.post("/attempts", {"items": [attempt(extra_field=1)]}), "extra_field")

    def test_缺必填字段(self):
        item = attempt()
        del item["question_id"]
        self.assert_invalid(self.post("/attempts", {"items": [item]}), "question_id")

    def test_字段类型与范围(self):
        bad = [
            attempt(correct=2),
            attempt(correct="1"),
            attempt(duration_ms=-1),
            attempt(duration_ms=10**12),
            attempt(question=""),
            attempt(question="x" * 201),
            attempt(question="a\x00b"),
            attempt(at="昨天"),
            attempt(at="2026-13-45T99:00:00"),
            attempt(at="x" * 41),
        ]
        for item in bad:
            with self.subTest(str(item)[:60]):
                self.assertEqual(self.post("/attempts", {"items": [item]}).status_code, 400)

    def test_整数不接受布尔(self):
        r = self.post("/exams", {"items": [{"subject_id": "s", "score": True, "passed": 1, "at": T0}]})
        self.assert_invalid(r, "score")

    def test_批量条数边界(self):
        self.assert_invalid(self.post("/attempts", {"items": []}), "items")
        too_many = [attempt(at=f"2026-10-02T14:{m:02d}:{s:02d}.000") for m in range(9) for s in range(60)]
        self.assertGreater(len(too_many), 500)
        self.assert_invalid(self.post("/attempts", {"items": too_many}), "items")
        ok = self.post("/attempts", {"items": too_many[:500]})
        self.assertEqual(ok.get_json()["inserted"], 500)

    def test_一条坏数据整批拒绝_不写一半(self):
        r = self.post("/attempts", {"items": [attempt(at=T0), attempt(at="坏")]})
        self.assert_invalid(r, "items[1].at")
        self.assertEqual(self.rows(schema.attempts), [])

    def test_请求体不是_JSON_对象(self):
        for payload in ("not json", "[]", "null"):
            r = self.client.post(BASE + "/attempts", data=payload, headers={**self.headers, "Content-Type": "application/json"})
            self.assertEqual(r.status_code, 400, payload)

    def test_items_不是数组(self):
        self.assert_invalid(self.post("/attempts", {"items": "x"}), "items")

    def test_分页参数非法(self):
        for query in ("?limit=0", "?limit=501", "?limit=abc", "?after_id=-1", "?after_id=x"):
            self.assertEqual(self.get("/attempts" + query).status_code, 400, query)

    def test_请求体过大_413(self):
        r = self.client.post(BASE + "/attempts", data=b"x" * (1024 * 1024 + 1), headers={**self.headers, "Content-Type": "application/json"})
        self.assertEqual(r.status_code, 413)

    def test_SQL_注入式输入只是普通字符串(self):
        evil = "x'); DROP TABLE attempts;--"
        self.post("/attempts", {"items": [attempt(question=evil)]})
        self.assertEqual(self.rows(schema.attempts)[0]["question_id"], evil)
        self.assertEqual(self.post("/attempts", {"items": [attempt(question="ok")]}).get_json()["inserted"], 1)


class AchievementTests(ApiCase):
    def test_首次写入(self):
        r = self.put("/achievements/streak7", {"at": T1})
        self.assertEqual(r.get_json(), {"key": "streak7", "at": T1})

    def test_保留更早的时间(self):
        self.put("/achievements/k", {"at": T1})
        self.assertEqual(self.put("/achievements/k", {"at": T0}).get_json()["at"], T0, "更早的覆盖")
        self.assertEqual(self.put("/achievements/k", {"at": T1}).get_json()["at"], T0, "更晚的不覆盖")
        self.assertEqual(self.get("/achievements").get_json()["items"], [{"key": "k", "at": T0}])

    def test_键与时间校验(self):
        self.assertEqual(self.put("/achievements/k", {}).status_code, 400)
        self.assertEqual(self.put("/achievements/k", {"at": "坏"}).status_code, 400)
        self.assertEqual(self.put("/achievements/k", {"at": T0, "x": 1}).status_code, 400)
        self.assertEqual(self.put("/achievements/" + "k" * 201, {"at": T0}).status_code, 400)


def draft(**extra):
    base = {
        "subject_id": "subject1", "title": "模拟考", "question_ids": '["a","b"]', "question_count": 100,
        "minutes": 45, "pass_score": 90, "points_per_question": 1, "mix": "{}", "full_bank": 0,
        "picked": "[]", "started_at": T0, "saved_at": T0,
    }
    return {**base, **extra}


class DraftTests(ApiCase):
    def test_存取删(self):
        self.assertEqual(self.get("/exam-drafts/main").status_code, 404)
        self.assertTrue(self.put("/exam-drafts/main", draft()).get_json()["applied"])
        got = self.get("/exam-drafts/main").get_json()
        self.assertEqual((got["draft_key"], got["title"], got["minutes"]), ("main", "模拟考", 45))
        r = self.client.delete(BASE + "/exam-drafts/main", headers=self.headers)
        self.assertEqual(r.status_code, 204)
        self.assertEqual(self.get("/exam-drafts/main").status_code, 404)

    def test_较新的覆盖较旧的(self):
        self.put("/exam-drafts/k", draft(saved_at=T0, picked="[1]"))
        self.assertTrue(self.put("/exam-drafts/k", draft(saved_at=T1, picked="[1,2]")).get_json()["applied"])
        self.assertEqual(self.get("/exam-drafts/k").get_json()["picked"], "[1,2]")

    def test_较旧的不覆盖较新的(self):
        self.put("/exam-drafts/k", draft(saved_at=T1, picked="[1,2]"))
        self.assertFalse(self.put("/exam-drafts/k", draft(saved_at=T0, picked="[1]")).get_json()["applied"])
        self.assertEqual(self.get("/exam-drafts/k").get_json()["picked"], "[1,2]")

    def test_删除不存在的草稿也_204(self):
        self.assertEqual(self.client.delete(BASE + "/exam-drafts/none", headers=self.headers).status_code, 204)

    def test_字段校验(self):
        self.assertEqual(self.put("/exam-drafts/k", {**draft(), "minutes": -1}).status_code, 400)
        body = draft()
        del body["title"]
        self.assertEqual(self.put("/exam-drafts/k", body).status_code, 400)


class FailureTests(unittest.TestCase):
    """数据库、配置出问题时的表现：503 和不泄露细节。"""

    def make(self, driver_engine=None):
        access.reset_rate_limits()
        app = Flask(__name__)
        init_driver_api(app, driver_engine=driver_engine)
        return app.test_client(), {"X-Athena-User": "tiger"}

    def test_表还没建_503_且不泄露细节(self):
        client, headers = self.make(driver_engine=memory_engine())  # 空库，没有表
        r = client.get(BASE + "/attempts", headers=headers)
        self.assertEqual(r.status_code, 503)
        text = r.get_data(as_text=True)
        for leak in ("sqlite", "OperationalError", "no such table", "SELECT", "Traceback"):
            self.assertNotIn(leak, text)

    def test_没配连接串_503(self):
        client, headers = self.make(driver_engine=None)
        with mock.patch.object(store, "_database_url", side_effect=store.NotConfigured("x")):
            r = client.get(BASE + "/attempts", headers=headers)
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.get_json()["error"], "not_configured")

    def test_未知路径是_404(self):
        # 路径不存在时 Flask 在进入蓝图前就返回 404，不会走令牌校验，也不暴露任何数据。
        client, headers = self.make(driver_engine=memory_engine())
        self.assertEqual(client.get(BASE + "/nothing").status_code, 404)
        self.assertEqual(client.get(BASE + "/nothing", headers=headers).status_code, 404)


class NormalizeTests(unittest.TestCase):
    def test_连接串驱动名(self):
        self.assertEqual(store._normalize("postgresql://u:p@h/db"), "postgresql+psycopg://u:p@h/db")
        self.assertEqual(store._normalize("postgresql+psycopg://u:p@h/db"), "postgresql+psycopg://u:p@h/db")


if __name__ == "__main__":
    unittest.main()


class MultiUserTests(ApiCase):
    """ADR 0071：同一份题库给多个学习者，个人数据按用户隔离、互不可见。"""

    def attempt(self, question_id: str, at: str, user: str) -> object:
        return self.post(
            "/attempts",
            {"items": [{"question_id": question_id, "topic_id": "t", "subject_id": "s",
                        "correct": True, "duration_ms": 0, "hesitant": False, "at": at}]},
            user=user,
        )

    def test_两个用户互不可见也不能靠同键互吞(self):
        # 同一题、同一时刻，两个用户各一条：去重键含 user，谁也不吞谁。
        self.assertEqual(self.attempt("q1", T0, "tiger").status_code, 200)
        self.assertEqual(self.attempt("q1", T0, "second").status_code, 200)
        # 各自只看到自己那条；返回行不回传 user（它是请求方自己的身份）。
        data = self.get("/attempts").get_json()
        self.assertEqual(len(data["items"]), 1)
        self.assertNotIn("user", data["items"][0])
        data = self.get("/attempts", user="second").get_json()
        self.assertEqual(len(data["items"]), 1)

    def test_成就与草稿按用户独立(self):
        self.assertEqual(self.put("/achievements/streak.5", {"at": T0}, user="tiger").status_code, 200)
        # second 解锁同一个成就，各记各的（时间不同也互不覆盖）。
        r = self.put("/achievements/streak.5", {"at": T1}, user="second").get_json()
        self.assertEqual(r["at"], T1)
        keys = [a["key"] for a in self.get("/achievements", user="second").get_json()["items"]]
        self.assertEqual(keys, ["streak.5"])

        draft = {"subject_id": "subject1", "title": "模拟考", "question_ids": "[]",
                 "question_count": 100, "minutes": 45, "pass_score": 90,
                 "points_per_question": 1, "mix": "{}", "full_bank": 0,
                 "picked": "{}", "started_at": T0}
        self.assertEqual(self.put("/exam-drafts/subject1.exam", draft, user="tiger").status_code, 200)
        self.assertEqual(self.put("/exam-drafts/subject1.exam", draft, user="second").status_code, 200)
        # tiger 删掉自己的草稿，second 的还在。
        self.assertEqual(self.client.delete(BASE + "/exam-drafts/subject1.exam",
                                           headers={**self.headers, "X-Athena-User": "tiger"}).status_code, 204)
        self.assertEqual(self.get("/exam-drafts/subject1.exam", user="second").status_code, 200)

    def test_缺用户头与空用户名都是400(self):
        r = self.client.get(BASE + "/attempts")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.get_json()["error"], "invalid")
        r = self.client.get(BASE + "/attempts", headers={"X-Athena-User": "  "})
        self.assertEqual(r.status_code, 400)
