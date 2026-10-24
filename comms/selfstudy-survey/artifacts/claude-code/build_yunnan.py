"""云南：由云南省招生考试院官方通告与《专业考试计划（2026 版）》生成 provinces/yunnan.json。
计划 .doc 用 Word COM 转文本（antiword 会丢表格）；只入库 080901。云南站点未取得 2026 年报考简章，考期留空。
用法：python -X utf8 build_yunnan.py <下载目录>
"""
import hashlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
N = "https://www.ynzs.cn/html/content/3787.html"  # 关于调整我省高等教育自学考试法学等专业考试计划的通告（2024-03-18）
DOC = "https://www.ynzs.cn/upload/files/2024/3/5dfc29ef76adc2a2.doc"  # 附件 1：专业考试计划（2026 版）
LINK = "https://www.ynzs.cn/upload/files/2025/12/f453aad20c7098f3.pdf"  # 附件 2：新旧计划对应衔接表（2026 版）

R, E = "required", "elective"
G = "选考课程不得少于 5 门，且不得少于 23 学分"
rows = [  # (code, name, credits, category, pair, elective_group) 逐行抄自计划表
    ("03708", "中国近现代史纲要", 2, "public", None, None), ("03709", "马克思主义基本原理概论", 4, "public", None, None),
    ("13000", "英语（专升本）", 7, "public", None, None), ("00023", "高等数学（工本）", 10, R, None, None),
    ("02324", "离散数学", 4, R, None, None),
    ("13013", "高级语言程序设计", 4, R, None, None), ("13014", "高级语言程序设计", 2, "practice", "13013", None),
    ("13003", "数据结构与算法", 4, R, None, None), ("13004", "数据结构与算法", 2, "practice", "13003", None),
    ("13015", "计算机系统原理", 4, R, None, None), ("13180", "操作系统", 4, R, None, None),
    ("13175", "线性代数（工）", 3, E, None, G), ("13007", "编译原理", 4, E, None, G), ("13009", "数据库原理与技术", 4, E, None, G),
    ("13011", "人工智能与大数据", 6, E, None, G),
    ("13005", "软件工程", 3, E, None, G), ("13006", "软件工程", 2, "practice", "13005", G),
    ("13017", "计算机网络与信息安全", 6, E, None, G),
    ("07999", "毕业设计", 0, "graduation", None, None),
]
courses = Shard("courses")
crow = []
for code, name, cr, cat, pair, eg in rows:
    courses.add(code, {"name": name, "aliases": [], "kind": {"practice": "practice", "graduation": "graduation"}.get(cat, "theory"), "note": ""})
    note = "实践部分考试时间由主考学校安排，请考生与主考学校联系" if cat == "practice" else ""
    crow.append(course_row(code, name, cr, cat, pair=pair, note=note, elective_group=eg))
req = sum(c["credits"] for c in crow if not c["elective_group"] and c["category"] != "graduation")
assert req == 47, req  # 必考 47 + 选考下限 23 = 总学分 70

plan = {
    "id": "yn-080901-2026", "major": "080901", "track": None,
    "version": "专业考试计划（2026 版，2024-03-18 通告）", "effective": "2026-01", "state": "current",
    "total_credits": 70, "required_credits": 70,
    "rules": "官方表直接给出总学分 70（= 必考 47 + 选考下限 23）：必考课 9 门，选考课程不得少于 5 门且不得少于 23 学分；毕业设计不计学分。"
             "凡含理论考试与实践环节考核两部分的课程必须取得两部分合格成绩；实践部分考试时间与要求由主考学校安排。"
             "官方表思政课仍写旧代码 03708（2 学分）、03709（4 学分）；全国 2025 年起调整为 15040/15043/15044，云南后续衔接文件本轮未取得，此处照计划原文录入。"
             "参加本专业学习需自行完成“计算机应用技术（专科）”或“软件技术（专科）”专业必设课程有关知识学习。教材将于当次考试发布报考简章时公布。",
    "courses": crow,
    "graduation": {"thesis": False, "credits": 0, "note": "毕业环节：毕业设计 07999，不计学分，由主考学校安排，请考生与主考学校联系。"},
    "source_files": ["yn_plan2026_word.txt"],
    "verify": V(DOC, "《云南省高等教育自学考试专业考试计划（2026 版）》（.doc，Word 转文本）中「计算机科学与技术（专升本）」，专业代码 08090100，主考学校云南师范大学；见通告 " + N),
}
offerings = [{"major": "080901", "track": None, "local_code": "08090100", "status": "open", "hosts": ["云南师范大学"], "plans": ["yn-080901-2026"],
              "matched_by": "计划表专业名称「计算机科学与技术（专升本）」，云南省专业代码 08090100",
              "complete": {"courses": True, "credits": True, "textbook": False},
              "verify": V(DOC, "专业考试计划（2026 版）；通告 " + N + " 列明涉及调整的 9 个专升本专业含计算机科学与技术")}]
events = [{"date": "2024-03-18", "kind": "new-plan", "major": "080901",
           "text": "云南省招生考试院通告：计算机科学与技术等 9 个专升本专业调整考试计划；过渡期自公布之日至 2025-12-31，2026-01-01 起执行新计划、旧计划废止；新旧计划对应衔接表见通告附件 2；新计划教材于当次考试发布报考简章时公布。",
           "verify": V(N)}]
write_province("yunnan", {
    "authority": {"name": "云南省招生考试院", "url": "https://www.ynzs.cn/", "verify": V(N)},
    "selfstudy_portal": {"name": "云南省高等教育自学考试管理平台", "url": "http://zk.ynzs.cn/", "verify": V(N, "平台名称与网址取自搜索结果标题（域名 ynzs.cn 为考试院自有），未打开核实")},
    "calendar": [], "policy": {"entry": None, "graduate": None, "degree": None, "exemption": None},
    "offerings": offerings, "plans": [plan], "events": events,
})
courses.save()
sha = hashlib.sha256((DL / "yn_plan2026.doc").read_bytes()).hexdigest()
save_evidence("yunnan", "yn_plan2026_word.txt", (DL / "yn_plan2026_word.txt").read_text(encoding="utf-8"), DOC, "专业考试计划（2026 版）；Word COM 转文本，表格单元格以制表符分隔", sha)
save_evidence("yunnan", "yn_notice3787.txt", (DL / "n3787.txt").read_text(encoding="utf-8"), N, "调整专业考试计划通告页文本；HTML 去标签", hashlib.sha256((DL / "n3787.html").read_bytes()).hexdigest())
print("yunnan ok")
