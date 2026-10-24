"""湖南：由湖南省教育考试院官方文件生成 provinces/hunan.json。
来源：湘教考自字〔2024〕6号附件《湖南省高等教育自学考试专业考试计划（2024 年版）》（PDF，全文本）、
2026 年 10 月报考简章附表（开考专业与主考学校、社会型主考表、助学型标注）、
2026 年 10 月课程考试安排及教材目录（xlsx）。
用法：python -X utf8 build_hunan.py <下载目录>
"""
import hashlib
import pathlib
import re
import sys

import openpyxl

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
HOME = "https://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/web/ksyzkzx/"
N_PLAN = "https://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/web/ksyzkzx/202412/t20241202_33515314.html"  # 湘教考自字〔2024〕6号
N_JZ10 = "https://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/web/ksyzkzx/202607/t20260729_34035925.html"  # 2026 年 10 月报考简章
N_ARR10 = "https://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/web/ksyzkzx/202605/t20260515_33977962.html"  # 2026 年 10 月课程安排及教材目录
N_ARR04 = "https://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/web/ksyzkzx/202511/t20251107_33844225.html"  # 2026 年 4 月课程安排及教材目录
N_JZ04 = "https://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/web/ksyzkzx/202601/t20260114_33892864.html"  # 2026 年 4 月报考简章
Z_PLAN = "https://www.hneeb.cn/hnxxg/761/762/20241202.zip"
X_JZ10 = "https://www.hneeb.cn/hnxxg/761/762/2026072901.xlsx"
X_ARR10 = "https://www.hneeb.cn/hnxxg/761/764/2026051501.xlsx"

MAJORS = ["080801", "080901", "080902", "080905"]  # 湖南开考的范围内专业（附表 1 核对）

plan_txt = (DL / "hn_plan2024.txt").read_text(encoding="utf-8")
pages = re.split(r"(?m)^=== p(\d+) ===$", plan_txt)  # [pre, no, text, no, text ...]
page_text = {int(pages[i]): pages[i + 1] for i in range(1, len(pages), 2)}


def fw(s: str) -> str:
    """半角括号换全角，与已有课程库的名称写法一致。"""
    return re.sub(r"\s+", "", s.replace("(", "（").replace(")", "）"))


ROW = re.compile(r"^(?:(\d{1,2})\s+)?(\d{5})\s+(.+?)\s+(\d+(?:\.\d+)?)(?:\s+(.*))?$")


def plan_section(code):
    """返回 (说明句, 课程表文本)：定位『专业名称：… 代码：<code>』所在页起、到『四、毕业要求』止。"""
    head = None
    for no, t in page_text.items():
        if f"代码：{code}" in t and "课程类别" in t:
            head = no
    if head is None:
        raise SystemExit(f"找不到 {code} 的课程表页")
    # 说明句在前一页末或本页前
    prev = page_text[head - 1]
    k = prev.rfind("本专业课程设置如下表")
    intro = prev[k:] if k >= 0 else ""
    body = page_text[head]
    n = head
    while "四、毕业要求" not in page_text[n] and "总学分" not in page_text[n]:
        n += 1
        body += "\n" + page_text[n]
    end = body.find("四、毕业要求")
    return intro, body[: end if end >= 0 else None], head


def parse_table(body):
    lines = [l.strip() for l in body.split("\n")]
    rows, mode, started = [], "required", False
    seen_single = []
    for i, l in enumerate(lines):
        if l.endswith("备注"):
            started = True
            continue
        if not started:
            continue
        if l.startswith("总学分"):
            break
        # 选考课竖排标记：单字行「选」「考」「课」，出现在必考课之后
        if l == "选" and i + 1 < len(lines) and lines[i + 1] == "考" and rows:
            mode = "elective"
            continue
        l2 = l.replace("毕业环节", "").strip()
        m = ROW.match(l2)
        if m and not l2.startswith("选考门数"):
            code, name, cr, note = m.group(2), m.group(3), float(m.group(4)), m.group(5) or ""
            rows.append({"seq": m.group(1), "code": code, "name": fw(name), "credits": int(cr) if cr == int(cr) else cr,
                         "mode": mode, "note": note.strip(), "grad": "毕业环节" in l or "毕业论文" in name})
    return rows


