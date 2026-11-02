"""浙江：浙江省教育考试院《浙江省高等教育自学考试专业考试计划（2023 年）》（2025 年 5 月更新，浙教试院〔2023〕105 号附件）。
范围内只有 080901 计算机科学与技术（主考浙江工业大学、宁波工程学院）；专业对应表（官方，2025 年 5 月更新）全表未列其余范围内专业。
2026 年考期、政策原文本轮只取得通知正文与报考须知里的部分条款，其余待查。
用法：python -X utf8 build_zhejiang.py <目录>   目录里放 zj_3655.html、zj_3655.txt、zj_plan.docx、zj_plan.txt（docx 抽取）、zj_notice.pdf、zj_notice.pdf.txt
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
N = "https://www.zjzs.net/art/2024/1/4/art_41_3655.html"
PDF_NOTICE = "https://www.zjzs.net/attach/0/607f14be2251436f99700a14a41c39b9.pdf"
DOCX = "https://www.zjzs.net/module/download/downfile.jsp?classid=0&filename=2506191200127843.docx"
BASE = "浙江省教育考试院《关于公布〈浙江省高等教育自学考试专业考试计划（2023 年）〉的通知》（浙教试院〔2023〕105 号，2023-12-27，页面发布 2024-01-04）"

PUBLIC = [("15040", "习近平新时代中国特色社会主义思想概论", 3), ("15043", "中国近现代史纲要", 3), ("15044", "马克思主义基本原理", 3), ("13000", "英语（专升本）", 7)]
REQ = [("00023", "高等数学（工本）", 10, None), ("02324", "离散数学", 4, None), ("13013", "高级语言程序设计", 4, None), ("13014", "高级语言程序设计", 2, "13013"),
       ("13003", "数据结构与算法", 4, None), ("13004", "数据结构与算法", 2, "13003"), ("13015", "计算机系统原理", 4, None), ("13180", "操作系统", 4, None)]
ELE = [("13175", "线性代数（工）", 3, "elective", None), ("14263", "数字逻辑设计", 4, "elective", None), ("13009", "数据库原理与技术", 4, "elective", None),
       ("13017", "计算机网络与信息安全", 6, "elective", None), ("13011", "人工智能与大数据", 6, "elective", None),
       ("13215", "Java语言程序设计", 3, "elective", None), ("13216", "Java语言程序设计", 1, "practice", "13215"),
       ("14840", "网络操作系统（实践）", 3, "practice", None), ("14841", "网页设计技术（实践）", 4, "practice", None)]
GRAD = ("11689", "计算机科学与技术（本科）毕业论文")

courses = Shard("courses")
rows = [(c, n, cr, "public", None) for c, n, cr in PUBLIC] + [(c, n, cr, "practice" if p else "required", p) for c, n, cr, p in REQ] + ELE
req = sum(r[2] for r in rows if r[3] in ("public", "required") or (r[3] == "practice" and r[4] and r[4] in {x[0] for x in rows if x[3] in ("public", "required")}))
assert req == 50, req
EG = "推荐选考课（选考课程不少于 5 门，不低于 23 学分，其中实践不超过 8 学分）"
crow = []
for code, name, cr, cat, pair in rows:
    courses.add(code, {"name": name, "aliases": [], "kind": "practice" if cat == "practice" else "theory", "note": ""})
    crow.append(course_row(code, name, cr, cat, pair=pair, textbook=None, note="", elective_group=EG if cat in ("elective",) or (cat == "practice" and (pair is None or pair in {r[0] for r in ELE})) else None))
courses.add(GRAD[0], {"name": GRAD[1], "aliases": [], "kind": "graduation", "note": ""})
crow.append(course_row(GRAD[0], GRAD[1], 0, "graduation", note="", elective_group=None))
# 带「（实践）」后缀的独立实践课（无理论配对）按原名保留
plan = {
    "id": "zj-080901-2023", "major": "080901", "track": None,
    "version": "专业考试计划（2023 年，2025 年 5 月更新；浙教试院〔2023〕105 号）", "effective": "2024-10", "state": "current",
    "total_credits": 73, "required_credits": 73,
    "rules": "官方表总学分 73：必考课（公共基础课 4 门 16 学分 + 专业核心课 6 门 34 学分，共 10 门 50 学分）+ 选考课不少于 5 门、不低于 23 学分，其中实践不超过 8 学分；"
             "选考课可在本专业推荐选考课中选，也可在本省现行开考的其他专升本专业中选与本专业计划不同的课程；含理论和实践的课程，实践部分不计课程门数。"
             "毕业论文（11689）为必考环节、学分 0。2024-04 前注册的老考生可按原计划（专业代码末位为 Y）考试，原计划必考课 2027-10 最后一次考试，2027-12 底最后一次受理毕业申请。",
    "courses": crow,
    "graduation": {"thesis": True, "credits": 0, "note": "毕业论文原则上须参加毕业证书上副署的主考学校组织的考核答辩（原浙江大学主考的专业除外）。"},
    "source_files": ["zj_plan.txt"],
    "verify": V(N, f"{BASE}附件《专业考试计划（2023 年）（2025 年 5 月更新）》docx（{DOCX}）第 16 个专业；主考学校：浙江工业大学、宁波工程学院"),
}
p = CONTENT / "provinces" / "zhejiang.json"
d = provlib._load(p)
d["authority"] = {"name": "浙江省教育考试院", "url": "https://www.zjzs.net/", "verify": V(N, BASE)}
d["selfstudy_portal"] = {"name": "浙江省教育考试院自学考试信息网", "url": "https://zk.zjzs.net/", "verify": V(PDF_NOTICE, "报考须知称开考课程及时间安排在自学考试信息网 zk.zjzs.net「报名－报考简章」查询")}
d["policy"]["entry"] = {"text": "中华人民共和国公民不受性别、年龄、民族、种族和已受教育程度限制均可报考；报考专升本专业的考生申请本科毕业时必须具有国家承认学历的国民教育系列专科及以上学历证书；护理学（专升本）、护理（专科）限在浙江医疗机构从事护理工作并获得护士执业资格的在职人员，公安管理学（专升本）限公安干警、武警和保卫干部。",
                        "verify": V(PDF_NOTICE, "浙江省教育考试院自学考试报考须知 PDF「二、报考条件」（未标注年份，沿用 2024 年起的专业计划口径）")}
d["policy"]["degree"] = {"text": "学位授予仍按现行规定执行；除主考学校另有规定外，不考或免考英语（专升本）、第二外语者，不授学位。", "verify": V(N, "通知第七条")}
d["policy"]["exemption"] = {"text": "课程免考与顶替按浙教试院〔2023〕108 号《浙江省高等教育自学考试课程顶替规定》《课程免考规定》《省际转考管理规定》执行（通知页 https://www.zjzs.net/art/2024/1/4/art_41_3670.html）；规定全文本轮未取得。",
                            "verify": V(PDF_NOTICE, "报考须知「课程顶替」条款指向该通知")}
d["offerings"] = [{"major": "080901", "track": None, "local_code": "080901", "status": "open", "hosts": ["浙江工业大学", "宁波工程学院"], "plans": [plan["id"]],
                   "matched_by": "专业对应表：现专业 080901 计算机科学与技术，原专业 1082208 计算机信息管理、1080702 计算机及应用",
                   "complete": {"courses": True, "credits": True, "textbook": False},
                   "verify": V(N, f"{BASE}附件专业考试计划第 16 个专业；主考学校：浙江工业大学、宁波工程学院")}] + none_offerings(
    load_scope(), {"080901"}, V(N, f"{BASE}附件《专业对应表（2023 年）（2025 年 5 月更新）》专升本部分（序号 1~35）全表未列此专业；2025 年 5 月更新之后新增的专业未逐条核对"))
d["plans"] = [plan]
d["events"] = [e for e in d["events"] if e.get("date") != "2024-10"] + [
    {"date": "2024-10", "kind": "new-plan", "text": "自 2024 年 10 月考试（7 月报名）起，原计划停止接纳新考生；新考生全部执行《专业考试计划（2023 年）》。老考生（2024 年 4 月考试前已注册）在 2027 年底前可按原计划申请毕业，2028 年 1 月起均按新计划；原计划必考课 2027 年 10 月最后一次考试。",
     "verify": V(N, "通知第三条")},
]
provlib._save(p, d)
courses.save()

dst = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence" / "zhejiang"
dst.mkdir(parents=True, exist_ok=True)
shutil.copy2(DL / "zj_plan.docx", dst / "zj_plan_2023_updated_202505.docx")
shutil.copy2(DL / "zj_notice.pdf", dst / "zj_baokao_xuzhi.pdf")
for fname, txt, url, note, raw in (
    ("zj_3655.txt", "zj_3655.txt", N, "专业考试计划通知页面文本（含专业对应表）；HTML 去标签", "zj_3655.html"),
    ("zj_plan.txt", "zj_plan.txt", DOCX, "专业考试计划（2023 年）（2025 年 5 月更新）docx 全文抽取", "zj_plan.docx"),
    ("zj_notice.pdf.txt", "zj_notice.pdf.txt", PDF_NOTICE, "报考须知 PDF 抽取", "zj_notice.pdf"),
):
    save_evidence("zhejiang", fname, (DL / txt).read_text(encoding="utf-8"), url, note, hashlib.sha256((DL / raw).read_bytes()).hexdigest())
print("zhejiang ok")
