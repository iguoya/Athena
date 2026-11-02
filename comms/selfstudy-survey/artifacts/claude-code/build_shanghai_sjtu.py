"""上海：补入上海交通大学计算机科学与技术（专升本，080901）考试计划（主考院校官网原文）、2026 年 10 月课程日程（上海市教育考试院）。
使用者 2026-11-02 在浏览器里下载：
  - 上海交通大学终身教育学院「考试计划-计算机科学与技术（专升本）」页 https://ce.sjtu.edu.cn/zxks/jxjh/1068（官方，主考院校原文）
  - 上海市教育考试院 2026 年 10 月各专业课程考试日程安排表 https://www.shmeea.edu.cn/download/20260520/1.pdf（来源页 .../page/04200/20260520/20257.html）
  - 上海市高等教育自学考试专业分类表（2025 年）https://www.shmeea.edu.cn/download/20250221/2.pdf（来源页 .../page/04300/20250226/19127.html）：080901 列在「预警专业」
官方页没有给总学分；必考课合计 73 学分是按表逐行核算的，rules 里写明；选考二选一与加考课不计入。
用法：python -X utf8 build_shanghai_sjtu.py <抽取目录> <Downloads 目录>
  抽取目录里放 `上海交通大学 自学考试 终身教育学院-成人高等教育 官网2222.html.txt`、1.pdf.txt、2.pdf.txt
"""
import hashlib
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-02"
from provlib import *  # noqa: E402,F403

EX, DL = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
PLAN_URL = "https://ce.sjtu.edu.cn/zxks/jxjh/1068"
SCHED_URL = "https://www.shmeea.edu.cn/page/04200/20260520/20257.html"
SCHED_PDF = "https://www.shmeea.edu.cn/download/20260520/1.pdf"
CLASS_URL = "https://www.shmeea.edu.cn/page/04300/20250226/19127.html"
CLASS_PDF = "https://www.shmeea.edu.cn/download/20250221/2.pdf"
HTML = DL / "上海交通大学 自学考试 终身教育学院-成人高等教育 官网2222.html"

# (code, 官方页写法, credits, category, pair, 官方页考试类别/备注)
ROWS = [
    ("15040", "习近平新时代中国特色社会主义思想概论", 3, "public", None, ""),
    ("15043", "中国近现代史纲要", 2, "public", None, "官方页写 2 学分（可替换旧课程 03708）"),
    ("15044", "马克思主义基本原理概论", 4, "public", None, "官方页写 4 学分、名称「马克思主义基本原理概论」（可替换旧课程 03709）"),
    ("13000", "英语（专升本）", 7, "public", None, ""),
    ("00023", "高等数学（工本）", 10, "required", None, ""),
    ("02324", "离散数学", 4, "required", None, ""),
    ("04737", "C++程序设计", 3, "required", None, ""),
    ("04738", "C++程序设计（实践）", 2, "practice", "04737", ""),
    ("13003", "数据结构与算法", 4, "required", None, ""),
    ("13004", "数据结构与算法（实践）", 2, "practice", "13003", ""),
    ("13015", "计算机系统原理", 4, "required", None, ""),
    ("13180", "操作系统", 4, "required", None, ""),
    ("02327", "操作系统（实践）", 1, "practice", "13180", ""),
    ("13170", "数据库及其应用", 4, "required", None, ""),
    ("13171", "数据库及其应用（实践）", 1, "practice", "13170", ""),
    ("13005", "软件工程", 3, "required", None, ""),
    ("13006", "软件工程（实践）", 2, "practice", "13005", ""),
    ("13017", "计算机网络与信息安全", 6, "required", None, ""),
    ("13215", "Java语言程序设计", 3, "required", None, ""),
    ("13216", "Java语言程序设计（实践）", 1, "practice", "13215", ""),
    ("13175", "线性代数（工）", 3, "required", None, ""),
    ("13011", "人工智能与大数据", 6, "elective", None, "与 14260 二选一，通过其中任一门即可"),
    ("14260", "数字电路与逻辑设计", 4, "elective", None, "与 13011 二选一，通过其中任一门即可"),
    ("13176", "电子技术基础", 4, "topup", None, "加考：非理工类专科起点才需加试，本科和理工类专科生不需要"),
    ("13177", "电子技术基础（实践）", 2, "practice", "13176", "加考：非理工类专科起点才需加试"),
    ("02318", "计算机组成原理", 4, "topup", None, "加考：非理工类专科起点才需加试"),
]
GRAD = ("11689", "毕业设计", "官方页写作「毕业设计」，原 10203")

lib = {}
for f in (CONTENT / "courses").glob("*.json"):
    lib.update(provlib._load(f)["courses"])
courses = Shard("courses")


def lib_name(code, name):
    """课程库已有该代码就沿用库里的名称（实践课用理论课名），官方页写法不同的写进行 note。"""
    base = name[: -len("（实践）")] if name.endswith("（实践）") else name
    base = base.replace("(实践)", "")
    return lib[code]["name"] if code in lib else base


