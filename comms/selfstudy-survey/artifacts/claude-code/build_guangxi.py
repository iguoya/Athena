"""广西：由广西招生考试院官方公告与附件生成 provinces/guangxi.json。
来源：专业考试计划调整公告（2027 版计划、过渡期）、专业考试计划（2027 版）与课程设置 PDF、36 个专业停考方案、2026 年统考课程安排通知。
广西现行（至 2026-12-31）仍按原计划考试与毕业，原计划课程表本轮未取得，只入库 2027 版计划（state=upcoming）。
用法：python -X utf8 build_guangxi.py <下载目录>
"""
import hashlib
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
HOME = "https://www.gxeea.cn/"
N_ADJ = "https://www.gxeea.cn/view/content_1148_31019.htm"  # 调整专业考试计划的公告（2024-10-29）
N_STOP = "https://www.gxeea.cn/view/content_1013_30189.htm"  # 36 个专业停考方案（2024-05-20）
N_2026 = "https://www.gxeea.cn/view/content_1148_32355.htm"  # 2026 年统考课程安排事项通知（2025-12-15）
P_PLAN = "http://www.gxeea.cn/gallary/upload_images//1148_31209_1737514533899.pdf"
P_KCSZ = "http://www.gxeea.cn/gallary/upload_images//1148_31019_1730169712959.pdf"
# plan 的 verify.source 要求 https：广西站点 http/https 同域，取 https 形式
https = lambda u: u.replace("http://", "https://")  # noqa: E731


def fw(s):
    return re.sub(r"\s+", "", s.replace("(", "（").replace(")", "）"))


kcsz = (DL / "gx_kcsz2027.txt").read_text(encoding="utf-8")
i = kcsz.find("专业代码：080901")
seg = kcsz[i : kcsz.find("土木工程\n专业代码", i)]
ROW = re.compile(r"^(?:(\d{1,2})\s+)?(\d{5})\s+(.+?)\s+(\d+(?:\.\d+)?)\s+(公共课|专业课|实践课|毕业考核)$")
ATTR = {"公共课": "public", "专业课": "core", "实践课": "practice", "毕业考核": "graduation"}
courses = Shard("courses")
crow, last = [], {}
for line in seg.split("\n"):
    m = ROW.match(line.strip())
    if not m:
        continue
    code, name, cr, attr = m.group(2), fw(m.group(3)), float(m.group(4)), m.group(5)
    cr = int(cr) if cr == int(cr) else cr
    cat, pair = ATTR[attr], None
    if cat == "practice":
        base = name[: -len("（实践）")] if name.endswith("（实践）") else name
        pair = last.get(base)
        name = base if pair else name
    else:
        last[name] = code
    kind = {"practice": "practice", "graduation": "graduation"}.get(cat, "theory")
    courses.add(code, {"name": name, "aliases": [], "kind": kind, "note": ""})
    crow.append(course_row(code, name, cr, cat, pair=pair))
TOTAL = 75
assert sum(c["credits"] for c in crow) == TOTAL, sum(c["credits"] for c in crow)

plan = {
    "id": "gx-080901-2027", "major": "080901", "track": None,
    "version": "专业考试计划（2027 版，2024-10-29 公告）", "effective": "2027-01", "state": "upcoming",
    "total_credits": TOTAL, "required_credits": TOTAL,
    "rules": "全部必考；总学分 75（官方表直接给出，各行学分求和一致）；官方表「属性」列把 高等数学、离散数学 与思政课、英语同归「公共课」，其余为专业课、实践课、毕业考核。"
             "不参加 13000 英语（专升本）的考生，可在本专业课程考试计划外所有开考课程中选考不少于 2 门、合计学分不低于 7 学分的课程；不参加 00023 高等数学（工本）的，选考不少于 2 门、合计不低于 10 学分的课程；所选课程应是未曾用于办理其他专业毕业证书的课程。"
             "广西现行（至 2026-12-31 的过渡期内）仍按原计划考试与毕业，2027-01-01 起所有新老考生按本计划；原计划课程表本轮未取得。",
    "courses": crow,
    "graduation": {"thesis": True, "credits": 0, "note": "毕业论文 06999，不计学分；取得所有课程合格成绩后按主考学校要求撰写并答辩合格；社会考生参加毕业考核与申请毕业证的学校须是同一所主考学校。"},
    "source_files": ["gx_kcsz2027_080901.txt", "gx_plan2027_toc.txt"],
    "verify": V(https(P_KCSZ), "《广西高等教育自学考试专业考试计划课程设置（2027 版）》PDF 中 080901 计算机科学与技术页（公告附件 2，见 " + N_ADJ + "）"),
}

