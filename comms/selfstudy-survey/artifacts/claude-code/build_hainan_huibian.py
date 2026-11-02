"""海南：由《海南省高等教育自学考试开考专业汇编（2025 年修订版）》（官方公告附件 PDF，95 页）补入开设矩阵与计划。
汇编目录列本科 53 个专业，是官方全表：范围内只有 080901 计算机科学与技术、080902 软件工程、080801 自动化。
课程行逐行抄自 PDF（pymupdf 抽取后人工对页核对，学分求和与官方「必考/选考学分」「总学分」一致）。
用法：python -X utf8 build_hainan_huibian.py <目录>   目录里放 hn_huibian.pdf、hn_huibian.txt（pymupdf 抽取）
"""
import hashlib
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-02"
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
NOTICE = "https://ea.hainan.gov.cn/ywdt/zxks/202506/t20250626_3886359.html"
PDF = "http://ea.hainan.gov.cn/ywdt/zxks/202506/P020250626391691488847.pdf"
STOP = "https://ea.hainan.gov.cn/ywdt/zxks/202610/t20261030_4170790.html"
BASE = "海南省考试局《海南省高等教育自学考试开考专业汇编（2025 年修订版）》（2025-06-26 公告附件 PDF，海南省考试局 2025-02 编印）"

PUBLIC = [("15040", "习近平新时代中国特色社会主义思想概论", 3), ("15043", "中国近现代史纲要", 3), ("15044", "马克思主义基本原理", 3), ("13000", "英语（专升本）", 7)]
# 每行：(code, name, credits, category, pair)；practice 行 name 取理论课名（课程库约定），pair 指理论课代码
PLANS = {
    "080901": {
        "page": 3, "pdf_page": 10, "total": 75, "req": 50, "el": (5, 25), "mode": "社会与助学",
        "hosts": ["海南大学", "海南师范大学", "长沙理工大学"],
        "host_note": "海南大学（社会、助学）、海南师范大学（助学）、长沙理工大学（助学）",
        "rows": [
            ("00023", "高等数学（工本）", 10, "required", None), ("02324", "离散数学", 4, "required", None),
            ("13013", "高级语言程序设计", 4, "required", None), ("13014", "高级语言程序设计", 2, "practice", "13013"),
            ("13003", "数据结构与算法", 4, "required", None), ("13004", "数据结构与算法", 2, "practice", "13003"),
            ("13015", "计算机系统原理", 4, "required", None), ("13180", "操作系统", 4, "required", None),
            ("13017", "计算机网络与信息安全", 6, "elective", None), ("13011", "人工智能与大数据", 6, "elective", None),
            ("14263", "数字逻辑设计", 4, "elective", None),
            ("13005", "软件工程", 3, "elective", None), ("13006", "软件工程", 2, "practice", "13005"),
            ("02325", "计算机系统结构", 4, "elective", None),
        ],
        "grad": ("07999", "毕业设计"), "need": "不少于 15 门",
    },
    "080902": {
        "page": 39, "pdf_page": 46, "total": 73, "req": 51, "el": (5, 22), "mode": "助学",
        "hosts": ["海南师范大学"], "host_note": "海南师范大学（助学）",
        "rows": [
            ("00023", "高等数学（工本）", 10, "required", None), ("02324", "离散数学", 4, "required", None),
            ("13013", "高级语言程序设计", 4, "required", None), ("13014", "高级语言程序设计", 2, "practice", "13013"),
            ("13003", "数据结构与算法", 4, "required", None), ("13004", "数据结构与算法", 2, "practice", "13003"),
            ("13180", "操作系统", 4, "required", None),
            ("13005", "软件工程", 3, "required", None), ("13006", "软件工程", 2, "practice", "13005"),
            ("13008", "软件质量保证与测试", 4, "elective", None), ("14126", "软件过程与管理", 4, "elective", None),
            ("13009", "数据库原理与技术", 4, "elective", None), ("13010", "人机交互的软件工程方法", 4, "elective", None),
            ("13011", "人工智能与大数据", 6, "elective", None),
        ],
        "grad": ("07999", "毕业设计"), "need": "不少于 15 门",
    },
    "080801": {
        "page": 38, "pdf_page": 45, "total": 73, "req": 51, "el": (4, 22), "mode": "助学",
        "hosts": ["海南师范大学"], "host_note": "海南师范大学（助学）",
        "rows": [
            ("00023", "高等数学（工本）", 10, "required", None), ("13175", "线性代数（工）", 3, "required", None),
            ("04737", "C++程序设计", 3, "required", None), ("04738", "C++程序设计", 2, "practice", "04737"),
            ("14745", "自动控制原理（本）", 5, "required", None), ("14746", "自动控制原理（本）", 1, "practice", "14745"),
            ("01644", "单片机原理与接口技术", 4, "required", None), ("01645", "单片机原理与接口技术", 2, "practice", "01644"),
            ("08244", "现代控制工程", 5, "required", None),
            ("07454", "传感器技术与应用", 4, "elective", None), ("09121", "传感器技术与应用", 1, "practice", "07454"),
            ("08173", "过程控制工程", 4, "elective", None), ("08174", "过程控制工程", 2, "practice", "08173"),
            ("08241", "计算机控制系统", 6, "elective", None), ("08242", "计算机控制系统", 1, "practice", "08241"),
            ("09122", "电气控制及PLC技术", 2, "elective", None), ("09123", "电气控制及PLC技术", 2, "practice", "09122"),
        ],
        "grad": ("07999", "毕业设计"), "need": "不少于 14 门",
    },
}

