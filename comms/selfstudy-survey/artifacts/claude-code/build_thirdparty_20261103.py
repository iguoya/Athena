"""使用者 2026-11-03 裁决：第三方自考网页面可信，可作课程表与结论的来源（级别照实标 report）。据此入库：
  重庆：自考本科网 080901 2026 版计划（页面有缺字，课程名按课程代码取课程库名称，学分与总学分 74 逐行求和复核）、全省专业及院校一览表（「不开设」结论）；
  北京：华夏大地教育网转载的 01B0015（计算机科学与技术）目录表——主考院校北京邮电大学与课程表（页面课程代码缺前导零，已按课程库补齐）；
  山西：山西自考网 080901 课程表——页面是旧版计划（英语（二）14 学分、毕业论文 6 学分、总学分 80），标 legacy；
  云南：云南自考网 080901 课程表——已按 2025 年起思政课口径更新、总学分 73，作为现行计划；原 2024 版官方计划标 legacy。
用法：python -X utf8 build_thirdparty_20261103.py <抽取目录> <Downloads 目录>
"""
import hashlib
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-03"
from provlib import *  # noqa: E402,F403
from planlib import attach, build_plan  # noqa: E402

EX, DL = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
EVI = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence"
PUB = lambda: [("15040", "习近平新时代中国特色社会主义思想概论", 3, "public", None, "", None), ("15043", "中国近现代史纲要", 3, "public", None, "", None),
               ("15044", "马克思主义基本原理", 3, "public", None, "", None), ("13000", "英语（专升本）", 7, "public", None, "", None)]


def R(code, name, cr, pair=None, cat="required", note="", eg=None):
    return (code, name, cr, "practice" if pair else cat, pair, note, eg)


def check_total(rows, grad_cr, total):
    s = sum(r[2] for r in rows) + grad_cr
    assert s == total, (s, total)


def p_report(pid, major, url, title, version, effective, total, required, rules, rows, grad, note, state="current"):
    plan, courses = build_plan(pid, major, version, effective, total, required, rules, rows, grad,
                               V(url, title + "（第三方页面，使用者裁决可信；官方原文到手后替换）", level="report"), note, [])
    plan["state"] = state
    return plan, courses


# ---------------- 重庆 ----------------
CQ_PLAN = "https://www.zikaoben.cn/zklist/major-21266.html"
CQ_LIST = "https://www.zikaoben.cn/cate/tid-128"
cq_rows = PUB() + [R("00023", "高等数学（工本）", 10), R("13175", "线性代数（工）", 3), R("02324", "离散数学", 4), R("13013", "高级语言程序设计", 4), R("13014", "高级语言程序设计（实践）", 2, "13013"),
                   R("13003", "数据结构与算法", 4), R("13004", "数据结构与算法（实践）", 2, "13003"), R("13015", "计算机系统原理", 4), R("13180", "操作系统", 4),
                   R("13009", "数据库原理与技术", 4), R("13005", "软件工程", 3), R("13006", "软件工程（实践）", 2, "13005"), R("13017", "计算机网络与信息安全", 6), R("14349", "网络应用开发与系统集成", 6)]
check_total(cq_rows, 0, 74)
plan, courses = p_report("cq-080901-2026", "080901", CQ_PLAN, "自考本科网「重庆自考计算机科学与技术专业（本科）」，页面标注计划版本 2026 年版，主考重庆科技大学、重庆理工大学、重庆三峡科技大学、重庆交通大学",
                         "专业考试计划（页面标注 2026 年版；重庆自 2026 年起 46 个专业启用《高等教育自学考试重庆市专业考试计划（2024 年）》）", "2026-01", 74, 74,
                         "页面总学分 74，列 15 门课程（含配套实践课）逐行求和 74，全部为必考；毕业论文（11689）不计学分。页面文本有缺字（如「计算机科学与（）」），课程名按课程代码取课程库名称，学分以求和复核。",
                         cq_rows, ("11689", "计算机科学与技术（本科）毕业论文", "不计学分"), "毕业论文不计学分，实践性环节与论文由主考学校组织考核（页面给出高级语言程序设计、数据结构与算法、软件工程实践考核方式与评分结构）。")
