"""甘肃：080901 计算机科学与技术（专升本）课程设置（兰州大学主考）。
来源：使用者 2026-11-03 对自考本科网「甘肃自考计算机科学与技术专业（本科）」页的截图（19 行，第三方级，页面网址未保存）；
序号 1~17 与使用者 2026-11-02 对甘肃省教育考试院报名平台「开考专业查询」页的截图（官方，兰州大学）逐行一致，交叉核对通过。
页面没有总学分、没有区分必考选考：逐行相加 77 学分（核算值），全部先按必考录并在 rules 说明。
用法：python -X utf8 build_gansu_plan.py <Downloads 目录>
"""
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-03"
from provlib import *  # noqa: E402,F403
from planlib import attach, build_plan  # noqa: E402

DL = pathlib.Path(sys.argv[1])
SRC = "https://www.zikaoben.cn/"


def R(code, name, cr, pair=None, cat="required"):
    return (code, name, cr, "practice" if pair else cat, pair, "", None)


rows = [("15043", "中国近现代史纲要", 3, "public", None, "", None), ("15044", "马克思主义基本原理", 3, "public", None, "", None), ("13000", "英语（专升本）", 7, "public", None, "", None),
        R("00023", "高等数学（工本）", 10), R("02324", "离散数学", 4), R("13015", "计算机系统原理", 4), R("13180", "操作系统", 4), R("13003", "数据结构与算法", 4),
        R("13004", "数据结构与算法（实践）", 2, "13003"), R("13013", "高级语言程序设计", 4), R("13014", "高级语言程序设计（实践）", 2, "13013"), R("02325", "计算机系统结构", 4),
        R("13005", "软件工程", 3), R("13006", "软件工程（实践）", 2, "13005"), R("13011", "人工智能与大数据", 6), R("13017", "计算机网络与信息安全", 6), R("14349", "网络应用开发与系统集成", 6),
        ("15040", "习近平新时代中国特色社会主义思想概论", 3, "public", None, "", None)]
assert sum(r[2] for r in rows) == 77
plan, courses = build_plan("gs-080901-2026", "080901", "专业课程设置与学分（页面未标版本；思政课为 15040/15043/15044 新口径）", "2025-01", 77, 77,
                           "页面没有总学分，也没有区分必考与选考；18 行课程（含配套实践课）学分逐行相加 77，为核算值，官方原表未直接给出，全部先按必考录——其中 13011/13017/14349 等是否选考以甘肃省教育考试院完整计划为准。"
                           "序号 1~17 与甘肃省教育考试院报名平台「开考专业查询」页（兰州大学主考）逐行一致；毕业论文 11689 学分 0。",
                           rows, ("11689", "计算机科学与技术（本科）毕业论文", "页面标「毕业论文」，学分 0"),
                           V(SRC, "自考本科网「甘肃自考计算机科学与技术专业（本科）」页，使用者 2026-11-03 截图（第三方，使用者裁决可信；页面网址未保存）；序号 1~17 与甘肃省教育考试院报名平台截图（官方）逐行一致", level="report"),
                           "毕业论文学分 0，实践与论文由主考学校（兰州大学）组织。", [])
courses.save()
attach("gansu", plan, lambda o: o["major"] == "080901", {"complete": {"courses": True, "credits": True, "textbook": False}})
shutil.copy2(DL / "Screenshot 2026-11-03 100715_edited.pdf", provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence" / "gansu" / "gs_plan_080901_zikaoben_screenshot.pdf")
print("gansu plan ok")
