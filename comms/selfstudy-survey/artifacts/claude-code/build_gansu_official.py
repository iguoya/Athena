"""甘肃：甘肃省教育考试院报名平台 kw.ganseea.cn 的公开信息页（官方，单页应用，须用浏览器渲染后读取；程序直连只得空壳）。
  - /public-info/kkzy「开考专业查询」：2026 年面向社会开考专业目录（专科 8、专升本 15）与每个专业的课程设置与学分、主考院校
  - /public-info/yyxzykkkc：2026 年 10 月「应用型」开考专业及课程考试时间安排表（专科 6、专升本 28）
范围内：社会型 080901（兰州大学）、080202（兰州理工大学）；应用型 080901、080202、080207、080601、080208（该页只给课程安排，无主考院校与学分）。
页面没有总学分、没有区分必考选考：课程行学分逐行相加（080901 为 77，080202 为 77），为核算值。
用法：python -X utf8 build_gansu_official.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-03"
from provlib import *  # noqa: E402,F403
from planlib import build_plan  # noqa: E402

KK = "https://kw.ganseea.cn/public-info/kkzy"
YY = "https://kw.ganseea.cn/public-info/yyxzykkkc"


def R(code, name, cr, pair=None, cat="required"):
    return (code, name, cr, "practice" if pair else cat, pair, "", None)


PUB = [("15043", "中国近现代史纲要", 3, "public", None, "", None), ("15044", "马克思主义基本原理", 3, "public", None, "", None),
       ("15040", "习近平新时代中国特色社会主义思想概论", 3, "public", None, "", None), ("13000", "英语（专升本）", 7, "public", None, "", None)]
ME = PUB + [R("13174", "概率论与数理统计（工）", 3), R("02202", "传感器与检测技术", 4), R("02203", "传感器与检测技术（实践）", 1, "02202"),
            R("02205", "微型计算机原理与接口技术", 4), R("02206", "微型计算机原理与接口技术（实践）", 2, "02205"), R("02204", "经济管理", 5),
            R("02209", "机械制造装备设计", 5), R("02210", "机械制造装备设计（实践）", 2, "02209"), R("01928", "液压与气动技术", 4), R("01929", "液压与气动技术（实践）", 3, "01928"),
            R("05785", "数控原理与数控技术运用", 5), R("05786", "数控原理与数控技术运用（实践）", 2, "05785"), R("02213", "精密加工与特种加工", 6),
            R("11184", "先进制造技术", 4), R("11185", "先进制造技术（实践）", 1, "11184"), R("02643", "质量管理（二）", 6),
            R("02207", "电气传动与可编程控制器（PLC）", 3), R("02208", "电气传动与可编程控制器（PLC）（实践）", 1, "02207")]
CS = [("15043", "中国近现代史纲要", 3, "public", None, "", None), ("15044", "马克思主义基本原理", 3, "public", None, "", None), ("13000", "英语（专升本）", 7, "public", None, "", None),
      R("00023", "高等数学（工本）", 10), R("02324", "离散数学", 4), R("13015", "计算机系统原理", 4), R("13180", "操作系统", 4), R("13003", "数据结构与算法", 4),
      R("13004", "数据结构与算法（实践）", 2, "13003"), R("13013", "高级语言程序设计", 4), R("13014", "高级语言程序设计（实践）", 2, "13013"), R("02325", "计算机系统结构", 4),
      R("13005", "软件工程", 3), R("13006", "软件工程（实践）", 2, "13005"), R("13011", "人工智能与大数据", 6), R("13017", "计算机网络与信息安全", 6),
      R("14349", "网络应用开发与系统集成", 6), ("15040", "习近平新时代中国特色社会主义思想概论", 3, "public", None, "", None)]
assert sum(r[2] for r in ME) == 77 and sum(r[2] for r in CS) == 77

RULES = "页面没有总学分，也没有区分必考与选考；课程行（含配套实践课）学分逐行相加 {t}，为核算值，官方页未直接给出，全部先按必考录。"
p = CONTENT / "provinces" / "gansu.json"
d = provlib._load(p)
plans = []
for pid, major, host, rows, grad in (("gs-080901-2026", "080901", "兰州大学", CS, ("11689", "计算机科学与技术（本科）毕业论文")),
                                    ("gs-080202-2026", "080202", "兰州理工大学", ME, ("14875", "机械设计制造及其自动化（本科）毕业论文"))):
    plan, courses = build_plan(pid, major, "专业课程设置与学分（报名平台「开考专业查询」，页面未标版本）", "未标注", 77, 77, RULES.format(t=77), rows, (grad[0], grad[1], "页面学分 0"),
                               V(KK, f"甘肃省教育考试院报名平台「开考专业查询」：{ '080901GS 计算机科学与技术（专升本）' if major == '080901' else '080202GS 机械设计制造及其自动化（专升本）'}，主考院校{host}"),
                               "毕业论文学分 0，由主考学校组织。", [])
    courses.save()
    plans.append(plan)
d["plans"] = plans
d["offerings"] = [o for o in d["offerings"] if o["major"] not in ("080901", "080202", "080207", "080601", "080208")] + [
    {"major": "080901", "track": "社会型", "local_code": "080901GS", "status": "open", "hosts": ["兰州大学"], "mode": "社会型", "plans": ["gs-080901-2026"],
     "matched_by": None, "complete": {"courses": True, "credits": True, "textbook": False},
     "verify": V(KK, "2026 年面向社会开考专业目录：080901GS 计算机科学与技术（专升本），主考院校兰州大学")},
    {"major": "080901", "track": "应用型", "local_code": "080901GS", "status": "open", "hosts": [], "mode": "应用型", "plans": [],
     "matched_by": None, "complete": {"courses": False, "credits": False, "textbook": False},
     "verify": V(YY, "2026 年 10 月「应用型」开考专业及课程考试时间安排表列有 080901GS；该页只给课程时间安排（14349、15044、13017、13180），无主考院校，主考院校待查")},
    {"major": "080202", "track": "社会型", "local_code": "080202GS", "status": "open", "hosts": ["兰州理工大学"], "mode": "社会型", "plans": ["gs-080202-2026"],
     "matched_by": None, "complete": {"courses": True, "credits": True, "textbook": False},
     "verify": V(KK, "2026 年面向社会开考专业目录：080202GS 机械设计制造及其自动化（专升本），主考院校兰州理工大学")},
    {"major": "080202", "track": "应用型", "local_code": "080202GS", "status": "open", "hosts": [], "mode": "应用型", "plans": [],
     "matched_by": None, "complete": {"courses": False, "credits": False, "textbook": False},
     "verify": V(YY, "2026 年 10 月「应用型」安排表列有 080202GS；无主考院校，主考院校待查")},
    {"major": "080207", "track": "应用型", "local_code": "080207GS", "status": "open", "hosts": [], "mode": "应用型", "plans": [],
     "matched_by": None, "complete": {"courses": False, "credits": False, "textbook": False},
     "verify": V(YY, "2026 年 10 月「应用型」安排表列有 080207GS 车辆工程（课程 15044、06357、06361、02204）；无主考院校，主考院校待查")},
    {"major": "080601", "track": "应用型", "local_code": "080601GS", "status": "open", "hosts": [], "mode": "应用型", "plans": [],
     "matched_by": None, "complete": {"courses": False, "credits": False, "textbook": False},
     "verify": V(YY, "2026 年 10 月「应用型」安排表列有 080601GS 电气工程及其自动化（课程 15044、04108、02268、08175）；无主考院校，主考院校待查")},
    {"major": "080208", "track": "应用型", "local_code": "C080208GS", "status": "open", "hosts": [], "mode": "应用型", "plans": [],
     "matched_by": None, "complete": {"courses": False, "credits": False, "textbook": False},
     "verify": V(YY, "2026 年 10 月「应用型」安排表列有 C080208GS 汽车服务工程（课程 04912、15044、08570、15040、05871、05870）；无主考院校，主考院校待查")},
]
provlib._save(p, d)
print("gansu official ok")
