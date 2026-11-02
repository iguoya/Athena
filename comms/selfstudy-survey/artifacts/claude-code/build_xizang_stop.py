"""西藏：2026-03-13《关于自考停考专业的通知》——本科通信工程（080703）、网络工程（080903）自 2026 年 4 月起不再接收新生报考。
西藏各专业开考信息在「西藏自治区高等教育自学考试信息发布平台」（动态页，程序请求 404），其余专业是否开设本轮未取得，仍待查。
用法：python -X utf8 build_xizang_stop.py <目录>   目录里放 xz_138_7594.html、xz_138_7594.txt
"""
import hashlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-02"
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
URL = "http://zsks.edu.xizang.gov.cn/92/138/7594.html"
NOTE = ("西藏自治区教育考试院 2026-03-13《关于自考停考专业的通知》：停考报考人数连续五年少于 30 人的 9 个专业（本科 4 个：通信工程、网络工程、英语、金融学；专科 5 个）；"
        "2026 年 4 月起不再接收新生报考，在籍考生 3 年续考期，2028 年 10 月为最后一次考试，2029-12-31 后不再办理毕业证与转考")


def stopped(major, name):
    return {"major": major, "track": None, "status": "stopped", "hosts": [], "plans": [],
            "matched_by": f"通知停考专业名称「{name}（本科）」",
            "complete": {"courses": False, "credits": False, "textbook": False}, "verify": V(URL, NOTE)}


p = CONTENT / "provinces" / "xizang.json"
d = provlib._load(p)
ids = {"080703", "080903"}
d["offerings"] = [stopped("080703", "通信工程"), stopped("080903", "网络工程")] + [o for o in d["offerings"] if o["major"] not in ids]
d["events"] = [e for e in d["events"] if e.get("date") != "2026-03-13"] + [
    {"date": "2026-03-13", "kind": "stop", "text": "停考通信工程（080703）、网络工程（080903）等 9 个报考人数连续五年少于 30 人的专业：2026 年 4 月起不再接收新生，在籍考生 3 年续考期，2028 年 10 月为最后一次考试，2029-12-31 后不再办理毕业证与转考。",
     "verify": V(URL, "通知正文")},
]
provlib._save(p, d)
raw = DL / "xz_138_7594.html"
save_evidence("xizang", "xz_stop_notice_20260313.txt", (DL / "xz_138_7594.txt").read_text(encoding="utf-8"), URL, "西藏自治区教育考试院《关于自考停考专业的通知》页面文本", hashlib.sha256(raw.read_bytes()).hexdigest())
print("xizang ok")
