"""甘肃：报名平台「自考教材信息」页（https://kw.ganseea.cn/public-info/zkjcxx，官方，浏览器渲染后读取）给甘肃两个计划（080901、080202）的理论课挂教材。
同书同版（书名、版次、出版社都一致）沿用教材库已有 id，没有的新建 tb-gs-<课程代码>-<年份>。实践课不挂教材。
用法：python -X utf8 build_gansu_textbooks.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-03"
from provlib import *  # noqa: E402,F403

URL = "https://kw.ganseea.cn/public-info/zkjcxx"
# 课程代码 → (教材名称, 作者, 版次, 出版社)，逐字取自页面表格
TB = {
    "15043": ("中国近现代史纲要", "本书编写组", "2023年版", "高等教育出版社"),
    "15044": ("马克思主义基本原理", "本书编写组", "2023年版", "高等教育出版社"),
    "15040": ("习近平新时代中国特色社会主义思想概论", "本书编写组", None, "高等教育出版社、人民出版社"),
    "13000": ("英语（专升本）", "韩宝成、罗凯洲", "2026年版", "外语教学与研究出版社"),
    "00023": ("高等数学（工本）", "陈兆斗、马鹏", "2023年版", "北京大学出版社"),
    "02324": ("离散数学", "辛运帏", "2014年版", "机械工业出版社"),
    "13015": ("计算机系统原理", "袁春风", "2023年版", "机械工业出版社"),
    "13180": ("操作系统", "陈向群、孙卫真", "2023年版", "机械工业出版社"),
    "13003": ("数据结构与算法", "辛运帏、陈朔鹰", "2024年版", "机械工业出版社"),
    "13013": ("高级语言程序设计", "郑岩", "2017年版", "机械工业出版社"),
    "02325": ("计算机体系结构基础", "胡伟武等", "2021年版", "机械工业出版社"),
    "13005": ("软件工程", "张琼声", "2024年版", "机械工业出版社"),
    "13011": ("大数据与人工智能", "杨忠宝、佘向飞", "2022年版", "北京大学出版社"),
    "13017": ("计算机网络与信息安全", "李全龙", "2024年版", "机械工业出版社"),
    "14349": ("Web开发技术实战教程", "唐友等", "2022年版", "化学工业出版社"),
    "13174": ("概率论与数理统计（工）", "孙洪祥、张志刚", "2023年版", "北京大学出版社"),
    "02202": ("传感器与检测技术", "邓鹏等", "2020年版", "电子科技大学出版社"),
    "02205": ("微型计算机原理与接口技术", "徐骏善、朱岩", "2014年版", "机械工业出版社"),
    "02204": ("经济管理", "米锋", "2024年版", "机械工业出版社"),
    "02209": ("机械制造装备设计", "张福、王晓方", "2014年版", "华中科技大学出版社"),
    "01928": ("液压与气压传动（第四版）", "刘银水、许福玲", "2016年版", "机械工业出版社"),
    "05785": ("机床数控技术（第三版）", "胡占齐、杨莉", "2014年版", "机械工业出版社"),
    "02213": ("精密与特种加工技术", "张国智、王中营", "2013年版", "华中科技大学出版社"),
    "11184": ("先进制造技术（第四版）", "任小中、赵让乾", "2021年版", "华中科技大学出版社"),
    "02643": ("质量管理（第三版）", "马风才、谷炜", "2017年版", "机械工业出版社"),
    "02207": ("机电传动控制", "胡世军、张大志", "2014年版", "华中科技大学出版社"),
}
books = Shard("textbooks")
existing = {}
for pool in (books.items, books.others):
    for k, v in pool.items():
        existing[(v["title"], v.get("edition"), v.get("publisher"))] = k


def ident(code, edition):
    import re
    y = re.search(r"(\d{4})", edition or "")
    return f"tb-gs-{code}-{y[1] if y else 'x'}"


ids = {}
for code, (title, authors, edition, pub) in TB.items():
    key = (title, edition, pub)
    if key in existing:
        ids[code] = existing[key]
        continue
    bid = ident(code, edition)
    books.add(bid, {"title": title, "authors": [a for a in authors.replace("等", "").split("、") if a], "publisher": pub, "edition": edition or "未标注", "isbn": None, "kind": None,
                    "outline": "考试大纲见甘肃省教育考试院（自学考试省级课程大纲页）",
                    "verify": V(URL, "甘肃省教育考试院报名平台「自考教材信息」页")})
    ids[code] = bid
books.save()

p = CONTENT / "provinces" / "gansu.json"
d = provlib._load(p)
n = 0
for plan in d["plans"]:
    for c in plan["courses"]:
        if c["code"] in ids and c["category"] != "practice":
            c["textbook"] = ids[c["code"]]
            n += 1
    plan["rules"] += "教材取自甘肃省教育考试院「自考教材信息」页。"
for o in d["offerings"]:
    if o.get("plans"):
        o["complete"]["textbook"] = True
provlib._save(p, d)
print("gansu textbooks ok", n, "rows;", len(ids), "books;", sum(1 for c in ids.values() if not c.startswith("tb-gs-")), "reused")
