"""山东：由山东省教育招生考试院官方文件生成 provinces/shandong.json。
用法：python -X utf8 build_shandong.py <下载目录>   （目录里放 sd_kcsz2026.txt/pdf、sd_sched10.txt/xlsx、sd_books10.xlsx、sd6368.txt/html）
"""
import hashlib
import pathlib
import sys

import openpyxl

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
SDZK = "https://www.sdzk.cn/"
N_OCT = "https://www.sdzk.cn/NewsInfo.aspx?NewsID=7204"  # 鲁招考〔2026〕61号 2026 年 10 月报名通知
N_APR = "https://www.sdzk.cn/NewsInfo.aspx?NewsID=7094"  # 鲁招考〔2025〕118号 2026 年 4 月报名通知
N_ADJ = "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6367"  # 鲁自考委〔2023〕4号 计划调整通知
N_FAQ = "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6368"  # 计划调整政策三十问
X_SCHED = "https://www.sdzk.cn/Floadup/file/20260528/6391555806427097082286288.xlsx"  # 附件1：2026 年 10 月开考专业及考试时间安排
X_BOOKS = "https://www.sdzk.cn/Floadup/file/20260528/6391555807642938913407189.xlsx"  # 附件2：课程教材安排一览表
T_KCSZ = ("https://jyj.weihai.gov.cn/module/download/downfile.jsp?classid=0&showname=%E5%B1%B1%E4%B8%9C%E7%9C%81%E9%AB%98%E7%AD%89%E6%95%99%E8%82%B2%E8%87%AA%E5%AD%A6%E8%80%83%E8%AF%95"
          "%E4%B8%93%E4%B8%9A%E8%AF%BE%E7%A8%8B%E8%AE%BE%E7%BD%AE%E8%A1%A8%EF%BC%882026%E7%89%88%EF%BC%89.pdf&filename=411743bab7574219970331c1cb049b94.pdf")

# ---- 080901 课程设置表（2026 版），逐行抄自 sd_kcsz2026.txt 的「计算机科学与技术专业（专升本）课程设置表」----
ROWS = [
    ("15040", "习近平新时代中国特色社会主义思想概论", 3, "public", None),
    ("15043", "中国近现代史纲要", 3, "public", None),
    ("15044", "马克思主义基本原理", 3, "public", None),
    ("13000", "英语（专升本）", 7, "public", None),
    ("00023", "高等数学（工本）", 10, "required", None),
    ("02324", "离散数学", 4, "required", None),
    ("13003", "数据结构与算法", 4, "required", None), ("13004", "数据结构与算法", 2, "practice", "13003"),
    ("13005", "软件工程", 3, "required", None), ("13006", "软件工程", 2, "practice", "13005"),
    ("13013", "高级语言程序设计", 4, "required", None), ("13014", "高级语言程序设计", 2, "practice", "13013"),
    ("13015", "计算机系统原理", 4, "required", None),
    ("01023", "数据库技术及应用（实践）", 4, "practice", None),
    ("13180", "操作系统", 4, "required", None),
    ("13009", "数据库原理与技术", 4, "required", None),
    ("13011", "人工智能与大数据", 6, "required", None),  # 备注「实践考核」
    ("14565", "移动应用程序设计", 4, "required", None), ("14566", "移动应用程序设计", 1, "practice", "14565"),
    ("07999", "毕业设计", 0, "graduation", None),
]
TOTAL = 74  # 官方课程设置表「总学分 74」

# ---- 教材：附件 2 的课程教材安排一览表 ----
X_BOOKS04 = "https://www.sdzk.cn/Floadup/file/20251212/6390113531174934016182084.xlsx"  # 2026 年 4 月课程教材一览表（鲁招考〔2025〕118号附件2）
# 教材表按考次公布：10 月表优先，10 月没排的课程取 4 月表（同一门课两表都有时教材一致）
book_rows = {}
for fn, tag in (("sd_books04.xlsx", "apr"), ("sd_books10.xlsx", "oct")):
    wb = openpyxl.load_workbook(DL / fn, data_only=True)
    for r in wb.active.iter_rows(values_only=True):
        if r and r[1] and str(r[1]).strip().isdigit() and len(str(r[1]).strip()) == 5:
            book_rows[str(r[1]).strip()] = (r, tag)