# ---- 教材：2026 年 10 月与 4 月课程安排及教材目录（按课程代码）----
def load_books(fn):
    wb = openpyxl.load_workbook(DL / fn, data_only=True)
    out = {}
    for r in wb.active.iter_rows(values_only=True):
        if r and len(r) == 9:  # 4 月表没有「序号」列，补齐成 10 列与 10 月表同形
            r = (None,) + tuple(r)
        if r and len(r) >= 10 and r[4] and str(r[4]).strip().isdigit() and len(str(r[4]).strip()) == 5 and r[5]:
            out.setdefault(str(r[4]).strip(), r)
    return out


books10 = load_books("hn_arr10.xlsx")
books04 = load_books("hn_arr04.xlsx") if (DL / "hn_arr04.xlsx").exists() else {}

courses, books = Shard("courses"), Shard("textbooks")
plans, offerings, notes = [], [], {}

# ---- 附表 1：开考专业与主考学校 ----
wb = openpyxl.load_workbook(DL / "jz10.xlsx", data_only=True)
t1 = wb["表1专升本"]
hosts = {}
for r in t1.iter_rows(values_only=True):
    if r and r[1] in MAJORS and r[3]:
        raw = str(r[3]).strip()
        name = re.sub(r"^\d{4}", "", raw)
        social = "▲" in name
        name = name.replace("▲", "").replace("●", "")
        hosts.setdefault(r[1], []).append((name, social))
t3 = wb["表3助学型及限制报考专业"]
assisted = {r[1] for r in t3.iter_rows(values_only=True) if r and r[1] in MAJORS}

