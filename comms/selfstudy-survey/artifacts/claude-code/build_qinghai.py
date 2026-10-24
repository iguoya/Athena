"""青海：青海省教育招生考试院《青海省高等教育自学考试专业考试计划》（2026-02-25，16 个专业）。
计划 PDF 对本机下载经常被服务器截断，用 scratchpad/rangedl.py 按 Range 分块续传取全（616426 字节）。
用法：python -X utf8 build_qinghai.py <下载目录>
"""
import hashlib
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
PDF = "https://www.qhjyks.com/docs/20260225143853348139.pdf"
N = "https://www.qhjyks.com/ztzl/zxksz/5706.htm"  # 2026 年上半年成绩发布与毕业申请通告（2026-04-24），附该计划 PDF
HOME = "https://www.qhjyks.com/"

t = (DL / "qh_plan.txt").read_text(encoding="utf-8")
i = t.find("计算机科学与技术（专升本）考试计划")
seg = t[i: t.find("=== p10 ===", i)]
rows = [  # 逐行抄自该页：(代码, 名称, 学分, 类别, 配对)
    ("15040", "习近平新时代中国特色社会主义思想概论", 3, "public", None), ("15043", "中国近现代史纲要", 3, "public", None),
    ("15044", "马克思主义基本原理", 3, "public", None), ("13000", "英语（专升本）", 7, "public", None),
    ("13009", "数据库原理与技术", 4, "required", None), ("13017", "计算机网络与信息安全", 6, "required", None),
    ("13005", "软件工程", 3, "required", None), ("13006", "软件工程", 2, "practice", "13005"),
    ("13180", "操作系统", 4, "required", None),
    ("13013", "高级语言程序设计", 4, "required", None), ("13014", "高级语言程序设计", 2, "practice", "13013"),
    ("13003", "数据结构与算法", 4, "required", None), ("13004", "数据结构与算法", 2, "practice", "13003"),
    ("00023", "高等数学（工本）", 10, "required", None), ("02324", "离散数学", 4, "required", None),
    ("13175", "线性代数（工）", 3, "required", None), ("13015", "计算机系统原理", 4, "required", None),
    ("14263", "数字逻辑设计", 4, "required", None), ("13007", "编译原理", 4, "required", None),
    ("07999", "毕业设计", 0, "graduation", None),
]
for code, *_ in rows:  # 与原文逐码核对：每个课程代码都必须出现在该页文本里
    assert code in seg, code
courses = Shard("courses")
crow = []
for code, name, cr, cat, pair in rows:
    courses.add(code, {"name": name, "aliases": [], "kind": {"practice": "practice", "graduation": "graduation"}.get(cat, "theory"), "note": ""})
    crow.append(course_row(code, name, cr, cat, pair=pair))
assert sum(c["credits"] for c in crow) == 76

plan = {
    "id": "qh-080901-2026", "major": "080901", "track": None,
    "version": "专业考试计划（2026-02-25 发布，2026 年起按此申请毕业）", "effective": "2026-01", "state": "current",
    "total_credits": 76, "required_credits": 76,
    "rules": "官方表「总学分 76」，各行学分求和一致；全部为新计划必考课，毕业设计不计学分。「旧计划课程顶替方式」栏给出旧课程（如 04735 数据库系统原理、02331 数据结构等）对新课程的顶替；"
             "高等数学（工本）须 2 门旧课程（网络经济与企业管理、概率论与数理统计（二）、管理经济学、计算机系统结构、运筹学基础、信息系统开发与管理、信息资源管理中任选）顶替，其余课程任意 1 门顶替 1 门。"
             "2026 年起考生只能按该计划申请毕业，且只能用计划中的旧课程顶替新课程；计划含英语（专升本）时，考生可选考合计不少于 7 学分、未曾用于申请自学考试毕业证书的其他课程顶替，是否影响学位申请须咨询主考学校。",
    "courses": crow,
    "graduation": {"thesis": True, "credits": 0, "note": "毕业设计 07999，不计学分；毕业申请条件见《青海省高等教育自学考试毕业审定工作实施细则（试行）》。"},
    "source_files": ["qh_plan.txt"],
    "verify": V(PDF, "《青海省高等教育自学考试专业考试计划》PDF 第 9 页「计算机科学与技术（专升本）考试计划」，专业代码 080901，主考学校青海师范大学；发布见通告 " + N),
}
scope = load_scope()
offerings = [{"major": "080901", "track": None, "status": "open", "hosts": ["青海师范大学"], "plans": ["qh-080901-2026"],
              "complete": {"courses": True, "credits": True, "textbook": False},
              "verify": V(PDF, "专业考试计划 PDF：080901 计算机科学与技术（专升本），主考学校青海师范大学")}]
offerings += none_offerings(scope, {"080901"}, V(PDF, "2026-02-25 发布的《青海省高等教育自学考试专业考试计划》列全 16 个开考专业（专科 5、本科 11），其中无此专业；青海省教育考试网另有 2026-08-26 发布的「中文等 3 个高等教育自学考试新开专业」考试计划附件（未逐项核对是否含范围内专业）"))
write_province("qinghai", {
    "authority": {"name": "青海省教育招生考试院（青海省教育考试网）", "url": HOME, "verify": V(N)},
    "selfstudy_portal": {"name": "青海省自学考试考生服务平台", "url": "https://zxks.qhjyks.com:9527/login", "verify": V(N, "通告：考生登录服务平台查成绩、申请毕业、打印准考证")},
    "calendar": [],
    "policy": {
        "entry": None,
        "graduate": {"text": "毕业申请：上半年网上申请 5 月下旬、现场审核确认；申请本科毕业须提交专科（或以上）《教育部学历证书电子注册备案表》或《中国高等教育学历认证报告》，并通过学信网授权前置学历；实践课或毕业论文成绩须由主考学校录入后方可申请。2026 年起按专业考试计划申请毕业，只能用计划中的旧课程顶替新课程。", "verify": V(N, "2026 年上半年成绩发布及毕业申请通告（2026-04-24）")},
        "degree": {"text": "使用其他课程顶替英语（专升本）是否影响学位申请，须提前咨询主考学校。", "verify": V(N)},
        "exemption": None,
    },
    "offerings": offerings, "plans": [plan],
    "events": [{"date": "2026-02-25", "kind": "new-plan", "text": "青海省教育招生考试院发布《青海省高等教育自学考试专业考试计划》（16 个专业含计算机科学与技术（专升本），主考青海师范大学）；2026 年起考生按该计划申请毕业。", "verify": V(PDF)}],
})
courses.save()
sha = lambda p: hashlib.sha256((DL / p).read_bytes()).hexdigest()  # noqa: E731
save_evidence("qinghai", "qh_plan_full.txt", t, PDF, "青海省高等教育自学考试专业考试计划（16 页，Range 分块续传取全）；pypdf 抽取", sha("qh_plan_full.pdf"))
print("qinghai ok")
