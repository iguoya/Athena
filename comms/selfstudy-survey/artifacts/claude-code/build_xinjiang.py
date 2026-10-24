"""新疆：新疆教育考试院《2026 年全国高等教育自学考试报考简章》（含开考专业、课程设置明细表）生成 provinces/xinjiang.json。
简章列出全部 12 个本科专业（含停考的信息管理与信息系统），范围内只有 080901 计算机科学与技术（2026 年 4 月起新开考，主考院校新疆师范大学）。
用法：python -X utf8 build_xinjiang.py <下载目录>
"""
import hashlib
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
N = "https://www.xjzk.gov.cn/c/2025-12-18/494952.shtml"  # 新疆维吾尔自治区2026年全国高等教育自学考试报考简章（页面）
P = "https://www.xjzk.gov.cn/upload/resources/file/2025/12/18/29840.pdf"  # 简章 PDF

txt = (DL / "xj_jz2026.txt").read_text(encoding="utf-8")
i = txt.find("计算机科学与技术（专升本）专业课程设置明细表\n专业代码")
seg = txt[i: txt.find("=== p39 ===", i)]
ROW = re.compile(r"^(?:(\d{1,2})\s+)?(\d{5})\s+(.+?)\s+(\d+)$")
fw = lambda s: re.sub(r"\s+", "", s.replace("(", "（").replace(")", "）"))  # noqa: E731
courses = Shard("courses")
crow, last = [], {}
for line in seg.split("\n"):
    m = ROW.match(line.strip())
    if not m:
        continue
    code, name, cr = m.group(2), fw(m.group(3)), int(m.group(4))
    cat, pair = "required", None
    if code in ("15040", "03708", "03709", "13000"):
        cat = "public"
    if name.endswith("（实践）"):
        base = name[:-4]
        cat, pair, name = "practice", last.get(base), (base if last.get(base) else name)
    else:
        last[name] = code
    courses.add(code, {"name": name, "aliases": [], "kind": "practice" if cat == "practice" else "theory", "note": ""})
    crow.append(course_row(code, name, cr, cat, pair=pair,
                           note="官方表思政课列 15040 + 旧代码 03708/03709，按原文录入" if code in ("03708", "03709") else ""))
assert sum(c["credits"] for c in crow) == 74, sum(c["credits"] for c in crow)
assert len(crow) == 18, len(crow)

plan = {
    "id": "xj-080901-2026", "major": "080901", "track": None,
    "version": "2026 年报考简章附件 2 专业课程设置明细表（新专业计划自 2024 年起实施，旧计划 2026 年 1 月废止）", "effective": "2026-04", "state": "current",
    "total_credits": 74, "required_credits": 74,
    "rules": "官方表直接给出：计划课程设置 16 门、总学分 74（实践考核环节不计入课程总门数；各行学分求和一致）。"
             "官方表思政课写 15040（3 学分）+ 03708（2 学分）+ 03709（4 学分），与全国 2025 年起调整后的 15040/15043/15044 不一致，此处照简章原文录入。"
             "含实践的课程及实践学分：高级语言程序设计（实践）2、数据结构与算法（实践）2、软件工程（实践）2；另有毕业设计（不计学分）。",
    "courses": crow,
    "graduation": {"thesis": False, "credits": 0, "note": "毕业设计（答辩），不计学分；完成实践环节考核及毕业设计答辩后准予毕业；实践性环节考核与论文答辩由主考院校自考办组织。"},
    "source_files": ["xj_jz2026_excerpt.txt"],
    "verify": V(P, "简章 PDF 附件 2「计算机科学与技术（专升本）专业课程设置明细表」，专业代码 080901，主考院校新疆师范大学；页面 " + N),
}
scope = load_scope()
offerings = [{"major": "080901", "track": None, "status": "open", "hosts": ["新疆师范大学"], "plans": ["xj-080901-2026"],
              "complete": {"courses": True, "credits": True, "textbook": False},
              "verify": V(P, "简章：自 2026 年 4 月考试起开考计算机科学与技术（专升本），专业代码 080901，主考院校新疆师范大学")}]
offerings += none_offerings(scope, {"080901"}, V(P, "简章列出全部开考专业 19 个（专科 7、本科 12），本科 12 个中无此专业（含已转停考的信息管理与信息系统）"))
events = [
    {"date": "2024-01", "kind": "new-plan", "text": "新疆自学考试自 2024 年起实施新专业计划课程设置，2026 年 1 月旧专业计划废止，所有考生须按新计划申请毕业；新旧课程过渡顶替见简章附件 3。", "verify": V(P)},
    {"date": "2025-04", "kind": "stop", "text": "英语（专科）970202 与信息管理与信息系统（本科）120102 调整为停考专业，不接受新考生报名，2027 年 10 月考试起不再安排课程考试，2028 年起不再办理毕业证书。", "verify": V(P)},
    {"date": "2026-04", "kind": "new-plan", "major": "080901", "text": "自 2026 年 4 月考试起开考计算机科学与技术（专升本），专业代码 080901，主考院校新疆师范大学；报考统一登录新疆招生网高等教育自学考试管理系统。", "verify": V(P)},
]
write_province("xinjiang", {
    "authority": {"name": "新疆教育考试院", "url": "https://www.xjzk.gov.cn/", "verify": V(N)},
    "selfstudy_portal": {"name": "新疆招生网·高等教育自学考试管理系统", "url": "https://www.xjzk.gov.cn/", "verify": V(P, "简章称考生统一登录新疆招生网高等教育自学考试管理系统；系统独立网址简章未给出，暂填新疆教育考试院门户")},
    "calendar": [
        {"session": "2026-04", "exam": "2026-04-11~12", "register": "2026-03-02 12:00~03-06 18:00", "verify": V(P)},
        {"session": "2026-10", "exam": "2026-10-24~25", "register": "2026-08-31 12:00~09-04 18:00", "verify": V(P)},
    ],
    "policy": {
        "entry": {"text": "中华人民共和国公民不受性别、民族和已受教育程度等限制均可报名；可同时报考专科与本科层次各专业课程，本科毕业手续须在获得专科毕业证半年之后办理。", "verify": V(P, "简章二、三")},
        "graduate": {"text": "通过专业计划全部课程考试，完成实践环节考核及毕业设计答辩，思想品德符合要求，准予毕业并颁发自学考试本科毕业证书；毕业手续每年上半年 6 月或下半年 12 月前办理。", "verify": V(P, "简章一、八")},
        "degree": {"text": "自学考试本科毕业考生可向有学位授予权的主考院校申请学位，条件由主考院校制定（080901 可按新疆师范大学学位授予相关规定申请）。", "verify": V(P, "简章一、八")},
        "exemption": {"text": "已通过 03708 / 03709 / 03706 / 12656 的考生，不再要求参加对应的 15043 / 15044 / 15042 / 15041；新旧专业计划课程按简章附件 3 过渡顶替表顶替。", "verify": V(P, "简章一（二）4")},
    },
    "offerings": offerings, "plans": [plan], "events": events,
})
courses.save()
sha = lambda p: hashlib.sha256((DL / p).read_bytes()).hexdigest()  # noqa: E731
excerpt = "\n".join(re.split(r"(?m)^(?==== p)", txt)[:8]) + "\n=== p37-38 ===\n" + seg
save_evidence("xinjiang", "xj_jz2026_excerpt.txt", excerpt, P, "2026 年全国高等教育自学考试报考简章（76 页）：正文 p1-7 与 080901 明细表；全文未入库", sha("xj_jz2026.pdf"))
print("xinjiang ok", len(crow))