courses.save()
p = CONTENT / "provinces" / "chongqing.json"
d = provlib._load(p)
d["plans"] = [x for x in d["plans"] if x["id"] != plan["id"]] + [plan]
V_CQ = V(CQ_LIST, "自考本科网「重庆自学考试专业及院校一览表」（第三方，使用者裁决可信；页面称现开考 48 个专业，表中列出 47 个，有 1 个未在表中，未能核对）", level="report")
keep = {"080703": ("重庆邮电大学", "open"), "080901": None, "080903": None}
for o in d["offerings"]:
    o["verify"] = V(CQ_LIST, o["verify"]["note"].replace("第三方，页面声明以重庆市教育考试院公示为准", "第三方，使用者裁决可信；官方开考专业表到手后替换").replace("官方开考专业表待核", ""), level="report")
    if o["major"] == "080901":
        o["plans"] = [plan["id"]]
        o["complete"] = {"courses": True, "credits": True, "textbook": False}
d["offerings"] = [o for o in d["offerings"] if o["status"] != "none"] + none_offerings(load_scope(), {"080703", "080901", "080903"}, V_CQ)
provlib._save(p, d)

# ---------------- 北京 ----------------
BJ = "https://www.edu-edu.com/zikao/beijing/zkzy/65318.html"
SEL = "选考课：7 门选 5 门，选考学分不低于 23 分"
bj_rows = PUB() + [R("00023", "高等数学（工本）", 10, note="页面写作代码「23」，按课程库补齐"), R("02324", "离散数学", 4, note="页面写作代码「2324」，按课程库补齐"),
                   R("13013", "高级语言程序设计", 4), R("13014", "高级语言程序设计（实践）", 2, "13013"), R("13003", "数据结构与算法", 4), R("13004", "数据结构与算法（实践）", 2, "13003"),
                   R("13015", "计算机系统原理", 4), R("13180", "操作系统", 4),
                   R("13009", "数据库原理与技术", 4, cat="elective", note="页面考核方式写作「实践」", eg=SEL), R("13007", "编译原理", 4, cat="elective", eg=SEL),
                   R("13005", "软件工程", 4, cat="elective", note="页面写作 4 学分（其他省为 3）；配套实践 1 学分", eg=SEL), R("13006", "软件工程（实践）", 1, "13005", eg=SEL),
                   R("13017", "计算机网络与信息安全", 6, cat="elective", eg=SEL), R("14349", "网络应用开发与系统集成", 6, cat="elective", eg=SEL),
                   R("06627", "网页制作与网站建设", 5, cat="elective", note="页面写作代码「6627」，考核方式写作「实践」，按课程库补齐", eg=SEL), R("14899", "大数据技术基础（实践）", 5, cat="elective", eg=SEL)]
req = sum(r[2] for r in bj_rows if r[3] in ("public", "required") or (r[3] == "practice" and r[4] in ("13013", "13003")))
assert req == 50, req
plan, courses = p_report("bj-080901-2025", "080901", BJ, "华夏大地教育网转载「2025 年下半年北京自考本科计算机科学与技术专业目录表」（页面标来源北京教育考试院），北京码 01B0015，主考院校北京邮电大学",
                         "目录表（2025 年下半年版，页面未标专业计划版本）", "2025-10", 73, 73,
                         "页面列必考课 50 学分（序号 1~10，含配套实践课）、7 门选考课选 5 门且选考学分不低于 23 学分；总学分 73 为核算值（50 + 23），页面未直接给出。页面课程代码缺前导零的行已按课程库补齐（23→00023、2324→02324、6627→06627）；"
                         "软件工程写 4 学分、实践 1 学分，与其他省 3+2 不同，按页面照录（两者合计同为 5）。",
                         bj_rows, ("11689", "计算机科学与技术（本科）毕业论文", "页面标「综合课 0 分」"), "毕业论文/毕业设计学分 0。")
