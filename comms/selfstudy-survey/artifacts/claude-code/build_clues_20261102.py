"""使用者 2026-11-02 下载/截图的零散资料入库：
  - 甘肃：甘肃省教育考试院报名平台「开考专业查询」截图（080901 主考院校兰州大学，课程表只截到前 17 行，网址未保存），官方，补 hosts。
  - 重庆：自考本科网（第三方）专业及院校一览表，只作开设线索（report）：080703/080901/080903 的主考院校与状态。
  - 山西：山西自考网（第三方）080901 专业页，只作线索（report）：主考院校太原理工大学。
  - 北京：华夏大地教育网转载北京教育考试院目录表（第三方）：080901 主考院校北京邮电大学，写进备注，不改来源级别。
第三方只能出现在开设记录的线索里，不写课程、政策，也不据此写「不开设」。
用法：python -X utf8 build_clues_20261102.py <Downloads 目录> <抽取目录>
"""
import hashlib
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-02"
from provlib import *  # noqa: E402,F403

DL, EX = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
EVI = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence"


def patch(pid, fn):
    p = CONTENT / "provinces" / f"{pid}.json"
    d = provlib._load(p)
    fn(d)
    provlib._save(p, d)


# ---- 甘肃 ----
def gansu(d):
    for o in d["offerings"]:
        if o["major"] == "080901":
            o["hosts"] = ["兰州大学"]
            o["mode"] = "面向社会"
            o["verify"]["note"] = (o["verify"].get("note") or "") + "；主考院校兰州大学取自使用者 2026-11-02 对甘肃省教育考试院报名平台「开考专业查询」页（080901 计算机科学与技术（专升本））的截图，页面网址未保存，截图只含课程表前 17 行，计划未能入库"
    return d


patch("gansu", gansu)
(EVI / "gansu").mkdir(parents=True, exist_ok=True)
shutil.copy2(DL / "Screenshot 2026-11-02 215741_edited.pdf", EVI / "gansu" / "gs_kaokao_zhuanye_080901_screenshot.pdf")

# ---- 重庆 ----
CQ = "https://www.zikaoben.cn/cate/tid-128"
cq_note = "自考本科网「重庆自学考试专业及院校一览表」（第三方，页面声明以重庆市教育考试院公示为准）；官方开考专业表待核"


def cq_off(major, hosts, status):
    return {"major": major, "track": None, "status": status, "hosts": hosts, "mode": "面向社会", "plans": [],
            "complete": {"courses": False, "credits": False, "textbook": False}, "verify": V(CQ, cq_note, level="report")}


def chongqing(d):
    d["offerings"] = [cq_off("080703", ["重庆邮电大学"], "open"), cq_off("080901", ["重庆科技大学", "重庆理工大学", "重庆三峡科技大学", "重庆交通大学"], "open"),
                      cq_off("080903", ["西南大学", "重庆邮电大学", "重庆文理学院"], "stopped")]


patch("chongqing", chongqing)

# ---- 山西 ----
SX = "http://www.zkw.sx.cn/bkzy/34442.html"


def shanxi(d):
    d["offerings"] = [{"major": "080901", "track": None, "status": "open", "hosts": ["太原理工大学"], "plans": [],
                       "complete": {"courses": False, "credits": False, "textbook": False},
                       "verify": V(SX, "山西自考网（第三方，页面声明官方信息以山西教育考试院为准）080901 计算机科学与技术（本科）专业页：主考院校太原理工大学；该页课程表仍是旧计划（含 03708/03709 等），不采；官方开考专业表待核", level="report")}]


patch("shanxi", shanxi)

# ---- 北京 ----
BJ3 = "https://www.edu-edu.com/zikao/beijing/zkzy/65318.html"


def beijing(d):
    for o in d["offerings"]:
        if o["major"] == "080901":
            o["verify"]["note"] += f"；第三方线索（华夏大地教育网转载北京教育考试院目录表，{BJ3}）：01B0015 主考院校北京邮电大学，官方来源待核"


patch("beijing", beijing)
for name, src in (("sx_080901_zkw.html.txt", EX / "计算机科学与技术080901(本科专业段)自考专业信息_自考专业院校_山西自考网.html.txt"),):
    save_evidence("shanxi", name, src.read_text(encoding="utf-8"), SX, "山西自考网 080901 专业页（第三方），浏览器另存 HTML 去标签", hashlib.sha256((DL / "计算机科学与技术080901(本科专业段)自考专业信息_自考专业院校_山西自考网.html").read_bytes()).hexdigest())
save_evidence("chongqing", "cq_zikaoben_yuanxiao.html.txt", (EX / "重庆自学考试专业及院校一览表 - 自考本科网.html.txt").read_text(encoding="utf-8"), CQ, "自考本科网重庆专业及院校一览表（第三方），浏览器另存 HTML 去标签", hashlib.sha256((DL / "重庆自学考试专业及院校一览表 - 自考本科网.html").read_bytes()).hexdigest())
save_evidence("beijing", "bj_edu_edu_080901_mulu.html.txt", (EX / "2025年下半年北京自考本科计算机科学与技术专业目录表.html.txt").read_text(encoding="utf-8"), BJ3, "华夏大地教育网转载 2025 年下半年北京自考计算机科学与技术（专升本）目录表（第三方）", hashlib.sha256((DL / "2025年下半年北京自考本科计算机科学与技术专业目录表.html").read_bytes()).hexdigest())
print("clues ok")
