"""学习进度通用同步 API 测试（ADR 0155）。

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
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from nas_admin import access  # noqa: E402
from nas_admin.progress_api import init_progress_api  # noqa: E402

BASE = "/api/progress/v1"
T1 = "2026-10-13T01:00:00.000Z"
T2 = "2026-10-13T02:00:00.000Z"
T3 = "2026-10-13T03:00:00.000Z"


def row(tbl="knowledge_progress", pk="c.1", mode="lww", stamp=T1, data=None, deleted=False):
    item = {"tbl": tbl, "pk": pk, "mode": mode, "stamp": stamp}
    if deleted:
        item["deleted"] = True
    else:
        item["data"] = {"mastery": 1} if data is None else data
    return item


class ProgressApiCase(unittest.TestCase):
    def setUp(self) -> None:
        access.reset_rate_limits()
        self.engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        app = Flask(__name__)
        init_progress_api(app, engine=self.engine)
        self.client = app.test_client()

    def push(self, rows, *, app="c-plus-plus", device="pc-a", user="1", body=None):
        payload = body if body is not None else {"app": app, "device": device, "rows": rows}
        headers = {"X-Athena-User": user} if user is not None else {}
        return self.client.post(BASE + "/push", json=payload, headers=headers)

    def pull(self, *, app="c-plus-plus", since=0, limit=None, user="1"):
        query = f"?app={app}&since={since}" + (f"&limit={limit}" if limit else "")
        headers = {"X-Athena-User": user} if user is not None else {}
        return self.client.get(BASE + "/pull" + query, headers=headers)


class PushPullTests(ProgressApiCase):
    def test_推上去的行能拉回来(self):
        r = self.push([row(pk="c.1", data={"mastery": 3})])
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        self.assertEqual(r.get_json(), {"accepted": 1, "ignored": 0, "cursor": 1})
        pulled = self.pull().get_json()
        self.assertEqual(len(pulled["rows"]), 1)
        got = pulled["rows"][0]
        self.assertEqual((got["tbl"], got["pk"], got["data"], got["device"]), ("knowledge_progress", "c.1", {"mastery": 3}, "pc-a"))
        self.assertFalse(pulled["more"])

    def test_重复推送幂等(self):
        self.push([row()])
        again = self.push([row()]).get_json()
        self.assertEqual((again["accepted"], again["ignored"]), (0, 1))
        self.assertEqual(len(self.pull().get_json()["rows"]), 1)

    def test_按序号增量拉取(self):
        self.push([row(pk="a"), row(pk="b")])
        first = self.pull().get_json()
        self.push([row(pk="c")])
        later = self.pull(since=first["next"]).get_json()
        self.assertEqual([r["pk"] for r in later["rows"]], ["c"])

    def test_分页(self):
        self.push([row(pk=f"k{i}") for i in range(5)])
        page = self.pull(limit=2).get_json()
        self.assertEqual((len(page["rows"]), page["more"]), (2, True))
        rest = self.pull(since=page["next"], limit=10).get_json()
        self.assertEqual((len(rest["rows"]), rest["more"]), (3, False))

    def test_学习者与应用互相隔离(self):
        self.push([row()], user="1")
        self.assertEqual(self.pull(user="2").get_json()["rows"], [])
        self.assertEqual(self.pull(app="algorithms").get_json()["rows"], [])


class MergeTests(ProgressApiCase):
    def test_lww_新者胜(self):
        self.push([row(stamp=T1, data={"mastery": 1})])
        r = self.push([row(stamp=T2, data={"mastery": 4})], device="pc-b").get_json()
        self.assertEqual(r["accepted"], 1)
        got = self.pull().get_json()["rows"][0]
        self.assertEqual((got["data"], got["device"]), ({"mastery": 4}, "pc-b"))

    def test_lww_旧者被忽略(self):
        self.push([row(stamp=T2, data={"mastery": 4})])
        r = self.push([row(stamp=T1, data={"mastery": 1})], device="pc-b").get_json()
        self.assertEqual((r["accepted"], r["ignored"]), (0, 1))
        self.assertEqual(self.pull().get_json()["rows"][0]["data"], {"mastery": 4})

    def test_lww_同一时刻按设备名定胜负且确定(self):
        self.push([row(stamp=T1, data={"v": "a"})], device="pc-a")
        self.push([row(stamp=T1, data={"v": "b"})], device="pc-b")  # pc-b > pc-a，胜
        self.push([row(stamp=T1, data={"v": "a"})], device="pc-a")  # 再来一次，败
        self.assertEqual(self.pull().get_json()["rows"][0]["data"], {"v": "b"})

    def test_append_只记第一次(self):
        self.push([row(tbl="attempts", pk="q1|t1", mode="append", stamp=T1, data={"ok": 1})])
        r = self.push([row(tbl="attempts", pk="q1|t1", mode="append", stamp=T3, data={"ok": 0})], device="pc-b").get_json()
        self.assertEqual((r["accepted"], r["ignored"]), (0, 1))
        self.assertEqual(self.pull().get_json()["rows"][0]["data"], {"ok": 1})

    def test_append_墓碑标记删除但保留原数据(self):
        # ADR 0156：事件表的删除也是一个新增的事实（墓碑），不是真删——原数据留着，可审计、可恢复。
        self.push([row(tbl="attempts", pk="q1|t1", mode="append", stamp=T1, data={"ok": 1})])
        r = self.push([row(tbl="attempts", pk="q1|t1", mode="append", stamp=T2, deleted=True)], device="pc-b").get_json()
        self.assertEqual((r["accepted"], r["ignored"]), (1, 0))
        got = self.pull().get_json()["rows"][0]
        self.assertTrue(got["deleted"])
        self.assertEqual(got["data"], {"ok": 1})
        self.assertEqual(got["device"], "pc-b")

    def test_append_墓碑只增不减_重复与复活都被忽略(self):
        self.push([row(tbl="attempts", pk="q1|t1", mode="append", stamp=T1, data={"ok": 1})])
        self.push([row(tbl="attempts", pk="q1|t1", mode="append", stamp=T2, deleted=True)], device="pc-b")
        top = self.pull().get_json()["next"]
        again = self.push([row(tbl="attempts", pk="q1|t1", mode="append", stamp=T3, deleted=True)], device="pc-c").get_json()
        revive = self.push([row(tbl="attempts", pk="q1|t1", mode="append", stamp=T3, data={"ok": 0})], device="pc-c").get_json()
        self.assertEqual((again["accepted"], revive["accepted"]), (0, 0))
        got = self.pull().get_json()
        self.assertEqual(got["next"], top, "被忽略的写入不该分配新序号")
        self.assertTrue(got["rows"][0]["deleted"])

    def test_append_对没见过的键直接落墓碑(self):
        r = self.push([row(tbl="attempts", pk="q9|t9", mode="append", stamp=T1, deleted=True)]).get_json()
        self.assertEqual(r["accepted"], 1)
        got = self.pull().get_json()["rows"][0]
        self.assertTrue(got["deleted"])
        self.assertIsNone(got["data"])

    def test_删除是一行带标记的记录并清掉数据(self):
        self.push([row(stamp=T1)])
        self.push([row(stamp=T2, deleted=True)], device="pc-b")
        got = self.pull().get_json()["rows"][0]
        self.assertTrue(got["deleted"])
        self.assertIsNone(got["data"])

    def test_删除之后更旧的写入不能复活(self):
        self.push([row(stamp=T2, deleted=True)])
        self.push([row(stamp=T1, data={"mastery": 9})], device="pc-b")
        self.assertTrue(self.pull().get_json()["rows"][0]["deleted"])


class ValidationTests(ProgressApiCase):
    def assert_invalid(self, response, needle=""):
        self.assertEqual(response.status_code, 400, response.get_data(as_text=True))
        body = response.get_json()
        self.assertEqual(body["error"], "invalid")
        self.assertIn(needle, body["message"])

    def test_缺学习者头(self):
        self.assert_invalid(self.push([row()], user=None), "X-Athena-User")
        self.assert_invalid(self.pull(user=None), "X-Athena-User")

    def test_学习者编号越界(self):
        self.assert_invalid(self.push([row()], user="0"), "X-Athena-User")
        self.assert_invalid(self.push([row()], user="1000"), "X-Athena-User")

    def test_应用id格式(self):
        self.assert_invalid(self.push([row()], app="C++"), "app")
        self.assert_invalid(self.pull(app="Bad_App"), "app")

    def test_时间必须是UTC格式(self):
        self.assert_invalid(self.push([row(stamp="2026-10-13 01:00:00")]), "stamp")
        self.assert_invalid(self.push([row(stamp="2026-10-13T01:00:00+08:00")]), "stamp")

    def test_时间的小数位必须是三位毫秒(self):
        # 字符串比较只在格式一致时等于时间比较：无小数、微秒与毫秒混用会把先后比反
        # （"03.5Z" < "03Z"、"03.123456Z" < "03.123Z"），所以只认固定三位。
        for bad in ("2026-10-13T01:00:00Z", "2026-10-13T01:00:00.5Z", "2026-10-13T01:00:00.123456Z"):
            self.assert_invalid(self.push([row(stamp=bad)]), "stamp")

    def test_模式只有两种(self):
        self.assert_invalid(self.push([row(mode="merge")]), "mode")

    def test_未知字段被拒绝(self):
        bad = row()
        bad["oops"] = 1
        self.assert_invalid(self.push([bad]), "oops")
        self.assert_invalid(self.push([], body={"app": "x", "device": "d", "rows": [], "extra": 1}), "extra")

    def test_未删除的行必须带数据(self):
        item = row()
        del item["data"]
        self.assert_invalid(self.push([item]), "data")

    def test_数据必须是对象(self):
        item = row()
        item["data"] = [1, 2]
        self.assert_invalid(self.push([item]), "data")

    def test_表名格式(self):
        self.assert_invalid(self.push([row(tbl="a b")]), "tbl")

    def test_一批最多500行(self):
        self.assert_invalid(self.push([row(pk=str(i)) for i in range(501)]), "rows")

    def test_校验失败时整批不落库(self):
        self.assert_invalid(self.push([row(pk="ok"), row(mode="bad")]))
        self.assertEqual(self.pull().get_json()["rows"], [])

    def test_拉取参数必须是整数(self):
        r = self.client.get(BASE + "/pull?app=x&since=abc", headers={"X-Athena-User": "1"})
        self.assert_invalid(r, "since")


class AccessTests(ProgressApiCase):
    def test_不需要令牌(self):
        self.assertEqual(self.push([row()]).status_code, 200)

    def test_超过限流返回429(self):
        with mock.patch.object(access, "RATE_LIMIT", 2):
            self.assertEqual(self.pull().status_code, 200)
            self.assertEqual(self.pull().status_code, 200)
            self.assertEqual(self.pull().status_code, 429)

    def test_响应不缓存(self):
        self.assertEqual(self.pull().headers.get("Cache-Control"), "no-store")


if __name__ == "__main__":
    unittest.main()
