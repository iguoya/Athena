"""河北：补入 2026 版新专业考试计划（河北省教育考试院自学考试网上信息系统「开考专业」页的计划 PDF，使用者 2026-11-02 浏览器下载）。
080901 计算机科学与技术（河北大学）、080701 电子信息工程（河北科技大学）。来源网址取自下载文件的 Zone.Identifier。
用法：python -X utf8 build_hebei_plans.py <Downloads 目录> <抽取目录>
"""
import hashlib
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-02"
from provlib import *  # noqa: E402,F403
from planlib import attach, build_plan  # noqa: E402

DL, EX = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
BASE = "https://zk.hebeea.edu.cn/HebzkWeb/kkzyWjView?id="
U1 = BASE + "402883177ae732ba017b56c126a00023&type=xzyjh"  # 080901
U2 = BASE + "402883177ae732ba017b53115b56001d&type=xzyjh"  # 080701
F1, F2 = "kkzyWjView (1).pdf", "kkzyWjView.pdf"

PUB = [("15040", "习近平新时代中国特色社会主义思想概论", 3, "public", None, "", None), ("15043", "中国近现代史纲要", 3, "public", None, "", None),
       ("15044", "马克思主义基本原理", 3, "public", None, "", None), ("13000", "英语(专升本)", 7, "public", None, "", None)]


def R(code, name, cr, pair=None):
    return (code, name, cr, "practice" if pair else "required", pair, "", None)


cs_rows = PUB + [R("00023", "高等数学(工本)", 10), R("02324", "离散数学", 4), R("13013", "高级语言程序设计", 4), R("13014", "高级语言程序设计(实践)", 2, "13013"),
                 R("13003", "数据结构与算法", 4), R("13004", "数据结构与算法(实践)", 2, "13003"), R("13015", "计算机系统原理", 4), R("13180", "操作系统", 4),
                 R("14263", "数字逻辑设计", 4), R("13009", "数据库原理与技术", 4), R("13005", "软件工程", 3), R("13017", "计算机网络与信息安全", 6), R("14349", "网络应用开发与系统集成", 6)]
ee_rows = PUB + [R("00023", "高等数学(工本)", 10), R("08947", "电路分析", 3), R("08948", "电路分析(实践)", 1, "08947"), R("14026", "模拟电子技术", 4), R("14027", "模拟电子技术(实践)", 1, "14026"),
                 R("14260", "数字电路与逻辑设计", 4), R("14261", "数字电路与逻辑设计(实践)", 1, "14260"), R("02354", "信号与系统", 4), R("02355", "信号与系统(实践)", 1, "02354"),
                 R("02363", "通信原理", 4), R("13060", "电磁场与电磁波", 4), R("02356", "数字信号处理", 4), R("02357", "数字信号处理(实践)", 1, "02356"),
                 R("14319", "图像处理", 4), R("13013", "高级语言程序设计", 4), R("13014", "高级语言程序设计(实践)", 2, "13013"), R("14745", "自动控制原理(本)", 5)]
for rows, t in ((cs_rows, 73), (ee_rows, 73)):
    assert sum(r[2] for r in rows) == t, sum(r[2] for r in rows)

RULES = "官方表「总学分 73」，各行学分求和一致；全部为必考课，没有选考课；毕业设计/毕业论文必做、不计学分。表标题为「专业课程设置与学分（新专业计划）」。"
jobs = [
    ("hb-080901-2026", "080901", U1, F1, "河北大学", cs_rows, ("07999", "毕业设计", ""), "计算机科学与技术（本科）专业课程设置与学分（新专业计划），主考学校河北大学"),
    ("hb-080701-2026", "080701", U2, F2, "河北科技大学", ee_rows, ("11561", "电子信息工程毕业论文（设计）", ""), "电子信息工程（本科）专业课程设置与学分（新专业计划），主考学校河北科技大学"),
]
dst = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence" / "hebei"
shards = None
for pid, major, url, fname, host, rows, grad, title in jobs:
    plan, courses = build_plan(pid, major, "2026 版新专业考试计划（河北省教育考试院「开考专业」页）", "2026-01", 73, 73, RULES, rows, grad,
                               V(url, f"河北省教育考试院高等教育自学考试网上信息系统「开考专业」页计划 PDF：{title}"),
                               "毕业设计/论文必做，不计学分；实践与毕业环节由主考学校组织。", [fname + ".txt"])
    courses.save()
    attach("hebei", plan, lambda o, m=major: o["major"] == m, {"complete": {"courses": True, "credits": True, "textbook": False}})
    shutil.copy2(DL / fname, dst / f"hb_plan_{major}_2026.pdf")
    save_evidence("hebei", f"hb_plan_{major}_2026.pdf.txt", (EX / (fname + ".txt")).read_text(encoding="utf-8"), url, f"{title}；pymupdf 抽取", hashlib.sha256((DL / fname).read_bytes()).hexdigest())
print("hebei plans ok")
