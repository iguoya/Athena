"""天津：招考资讯网（zhaokao.net）2025-11-25《2026 年上半年天津市高等教育自学考试非笔试课程和毕业环节主考院校联系报到一览表》（xlsx，官方），
使用者 2026-11-02 浏览器下载，来源网址取自下载文件的 Zone.Identifier。
表里 080901 计算机科学与技术（专升本）：天津工业大学继续教育学院；另一行 080901 紧接在「510201 计算机应用技术（专科）— 天津师范大学计算机与信息工程学院」之后，
主考院校栏空（原表合并单元格），按上一行归天津师范大学计算机与信息工程学院；080902 软件工程：天津理工大学继续教育学院；080701 电子信息工程：中国民航大学继续教育学院。
这张表只管非笔试课程和毕业环节，不是全省开考专业总表，所以不据此写「不开设」。
用法：python -X utf8 build_tianjin_official.py <Downloads 目录> <抽取目录>
"""
import hashlib
import pathlib
import shutil
import sys

import openpyxl

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-02"
from provlib import *  # noqa: E402,F403

DL, EX = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
F = "00300010910_876e090c.xlsx"
PAGE = "http://www.zhaokao.net/zxks/system/2025/11/25/030009183.shtml"
URL = "http://www.zhaokao.net/zxks/doc/003/000/109/00300010910_876e090c.xlsx"
NOTE = f"招考资讯网 2025-11-25《2026 年上半年天津市高等教育自学考试非笔试课程和毕业环节主考院校联系报到一览表》（{URL}）"

# 逐行核对：读 xlsx，按「空主考院校沿用上一行」的合并单元格规则求 080901/080902/080701 的主考院校
ws = openpyxl.load_workbook(DL / F, data_only=True).active
hosts, last = {}, None
for r in ws.iter_rows(values_only=True):
    code, name, host = (r[0] or "").strip() if isinstance(r[0], str) else r[0], r[1], r[2]
    if host:
        last = str(host).strip()
    if code in ("080901", "080902", "080701"):
        h = (last or "").split("（")[0].split("\n")[0].split(" ")[0]
        hosts.setdefault(code, [])
        if h not in hosts[code]:
            hosts[code].append(h)
# 主考院校名取学校全称（去掉学院办公室等后缀）
def school(h):
    for s in ("天津工业大学", "天津师范大学", "天津理工大学", "中国民航大学"):
        if h.startswith(s):
            return s
    raise SystemExit(f"未识别主考院校：{h}")


hs = {k: [school(h) for h in v] for k, v in hosts.items()}
assert hs == {"080901": ["天津工业大学", "天津师范大学"], "080902": ["天津理工大学"], "080701": ["中国民航大学"]}, hs

p = CONTENT / "provinces" / "tianjin.json"
d = provlib._load(p)
d["authority"] = {"name": "天津市教育招生考试院（招考资讯网）", "url": "https://www.zhaokao.net/", "verify": V(PAGE, "招考资讯网为天津市高等教育自学考试官方发布与考生服务入口；一览表正文写作「招考资讯网（www.zhaokao.net）—自学考试—天津市高等教育自学考试考生服务平台」，机构名取该网站主办单位")}
d["selfstudy_portal"] = {"name": "天津市高等教育自学考试考生服务平台", "url": "https://www.zhaokao.net/", "verify": V(PAGE, "一览表说明 1：考生登录招考资讯网—自学考试—天津市高等教育自学考试考生服务平台报考")}
new = []
for o in d["offerings"]:
    if o["major"] in ("080901", "080902"):
        o["status"] = "open"
        o["hosts"] = hs[o["major"]]
        o["verify"] = V(PAGE, NOTE + f"：{'、'.join(hs[o['major']])}（天津师范大学一行的主考院校栏为合并单元格，按上一行归属）；开考状态与第三方转载的 2026 年下半年一览表一致，官方一览表待核；计划与课程待查" if o["major"] == "080901" else NOTE + "：天津理工大学继续教育学院；开考状态与第三方转载的 2026 年下半年一览表一致，官方一览表待核；计划与课程待查")
    if o["major"] == "080701":
        o["hosts"] = hs["080701"]
        o["verify"] = V("https://www.edu-edu.com/zikao/tianjin/zkbm/66489.html", "第三方转载一览表备注称：2025 年 4 月考试报名起不再接收新考生，2027 年起停止安排考试、停办毕业证（待官方一览表核实）；" + NOTE + "：中国民航大学继续教育学院", level="report")
provlib._save(p, d)

dst = provlib.ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence" / "tianjin"
dst.mkdir(parents=True, exist_ok=True)
shutil.copy2(DL / F, dst / "tj_feibishi_zhukao_2026-04.xlsx")
save_evidence("tianjin", "tj_feibishi_zhukao_2026-04.xlsx.txt", (EX / (F + ".txt")).read_text(encoding="utf-8"), URL, "2026 年上半年非笔试课程和毕业环节主考院校联系报到一览表（xlsx，openpyxl 抽取）；来源页 " + PAGE, hashlib.sha256((DL / F).read_bytes()).hexdigest())
print("tianjin official ok", hs)
