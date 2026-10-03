"""学习诊断（主仓库 ADR 0076 决策 10）：记忆保持、错因、选错的方式、强化练习成效。

**口径与客户端完全一致**（ADR 0069：与客户端不一致时以客户端为准）——定义、门槛、阈值都照
`subjects/driver/lib/diagnosis.dart` 一一对应；改一边要改另一边。

服务端**读不到题库内容**（应用间构建隔离，路由器上没有驾考题库），所以这里只做「只靠作答记录就能算」
的几块：
- 记忆保持（只要作答时间序列）；
- 错因：粗心 / 不会 / 不熟（只要用时和对错）；
- 选错的方式：能算「反复选同一个错选项」（只要所选选项和对错）；多选题漏选还是多选需要知道正确答案，
  服务端算不了；
- 强化练习成效与变式差距（只要场合、选题理由和对错）。
「与全国错误率比」需要题库里的 `error_rate`，服务端没有，不做，页面上明说去客户端看。

全部按**单个学习者**算：遗忘、错因都是「这个人」的事，混着算没有意义。
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime
from typing import Any, Iterable

# ---- 阈值（与 lib/diagnosis.dart 同值）
RETENTION_MIN_SAMPLE = 15
CAUSE_MIN_CORRECT_FOR_MEDIAN = 20
FAST_RATIO = 0.6
SLOW_RATIO = 1.6
DURATION_CAP_MS = 300_000
VARIANT_GAP_ENOUGH = 10

RETENTION_EDGES = [
    ("同一天", 0, 0),
    ("隔 1 天", 1, 1),
    ("隔 2～3 天", 2, 3),
    ("隔 4～7 天", 4, 7),
    ("隔 8～14 天", 8, 14),
    ("隔 15 天以上", 15, 10**9),
]

CAUSES = ("careless", "unknown", "ordinary", "shaky")
CAUSE_LABELS = {"careless": "粗心", "unknown": "不会", "ordinary": "一般错", "shaky": "不熟"}
CAUSE_ADVICE = {
    "careless": "答得比平时快很多就错了：多半没读完题干或选项。放慢一点，圈出题干里的限定词再选。",
    "unknown": "想了很久还是错：这是真的没掌握，回去看条文和解析，再用强化练习复测。",
    "ordinary": "用时正常的错题：按错题本和强化练习的复测去消化就行。",
    "shaky": "答对了但比平时慢很多：知道，但不扎实。间隔复习最适合这类题。",
}

REASON_LABELS = {
    "retest": "复测错题 · 转正率",
    "variant": "同考点变式 · 答对率",
    "weak": "薄弱章节 · 答对率",
    "due": "到期复习 · 保持率",
    "fill": "补足 · 答对率",
}


def _parse(at: Any) -> datetime | None:
    if not isinstance(at, str):
        return None
    try:
        return datetime.fromisoformat(at)
    except ValueError:
        return None


def _day(at: datetime) -> date:
    return at.date()


Row = dict[str, Any]


def _clean(rows: Iterable[Row]) -> list[Row]:
    """补上解析好的时间；时间解析不了的行跳过（与客户端 allAttempts 同）。"""
    out: list[Row] = []
    for r in rows:
        when = _parse(r.get("at"))
        if when is not None:
            out.append({**r, "_at": when, "correct": bool(r.get("correct"))})
    return out


# ---------------------------------------------------------------- 记忆保持


def forgetting_curve(rows: Iterable[Row]) -> list[dict[str, Any]]:
    """同一道题**相邻两次**作答，前一次答对，按间隔的日历天数分档，看后一次答对的比例。"""
    by_question: dict[str, list[Row]] = defaultdict(list)
    for r in _clean(rows):
        by_question[r["question_id"]].append(r)
    n = [0] * len(RETENTION_EDGES)
    ok = [0] * len(RETENTION_EDGES)
    for attempts in by_question.values():
        attempts.sort(key=lambda r: r["_at"])
        for previous, current in zip(attempts, attempts[1:]):
            if not previous["correct"]:
                continue
            gap = (_day(current["_at"]) - _day(previous["_at"])).days
            for slot, (_, low, high) in enumerate(RETENTION_EDGES):
                if low <= gap <= high:
                    n[slot] += 1
                    if current["correct"]:
                        ok[slot] += 1
                    break
    return [
        {
            "label": RETENTION_EDGES[i][0],
            "n": n[i],
            "correct": ok[i],
            "rate": (ok[i] / n[i]) if n[i] else None,
            "enough": n[i] >= RETENTION_MIN_SAMPLE,
        }
        for i in range(len(RETENTION_EDGES))
    ]


# ---------------------------------------------------------------- 错因


def error_causes(rows: Iterable[Row], topic_titles: dict[str, str]) -> dict[str, Any]:
    """标尺是这位学习者自己答对题的用时中位数：比它快很多就错的叫粗心，比它慢很多还错的叫不会，
    答对但慢很多的叫不熟。用时无效（0 或超过封顶）的不参与。"""
    valid = [r for r in _clean(rows) if 0 < int(r.get("duration_ms") or 0) <= DURATION_CAP_MS]
    correct_times = sorted(int(r["duration_ms"]) for r in valid if r["correct"])
    counts = {c: 0 for c in CAUSES}
    if len(correct_times) < CAUSE_MIN_CORRECT_FOR_MEDIAN:
        return {"median_ms": None, "counts": counts, "sample": len(valid), "by_cause": {}}
    median = correct_times[len(correct_times) // 2]
    by_topic: dict[str, Counter] = {c: Counter() for c in CAUSES}
    for r in valid:
        d = int(r["duration_ms"])
        fast, slow = d <= median * FAST_RATIO, d >= median * SLOW_RATIO
        if not r["correct"]:
            cause = "careless" if fast else ("unknown" if slow else "ordinary")
        elif slow:
            cause = "shaky"
        else:
            continue
        counts[cause] += 1
        by_topic[cause][r["topic_id"]] += 1
    by_cause = {
        cause: [{"title": topic_titles.get(t, t), "n": c} for t, c in by_topic[cause].most_common(3)]
        for cause in CAUSES
    }
    return {"median_ms": median, "counts": counts, "sample": len(valid), "by_cause": by_cause}


# ---------------------------------------------------------------- 选错的方式


def confusion(rows: Iterable[Row], topic_titles: dict[str, str], limit: int = 10) -> dict[str, Any]:
    """只看记了所选选项的答错作答。单选和判断题看是不是总选同一个错选项；多选题（所选里有逗号）
    只数个数——漏选还是多选需要正确答案，服务端没有题库，算不了。"""
    wrong_total = with_chosen = multi_wrong = 0
    picks: Counter = Counter()
    topic_of: dict[str, str] = {}
    for r in _clean(rows):
        if r["correct"]:
            continue
        wrong_total += 1
        chosen = r.get("chosen")
        if not chosen:
            continue
        with_chosen += 1
        topic_of[r["question_id"]] = r["topic_id"]
        if "," in chosen:
            multi_wrong += 1
        else:
            picks[(r["question_id"], chosen)] += 1
    repeated = sorted(((q, c, n) for (q, c), n in picks.items() if n >= 2), key=lambda t: (-t[2], t[0]))
    return {
        "wrong_total": wrong_total,
        "with_chosen": with_chosen,
        "multi_wrong": multi_wrong,
        "repeated": [
            {
                "question_id": q,
                "serial": q.removeprefix("drive."),
                "topic": topic_titles.get(topic_of.get(q, ""), topic_of.get(q, "")),
                "chosen": c,
                "times": n,
            }
            for q, c, n in repeated[:limit]
        ],
    }


# ---------------------------------------------------------------- 强化练习成效


def reason_outcomes(rows: Iterable[Row]) -> list[dict[str, Any]]:
    n: Counter = Counter()
    ok: Counter = Counter()
    for r in _clean(rows):
        reason = r.get("reason")
        if r.get("kind") != "reinforce" or not reason:
            continue
        n[reason] += 1
        if r["correct"]:
            ok[reason] += 1
    return [
        {"reason": reason, "label": label, "n": n[reason], "correct": ok[reason], "rate": ok[reason] / n[reason]}
        for reason, label in REASON_LABELS.items()
        if n[reason]
    ]


def variant_gap(outcomes: list[dict[str, Any]]) -> dict[str, Any] | None:
    """复测原题答对率减去同考点变式答对率；正数 = 换了问法就答不好。两类都有才算得出。"""
    retest = next((o for o in outcomes if o["reason"] == "retest"), None)
    variant = next((o for o in outcomes if o["reason"] == "variant"), None)
    if retest is None or variant is None:
        return None
    return {
        "retest_rate": retest["rate"],
        "retest_n": retest["n"],
        "variant_rate": variant["rate"],
        "variant_n": variant["n"],
        "gap": retest["rate"] - variant["rate"],
        "enough": retest["n"] >= VARIANT_GAP_ENOUGH and variant["n"] >= VARIANT_GAP_ENOUGH,
    }


# ---------------------------------------------------------------- 取数


def _learner_names() -> dict[str, str]:
    """学习者目录（后台库 athena_users）里的称呼。目录读不到不影响诊断，退回显示编号。"""
    from sqlalchemy import select

    from nas_admin.user_api import directory

    try:
        engine = directory.engine()
        directory.ensure_table(engine)
        with engine.connect() as conn:
            return {str(r.id): r.name for r in conn.execute(select(directory.users.c.id, directory.users.c.name))}
    except Exception:  # noqa: BLE001 —— 称呼只是装饰，任何失败都降级
        return {}


def learners() -> list[dict[str, Any]]:
    """有作答记录的学习者，作答最多的排前面（页面默认选第一个）。"""
    from sqlalchemy import func, select

    from nas_admin.driver_api import schema, store

    a = schema.attempts
    with store.engine().connect() as conn:
        counts = conn.execute(
            select(a.c.user, func.count()).group_by(a.c.user).order_by(func.count().desc(), a.c.user)
        ).all()
    names = _learner_names()
    return [
        {"id": user, "name": names.get(user, f"学习者 {user}"), "attempts": int(n)}
        for user, n in counts
    ]


def attempts_of(user: str) -> list[Row]:
    from sqlalchemy import select

    from nas_admin.driver_api import schema, store

    a = schema.attempts
    cols = [a.c.question_id, a.c.topic_id, a.c.correct, a.c.duration_ms, a.c.at, a.c.kind, a.c.chosen, a.c.reason]
    with store.engine().connect() as conn:
        return [dict(r._mapping) for r in conn.execute(select(*cols).where(a.c.user == user).order_by(a.c.at))]


# ---------------------------------------------------------------- 汇总


def build(rows: list[Row], topic_titles: dict[str, str]) -> dict[str, Any]:
    outcomes = reason_outcomes(rows)
    return {
        "attempts": len(rows),
        "retention": forgetting_curve(rows),
        "causes": {**error_causes(rows, topic_titles), "labels": CAUSE_LABELS, "advice": CAUSE_ADVICE},
        "confusion": confusion(rows, topic_titles),
        "outcomes": outcomes,
        "variant_gap": variant_gap(outcomes),
    }