courses = Shard("courses")
plans, offerings = [], []
for major, P in PLANS.items():
    rows = [(c, n, cr, "public", None) for c, n, cr in PUBLIC] + P["rows"]
    req = sum(cr for c, n, cr, cat, pair in rows if cat in ("public", "required")) + sum(
        cr for c, n, cr, cat, pair in rows if cat == "practice" and next(r[3] for r in rows if r[0] == pair) in ("public", "required"))
    el = sum(cr for c, n, cr, cat, pair in rows if cat == "elective") + sum(
        cr for c, n, cr, cat, pair in rows if cat == "practice" and next(r[3] for r in rows if r[0] == pair) == "elective")
    assert req == P["req"] and el == P["el"][1] and req + el == P["total"], (major, req, el)
    eg = f"选考课（选考课程 {P['el'][0]} 门，{P['el'][1]} 学分）"
    crow = []
    for code, name, cr, cat, pair in rows:
        courses.add(code, {"name": name, "aliases": [], "kind": "practice" if cat == "practice" else "theory", "note": ""})
        in_el = cat == "elective" or (cat == "practice" and next(r[3] for r in rows if r[0] == pair) == "elective")
        crow.append(course_row(code, name, cr, cat, pair=pair, textbook=None, note="", elective_group=eg if in_el else None))
    gc, gn = P["grad"]
    courses.add(gc, {"name": gn, "aliases": [], "kind": "graduation", "note": ""})
    crow.append(course_row(gc, gn, 0, "graduation", note="", elective_group=None))
    pid = f"hi-{major}-2025"
    plans.append({
        "id": pid, "major": major, "track": None,
        "version": "开考专业汇编（2025 年修订版，海南省考试局 2025-02 编印，2025-06-26 公告发布）", "effective": "2025-06", "state": "current",
        "total_credits": P["total"], "required_credits": P["total"],
        "rules": f"官方表：必考课程 {10} 门 {P['req']} 学分，选考课程 {P['el'][0]} 门 {P['el'][1]} 学分，总学分 {P['total']}；考试课程不得少于{P['need'].replace('不少于 ', '')}，总学分不得少于 {P['total']}。"
                 "考试课程相关的实践考核环节不单独计入课程总门数；理论考试与实践环节考核两部分都合格方能获得该门课程学分，实践环节须在全部理论课合格后报考，由主考学校负责。"
                 "学位授予的具体要求由主考学校根据相关规定确定。选考课表所列课程数与官方「选考课程 N 门」一致，以 elective 标注。",
        "courses": crow,
        "graduation": {"thesis": True, "credits": 0, "note": "毕业环节（毕业设计）为必考课程，学分 0；考核由主考学校负责。"},
        "source_files": ["hn_huibian.pdf.txt"],
        "verify": V(NOTICE, f"{BASE}第 {P['page']} 页（PDF 第 {P['pdf_page']} 页）；附件 {PDF}"),
    })
    note = f"{BASE}目录列本科 53 个专业；主考院校：{P['host_note']}；开考方式：{P['mode']}"
    if major == "080801":
        note += f"；另据海南省考试局 2026-10-30 公告（{STOP}），自动化（专升本）自 2027-01-01 起停止接受新生注册报名"
    offerings.append({"major": major, "track": None, "status": "open", "hosts": P["hosts"], "mode": P["mode"], "plans": [pid],
                      "complete": {"courses": True, "credits": True, "textbook": False}, "verify": V(NOTICE, note)})

none_v = V(NOTICE, f"{BASE}目录列本科 53 个专业（面向社会与助学 7 个、助学 46 个），全表未列此专业；汇编之后的新增开考专业未逐条核对")
p = CONTENT / "provinces" / "hainan.json"
d = provlib._load(p)
d["offerings"] = offerings + none_offerings(load_scope(), set(PLANS), none_v)
d["plans"] = plans
d["events"] = [e for e in d["events"] if e.get("date") != "2025-06-26"] + [
    {"date": "2025-06-26", "kind": "new-plan", "text": "海南省考试局发布《海南省高等教育自学考试开考专业汇编（2025 年修订版）》，依据考委〔2024〕1 号调整思想政治理论课课程设置；本科 53 个专业，毕业需总学分不少于 73、考试课程不少于 14 门。",
     "verify": V(NOTICE, "公告页与附件 PDF")},
]
provlib._save(p, d)
courses.save()
save_evidence("hainan", "hn_huibian.pdf.txt", (DL / "hn_huibian.txt").read_text(encoding="utf-8"), PDF, "开考专业汇编（2025 年修订版）全文 95 页，pymupdf 抽取", hashlib.sha256((DL / "hn_huibian.pdf").read_bytes()).hexdigest())
dst = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence" / "hainan"
dst.mkdir(parents=True, exist_ok=True)
shutil.copy2(DL / "hn_huibian.pdf", dst / "hn_huibian.pdf")
print("hainan ok", len(plans), "plans", len(d["offerings"]), "offerings")