scope = load_scope()
V_STOP = lambda cn: V(N_STOP, f"36 个专业停考方案（桂考委 2024-05-20）{cn}：2024-07-01 起不再接纳新考生，2026 年 4 月最后一次组织课程考试，2026 年 12 月最后一次办理毕业资格审定")  # noqa: E731
offerings = [
    {"major": "080901", "track": None, "status": "open", "hosts": ["桂林电子科技大学"], "plans": ["gx-080901-2027"],
     "complete": {"courses": True, "credits": True, "textbook": False},
     "verify": V(https(P_PLAN), "专业考试计划（2027 版）080901 计算机科学与技术（专升本），主考学校桂林电子科技大学；每个专业只设 1 所主考学校、面向社会开考；现行仍按原计划，2027 年起按新计划")},
    {"major": "080701", "track": None, "status": "stopped", "hosts": ["桂林电子科技大学"], "verify": V_STOP("电子信息工程")},
    {"major": "080703", "track": None, "status": "stopped", "hosts": ["桂林电子科技大学"], "verify": V_STOP("通信工程")},
    {"major": "080903", "track": None, "status": "stopped", "hosts": ["广西大学"], "verify": V_STOP("网络工程")},
]
offerings += none_offerings(scope, {"080901", "080701", "080703", "080903"},
                            V(https(P_PLAN), "专业考试计划（2027 版）目录列出全部 31 个新计划专业（另有大数据与会计专科沿用原计划），共 32 个开考专业，其中无此专业；36 个停考专业清单亦未列"))

events = [
    {"date": "2024-05-20", "kind": "stop", "major": "080701", "text": "广西停考 36 个专业，含电子信息工程（桂林电子科技大学）：2024-07-01 起不再接纳新考生，2026 年 4 月最后一次课程考试，2026 年 12 月最后一次办理毕业审定。", "verify": V(N_STOP)},
    {"date": "2024-05-20", "kind": "stop", "major": "080703", "text": "广西停考 36 个专业，含通信工程（桂林电子科技大学）：2024-07-01 起不再接纳新考生，2026 年 4 月最后一次课程考试，2026 年 12 月最后一次办理毕业审定。", "verify": V(N_STOP)},
    {"date": "2024-05-20", "kind": "stop", "major": "080903", "text": "广西停考 36 个专业，含网络工程（广西大学）：2024-07-01 起不再接纳新考生，2026 年 4 月最后一次课程考试，2026 年 12 月最后一次办理毕业审定。", "verify": V(N_STOP)},
    {"date": "2024-10-29", "kind": "new-plan", "text": "广西公布《专业考试计划（2027 版）》：32 个开考专业中 31 个自 2027-01-01 起按新计划，过渡期 2024-12-31 至 2026-12-31 内仍按原计划考试与毕业；每个专业设 1 所主考学校；本科层次课程总数不少于 14 门、总学分不少于 73。", "verify": V(N_ADJ)},
]
write_province("guangxi", {
    "authority": {"name": "广西招生考试院", "url": HOME, "verify": V(N_2026)},
    "selfstudy_portal": None,  # 广西自学考试网上系统网址（zk1.gxeea.cn:8001）仅见于搜索摘要转述，未打开核实，不入库
    "calendar": [
        {"session": "2026-04", "exam": "2026-04-11~12", "verify": V(N_2026, "2026 年全年安排 2 次自学考试")},
        {"session": "2026-10", "exam": "2026-10-24~25", "verify": V(N_2026, "2026 年全年安排 2 次自学考试")},
    ],
    "policy": {
        "entry": {"text": "申请毕业时须持有国家承认学历的专科（或以上）学历证书（证书信息学信网可查）；国（境）外学历须提供教育部留学服务中心认证书。", "verify": V(https(P_KCSZ), "2027 版 080901 计划说明 2")},
        "graduate": {"text": "取得所有课程合格成绩，按主考学校要求撰写毕业论文并答辩合格方具备毕业条件；凡含理论考试与实践环节考核两部分的课程，须两部分都合格才算获得该课程学分；社会考生参加毕业考核与申请毕业证的学校须是同一所主考学校。", "verify": V(N_ADJ)},
        "degree": {"text": "本科层次专业考生申请学士学位，须关注主考学校关于申请自学考试学士学位的有关规定。", "verify": V(N_ADJ)},
        "exemption": {"text": "旧计划已合格课程按《新旧课程顶替对照表（2027 版）》顶替并换算学分；停考专业 2027-01-01 起未毕业的在籍考生，已合格课程继续有效，转入其他开考专业时代码与名称一致的课程无需再考，成绩不设有效期。", "verify": V(N_STOP, "与 " + N_ADJ + " 合并概括")},
    },
    "offerings": offerings, "plans": [plan], "events": events,
})
courses.save()


def sha(p):
    return hashlib.sha256((DL / p).read_bytes()).hexdigest()


toc = (DL / "gx_plan2027.txt").read_text(encoding="utf-8")
save_evidence("guangxi", "gx_plan2027_toc.txt", toc[: toc.find("=== p3 ===")], P_PLAN, "专业考试计划（2027 版）目录页（全部 31 个新计划专业）；全文 248 页未入库", sha("gx_plan2027.pdf"))
save_evidence("guangxi", "gx_kcsz2027_080901.txt", seg, P_KCSZ, "课程设置（2027 版）中 080901 计算机科学与技术页", sha("gx_kcsz2027.pdf"))
for fn, n, url, note in (("gx_stop36.txt", "n30189", N_STOP, "36 个专业停考方案公告页文本"), ("gx_adj2027.txt", "n31019", N_ADJ, "专业考试计划调整公告页文本"), ("gx_2026notice.txt", "n32355", N_2026, "2026 年统考课程安排事项通知页文本")):
    save_evidence("guangxi", fn, (DL / f"{n}.txt").read_text(encoding="utf-8"), url, note, sha(f"{n}.html"))
print("guangxi ok", len(crow), "rows")
