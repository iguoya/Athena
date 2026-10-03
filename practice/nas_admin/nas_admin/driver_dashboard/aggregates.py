"""驾考进度的聚合统计（只读）。

全部用 SQLAlchemy Core 构造，只发 SELECT；连接复用 driver_api 的低权限角色
（无 DDL，见 docs/driver-api.md 部署一节）。

口径（ADR 0069：与客户端不一致时以客户端为准）：
- 「按天」= `at` 的前 10 个字符。`at` 是客户端本地的 ISO-8601 串、服务端原样保存
  （0068 同步模型），前缀分组与客户端的字符串比较同口径，不引入数据库时区。
- 连续练习天数 = 客户端 `DailyActivityChart.dayStreak`（look.dart）：从今天往前数，
  连续有练习的天数；今天还没练就是 0。窗口末端用服务器本机日期——家用环境下服务端
  与客户端同时区，只有跨时区查看时「今天」一格才可能错位。
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import Connection, and_, func, or_, select

from nas_admin.driver_api import schema
from nas_admin.driver_api import store

DAILY_WINDOW = 30  # 每日趋势的天数窗口，对齐客户端首页「最近 14 天」的思路放宽到月

# 科目 id 与标题来自 subjects/driver/content/curriculum.json（subject3 是路考，
# 不在题库里，练车数据不带科目）。这里只放展示名，不复制内容（应用间构建隔离）。
# wrong / review 不是科目，是客户端的练习场景（错题本、考前复习，home.dart 的
# _wrongId / _reviewId）——作答记录里带这两个 subject_id，正确率单独看才有意义。
SUBJECT_TITLES: dict[str, tuple[str, str]] = {
    "subject1": ("科目一", "道路交通安全法律、法规和相关知识"),
    "subject2": ("科目二", "场地驾驶技能（C2）"),
    "subject4": ("科目四", "安全文明驾驶常识"),
    "wrong": ("错题本", "错题重练"),
    "review": ("复习", "考前复习"),
}

# 章节展示名同样来自 curriculum.json 的 topic 标题（只放名字，不复制教学内容，
# 与 SUBJECT_TITLES 同一先例）。服务端不读 driver 的内容 JSON——应用间构建隔离。
TOPIC_TITLES: dict[str, str] = {
    "drive.s1.license": "驾驶证与准驾",
    "drive.s1.registration": "机动车登记与检验",
    "drive.s1.henan": "河南地方法规",
    "drive.s1.rules": "通行、超车与让行",
    "drive.s1.alcohol": "饮酒、疲劳与安全义务",
    "drive.s1.penalty": "违法记分与处罚",
    "drive.s1.accident": "交通事故处理",
    "drive.s1.signals": "交通信号与标志",
    "drive.s1.lights": "灯光使用",
    "drive.s1.highway": "高速公路",
    "drive.s1.occupants": "安全带、停放与乘员",
    "drive.s2.general": "合格标准与通用评判",
    "drive.s2.reverse": "倒车入库",
    "drive.s2.parallel": "侧方停车",
    "drive.s2.curve": "曲线行驶",
    "drive.s2.corner": "直角转弯",
    "drive.s4.crash": "事故现场与责任",
    "drive.s4.lights": "灯光与视线",
    "drive.s4.weather": "恶劣气象与复杂道路",
    "drive.s4.emergency": "故障、警告标志与避险",
    "drive.s4.yield": "让行与弱势交通参与者",
    "drive.s4.maneuver": "行车操作与车距",
    "drive.s4.civil": "安全文明驾驶",
    "drive.s4.aid": "伤员救护义务",
}

# 正式科目（wrong / review 是练习场景，不算章节归属的科目）
REAL_SUBJECTS = ("subject1", "subject2", "subject4")
# 理论考试的科目（科目一是法规、科目四是安全文明；科目二是场地实操、科目三是
# 路考，不是理论考试）——分科标签页只做这两科，科目二的练习仍在总览可见。
THEORY_SUBJECTS = ("subject1", "subject4")

EXAM_PASS_LINE = 90  # 100 分制下的及格线，仅作图表参考线；数据里已有 passed

# 单题用时统计上限（driver ADR 0057 客户端封顶同值）：历史挂机脏值不拉偏平均。
DURATION_CAP_MS = 300_000


def _day_of(at: Any) -> Any:
    return func.substr(at, 1, 10)


def collect(days: int = DAILY_WINDOW) -> dict[str, Any]:
    """一次连接跑完全部聚合。调用方负责把异常映射成降级响应。"""
    with store.engine().connect() as conn:
        return {
            "overview": _overview(conn),
            "daily": _daily(conn, days),
            "calendar": _calendar(conn),
            "subjects": _subjects(conn),
            "sunburst": _sunburst(conn),
            "radar": _radar(conn),
            "exams": _exam_list(conn),
            "achievements": _achievement_list(conn),
            "details": {sid: _subject_detail(conn, sid) for sid in THEORY_SUBJECTS},
        }


def _topic_subject(topic_id: str) -> str | None:
    """章节 id（drive.s1.rules）归属的科目（subject1）；格式不合返回 None。
    错题本/复习场景的 subject_id 是 wrong/review，章节归属要看 topic 前缀。"""
    parts = topic_id.split(".")
    if len(parts) == 3 and parts[1][:1] == "s" and parts[1][1:].isdigit():
        return f"subject{parts[1][1:]}"
    return None


def _subject_detail(conn: Connection, subject_id: str) -> dict[str, Any] | None:
    """单科目深挖（ADR 0069 的展示范围）。

    练习 = 该科目的正式作答；错题重练 = wrong/review 场景里挂在该科目章节上的作答。
    模拟考只有科目级分数（exams 表不记逐题），按章节的考试数据需要客户端补记录，
    这里不虚构。库里另有 hesitant（迟疑）列，但客户端早已去掉迟疑概念（driver
    提交 3c4276b），那是迁移遗留的历史字段，不参与统计。没练过也没考过的科目
    返回 None，前端不出这个标签页。
    """
    a = schema.attempts
    rows = conn.execute(
        select(a.c.topic_id, func.count(), func.coalesce(func.sum(a.c.correct), 0))
        .where(a.c.subject_id == subject_id)
        .group_by(a.c.topic_id)
    ).all()
    day_rows = conn.execute(
        select(a.c.topic_id, _day_of(a.c.at).label("day"), func.count(), func.coalesce(func.sum(a.c.correct), 0))
        .where(a.c.subject_id == subject_id)
        .group_by(a.c.topic_id, "day")
    ).all()
    chapters = [
        {
            "id": r[0],
            "title": TOPIC_TITLES.get(r[0], r[0]),
            "attempts": int(r[1]),
            "correct": int(r[2]),
            "rate": round(int(r[2]) / int(r[1]), 4) if r[1] else None,
        }
        for r in sorted(rows, key=lambda r: -r[1])
    ]
    if not chapters and not day_rows:
        exams_n = conn.execute(
            select(func.count()).select_from(schema.exams).where(schema.exams.c.subject_id == subject_id)
        ).scalar_one()
        if exams_n == 0:
            return None
    # 错题/复习场景按章节归属进该科目
    wrong_rows = conn.execute(
        select(a.c.topic_id, a.c.subject_id, func.count(), func.coalesce(func.sum(a.c.correct), 0))
        .where(a.c.subject_id.in_(["wrong", "review"]))
        .group_by(a.c.topic_id, a.c.subject_id)
    ).all()
    wrong_drill: dict[str, dict[str, int]] = {}
    for topic, place, n, correct in wrong_rows:
        if _topic_subject(topic) != subject_id:
            continue
        slot = wrong_drill.setdefault(topic, {"attempts": 0, "correct": 0})
        slot["attempts"] += int(n)
        slot["correct"] += int(correct)

    wrong = _wrong_analysis(conn, subject_id, chapters)
    _exam_chapters(conn, subject_id, chapters)

    return {
        "title": SUBJECT_TITLES.get(subject_id, (subject_id,))[0],
        "chapters": chapters,
        "chapter_days": [
            {"topic": r[0], "title": TOPIC_TITLES.get(r[0], r[0]), "day": str(r[1]), "attempts": int(r[2]), "correct": int(r[3])}
            for r in day_rows
        ],
        "wrong_drill": [
            {"id": t, "title": TOPIC_TITLES.get(t, t), "attempts": v["attempts"],
             "rate": round(v["correct"] / v["attempts"], 4) if v["attempts"] else None}
            for t, v in sorted(wrong_drill.items(), key=lambda kv: -kv[1]["attempts"])
        ],
        "wrong": wrong,
    }


def _exam_chapters(conn: Connection, subject_id: str, chapters: list[dict[str, Any]]) -> None:
    """模拟考的章节维度（driver ADR 0057 的 kind='exam'）：每章的考试作答量、
    正确率与丢分题数，并进章节列表。没有模拟考作答的科目全部为 0/None，
    前端不画这张图。"""
    a = schema.attempts
    rows = conn.execute(
        select(a.c.topic_id, func.count(), func.coalesce(func.sum(a.c.correct), 0))
        .where(and_(a.c.subject_id == subject_id, a.c.kind == "exam"))
        .group_by(a.c.topic_id)
    ).all()
    missed: dict[str, int] = {}
    for topic, _q in conn.execute(
        select(a.c.topic_id, a.c.question_id).where(and_(a.c.subject_id == subject_id, a.c.kind == "exam", a.c.correct == 0)).distinct()
    ):
        missed[topic] = missed.get(topic, 0) + 1
    stats = {r[0]: (int(r[1]), int(r[2])) for r in rows}
    for chapter in chapters:
        n, correct = stats.get(chapter["id"], (0, 0))
        chapter["exam_attempts"] = n
        chapter["exam_rate"] = round(correct / n, 4) if n else None
        chapter["exam_wrong_questions"] = missed.get(chapter["id"], 0)


def _wrong_analysis(conn: Connection, subject_id: str, chapters: list[dict[str, Any]]) -> dict[str, Any]:
    """错题深挖：状态、消化曲线、顽固榜，并把章节错题维度并回章节列表。

    口径（写清楚，客户端语义为准的例外见 ADR 0069）：
    - 一道题的「见到次数」不分场景——正式练习、错题本、复习都算一次作答；
    - 「已攻克」= 曾经答错、且**最近两次**作答都答对（连对口径，防蒙对）；只见过
      一次或最近两次里有错的都算「仍错着」；
    - 消化曲线 = 同一道题第 n 次作答时的正确率，回答「重练到第几遍才稳」。

    数据量（每科目数千行）一次拉全在 Python 聚合，比多层窗口函数可读。
    """
    a = schema.attempts
    short = "s" + subject_id.removeprefix("subject")  # subject1 → s1，对应 topic 前缀 drive.s1.
    scope = or_(
        a.c.subject_id == subject_id,
        and_(a.c.subject_id.in_(["wrong", "review"]), a.c.topic_id.like(f"drive.{short}.%")),
    )
    rows = conn.execute(
        select(a.c.question_id, a.c.topic_id, a.c.correct, a.c.at).where(scope).order_by(a.c.question_id, a.c.at)
    ).all()

    per_q: dict[str, dict[str, Any]] = {}
    for qid, topic, correct, _at in rows:
        per_q.setdefault(qid, {"topic": topic, "seq": []})["seq"].append(int(correct))

    by_topic_wrong: dict[str, set[str]] = {}
    by_topic_seen: dict[str, set[str]] = {}
    curve: dict[int, list[int]] = {}
    ever_wrong = fixed = 0
    stubborn: list[dict[str, Any]] = []
    for qid, item in per_q.items():
        seq = item["seq"]
        by_topic_seen.setdefault(item["topic"], set()).add(qid)
        for n, correct in enumerate(seq, 1):
            slot = curve.setdefault(n, [0, 0])
            slot[0] += 1
            slot[1] += correct
        wrongs = seq.count(0)
        if wrongs == 0:
            continue
        ever_wrong += 1
        by_topic_wrong.setdefault(item["topic"], set()).add(qid)
        if len(seq) >= 2 and seq[-1] == 1 and seq[-2] == 1:
            fixed += 1
            state = "fixed"
        else:
            state = "still"
        stubborn.append({"qid": qid, "topic": item["topic"], "wrongs": wrongs, "total": len(seq), "state": state})

    # 章节错题维度并回章节列表。只在错题本/复习里出现、正式练习为 0 的章节也补进
    # 列表（attempts 0 但带着错题统计）——否则那些章的错题就无处安放。
    chapter_by_id = {c["id"]: c for c in chapters}
    for topic, seen in by_topic_seen.items():
        chapter = chapter_by_id.get(topic)
        if chapter is None:
            chapter = {"id": topic, "title": TOPIC_TITLES.get(topic, topic),
                       "attempts": 0, "correct": 0, "rate": None}
            chapter_by_id[topic] = chapter
            chapters.append(chapter)
        chapter["questions"] = len(seen)
        chapter["wrong_questions"] = len(by_topic_wrong.get(topic, set()))
        chapter["miss_rate"] = round(chapter["wrong_questions"] / len(seen), 4) if seen else None

    stubborn.sort(key=lambda s: (-s["wrongs"], s["qid"]))
    return {
        "questions": len(per_q),
        "ever_wrong": ever_wrong,
        "fixed": fixed,
        "still": ever_wrong - fixed,
        "repeat_curve": [
            {"n": n, "count": slot[0], "rate": round(slot[1] / slot[0], 4)} for n, slot in sorted(curve.items())
        ],
        "stubborn": [
            {
                "title": TOPIC_TITLES.get(s["topic"], s["topic"]),
                "no": s["qid"].rsplit(".", 1)[-1],
                "wrongs": s["wrongs"],
                "total": s["total"],
                "fixed": s["state"] == "fixed",
            }
            for s in stubborn[:10]
        ],
    }


def _overview(conn: Connection) -> dict[str, Any]:
    a = schema.attempts
    total, correct = conn.execute(select(func.count(), func.coalesce(func.sum(a.c.correct), 0))).one()
    avg_ms = conn.execute(select(func.avg(a.c.duration_ms)).where(a.c.duration_ms.between(1, DURATION_CAP_MS))).scalar_one()
    last_day = conn.execute(select(func.max(_day_of(a.c.at)))).scalar_one()
    exams_n = conn.execute(select(func.count()).select_from(schema.exams)).scalar_one()
    achievements_n = conn.execute(select(func.count()).select_from(schema.achievements)).scalar_one()
    drills = conn.execute(select(func.count()).select_from(schema.drill_runs)).scalar_one()
    rehearsals = conn.execute(select(func.count()).select_from(schema.rehearsals)).scalar_one()
    return {
        "attempts": int(total),
        "correct": int(correct),
        "rate": round(int(correct) / int(total), 4) if total else None,
        "avg_duration_ms": round(avg_ms) if avg_ms is not None else None,
        "exams": int(exams_n),
        "achievements": int(achievements_n),
        "drills": int(drills),
        "rehearsals": int(rehearsals),
        "last_day": last_day,
    }


def _daily(conn: Connection, days: int) -> list[dict[str, Any]]:
    """按天聚合后补齐窗口里的空白天，时间正序（老的在左），对齐客户端图表。"""
    a = schema.attempts
    rows = conn.execute(
        select(_day_of(a.c.at).label("day"), func.count(), func.coalesce(func.sum(a.c.correct), 0)).group_by("day")
    ).all()
    by_day = {str(r[0]): (int(r[1]), int(r[2])) for r in rows}
    today = date.today()
    window = []
    for offset in range(days - 1, -1, -1):
        day = (today - timedelta(days=offset)).isoformat()
        n, correct = by_day.get(day, (0, 0))
        window.append({"date": day, "attempts": n, "correct": correct})
    return window


def day_streak(daily: list[dict[str, Any]]) -> int:
    """客户端 dayStreak 口径：从今天（窗口最后一天）往前数，连续有练习的天数。"""
    streak = 0
    for row in reversed(daily):
        if row["attempts"] == 0:
            break
        streak += 1
    return streak


def _subjects(conn: Connection) -> list[dict[str, Any]]:
    a, e = schema.attempts, schema.exams
    by_attempts = {
        r[0]: (int(r[1]), int(r[2]))
        for r in conn.execute(select(a.c.subject_id, func.count(), func.coalesce(func.sum(a.c.correct), 0)).group_by(a.c.subject_id))
    }
    by_exams = {
        r[0]: (int(r[1]), float(r[2]) if r[2] is not None else None, int(r[3]))
        for r in conn.execute(select(e.c.subject_id, func.count(), func.avg(e.c.score), func.coalesce(func.sum(e.c.passed), 0)).group_by(e.c.subject_id))
    }
    out = []
    for sid in sorted(set(by_attempts) | set(by_exams)):
        short, full = SUBJECT_TITLES.get(sid, (sid, sid))
        attempts, correct = by_attempts.get(sid, (0, 0))
        exams_n, exam_avg, exam_passed = by_exams.get(sid, (0, None, 0))
        out.append(
            {
                "id": sid,
                "title": short,
                "full_title": full,
                "attempts": attempts,
                "correct": correct,
                "rate": round(correct / attempts, 4) if attempts else None,
                "exams": exams_n,
                "exam_avg": round(exam_avg, 1) if exam_avg is not None else None,
                "exam_passed": exam_passed,
            }
        )
    return out


def _exam_list(conn: Connection) -> list[dict[str, Any]]:
    e = schema.exams
    rows = conn.execute(select(e.c.at, e.c.subject_id, e.c.score, e.c.passed).order_by(e.c.at)).all()
    return [
        {"at": r[0], "subject": SUBJECT_TITLES.get(r[1], (r[1],))[0], "score": int(r[2]), "passed": bool(r[3])}
        for r in rows
    ]


def _achievement_label(key: str) -> str:
    """成就文案在客户端是解锁时动态生成的（progress.dart），库里只有 key 与时间；
    这里从 key 推导可读名，不复制题库内容。"""
    if key.startswith("streak."):
        return f"连对 {key.removeprefix('streak.')} 题"
    if key.startswith("topic."):
        return "章节过关"
    if key.startswith("exam.pass."):
        subject = key.removeprefix("exam.pass.")
        return f"{SUBJECT_TITLES.get(subject, (subject,))[0]}模拟考首次及格"
    return key


def _achievement_list(conn: Connection) -> list[dict[str, Any]]:
    a = schema.achievements
    rows = conn.execute(select(a.c.key, a.c.at).order_by(a.c.at, a.c.key)).all()
    return [{"key": r[0], "label": _achievement_label(r[0]), "at": r[1]} for r in rows]


# ---------------------------------------------------------------- 可视化扩展（二期）


def _calendar(conn: Connection) -> list[list[Any]]:
    """全量按天的作答量，给日历热力图（[日期, 量] 对；没练的日子不出现在列表里，
    由前端日历底色表达）。GROUP BY 必须引用同一个标签列——各写一份 substr 表达式
    会生成两组绑定参数，PG 判定两表达式不同而报 GroupingError（SQLite 宽松测不出），
    与 _daily 同一模式。"""
    a = schema.attempts
    day = _day_of(a.c.at).label("day")
    rows = conn.execute(select(day, func.count()).group_by(day)).all()
    return [[str(r[0]), int(r[1])] for r in rows]


def _topic_stats(conn: Connection) -> dict[tuple[str, str], tuple[int, int]]:
    """(场景/科目, 章节) → (作答数, 答对数)。旭日与雷达共用这一份聚合。"""
    a = schema.attempts
    rows = conn.execute(
        select(a.c.subject_id, a.c.topic_id, func.count(), func.coalesce(func.sum(a.c.correct), 0)).group_by(a.c.subject_id, a.c.topic_id)
    ).all()
    return {(r[0], r[1]): (int(r[2]), int(r[3])) for r in rows}


def _sunburst(conn: Connection) -> list[dict[str, Any]]:
    """作答分布旭日：一级是场景/科目，二级是章节。量大的放前面，一眼看到主力。"""
    stats = _topic_stats(conn)
    grouped: dict[str, list[tuple[str, int, int]]] = {}
    for (subject, topic), (n, correct) in stats.items():
        grouped.setdefault(subject, []).append((topic, n, correct))
    out = []
    for subject, items in sorted(grouped.items(), key=lambda kv: -sum(i[1] for i in kv[1])):
        short = SUBJECT_TITLES.get(subject, (subject,))[0]
        out.append(
            {
                "name": short,
                "value": sum(i[1] for i in items),
                "children": [
                    {"name": TOPIC_TITLES.get(topic, topic), "value": n}
                    for topic, n, _ in sorted(items, key=lambda i: (-i[1], i[0]))
                ],
            }
        )
    return out


def _radar(conn: Connection) -> dict[str, Any]:
    """主修科目（正式科目中作答量最大）各章的正确率雷达。答得太少的章节
    正确率噪声大，不足 10 次的不进雷达。"""
    stats = _topic_stats(conn)
    totals: dict[str, int] = {}
    for (subject, _), (n, _) in stats.items():
        if subject in REAL_SUBJECTS:
            totals[subject] = totals.get(subject, 0) + n
    if not totals:
        return {"subject": None, "indicators": [], "values": []}
    main = max(totals, key=totals.get)
    short = SUBJECT_TITLES.get(main, (main,))[0]
    items = sorted(
        ((topic, n, correct) for (subject, topic), (n, correct) in stats.items() if subject == main and n >= 10),
        key=lambda i: (-i[1], i[0]),
    )
    return {
        "subject": short,
        "indicators": [{"name": TOPIC_TITLES.get(t, t), "max": 100} for t, _, _ in items],
        "values": [round(c / n * 100, 1) for _, n, c in items],
    }
