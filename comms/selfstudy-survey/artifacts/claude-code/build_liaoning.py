"""辽宁：辽宁招生考试之窗（lnzsks.com，辽宁省招生考试办公室，官方，程序可直接抓取）。
  - 2026 年下半年报考简章（2026-07-08）：开考专业全表（专科 7、专升本 38）、停考专业、报名条件；附表一（10 月理论课程安排，含辽宁专业序号/国标码）、
    附表三（实践环节考核课程安排，列每个专业的主考学校）、附表五（主考学校联系方式）
  - 2026 年上半年、下半年报名通知（报名与支付时间）
  - 2026 年上半年毕业申请须知、学历审查和课程免考实施细则（2026 年修订）
范围内专业：080901（辽宁大学、渤海大学）、080902（东北大学、大连东软信息学院、大连交通大学）、080905（沈阳大学）、080906（辽宁传媒学院）、080801（辽宁石油化工大学）；
简章的开考与停考专业全表没有范围内其他专业，写「不开设」。辽宁专业考试计划（学分、必考选考）本轮未取得，只录 2026 年 10 月开考课程。
用法：python -X utf8 build_liaoning.py <目录>   目录里放 IMS_*.html/.txt、fj01~fj05.pdf(.txt)
"""
import hashlib
import pathlib
import re
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-03"
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
BASE = "https://www.lnzsks.com/newsinfo/"
P = {
    "jz": BASE + "IMS_20260708_46185_mqz2C6QR9o.htm",   # 2026 下半年报考简章
    "tb": BASE + "IMS_20260708_46184_hLr8GEQn3s.htm",   # 2026 年 10 月理论课教材信息表
    "mk": BASE + "IMS_20260707_46182_lTsFw50J4P.htm",   # 免考实施细则（2026 修订）
    "bq": BASE + "IMS_20260601_45984_yufz1iwgE4.htm",   # 2026 上半年毕业申请须知
    "r10": BASE + "IMS_20260825_46365_gu6slJC1Q4.htm",  # 2026 下半年报名通知
    "r04": BASE + "IMS_20260224_45643_F5NsbzWoLh.htm",  # 2026 上半年报名通知
}
FJ = "https://www.lnzsks.com/lnzkbfiles/2026/2026zkjz0708fj0{}.pdf"

# 逐专业核对：附表一/三里取出的专业行（辽宁专业序号/国标码）、主考学校、10 月课程
txt1 = re.sub(r"\s+", " ", (DL / "fj01.pdf.txt").read_text(encoding="utf-8"))
txt3 = re.sub(r"\s+", " ", (DL / "fj03.pdf.txt").read_text(encoding="utf-8"))
txt5 = (DL / "fj05.pdf.txt").read_text(encoding="utf-8")
JOBS = [
    ("080901", "516", "计算机科学与技术", ["辽宁大学", "渤海大学"], "02324、15044、00023、13003、13013、13017、15040、13180、14349、15043、13000、13005、13009、13015"),
    ("080902", "522", "软件工程", ["东北大学", "大连东软信息学院", "大连交通大学"], "02324、15044、00023、13003、13013、13017、15040、13180、14126、15043、13000、13005、13009"),
    ("080905", "991", "物联网工程", ["沈阳大学"], "07454、12573、15044、00023、12585、15040、13958、15043、13000、14255"),
    ("080906", "922", "数字媒体技术", ["辽宁传媒学院"], "13181、13215、15044、00023、15040、13810、15043、13000"),
    ("080801", "792", "自动化", ["辽宁石油化工大学"], "07454、07844、15044、00023、08244、15040、04737、13175、15043、13000、14745"),
]
for code, no, name, hosts, courses in JOBS:
    assert f"{no}/{code} {name}（专升本）" in txt1, code
    seg = txt3[txt3.index(f"{no}/{code} {name}（专升本）"):][:700]
    # 主考学校列：专业行之后课程名后连续重复出现的学校名
    assert all(h in seg for h in hosts), (code, hosts, seg[:300])
for h in sorted({h for *_, hs, __ in JOBS for h in hs}):
    assert h in txt5, h

V_JZ = lambda note="": V(P["jz"], "辽宁省招生考试办公室《辽宁省2026年下半年高等教育自学考试报考简章》（2026-07-08）" + note)
offs = []
for code, no, name, hosts, courses in JOBS:
    offs.append({"major": code, "track": None, "local_code": f"{no}/{code}", "status": "open", "hosts": hosts, "plans": [],
                 "matched_by": f"附表一专业「{no}/{code} {name}（专升本）」（辽宁专业序号/国标专业代码）",
                 "complete": {"courses": False, "credits": False, "textbook": False},
                 "verify": V_JZ(f"附表一（2026 年 10 月理论课程，{FJ.format(1)}）：{courses}；主考学校取自附表三（实践环节考核课程安排，{FJ.format(3)}）：{'、'.join(hosts)}；"
                                "简章不含学分与必考选考，现行专业考试计划待查")})
none_v = V_JZ(f"二、开考专业（专科 7 个、专升本 38 个）与三、停考专业（附表一、二，{FJ.format(1)}、{FJ.format(2)}）全表未列此专业；范围内只有 080901、080902、080905、080906、080801")

