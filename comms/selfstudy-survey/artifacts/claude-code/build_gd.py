"""由广东省教育考试院官方 PDF 的文本生成广东试点数据（课程库、教材库、provinces/guangdong.json）。

课程行逐行抄自官方课程表；教材行由 2026 年 4、10 月教材表解析（粤考办〔2025〕20 号附件 3）。
思政课按粤考委〔2024〕5 号改为 15040/15043/15044 各 3 学分，其余课程行与基础计划一致。
"""
import json
import pathlib
import re
import sys

SCR = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])  # mentor/selfstudy-survey/content

DATE = "2026-10-24"
A = "https://eea.gd.gov.cn/attachment/0/532/532337/4260268.pdf"  # 粤考委〔2023〕4号 附件（新开考专业及考试计划）
B = "https://eea.gd.gov.cn/attachment/0/532/532589/4262692.pdf"  # 粤考委〔2023〕5号 附件（专业调整、新计划）
C = "https://eea.gd.gov.cn/attachment/0/602/602026/4833531.pdf"  # 粤考办〔2025〕20号 附件（2026 年 4、10 月课程表与教材表）
D = "https://eea.gd.gov.cn/attachment/0/568/568978/4641396.pdf"  # 2025 年 4、10 月课程表与教材表
N1 = "https://eea.gd.gov.cn/zxks/content/post_4260268.html"
N2 = "https://eea.gd.gov.cn/zxks/content/post_4262692.html"
N3 = "https://eea.gd.gov.cn/tzgg/content/post_4641808.html"
N4 = "https://eea.gd.gov.cn/zxks/content/post_4833531.html"


def V(source, note=None):
    d = {"level": "official", "source": source, "date": DATE}
    if note:
        d["note"] = note
    return d


# ---- 教材 ----
rows = {r["code"]: r for r in json.load(open(SCR / "gd_books_raw.json", encoding="utf-8"))}
PUB = {
    "机械工业出版社": "cmp", "高等教育出版社": "hep", "电子工业出版社": "phei", "清华大学出版社": "tup",
    "人民邮电出版社": "ptpress", "北京大学出版社": "pup", "外语教学与研究出版社": "fltrp",
    "国防工业出版社": "ndip", "中国科学技术出版社": "cstp", "中国计量出版社": "cmpress",
}


def parse_book(code):
    r = rows[code]
    t = r["rest"].split(" ")
    if code == "15040":
        return dict(title="习近平新时代中国特色社会主义思想概论", authors=["本书编写组"],
                    publisher="高等教育出版社、人民出版社", edition="未标注")
    if code == "08074":
        t = [t[0], t[1], t[2] + t[3], t[4], t[5]]
    elif code == "14255":
        t = [t[0], t[1], t[2] + t[3], t[4], t[5]]
    elif code == "13011":
        t = [t[0], t[1], t[2], t[3] + "、" + t[4], t[5]]
    assert len(t) == 5, (code, t)
    _, title, authors, pub, ed = t
    return dict(title=title, authors=authors.split("、"), publisher=pub, edition=ed)


def book_id(code, b):
    y = re.search(r"(\d{4})", b["edition"])
    pubs = [p for p in b["publisher"].split("、")]
    ab = PUB[pubs[0]] if pubs[0] in PUB else None
    if code == "13011":
        ab = "tup"
    if code == "15040":
        ab = "hep"
    assert ab, (code, b)
    return f"tb-{code}-{y.group(1) if y else 'x'}-{ab}"


# ---- 课程表（抄自官方课程设置与学分；思政课已按 2024-5 号调整）----
GOV = [
    ("15040", "习近平新时代中国特色社会主义思想概论", 3, "public", None),
    ("15043", "中国近现代史纲要", 3, "public", None),
    ("15044", "马克思主义基本原理", 3, "public", None),
]
ENG = ("13000", "英语（专升本）", 7, "public", None)
MATH = ("00023", "高等数学（工本）", 10, "required", None)


def T(code, name, cr):
    return (code, name, cr, "required", None)


def P(code, name, cr, pair):
    return (code, name, cr, "practice", pair)


def G(code, name):
    return (code, name, 0, "graduation", None)