courses, books = Shard("courses"), Shard("textbooks")
crow = []
for code, name, cr, cat, pair in ROWS:
    kind = {"practice": "practice", "graduation": "graduation"}.get(cat, "theory")
    if code == "13011":
        kind = "mixed"
    if code == "01023":
        kind = "practice"
    courses.add(code, {"name": name, "aliases": [], "kind": kind, "note": ""})
    tb = None
    if cat in ("public", "required") and code in book_rows:
        r, tag = book_rows[code]
        isbn = str(r[7]).strip() if r[7] else None
        bid = f"tb-{isbn}" if isbn else f"tb-sd-{code}"
        books.add(bid, {
            "title": str(r[4]).strip(), "authors": [a for a in str(r[6]).replace(" ", "").split("、") if a],
            "publisher": str(r[5]).strip(), "edition": "未标注", "isbn": isbn, "kind": None,
            "outline": "课程大纲见山东省教育招生考试院官网；笔试课程教材以当次考试公布为准，实践课程教材以主考学校当次考核公布为准",
            "verify": V(N_OCT if tag == "oct" else N_APR, ("附件2《山东省2026年10月高等教育自学考试课程教材安排一览表》" if tag == "oct" else "附件2《山东省2026年4月高等教育自学考试课程教材一览表》") + "；表内无版次列，ISBN 相同则内容相同"),
        })
        tb = bid
    elif cat in ("public", "required") and code != "13011":
        raise SystemExit(f"教材表缺 {code}")
    pr = {"type": "实践考核", "note": "课程设置表备注标注「实践考核」"} if code == "13011" else None
    crow.append(course_row(code, name, cr, cat, pair=pair, practice=pr, textbook=tb,
                           note="2026 年 4 月、10 月教材表均未列此课程" if code == "13011" else ""))
assert sum(c["credits"] for c in crow) == TOTAL

plan = {
    "id": "sd-080901-2026", "major": "080901", "track": None,
    "version": "专业课程设置表（2026 版，2025 年 12 月发布）", "effective": "2024-04", "state": "current",
    "total_credits": TOTAL, "required_credits": TOTAL,
    "rules": "全部必考、无选考；总学分 74（官方表直接给出，各行学分求和一致）。标注「实践考核」的课程除理论考试外须完成实践考核，实践部分通常有单独课程代码。"
             "鲁招考〔2025〕120号调整：2026 年 11 月 30 日前，考生可在 13017 计算机网络与信息安全 与 01023 数据库技术及应用（实践）中任选一门报考，2026 年 12 月 1 日起只能报考 01023；"
             "已通过 13017 的可顶替 01023。新计划自 2024 年上半年起执行（鲁自考委〔2023〕4号），旧计划自 2026 年 1 月 1 日全面停止。",
    "courses": crow,
    "graduation": {"thesis": True, "credits": 0, "note": "毕业设计 07999，不计学分；毕业环节考核须在所选主考学校参加，且申请毕业证与学士学位的学校必须是同一所。"},
    "source_files": ["sd_kcsz2026.txt", "sd_sched10.txt", "sd_books10.txt", "sd_books04.txt"],
    "verify": V(T_KCSZ, "山东省教育招生考试院《专业课程设置表（2026 版）》，取自威海市教育局网站（政府网）转载的 PDF；课程代码与 2026 年 10 月开考一览表（附件1）核对一致"),
}

scope = load_scope()
offerings = [
    {"major": "080901", "track": None, "status": "open", "hosts": ["山东大学"], "plans": ["sd-080901-2026"],
     "complete": {"courses": True, "credits": True, "textbook": False},
     "verify": V(X_SCHED, "2026 年 10 月开考专业、课程及考试时间安排一览表（附件1）：080901 计算机科学与技术，专升本，主考院校山东大学")},
    {"major": "080903", "track": None, "status": "stopped", "hosts": [],
     "verify": V(N_FAQ, "计划调整政策三十问：080903 网络工程于 2025 年 10 月组织最后一次理论考试，停考后不再安排考试及办理毕业手续")},
]
NONE_V = V(X_SCHED, "山东省 2026 年 10 月开考 46 个专业（38 个本科）一览表未列此专业；2026 版课程设置表目录亦未列")
offerings += none_offerings(scope, {"080901", "080903"}, NONE_V)

