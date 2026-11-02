"""北京：北京教育考试院《关于公布北京市高等教育自学考试 2026 年考试安排及有关事项的通知》（2025-11-25）。
通知列出 44 个安排考试的专业（正常开设 39、停考过渡 5），是官方全表；北京专业代码是自有体系（01B0015 = 计算机科学与技术专升本），按专业名称对应国标码。
范围内：计算机科学与技术（专升本）正常开设；网络工程（专升本）停考过渡（考生参加计算机科学与技术课程考试，北京码 01B0017）。
主考院校与专业考试计划不在通知内（计划在 zkxcx.bjeea.cn 的 FineReport 报表里，本轮未取得）。
用法：python -X utf8 build_beijing.py <目录>   目录里放 notice.html、notice.txt、sched_apr.pdf(.txt)、sched_oct.pdf(.txt)
"""
import hashlib
import pathlib
import shutil
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-02"
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
N = "https://www.bjeea.cn/html/selfstudy/xxfbt/2025/1125/87664.html"
U = "https://www.bjeea.cn/uploads/soft/251125/"
APR = U + urllib.parse.quote("北京市高等教育自学考试2026年4月笔试课程考试时间表.pdf")
OCT = U + urllib.parse.quote("北京市高等教育自学考试2026年10月笔试课程考试时间表.pdf")
BASE = "北京教育考试院《关于公布北京市高等教育自学考试2026年考试安排及有关事项的通知》（2025-11-25）"

p = CONTENT / "provinces" / "beijing.json"
d = provlib._load(p)
d["authority"] = {"name": "北京教育考试院", "url": "https://www.bjeea.cn/", "verify": V(N, BASE)}
d["calendar"] = [
    {"session": "2026-04", "exam": "2026-04-11~12", "note": "笔试课程报考时间由北京教育考试院网站和「北京自考」公众号另行公布（本轮未取得）", "verify": V(APR, "附件 1《2026年4月笔试课程考试时间表》（04 月 11 日星期六、12 日星期日）")},
    {"session": "2026-10", "exam": "2026-10-24~25", "note": "笔试课程报考时间另行公布（本轮未取得）", "verify": V(OCT, "附件 2《2026年10月笔试课程考试时间表》（10 月 24 日星期六、25 日星期日）")},
]
d["offerings"] = [
    {"major": "080901", "track": None, "local_code": "01B0015", "status": "open", "hosts": [], "plans": [],
     "matched_by": "北京专业代码 01B0015「计算机科学与技术（专升本）」，按专业名称对应国标 080901（北京码自成体系）",
     "complete": {"courses": False, "credits": False, "textbook": False},
     "verify": V(N, f"{BASE}：2026 年「正常开设」；2026 年 4 月考试课程（附件 1）：02324 离散数学、00023 高等数学（工本）、13007 编译原理、13003 数据结构与算法、13180 操作系统、13005 软件工程、13013 高级语言程序设计、13015 计算机系统原理、13017 计算机网络与信息安全、15040/15043/15044 思政课、13000 英语（专升本）；"
                  f"10 月（附件 2）：同上，13007 换为 14349 网络应用开发与系统集成。主考院校待查（通知不含主考院校与学分）")},
    {"major": "080903", "track": None, "local_code": "01B0017", "status": "stopped", "hosts": [], "plans": [],
     "matched_by": "通知「停考过渡期专业」第 1 条：网络工程专业（专升本）；时间表中与计算机科学与技术同行，北京码 01B0017",
     "complete": {"courses": False, "credits": False, "textbook": False},
     "verify": V(N, f"{BASE}：网络工程专业（专升本）为停考过渡期专业，考生参加计算机科学与技术专业（专升本）课程考试，合格课程可用于办理网络工程专业毕业；停考时间与详情见该通知引用的《关于调整汉语言文学专业（专科）等停考专业考试课程安排的通知》（本轮未取得）")},
] + none_offerings(load_scope(), {"080901", "080903"}, V(N, f"{BASE}：44 个安排考试的专业（正常开设 39、停考过渡 5）全表未列此专业；通知发布后新开考的专业另行通知，未核对"))
d["events"] = [e for e in d["events"] if e.get("date") != "2025-11-25"] + [
    {"date": "2025-11-25", "kind": "other", "text": "北京 2026 年共 44 个专业安排考试：正常开设 39 个（本科 24、专科 15 含大数据与会计等 3 个继续使用现行计划的专科专业），停考过渡 5 个（网络工程专升本，另有广播电视编导、动画、教育技术学、汽车服务工程 2026 年上半年最后一次考试）。",
     "verify": V(N)},
]
provlib._save(p, d)

dst = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence" / "beijing"
dst.mkdir(parents=True, exist_ok=True)
shutil.copy2(DL / "sched_apr.pdf", dst / "bj_sched_2026-04.pdf")
shutil.copy2(DL / "sched_oct.pdf", dst / "bj_sched_2026-10.pdf")
for name, txt, url, note, raw in (
    ("bj_notice_20251125.txt", "notice.txt", N, "2026 年考试安排及有关事项通知页面文本；HTML 去标签", "notice.html"),
    ("bj_sched_2026-04.pdf.txt", "sched_apr.pdf.txt", APR, "2026 年 4 月笔试课程考试时间表，pymupdf 抽取", "sched_apr.pdf"),
    ("bj_sched_2026-10.pdf.txt", "sched_oct.pdf.txt", OCT, "2026 年 10 月笔试课程考试时间表，pymupdf 抽取", "sched_oct.pdf"),
):
    save_evidence("beijing", name, (DL / txt).read_text(encoding="utf-8"), url, note, hashlib.sha256((DL / raw).read_bytes()).hexdigest())
print("beijing ok")