courses.save()
p = CONTENT / "provinces" / "beijing.json"
d = provlib._load(p)
d["plans"] = [x for x in d["plans"] if x["id"] != plan["id"]] + [plan]
for o in d["offerings"]:
    if o["major"] == "080901":
        o["hosts"] = ["北京邮电大学"]
        o["plans"] = [plan["id"]]
        o["complete"] = {"courses": True, "credits": True, "textbook": False}
        o["verify"]["note"] = o["verify"]["note"].replace("主考院校待查（通知不含主考院校与学分）", "通知不含主考院校与学分")
        o["verify"]["note"] = o["verify"]["note"].replace("第三方线索（华夏大地教育网转载北京教育考试院目录表，", "主考院校与课程表取自第三方（华夏大地教育网转载北京教育考试院目录表，使用者裁决可信，")
provlib._save(p, d)

# ---------------- 山西（旧计划） ----------------
SX = "http://www.zkw.sx.cn/bkzy/34442.html"
sx_rows = [("03708", "中国近现代史纲要", 2, "public", None, "", None), ("03709", "马克思主义基本原理概论", 4, "public", None, "", None), ("00015", "英语（二）", 14, "public", None, "", None),
           R("00023", "高等数学（工本）", 10), R("02197", "概率论与数理统计（二）", 3), R("02324", "离散数学", 4), R("02325", "计算机系统结构", 4),
           R("02326", "操作系统", 4), R("02327", "操作系统（实践）", 1, "02326"), R("02331", "数据结构", 3), R("04734", "数据结构（实践）", 2, "02331"),
           R("02333", "软件工程", 3), R("02334", "软件工程（实践）", 1, "02333"), R("04735", "数据库系统原理", 4), R("04736", "数据库系统原理（实践）", 2, "04735"),
           R("04737", "程序设计", 3), R("04738", "程序设计（实践）", 2, "04737"), R("04741", "计算机网络原理", 4), R("04747", "Java语言程序设计（一）", 3), R("04748", "Java语言程序设计（一）（实践）", 1, "04747")]
check_total(sx_rows, 6, 80)
plan, courses = p_report("sx-080901-legacy", "080901", SX, "山西自考网「080901 计算机科学与技术（本科）考试计划」，主考院校太原理工大学", "页面未标版本（旧计划）", "未标注", 80, 80,
                         "页面总学分 80，逐行求和一致：毕业论文 06999 计 6 学分；英语（二）14 学分；思政课仍是旧代码 03708/03709；全国 2025 年起思政课、2024 年起计算机类新专业基本规范已不是这套课程，"
                         "页面「专业开考安排」栏标注 2025 年，但课程表是旧版，标 legacy，不代表山西 2026 年现行计划（现行计划待查）。",
                         sx_rows, ("06999", "毕业论文", "页面写 6 学分", 6), "毕业论文计 6 学分。", state="legacy")
courses.save()
p = CONTENT / "provinces" / "shanxi.json"
d = provlib._load(p)
d["plans"] = [x for x in d["plans"] if x["id"] != plan["id"]] + [plan]
for o in d["offerings"]:
    if o["major"] == "080901":
        o["plans"] = [plan["id"]]
        o["complete"] = {"courses": False, "credits": False, "textbook": False}
        o["verify"] = V(SX, "山西自考网（第三方，使用者裁决可信）080901 专业页：主考院校太原理工大学；该页课程表是旧版计划（见 plans 里 legacy 计划），山西现行计划与官方开考专业表待查", level="report")
provlib._save(p, d)