events = [
    {"date": "2023-11-02", "kind": "new-plan", "text": "鲁自考委〔2023〕4号：专业考试计划调整，过渡期 2023-12-01 至 2025-12-31，2026-01-01 起旧计划全面停止、只按新计划毕业；46 个正常开考专业中，43 个自 2024 年上半年起按新计划课程考试。", "verify": V(N_FAQ)},
    {"date": "2025-10", "kind": "stop", "major": "080903", "text": "网络工程（本科）2025 年 10 月组织最后一次理论考试，此后不再安排考试及办理毕业手续。", "verify": V(N_FAQ)},
    {"date": "2025-12", "kind": "policy", "major": "080901", "text": "鲁招考〔2025〕120号：计算机科学与技术等 6 个专业部分课程调整——2026-11-30 前可在 13017 计算机网络与信息安全 与 01023 数据库技术及应用（实践）中任选，2026-12-01 起只能报 01023。", "verify": V(T_KCSZ, "来自课程设置表（2026 版）该专业说明栏")},
]

write_province("shandong", {
    "authority": {"name": "山东省教育招生考试院", "url": SDZK, "verify": V(N_OCT)},
    "selfstudy_portal": {"name": "山东省教育招生考试院·自学考试栏目（含网上报名系统入口）", "url": "https://www.sdzk.cn/NewsListM.aspx?BCID=5&CID=1163", "verify": V(N_OCT, "栏目页为搜索所得入口，通知正文提及自学考试网上报名系统")},
    "calendar": [
        {"session": "2026-04", "exam": "2026-04-11~12", "register": "2025-12-18~24", "verify": V(N_APR, "鲁招考〔2025〕118号")},
        {"session": "2026-10", "exam": "2026-10-24~25", "register": "2026-06-18~24（新生注册 06-18~21）", "verify": V(N_OCT, "鲁招考〔2026〕61号")},
    ],
    "policy": {
        "entry": None,
        "graduate": {"text": "考生须通过所有规定课程的考试或考核，取得相应学分且符合毕业条件，方可申请毕业；毕业环节（毕业论文、毕业设计、毕业考核等）须在所选主考学校参加。", "verify": V(T_KCSZ, "课程设置表使用说明")},
        "degree": {"text": "考生参加毕业环节考核与申请毕业证、学士学位的学校必须是同一所主考学校；申请学士学位前应了解主考学校的自学考试学士学位申请规定。", "verify": V(N_ADJ)},
        "exemption": None,
    },
    "offerings": offerings, "plans": [plan], "events": events,
})
courses.save()
books.save()

# 证据快照（文本）
for fn, src, url, note in (
    ("sd_kcsz2026.txt", "sd_kcsz2026.pdf", T_KCSZ, "专业课程设置表（2026 版）；pypdf 抽取，未校对"),
    ("sd_sched10.txt", "sd_sched10.xlsx", X_SCHED, "2026 年 10 月开考专业、课程及考试时间安排一览表；openpyxl 抽取"),
    ("sd_books10.txt", "sd_books10.xlsx", X_BOOKS, "2026 年 10 月课程教材安排一览表；openpyxl 抽取"),
    ("sd_books04.txt", "sd_books04.xlsx", X_BOOKS04, "2026 年 4 月课程教材一览表；openpyxl 抽取"),
    ("sd6368.txt", "sd6368.html", N_FAQ, "计划调整政策三十问；HTML 去标签"),
):
    sha = hashlib.sha256((DL / src).read_bytes()).hexdigest()
    save_evidence("shandong", fn, (DL / fn).read_text(encoding="utf-8"), url, note, sha)
print("shandong ok", len(offerings), "offerings")