for code in MAJORS:
    intro, body, pg = plan_section(code)
    rows = parse_table(body)
    mm = re.search(r"必考课程为\s*(\d+)\s*门，学分为\s*(\d+)\s*分。选考门数不少于\s*(\d+)\s*门，学分不低于\s*(\d+)\s*分", intro.replace("\n", ""))
    assert mm, (code, intro[:200])
    req_n, req_cr, el_n, el_cr = map(int, mm.groups())
    total = int(re.search(r"总学分\s*(\d+)", body).group(1))
    strong = {c for l in body.split(chr(10)) if "强实践" in l for c in re.findall(r"(\d{5})", l)}
    crow, last_theory = [], {}
    for r in rows:
        name, cat = r["name"], "required"
        code_, cr = r["code"], r["credits"]
        pair = None
        practice = None
        if r["grad"]:
            cat = "graduation"
        elif name.endswith("（实践）"):
            base = name[: -len("（实践）")]
            if base in last_theory:
                pair, name, cat = last_theory[base], base, "practice"
            else:
                cat = "practice"
        elif code_ in ("15040", "15043", "15044", "13000"):
            cat = "public"
        elif r["mode"] == "elective":
            cat = "elective"
        if cat not in ("practice", "graduation"):
            last_theory[name] = code_
        kind = {"practice": "practice", "graduation": "graduation"}.get(cat, "theory")
        courses.add(code_, {"name": name, "aliases": [], "kind": kind, "note": ""})
        tb = None
        if cat in ("public", "required", "elective"):
            br = books10.get(code_) or books04.get(code_)
            if br:
                isbn = None
                ym = re.search(r"(\d{4})", str(br[9] or ""))
                bid = f"tb-hn-{code_}-{ym[1] if ym else 'x'}"
                books.add(bid, {
                    "title": str(br[6]).strip(), "authors": [a for a in re.split(r"[、,，]", str(br[7]).replace(" ", "")) if a],
                    "publisher": str(br[8]).strip(), "edition": str(br[9]).strip(), "isbn": isbn, "kind": None,
                    "outline": "考试大纲见湖南省教育考试院；课程安排及教材目录按考次公布",
                    "verify": V(N_ARR10 if code_ in books10 else N_ARR04, ("2026 年 10 月" if code_ in books10 else "2026 年 4 月") + "湖南省高等教育自学考试课程考试安排及教材目录（xlsx）"),
                })
                tb = bid
        egroup = f"推荐选考课（选考门数不少于 {el_n} 门，学分不低于 {el_cr} 分）" if r["mode"] == "elective" and cat != "graduation" else None
        note = r["note"]
        if code_ in strong:
            practice = {"type": "强实践", "note": "计划说明标注为「强实践」课程（附表 4 强实践课程列表）"}
        row = course_row(code_, name, cr, cat, pair=pair, practice=practice, textbook=tb, note=note, elective_group=egroup)
        if cat == "practice" and r["mode"] == "elective":
            row["elective_group"] = egroup
        crow.append(row)
    assert crow
    pid = f"hn-{code}-2024"
    plans.append({
        "id": pid, "major": code, "track": None,
        "version": "专业考试计划（2024 年版，湘教考自字〔2024〕6号）；2026 年起全部按此版开考与毕业审核", "effective": "2024-10", "state": "current",
        "total_credits": total, "required_credits": total,
        "rules": f"必考课程 {req_n} 门 {req_cr} 学分（含思政课 3 门 9 学分）；选考门数不少于 {el_n} 门、学分不低于 {el_cr} 分；总学分 {total}（官方表直接给出，= 必考 {req_cr} + 选考下限 {el_cr}）。"
                 "考试课程相关的实践考核环节不单独计入课程总门数；考生取得理论课程合格成绩后方可报考相应实践，取得全部理论与实践合格成绩后方可报考毕业论文。"
                 "专科起点本科层次，申请毕业须提供国家承认学历的专科及以上毕业证书。表中选考课只列推荐选考课，选考课表里的课程以 elective 标注，实际考哪几门由考生按门数与学分下限自选。",
        "courses": crow,
        "graduation": {"thesis": True, "credits": 0, "note": "毕业环节考核课程（毕业论文/毕业设计等）为必考课程；实践环节与毕业环节的考核要求由主考学校公布。"},
        "source_files": ["hn_plan2024_excerpt.txt", "hn_jz10.txt", "hn_arr10.txt"],
        "verify": V(N_PLAN, f"《湖南省高等教育自学考试专业考试计划（2024 年版）》PDF（zip 附件 {Z_PLAN}）第 {pg} 页起；选考行 elective_group 标注选考门数与学分下限"),
    })
    hs = hosts[code]
    social = [h for h, s in hs if s]
    mode = "助学型" if code in assisted else ("社会型" if social else None)
    note = "湖南省 2026 年 10 月报考简章附表 1（开考专业主考学校）"
    if social:
        note += f"；▲为承担社会考生主考工作的学校：{'、'.join(social)}"
    if code in assisted:
        note += "；附表 3 标注为助学型专业"
    offerings.append({"major": code, "track": None, "status": "open", "hosts": [h for h, _ in hs], "mode": mode,
                      "plans": [pid], "complete": {"courses": True, "credits": True, "textbook": any(c["textbook"] for c in crow)},
                      "verify": V(X_JZ10, note)})

scope = load_scope()
offerings += none_offerings(scope, set(MAJORS), V(X_JZ10, "湖南省 2026 年 10 月报考简章附表 1《开考专业（专升本）》全表未列此专业；2026 年 4 月、10 月均开考 96 个专业"))