# ---------------- 云南（页面为更新后的 73 学分计划） ----------------
YN = "http://www.ynzk.yn.cn/benke888/22346.html"
yn_rows = [("15043", "中国近现代史纲要", 3, "public", None, "", None), ("15044", "马克思主义基本原理", 3, "public", None, "", None),
           ("15040", "习近平新时代中国特色社会主义思想概论", 3, "public", None, "", None), ("13000", "英语（专升本）", 7, "public", None, "", None),
           R("00023", "高等数学（工本）", 10), R("02324", "离散数学", 4), R("13013", "高级语言程序设计", 4), R("13014", "高级语言程序设计（实践）", 2, "13013"),
           R("13003", "数据结构与算法", 4), R("13004", "数据结构与算法（实践）", 2, "13003"), R("13015", "计算机系统原理", 4), R("13180", "操作系统", 4),
           R("13175", "线性代数（工）", 3, cat="elective", eg="选考课：不得少于 5 门，且不得少于 23 学分"), R("13007", "编译原理", 4, cat="elective", eg="选考课：不得少于 5 门，且不得少于 23 学分"),
           R("13009", "数据库原理与技术", 4, cat="elective", eg="选考课：不得少于 5 门，且不得少于 23 学分"), R("13011", "人工智能与大数据", 6, cat="elective", eg="选考课：不得少于 5 门，且不得少于 23 学分"),
           R("13005", "软件工程", 3, cat="elective", eg="选考课：不得少于 5 门，且不得少于 23 学分"), R("13006", "软件工程（实践）", 2, "13005", eg="选考课：不得少于 5 门，且不得少于 23 学分"),
           R("13017", "计算机网络与信息安全", 6, cat="elective", eg="选考课：不得少于 5 门，且不得少于 23 学分")]
req = sum(r[2] for r in yn_rows if r[3] in ("public", "required") or (r[3] == "practice" and r[4] in ("13013", "13003")))
assert req == 50, req
plan, courses = p_report("yn-080901-2026-update", "080901", YN, "云南自考网「计算机科学与技术（08090100）」，主考云南师范大学，思政课已按 15040/15043/15044 更新、总学分 73",
                         "专业考试计划（页面显示 2026 年起，思政课已更新；云南 2024-03 通告原文仍写旧思政代码）", "2026-01", 73, 73,
                         "页面总学分 73（必考 50 学分 + 选考不少于 5 门且不少于 23 学分）；必考课含思政 3 门 9 学分、英语（专升本）7 学分；选考课列 6 门（软件工程含配套实践）。"
                         "与 2024-03 官方计划（yn-080901-2026，总学分 70、思政仍写旧代码 03708/03709）相比，本计划按全国 2025 年起的思政课调整更新；毕业设计 07999 不计学分，由主考学校安排。",
                         yn_rows, ("07999", "毕业设计", "不计学分，由主考学校安排"), "毕业设计不计学分，由主考学校安排。")
courses.save()
p = CONTENT / "provinces" / "yunnan.json"
d = provlib._load(p)
for x in d["plans"]:
    if x["id"] == "yn-080901-2026":
        x["state"] = "legacy"
        x["rules"] += "【2026-11-03】云南自考网页面显示该专业计划已按全国 2025 年起的思政课调整更新、总学分 73（见计划 yn-080901-2026-update，第三方来源），本计划保留作 2024-03 通告原文。"
d["plans"] = [x for x in d["plans"] if x["id"] != plan["id"]] + [plan]
for o in d["offerings"]:
    if o["major"] == "080901":
        o["plans"] = ["yn-080901-2026-update", "yn-080901-2026"]
provlib._save(p, d)

# 证据
for prov, src, name, url, note in (("chongqing", EX / "重庆自考计算机科学与技术专业（本科）_考试科目_专业计划 - 自考本科网.html.txt", "cq_zikaoben_080901_plan.html.txt", CQ_PLAN, "自考本科网重庆 080901 专业计划页（第三方，页面文本有缺字）"),
                                   ("yunnan", EX / "计算机科学与技术08090100(本科段)自考专业信息- 自考专业 - 云南自考网.html.txt", "yn_ynzk_080901.html.txt", YN, "云南自考网 080901 专业页（第三方）")):
    raw = {"chongqing": "重庆自考计算机科学与技术专业（本科）_考试科目_专业计划 - 自考本科网.html", "yunnan": "计算机科学与技术08090100(本科段)自考专业信息- 自考专业 - 云南自考网.html"}[prov]
    save_evidence(prov, name, src.read_text(encoding="utf-8"), url, note, hashlib.sha256((DL / raw).read_bytes()).hexdigest())
print("thirdparty ok")