PLANS = {
    "080701": dict(
        id="gd-080701-2023", name="电子信息工程", base="71 学分（基础计划 15 门）", ver_total=74,
        hosts="佛山科学技术学院、广东技术师范大学", src=A, doc="粤考委〔2023〕4号附件 2", effective="2024-10",
        grad="毕业论文（设计）11561，不计学分。",
        rows=GOV + [ENG, MATH,
                    T("08947", "电路分析", 3), P("08948", "电路分析", 1, "08947"),
                    T("14026", "模拟电子技术", 4), P("14027", "模拟电子技术", 1, "14026"),
                    T("14260", "数字电路与逻辑设计", 4), P("14261", "数字电路与逻辑设计", 1, "14260"),
                    T("02354", "信号与系统", 4), P("02355", "信号与系统", 1, "02354"),
                    T("02363", "通信原理", 4),
                    T("02356", "数字信号处理", 4), P("02357", "数字信号处理", 1, "02356"),
                    T("13473", "电子测量原理及应用", 4), T("14319", "图像处理", 4),
                    T("01644", "单片机原理与接口技术", 4), P("01645", "单片机原理与接口技术", 2, "01644"),
                    T("13013", "高级语言程序设计", 4), P("13014", "高级语言程序设计", 2, "13013"),
                    G("11561", "电子信息工程毕业论文（设计）")]),
    "080901": dict(
        id="gd-080901-2026", name="计算机科学与技术", base="72 学分（新计划 15 门）", ver_total=75,
        hosts="华南师范大学、深圳大学、华南理工大学、广东外语外贸大学、广东财经大学", src=B, doc="粤考委〔2023〕5号附件 2", effective="2026-01",
        grad="毕业论文 11689，不计学分。",
        rows=GOV + [MATH, T("02324", "离散数学", 4), ENG,
                    T("13003", "数据结构与算法", 4), P("13004", "数据结构与算法", 2, "13003"),
                    T("13013", "高级语言程序设计", 4), P("13014", "高级语言程序设计", 2, "13013"),
                    T("13015", "计算机系统原理", 4), T("13180", "操作系统", 4),
                    T("03344", "信息与网络安全管理", 3), P("03345", "信息与网络安全管理", 2, "03344"),
                    T("08074", "计算机高级程序设计", 3), P("08075", "计算机高级程序设计", 2, "08074"),
                    T("13005", "软件工程", 3), P("13006", "软件工程", 2, "13005"),
                    T("13009", "数据库原理与技术", 4), T("13011", "人工智能与大数据", 6),
                    G("11689", "计算机科学与技术（本科）毕业论文")]),
    "080902": dict(
        id="gd-080902-2023", name="软件工程", base="70 学分（基础计划 15 门）", ver_total=73,
        hosts="广东外语外贸大学、华南理工大学", src=A, doc="粤考委〔2023〕4号附件 2", effective="2024-10",
        grad="软件工程毕业设计 10916，不计学分。",
        rows=GOV + [MATH, T("02324", "离散数学", 4), ENG,
                    T("13013", "高级语言程序设计", 4), P("13014", "高级语言程序设计", 2, "13013"),
                    T("13003", "数据结构与算法", 4), P("13004", "数据结构与算法", 2, "13003"),
                    T("13180", "操作系统", 4),
                    T("13005", "软件工程", 3), P("13006", "软件工程", 2, "13005"),
                    T("13008", "软件质量保证与测试", 4), T("13015", "计算机系统原理", 4),
                    T("13009", "数据库原理与技术", 4), T("07844", "人工智能导论", 4),
                    T("13420", "大数据概论", 5), P("13421", "大数据概论", 1, "13420"),
                    G("10916", "软件工程毕业设计")]),
    "080905": dict(
        id="gd-080905-2023", name="物联网工程", base="70 学分（基础计划 15 门）", ver_total=73,
        hosts="广东技术师范大学、广东工业大学", src=A, doc="粤考委〔2023〕4号附件 2", effective="2024-10",
        grad="物联网工程毕业论文 12590，不计学分。",
        rows=GOV + [MATH, ENG,
                    T("12572", "物联网工程导论", 4), T("14255", "数据通信基础", 4),
                    T("07454", "传感器技术与应用", 4), P("09121", "传感器技术与应用", 1, "07454"),
                    T("13247", "RFID原理及应用", 4), T("13958", "宽带IP网络", 4), T("14383", "物联网信息安全技术", 4),
                    T("01644", "单片机原理与接口技术", 4), P("01645", "单片机原理与接口技术", 2, "01644"),
                    T("12573", "无线传感网技术", 4), P("12574", "无线传感网技术", 2, "12573"),
                    ("12579", "物联网系统综合设计", 6, "practice", None),
                    T("02141", "计算机网络技术", 4),
                    G("12590", "物联网工程毕业论文")]),
}

