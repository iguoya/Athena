"""湖南：补 2026 年 4 月报考简章附表（hneeb.cn/hnxxg/761/762/20260114.xls，使用者 2026-11-02 下载）。
核对结果：4 月附表 1（专升本 74 个）+ 附表 2（专科 22 个）去重 96 个专业，范围内专业与 10 月一致（080801、080802T、080901、080902、080905）；
10 月附表 1+2 去重 95 个，差异只有 080204 机械电子工程（不在范围内）。据此更新「不开设」记录的依据说明。
用法：python -X utf8 build_hunan_april.py <Downloads 目录>
"""
import hashlib
import pathlib
import re
import sys

import openpyxl
import xlrd

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-02"
from provlib import *  # noqa: E402,F403

DL = pathlib.Path(sys.argv[1])
X04 = "https://www.hneeb.cn/hnxxg/761/762/20260114.xls"
N04 = "https://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/web/ksyzkzx/202601/t20260114_33892864.html"
X10 = "https://www.hneeb.cn/hnxxg/761/762/2026072901.xlsx"
SCOPE = {"080801", "080802T", "080901", "080902", "080905"}

b = xlrd.open_workbook(str(DL / "20260114.xls"))
a = []
lines = []
for i in (0, 1):
    s = b.sheet_by_index(i)
    c = set()
    for r in range(s.nrows):
        v = s.row_values(r)
        lines.append(" | ".join(str(x) for x in v))
        if len(v) > 1 and re.fullmatch(r"\d{6}[A-Z]*", str(v[1]).strip()):
            c.add(str(v[1]).strip())
    a.append(c)
u04 = a[0] | a[1]
assert (len(a[0]), len(a[1]), len(u04)) == (74, 22, 96), (len(a[0]), len(a[1]), len(u04))
assert SCOPE <= u04
wb = openpyxl.load_workbook(DL / "2026072901.xlsx", data_only=True)
u10 = set()
for n in wb.sheetnames[:2]:
    for r in wb[n].iter_rows(values_only=True):
        if r and len(r) > 1 and isinstance(r[1], str) and re.fullmatch(r"\d{6}[A-Z]*", r[1].strip()):
            u10.add(r[1].strip())
assert len(u10) == 95 and u04 - u10 == {"080204"} and not (u10 - u04), (len(u10), u04 ^ u10)
assert not ((u04 | u10) & ({"080701", "080702", "080703", "080704", "080705", "080706", "080903", "080904K", "080906", "080907T", "080908T", "080803T"}))

p = CONTENT / "provinces" / "hunan.json"
d = provlib._load(p)
note = (f"湖南省 2026 年 4 月报考简章附表 1《开考专业（专升本）》74 个 + 附表 2《开考专业（专科）》22 个，去重 96 个专业（{X04}）；"
        f"2026 年 10 月附表 1+2 去重 95 个（{X10}），两期差异只有 080204 机械电子工程（不在范围内）；范围内专业两期一致，全表未列此专业")
n = 0
for o in d["offerings"]:
    if o["status"] == "none":
        o["verify"] = V(X10, note)
        n += 1
provlib._save(p, d)
dst = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence" / "hunan"
save_evidence("hunan", "hn_jz04_fubiao.txt", "\n".join(lines), X04, f"2026 年 4 月报考简章附表 1、2（xls，xlrd 抽取）；来源页 {N04}", hashlib.sha256((DL / "20260114.xls").read_bytes()).hexdigest())
print("hunan april ok", n, "none records updated")
