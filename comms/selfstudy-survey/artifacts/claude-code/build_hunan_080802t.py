"""湖南 080802T 轨道交通信号与控制（中南大学，助学型）：补入 2024 年版专业考试计划，并回填教材。
使用者（2026-11-02）从 hneeb.cn 下载了 2024 年版计划 zip；本脚本只往已有 provinces/hunan.json 追加该专业的计划，
并把 offerings 里同专业的记录改成「计划已入库」，其余内容不动。
用法：python -X utf8 build_hunan_080802t.py <目录>   目录里放 hn_plan2024.txt（pypdf 抽取，带 `=== pN ===` 页标记）、
      hn_plan2024.pdf、arr10.xlsx（2026 年 10 月课程安排及教材目录）
"""
import hashlib
import pathlib
import re
import sys

import openpyxl

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-02"
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
CODE = "080802T"
N_PLAN = "https://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/web/ksyzkzx/202412/t20241202_33515314.html"
N_ARR10 = "https://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/web/ksyzkzx/202605/t20260515_33977962.html"
Z_PLAN = "https://www.hneeb.cn/hnxxg/761/762/20241202.zip"
X_ARR10 = "https://www.hneeb.cn/hnxxg/761/764/2026051501.xlsx"

txt = (DL / "hn_plan2024.txt").read_text(encoding="utf-8")
parts = re.split(r"(?m)^=== p(\d+) ===$", txt)
pages = {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}
page = next(n for n, t in pages.items() if f"代码：{CODE}" in t and "课程类别" in t)
body = pages[page]
body = body[: body.index("四、毕业要求")]


def fw(s):
    return re.sub(r"\s+", "", s.replace("(", "（").replace(")", "）"))


ROW = re.compile(r"^(?:(\d{1,2})\s+)?(\d{5})\s+(.+?)\s+(\d+)$")
lines = [l.strip() for l in body.split("\n")]
rows, mode = [], "required"
for i, l in enumerate(lines):
    if l == "选" and lines[i + 1] == "考":
        mode = "elective"
        continue
    m = ROW.match(l.replace("毕业环节", "").strip())
    if m and not l.startswith("选考门数"):
        rows.append((m.group(2), fw(m.group(3)), int(m.group(4)), mode, "毕业论文" in l))
total = int(re.search(r"总学分\s*(\d+)", body).group(1))
assert total == 73 and len(rows) == 24, (total, len(rows))
req = sum(r[2] for r in rows if r[3] == "required" and not r[4])
assert req == 50, req

wb = openpyxl.load_workbook(DL / "arr10.xlsx", data_only=True)
books10 = {}
for r in wb.active.iter_rows(values_only=True):
    if r and len(r) >= 10 and r[4] and str(r[4]).strip().isdigit() and len(str(r[4]).strip()) == 5 and r[5]:
        books10.setdefault(str(r[4]).strip(), r)

courses, books = Shard("courses"), Shard("textbooks")
EG = "推荐选考课（选考门数不少于 4 门，学分不低于 23 分）"
crow, last_theory = [], {}
for code, name, cr, mode, grad in rows:
    cat, pair = "required", None
    if grad:
        cat = "graduation"
    elif name.endswith("（实践）"):
        base = name[: -len("（实践）")]
        pair, name, cat = last_theory[base], base, "practice"
    elif code in ("15040", "15043", "15044", "13000"):
        cat = "public"
    elif mode == "elective":
        cat = "elective"
    if cat not in ("practice", "graduation"):
        last_theory[name] = code
    courses.add(code, {"name": name, "aliases": [], "kind": {"practice": "practice", "graduation": "graduation"}.get(cat, "theory"), "note": ""})
    tb = None
    br = books10.get(code)
    if br and cat in ("public", "required", "elective"):
        ym = re.search(r"(\d{4})", str(br[9] or ""))
        tb = f"tb-hn-{code}-{ym[1] if ym else 'x'}"
        if tb in books.items or tb in books.others:
            pass  # 同教材同目录已由湖南第一轮入库，核对日期不同不算冲突，沿用已有条目
        else:
          books.add(tb, {
            "title": str(br[6]).strip(), "authors": [a for a in re.split(r"[、,，]", str(br[7]).replace(" ", "")) if a],
            "publisher": str(br[8]).strip(), "edition": str(br[9]).strip(), "isbn": None, "kind": None,
            "outline": "考试大纲见湖南省教育考试院；课程安排及教材目录按考次公布",
            "verify": V(N_ARR10, "2026 年 10 月湖南省高等教育自学考试课程考试安排及教材目录（xlsx）"),
        })
    egroup = EG if mode == "elective" and cat != "graduation" else None
    crow.append(course_row(code, name, cr, cat, pair=pair, textbook=tb, note="", elective_group=egroup))

pid = f"hn-{CODE.lower()}-2024"
plan = {
    "id": pid, "major": CODE, "track": None,
    "version": "专业考试计划（2024 年版，湘教考自字〔2024〕6号）；2026 年起全部按此版开考与毕业审核", "effective": "2024-10", "state": "current",
    "total_credits": 73, "required_credits": 73,
    "rules": "必考课程 10 门 50 学分（含思政课 3 门 9 学分）；选考门数不少于 4 门、学分不低于 23 分；总学分 73（官方表直接给出，= 必考 50 + 选考下限 23）。"
             "考试课程相关的实践考核环节不单独计入课程总门数；考生取得理论课程合格成绩后方可报考相应实践，取得全部理论与实践合格成绩后方可报考毕业论文。"
             "专科起点本科层次，申请毕业须提供国家承认学历的专科及以上毕业证书。表中选考课只列推荐选考课，选考课表里的课程以 elective 标注，实际考哪几门由考生按门数与学分下限自选。",
    "courses": crow,
    "graduation": {"thesis": True, "credits": 0, "note": "毕业环节考核课程（毕业论文）为必考课程；实践环节与毕业环节的考核要求由主考学校公布。"},
    "source_files": ["hn_plan2024_excerpt.txt"],
    "verify": V(N_PLAN, f"《湖南省高等教育自学考试专业考试计划（2024 年版）》PDF（zip 附件 {Z_PLAN}）第 {page} 页；选考行 elective_group 标注选考门数与学分下限；新旧计划顶替表见同文件第 {page + 1} 页"),
}
p = CONTENT / "provinces" / "hunan.json"
d = provlib._load(p)
d["plans"] = [x for x in d["plans"] if x["major"] != CODE] + [plan]
for o in d["offerings"]:
    if o["major"] == CODE:
        o["plans"] = [pid]
        o["complete"] = {"courses": True, "credits": True, "textbook": any(c["textbook"] for c in crow)}
d["events"] = d.get("events", [])
provlib._save(p, d)
courses.save()
books.save()

excerpt = "\n".join(f"=== p{n} ===\n{pages[n]}" for n in (page - 1, page, page + 1))
sha = hashlib.sha256((DL / "hn_plan2024.pdf").read_bytes()).hexdigest()
save_evidence("hunan", "hn_080802t_plan_excerpt.txt", excerpt, Z_PLAN, f"专业考试计划（2024 年版）{CODE} 计划页（第 {page - 1}~{page + 1} 页），pypdf 抽取；zip 内 PDF 的 sha256 在 sha256 行", sha)
print("ok", len(crow), "rows")