crow, req = [], 0
for code, name, cr, cat, pair, note in ROWS:
    n = lib_name(code, name)
    notes = note
    official = name[: -len("（实践）")] if name.endswith("（实践）") else name
    if n != official:
        notes = (notes + "；" if notes else "") + f"官方页课程名写作「{name}」"
    courses.add(code, {"name": n, "aliases": [], "kind": "practice" if cat == "practice" else "theory", "note": ""})
    eg = "二选一（通过 13011、14260 中任一门即可）" if code in ("13011", "14260") else ("加考（非理工类专科起点才需加试）" if cat == "topup" or code == "13177" else None)
    crow.append(course_row(code, n, cr, cat, pair=pair, textbook=None, note=notes, elective_group=eg))
    if cat in ("public", "required") or (cat == "practice" and pair in {r[0] for r in ROWS if r[3] in ("public", "required")}):
        req += cr
assert req == 73, req
gc, gn, gnote = GRAD
gname = lib[gc]["name"] if gc in lib else gn
courses.add(gc, {"name": gname, "aliases": [], "kind": "graduation", "note": ""})
crow.append(course_row(gc, gname, 0, "graduation", note=gnote if gname != gn else "", elective_group=None))
pid = "sh-080901-sjtu-2026"
plan = {
    "id": pid, "major": "080901", "track": None,
    "version": "上海交通大学考试计划（本计划 2026 年起开始实施）", "effective": "2026-01", "state": "current",
    "total_credits": None, "required_credits": 73,
    "rules": "官方页没有给总学分。必考课（含思政 4 门 16 学分，其中 15043 写 2 学分、15044 写 4 学分，与全国 2025 年起思政课口径不同，按官方页照录）逐行相加 73 学分，为核算值，官方原表未直接给出；"
             "13011 人工智能与大数据、14260 数字电路与逻辑设计二选一（通过任一门即可）；电子技术基础（13176/13177）、计算机组成原理（02318）为加考，非理工类专科起点才需要，本科和理工类专科生不需要。"
             "老考生旧计划中通过的科目可对应新计划；外省转入时 2025 年及以前通过的旧计划理论课可接收，2026 年及以后通过的理论课仅同新计划课程代码者可接收，外省实践课一律不接收；与上海市教育考试院信息不一致以教育考试院为准。",
    "courses": crow,
    "graduation": {"thesis": True, "credits": 0, "note": "毕业设计（11689）为必考环节，学分 0。"},
    "source_files": ["sh_sjtu_plan_1068.html.txt"],
    "verify": V(PLAN_URL, "上海交通大学终身教育学院官网「考试计划-计算机科学与技术（专升本）」（主考院校原文），截至 2026-11-02 页面显示本专业处于预警状态"),
}

p = CONTENT / "provinces" / "shanghai.json"
d = provlib._load(p)
for o in d["offerings"]:
    if o["major"] == "080901":
        o["plans"] = [pid]
        o["mode"] = "面向社会"
        o["complete"] = {"courses": True, "credits": True, "textbook": False}
        o["verify"] = V(PLAN_URL, "上海交通大学主考、面向社会开考，官网称目前处于预警状态；上海市教育考试院 2025 年专业分类表（" + CLASS_PDF + "）将其列入「预警专业」；"
                        "2026 年 10 月课程日程（" + SCHED_PDF + "）：02324、15044、13215、02318（J）、13011、15040、00023、13003、13017、13176（J）、15043、13180、04737、13175、14260、13000、13005、13015、13170")
d["plans"] = [x for x in d["plans"] if x["id"] != pid] + [plan]
for c in d["calendar"]:
    if c["session"] == "2026-10":
        c["note"] = "各专业课程日程见沪教考院自考通知《2026 年 10 月上海市高等教育自学考试各专业课程考试日程安排表》（上午 9:00-11:30、下午 14:30-17:00，两天各两个时段）"
        c["verify"] = V(SCHED_URL, "上海市教育考试院 2026-05-20 发布；附件 PDF " + SCHED_PDF)
provlib._save(p, d)
courses.save()

dst = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence" / "shanghai"
shutil.copy2(HTML, dst / "sh_sjtu_plan_1068.html")
for f, name in ((DL / "1.pdf", "sh_sched_2026-10.pdf"), (DL / "2.pdf", "sh_classify_2025.pdf")):
    shutil.copy2(f, dst / name)
for src, name, url, note, raw in (
    (EX / (HTML.name + ".txt"), "sh_sjtu_plan_1068.html.txt", PLAN_URL, "上海交通大学考试计划页文本（浏览器另存 HTML 去标签）", HTML),
    (EX / "1.pdf.txt", "sh_sched_2026-10.pdf.txt", SCHED_PDF, "2026 年 10 月课程考试日程安排表，pymupdf 抽取", DL / "1.pdf"),
    (EX / "2.pdf.txt", "sh_classify_2025.pdf.txt", CLASS_PDF, "上海市高等教育自学考试专业分类表（2025 年），pymupdf 抽取", DL / "2.pdf"),
):
    save_evidence("shanghai", name, src.read_text(encoding="utf-8"), url, note, hashlib.sha256(raw.read_bytes()).hexdigest())
print("shanghai sjtu ok", len(crow), "rows")
