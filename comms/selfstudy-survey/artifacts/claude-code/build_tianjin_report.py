"""天津：官方招考资讯网（zhaokao.net）对程序请求不通，本轮只取得第三方转载的《2026年下半年天津自考开考专业及主考院校一览表》（华夏大地教育网，标注来源天津教育考试院，2026-05-19）。
按数据纪律，第三方只能作开设记录的线索（level: report）：不写课程、政策，不据此写「不开设」。官方一览表（报考须知附件 3）待使用者用浏览器取回。
用法：python -X utf8 build_tianjin_report.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-02"
from provlib import *  # noqa: E402,F403

URL = "https://www.edu-edu.com/zikao/tianjin/zkbm/66489.html"
NOTE = "华夏大地教育网转载《2026年下半年天津自考报名：开考专业及主考院校一览表》（页面注明来源天津教育考试院，2026-05-19）；第三方转载仅作线索，官方一览表（2026 年下半年报考须知附件 3）待核"


def o(major, hosts, status, extra=""):
    return {"major": major, "track": None, "status": status, "hosts": hosts, "plans": [],
            "complete": {"courses": False, "credits": False, "textbook": False},
            "verify": V(URL, NOTE + extra, level="report")}


p = CONTENT / "provinces" / "tianjin.json"
d = provlib._load(p)
d["offerings"] = [
    o("080901", ["天津工业大学", "天津师范大学"], "open"),
    o("080902", ["天津理工大学"], "open"),
    o("080701", ["中国民航大学"], "stopped", "；该页备注称 2025 年 4 月考试报名起不再接收新考生，2027 年起停止安排考试、停办毕业证"),
]
provlib._save(p, d)
print("tianjin ok")