events = [
    {"date": "2024-12-02", "kind": "new-plan", "text": "湘教考自字〔2024〕6号：公布《专业考试计划（2024 年版）》，收录 86 个现行开考专业；2024 年下半年起按新版开考，2024、2025 年为过渡期，2026 年起全部按 2024 版开考课程并审核毕业。", "verify": V(N_PLAN)},
]
write_province("hunan", {
    "authority": {"name": "湖南省教育考试院", "url": "https://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/web/ksyzkzx/", "verify": V(N_JZ10)},
    "selfstudy_portal": {"name": "湖南自考服务平台（报考简章所指的开考专业与主考学校查询入口）", "url": "https://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/web/ksyzkzx/", "verify": V(N_JZ04, "简章称考生可在「湖南自考服务平台」查看开考专业及主考学校；平台具体网址简章页未直接给出，此处暂填考试院自考栏目页")},
    "calendar": [
        {"session": "2026-04", "exam": "2026-04-11~12", "register": "理论课 2026-01-23 9:00~02-01 17:00；强实践/实践课 02-02~04；缴费截止 02-05 17:00", "verify": V(N_JZ04, "湖南省2026年4月高等教育自学考试报考简章")},
        {"session": "2026-10", "exam": "2026-10-24~25", "register": "理论课 2026-08-24 9:00~08-31 17:00；强实践/实践课 09-01 9:00~03 17:00；缴费截止 09-04 17:00", "verify": V(N_JZ10, "湖南省2026年10月高等教育自学考试报考简章")},
    ],
    "policy": {
        "entry": {"text": "新生入籍不受性别、年龄、民族、种族和已受教育程度限制（有特殊要求的专业除外）；各本科专业为专科起点本科层次，申请毕业须提供国家承认学历的专科及以上毕业证书。", "verify": V(N_JZ04, "2026 年 4 月报考简章「新生入籍」条款；毕业学历要求见各专业考试计划毕业要求")},
        "graduate": {"text": "取得专业考试计划规定的必考课、选考课（门数与学分达到下限）及毕业环节课程的合格成绩，政治思想品德经鉴定符合要求；2026 年起全部按 2024 版专业考试计划审核毕业。", "verify": V(N_PLAN)},
        "degree": None,
        "exemption": {"text": "课程免考与顶替按《湖南省高等教育自学考试课程免考顶替办法》和 2024 版计划的新旧计划课程顶替办法执行；公共政治课按原湘教考委〔2007〕12号文件顶替；同一专业不同版本计划课程允许延续顶替，不能跨专业或重复顶替。", "verify": V(N_PLAN, "湘教考自字〔2024〕6号通知正文「课程替代」")},
    },
    "offerings": offerings, "plans": plans, "events": events,
})
courses.save()
books.save()

# 证据
def sha(p):  # noqa
    return hashlib.sha256((DL / p).read_bytes()).hexdigest()


excerpt = "\n".join(f"=== p{n} ===\n{t}" for n, t in sorted(page_text.items()) if n <= 3 or any(f"代码：{c}" in t for c in MAJORS) or any(f"({c}" in t for c in MAJORS))
save_evidence("hunan", "hn_plan2024_excerpt.txt", excerpt, Z_PLAN, "专业考试计划（2024 年版）全文 393 页，此处仅摘前言与范围内专业的计划页；zip 内 PDF sha256 见 note", sha("hn_plan2024.pdf") + "（PDF 本体）")
save_evidence("hunan", "hn_jz10.txt", (DL / "hn_jz10.txt").read_text(encoding="utf-8"), X_JZ10, "2026 年 10 月报考简章附表 1-5；openpyxl 抽取", sha("jz10.xlsx"))
save_evidence("hunan", "hn_jz04.txt", (DL / "jz04.txt").read_text(encoding="utf-8"), N_JZ04, "2026 年 4 月报考简章页面文本；HTML 去标签", sha("jz04.html"))
save_evidence("hunan", "hn_jz10_page.txt", (DL / "jz10.txt").read_text(encoding="utf-8"), N_JZ10, "2026 年 10 月报考简章页面文本；HTML 去标签", sha("jz10.html"))
save_evidence("hunan", "hn_arr10.txt", (DL / "hn_arr10.txt").read_text(encoding="utf-8"), X_ARR10, "2026 年 10 月课程考试安排及教材目录；openpyxl 抽取", sha("arr10.xlsx"))
print("hunan ok", len(plans), "plans", len(offerings), "offerings")
