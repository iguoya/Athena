"""河北：2026 年上半年河北省高等教育自学考试报考简章（含附件 1 开考专业理论课程考试安排、附件 2 停考过渡专业安排；保定市教育考试院网站转载 PDF）。
附件 1、2 合计列出本省全部开考与停考过渡专业（带主考学校、开考方式、新旧专业代码）；范围内有 080901 计算机科学与技术（河北大学）、080701 电子信息工程（河北科技大学）。
河北 2026 年起执行新专业考试计划，计划文本与教材本轮未取得。
用法：python -X utf8 build_hebei.py <目录>   目录里放 hb04.pdf、hb04.pdf.txt
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
URL = "http://www.bdksy.cn/bdattachedksy/file/20251124/20251124102600011.pdf"
BASE = "2026 年上半年河北省高等教育自学考试报考简章 PDF（保定市教育考试院网站 2025-11-24 转载河北省教育考试院简章，含附件 1~4）"
V1 = V(URL, BASE, level="notice")


def off(major, local, name, host, courses):
    return {"major": major, "track": None, "local_code": major, "status": "open", "hosts": [host], "mode": "面向社会", "plans": [],
            "matched_by": f"附件 1 专业「{name}（本科）」，原专业代码 {local}",
            "complete": {"courses": False, "credits": False, "textbook": False},
            "verify": V(URL, f"{BASE}附件 1：{host}，面向社会；2026 年 4 月开考课程：{courses}。简章不含学分与教材，现行计划待查", level="notice")}


p = CONTENT / "provinces" / "hebei.json"
d = provlib._load(p)
d["authority"] = {"name": "河北省教育考试院", "url": "https://www.hebeea.edu.cn/", "verify": V(URL, BASE, level="notice")}
d["selfstudy_portal"] = {"name": "河北省教育考试院高等教育自学考试网上信息系统", "url": "https://zk.hebeea.edu.cn", "verify": V(URL, "简章「报考专业和课程」：考生登录该系统查阅信息、注册报考", level="notice")}
d["calendar"] = [{"session": "2026-04", "exam": "2026-04-11~12", "register": "理论课程网上报考、支付 2026-02-26~03-07（每天 8:00-22:00）；实践性环节网上报考 2025-11-25~30", "note": "成绩发布 2026-05-10 17:00 后", "verify": V1}]
d["policy"]["entry"] = {"text": "中华人民共和国公民不受性别、年龄、民族、种族和已受教育程度限制均可报名；已公布停考的专业仅限在籍考生报考；报考有特殊要求的专业须符合相关条件；报考本科专业的考生须在毕业前取得具备学历教育资格的高等学校或自考机构颁发的专科（或以上）学历证书，且学历信息在学信网可查；每次仅限选一个考区，最多报考两个专业，每半天限报一门课程。",
                        "verify": V1}
d["offerings"] = [
    off("080901", "082208 计算机信息管理", "计算机科学与技术", "河北大学", "02324 离散数学、00023 高等数学（工本）、13180 操作系统、13009 数据库原理与技术、13003 数据结构与算法、14349 网络应用开发与系统集成、13005 软件工程、13013 高级语言程序设计、13015 计算机系统原理、13017 计算机网络与信息安全，加思政课 15040/15043/15044 与 13000 英语（专升本）"),
    off("080701", "080753 电子信息工程", "电子信息工程", "河北科技大学", "02363 通信原理、00023 高等数学（工本）、02354 信号与系统、02356 数字信号处理、08947 电路分析、13013 高级语言程序设计、14026 模拟电子技术、14260 数字电路与逻辑设计、14745 自动控制原理（本），加思政课 15040/15043/15044 与 13000 英语（专升本）"),
] + none_offerings(load_scope(), {"080901", "080701"}, V(URL, f"{BASE}附件 1（开考专业）与附件 2（停考过渡专业）列出本省全部专业，范围内只有 080901、080701；2026 年下半年起新增的专业未逐条核对", level="notice"))
provlib._save(p, d)

dst = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence" / "hebei"
dst.mkdir(parents=True, exist_ok=True)
shutil.copy2(DL / "hb04.pdf", dst / "hb_jianzhang_2026-04.pdf")
save_evidence("hebei", "hb_jianzhang_2026-04.pdf.txt", (DL / "hb04.pdf.txt").read_text(encoding="utf-8"), URL, "2026 年上半年报考简章含附件 1~4，pymupdf 抽取，24 页", hashlib.sha256((DL / "hb04.pdf").read_bytes()).hexdigest())
print("hebei ok")