p = CONTENT / "provinces" / "liaoning.json"
d = provlib._load(p)
d["authority"] = {"name": "辽宁省招生考试办公室（辽宁招生考试之窗）", "url": "https://www.lnzsks.com/", "verify": V_JZ("；网站主管单位辽宁省高中等教育招生考试委员会办公室")}
d["selfstudy_portal"] = {"name": "辽宁省高等教育自学考试网上服务平台", "url": "https://zk.lnzsks.com/lnzk.wb/", "verify": V_JZ("「五、报名」：理论课、实践环节、转考、免考、毕业申请均通过该平台办理")}
d["calendar"] = [
    {"session": "2026-04", "exam": "2026-04-11~12", "register": "理论课、实践课报名 2026-03-02~09，网上支付截止 03-10", "verify": V(P["r04"], "辽宁省2026年上半年高等教育自学考试报名工作即将开始（2026-02-24）")},
    {"session": "2026-10", "exam": "2026-10-24~25", "register": "理论课、实践课报名 2026-09-01 9:00~09-07 22:00，网上支付截止 09-08 22:00", "verify": V(P["r10"], "辽宁省2026年下半年高等教育自学考试报名工作即将开始（2026-08-25）")},
]
d["policy"] = {
    "entry": {"text": "中华人民共和国公民不受性别、年龄、民族、种族和已受教育程度限制，有特殊要求的专业除外；被暂停参加自学考试且在停考期内者不得报名；申请专升本专业毕业的考生须持具有学历教育资格的高校或自考机构颁发的专科（或以上）学历证书，审核依据为《教育部学历证书电子注册备案表》或《中国高等教育学历认证报告》。护理学、药学、中药学、公安管理学（专升本）有限制报考条件。",
              "verify": V_JZ("「一、报名条件」")},
    "graduate": {"text": "毕业申请实行网上申请和审定：登录辽宁省高等教育自学考试网上服务平台选择“毕业申请”，系统按所选专业的毕业条件与新旧计划顶替方案筛选合格课程，申请本科毕业须通过学信网查验专科（或以上）学历，网上确认头像照片后网上缴纳毕业审定费 50 元；2026 年上半年申请时间为 6 月 10~17 日；考生因个人原因错过不补办。毕业证书上只加盖辽宁省高等教育自学考试委员会和主考学校印章。",
                 "verify": V(P["bq"], "辽宁省2026年上半年高等教育自学考试毕业申请须知（2026-06-01）")},
    "degree": None,
    "exemption": {"text": "按《辽宁省高等教育自学考试学历审查和课程免考实施细则（2026年修订）》：国家承认学历的专科及以上毕业生和自学考试毕业生可免考已学过且成绩合格、课程名称和要求相同的课程（专升本：本科以上毕业生可免已学课程，专科以上毕业生可免思政课；自学考试专科以上毕业生可免已学课程）；"
                            "电子信息类和计算机类专业毕业生可免考计算机应用基础（含实践）和管理系统中计算机应用（含实践）；全国计算机等级考试一级以上免计算机应用基础，二级 C 语言免高级语言程序设计（含实践）；PETS 三级以上免英语（专升本）等；通过网上服务平台申请、到市区招考办现场确认后网上缴费。",
                  "verify": V(P["mk"], "辽宁省高等教育自学考试学历审查和课程免考实施细则（2026年修订，2026-07-07）")},
}
d["offerings"] = offs + none_offerings(load_scope(), {j[0] for j in JOBS}, none_v)
d["events"] = [e for e in d["events"] if e.get("date") != "2026-07-08"] + [
    {"date": "2026-07-08", "kind": "other", "text": "辽宁 2026 年下半年开考专科 7 个、专升本 38 个专业；停考专业：船舶与海洋工程（2026 年上半年起不再安排课程考试）、汽车服务工程（2025 年上半年起停止接纳新考生）、工程管理（A 计划，2026 年上半年起停止接纳新考生）等，均不在调查范围内。", "verify": V_JZ("「二、开考专业」「三、停考专业和遗留问题处理」")},
]
provlib._save(p, d)

dst = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence" / "liaoning"
dst.mkdir(parents=True, exist_ok=True)
for key, fn in (("jz", "IMS_20260708_46185_mqz2C6QR9o"), ("tb", "IMS_20260708_46184_hLr8GEQn3s"), ("mk", "IMS_20260707_46182_lTsFw50J4P"), ("bq", "IMS_20260601_45984_yufz1iwgE4"), ("r10", "IMS_20260825_46365_gu6slJC1Q4"), ("r04", "IMS_20260224_45643_F5NsbzWoLh")):
    save_evidence("liaoning", f"ln_{key}.txt", (DL / f"{fn}.txt").read_text(encoding="utf-8"), P[key], "辽宁招生考试之窗页面文本（HTML 去标签）", hashlib.sha256((DL / f"{fn}.html").read_bytes()).hexdigest())
for i in (1, 2, 3, 5):
    shutil.copy2(DL / f"fj0{i}.pdf", dst / f"ln_jz_fj0{i}.pdf")
    save_evidence("liaoning", f"ln_jz_fj0{i}.pdf.txt", (DL / f"fj0{i}.pdf.txt").read_text(encoding="utf-8"), FJ.format(i), f"2026 年下半年报考简章附表 {'一二三四五'[i-1]}，pymupdf 抽取", hashlib.sha256((DL / f"fj0{i}.pdf").read_bytes()).hexdigest())
print("liaoning ok")