courses = {}
books = {}
plans = []
for major, p in PLANS.items():
    crow = []
    for code, name, cr, cat, pair in p["rows"]:
        kind = {"practice": "practice", "graduation": "graduation"}.get(cat, "theory")
        if code in courses and courses[code]["name"] != name:
            raise SystemExit(f"同代码不同名 {code}")
        courses[code] = {"name": name, "aliases": [], "kind": kind, "note": ""}
        tb = None
        if cat in ("public", "required") and code in rows:
            b = parse_book(code)
            bid = book_id(code, b)
            books[bid] = {
                **b, "isbn": None, "kind": None,
                "outline": "考试大纲在广东省自学考试管理系统专业计划栏查询（粤考办〔2025〕20号）；课程名前带▲的另可从中国教育考试网下载",
                "verify": V(N4, "2026 年 4、10 月广东省开考课程使用教材表（粤考办〔2025〕20号附件 3）"),
            }
            tb = bid
        elif cat in ("public", "required") and code not in rows:
            raise SystemExit(f"教材表缺 {code}")
        crow.append({"code": code, "name": name, "credits": cr, "category": cat, "elective_group": None,
                     "exam": None, "practice": None, "textbook": tb, "pair": pair, "note": ""})
    total = sum(c["credits"] for c in crow)
    assert total == p["ver_total"], (major, total)
    plans.append({
        "id": p["id"], "major": major, "track": None, "host": p["hosts"],
        "version": f"{p['doc']}，思政课按粤考委〔2024〕5号调整",
        "effective": p["effective"], "state": "current",
        "total_credits": total, "required_credits": total,
        "rules": f"基础计划为必考课 {p['base']}、全部必考无选考；思政课原为 03708（2 学分）、03709（4 学分），"
                 f"按粤考委〔2024〕5号改为 15040、15043、15044 各 3 学分，合计学分由此核算为 {total}（官方原表未直接给出该数）。"
                 "课程设有实践环节的，理论课与实践课各有课程代码与学分，实践考核由主考学校组织，采用五级评分制。",
        "courses": crow,
        "graduation": {"thesis": True, "credits": 0, "note": p["grad"] + "实践性学习环节考核要求由主考学校负责并公布。"},
        "verify": V(p["src"], f"{p['doc']}；思政课调整依据粤考委〔2024〕5号（{N3}）；2026 年 4、10 月课程表（{C}）所列课程代码与之一致"),
    })

OFFER = lambda major, status, hosts, plan, verify, track=None: {  # noqa: E731
    "major": major, "track": track, "status": status, "hosts": hosts, "plans": [plan] if plan else [], "verify": verify}
NONE_NOTE = "2026 年 4、10 月全省开考课程表与 2025 年表均未列此专业"
offerings = [
    OFFER("080701", "open", ["佛山科学技术学院", "广东技术师范大学"], "gd-080701-2023", V(N1, "首次开考 2024 年 10 月（粤考委〔2023〕4号）")),
    OFFER("080901", "open", ["华南师范大学", "深圳大学", "华南理工大学", "广东外语外贸大学", "广东财经大学"], "gd-080901-2026",
          V(N2, "主考学校取自 2025 年 4、10 月课程表所列专业建设主考学校的并集；2026 年起为单一新计划，主考学校以考试院当期公布为准")),
    OFFER("080902", "open", ["广东外语外贸大学", "华南理工大学"], "gd-080902-2023", V(N1, "首次开考 2024 年 10 月（粤考委〔2023〕4号）")),
    OFFER("080905", "open", ["广东技术师范大学", "广东工业大学"], "gd-080905-2023", V(N1, "首次开考 2024 年 10 月（粤考委〔2023〕4号）")),
    OFFER("080903", "stopped", ["广东外语外贸大学", "华南师范大学"], None, V(D, "2025 年 4、10 月课程表标「#」＝限期停考专业，不接受新生报名；2026 年表不再列")),
    OFFER("080801", "stopped", ["广东工业大学"], None, V(D, "2025 年 4、10 月课程表标「#」＝限期停考专业，不接受新生报名；2026 年表不再列")),
]
for m in ("080904K", "080910T", "080911TK", "080702", "080703", "080714T", "080717T", "080710T"):
    offerings.append(OFFER(m, "none", [], None, V(C, NONE_NOTE)))

events = [
    {"date": "2023-09-27", "kind": "new-plan", "major": "080701", "text": "粤考委〔2023〕4号：新开考电子信息工程（专升本），主考学校佛山科学技术学院、广东技术师范大学，首次开考 2024 年 10 月。", "verify": V(N1)},
    {"date": "2023-09-27", "kind": "new-plan", "major": "080902", "text": "粤考委〔2023〕4号：新开考软件工程（专升本），主考学校广东外语外贸大学、华南理工大学，首次开考 2024 年 10 月。", "verify": V(N1)},
    {"date": "2023-09-27", "kind": "new-plan", "major": "080905", "text": "粤考委〔2023〕4号：新开考物联网工程（专升本），主考学校广东技术师范大学、广东工业大学，首次开考 2024 年 10 月。", "verify": V(N1)},
    {"date": "2023-10-07", "kind": "new-plan", "major": "080901", "text": "粤考委〔2023〕5号：计算机科学与技术列入专业调整名单，仅调整考试计划、不调整专业代码和名称；2023-11-01 至 2025-12-31 为过渡期仍按旧计划，2026-01-01 起按新计划（15 门 72 学分，思政课按后续通知调整）；同一专业原有多个主考学校各自的计划合并为单一计划。", "verify": V(N2)},
    {"date": "2024-12-30", "kind": "policy", "text": "粤考委〔2024〕5号：本科（专升本）思政课调整为 15040 习近平新时代中国特色社会主义思想概论、15043 中国近现代史纲要、15044 马克思主义基本原理，各 3 学分；旧 03708 对应 15043、03709 对应 15044；2026 年起所有专业毕业时执行。", "verify": V(N3)},
    {"date": "2025-04", "kind": "other", "major": "080901", "text": "2025 年 4、10 月课程表中 080901 计算机科学与技术（本科）按专业建设主考学校分三个课程组：华南师范大学、深圳大学；华南理工大学、广东外语外贸大学；广东财经大学（计算机及应用）。各组课程不同（旧计划），2026 年起并为单一新计划。", "verify": V(D)},
    {"date": "2025-04", "kind": "stop", "major": "080903", "text": "网络工程（本科）在 2025 年 4、10 月课程表中标「#」，为限期停考专业，不接受新生报名，过渡期内相关课程继续安排考试。", "verify": V(D)},
    {"date": "2025-04", "kind": "stop", "major": "080801", "text": "自动化（本科）在 2025 年 4、10 月课程表中标「#」，为限期停考专业，不接受新生报名，过渡期内相关课程继续安排考试。", "verify": V(D)},
    {"date": "2025-12-22", "kind": "policy", "text": "粤考办〔2025〕20号：公布 2026 年 4 月（11—12 日）、10 月（24—25 日）开考课程安排和使用教材；2026 年起部分课程启用新教材与考试大纲，专业调整的各专业使用新代码、新名称、新计划，所有专业毕业时执行调整后的思政课要求。", "verify": V(N4)},
]

prov = {
    "schema": 1, "id": "guangdong", "name": "广东省",
    "authority": {"name": "广东省教育考试院", "url": "https://eea.gd.gov.cn/zxks/", "verify": V(N4)},
    "calendar": [
        {"session": "2026-04", "exam": "2026-04-11~12", "note": "报名时间未采集", "verify": V(N4)},
        {"session": "2026-10", "exam": "2026-10-24~25", "note": "报名时间未采集", "verify": V(N4)},
    ],
    "policy": {
        "entry": {"text": "持有具备学历教育资格的高等学校、高等教育自学考试机构颁发的专科（或以上）学历证书的考生，可取得本科段专业考试计划规定的课程成绩后毕业；申请毕业时须持该学历证书。", "verify": V(A, "各专业考试计划第二、四节通用表述")},
        "graduate": {"text": "取得专业考试计划规定的全部课程合格成绩，完成规定的毕业论文（设计）或其他实践性学习环节并合格，思想品德鉴定合格，由广东省自学考试委员会颁发毕业证书，主考学校副署，国家承认本科学历。", "verify": V(A, "各专业考试计划第二节通用表述")},
        "degree": {"text": "符合相应学位条件的本科毕业生，由有学位授予权的主考学校依照《中华人民共和国学位条例》等规定授予相应学位；具体条件由主考学校规定，未在此采集。", "verify": V(A, "各专业考试计划第二节通用表述")},
        "exemption": None,
    },
    "offerings": offerings, "plans": plans, "events": events,
}

(OUT / "provinces").mkdir(parents=True, exist_ok=True)
(OUT / "provinces" / "guangdong.json").write_text(json.dumps(prov, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
cdoc = json.loads((OUT / "courses.json").read_text(encoding="utf-8"))
cdoc["courses"] = dict(sorted({**cdoc.get("courses", {}), **courses}.items()))
(OUT / "courses.json").write_text(json.dumps(cdoc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
bdoc = json.loads((OUT / "textbooks.json").read_text(encoding="utf-8"))
bdoc["textbooks"] = dict(sorted({**bdoc.get("textbooks", {}), **books}.items()))
(OUT / "textbooks.json").write_text(json.dumps(bdoc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(len(plans), "plans", len(courses), "courses", len(books), "books")
