#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""蒙元并入唐宋（7 段）；补关隘/走廊/河运等地理点与 role 说明。"""

from __future__ import annotations

import json
from pathlib import Path

CONTENT = Path(__file__).resolve().parent.parent / "content"
ATLAS = CONTENT / "atlas.json"
TERR = CONTENT / "territories.json"

# 新增地理锚点：关隘、河运、丝路、边防、战略枢纽（示意坐标，府州/关级）
NEW_PLACES: list[dict] = [
    {
        "id": "tongguan",
        "modern": "潼关",
        "lon": 110.25,
        "lat": 34.61,
        "tier": "pass",
        "role": "关中东门，继函谷之后的仰攻咽喉；控渭洛交汇与黄河弯曲，谁守潼关谁守关中补给线。",
        "names": [{"from": -300, "name": "潼关"}],
    },
    {
        "id": "jiange",
        "modern": "剑阁",
        "lon": 105.52,
        "lat": 32.29,
        "tier": "pass",
        "role": "蜀道锁钥：栈道与剑门把关中—汉中—成都串成一条窄喉，北伐与入蜀都绕不开。",
        "names": [{"from": -300, "name": "剑阁", "also": ["剑门"]}],
    },
    {
        "id": "hanzhong",
        "modern": "汉中",
        "lon": 107.02,
        "lat": 33.07,
        "tier": "prefecture",
        "role": "秦岭南麓盆地，关中与巴蜀之间的战略跳板；粮储与栈道终点常在此交接。",
        "names": [{"from": -300, "name": "汉中"}],
    },
    {
        "id": "yanmenguan",
        "modern": "代县雁门关",
        "lon": 112.86,
        "lat": 39.18,
        "tier": "pass",
        "role": "太行—恒山北缘孔道，农耕区与草原之间的经典关隘；边防与互市常在此一线摆动。",
        "names": [{"from": -200, "name": "雁门关"}],
    },
    {
        "id": "juyongguan",
        "modern": "昌平居庸关",
        "lon": 116.07,
        "lat": 40.29,
        "tier": "pass",
        "role": "京师西北门户，军都山峡谷中的长城关城；护大都/北京北面的第一道险。",
        "names": [{"from": 400, "name": "居庸关"}],
    },
    {
        "id": "shanhaiguan",
        "modern": "山海关",
        "lon": 119.75,
        "lat": 39.98,
        "tier": "pass",
        "role": "辽西走廊入关第一关：山海之间的窄喉，连接华北平原与东北；明清易代的地理开关。",
        "names": [{"from": 1381, "name": "山海关", "also": ["榆关"]}],
    },
    {
        "id": "jiayuguan",
        "modern": "嘉峪关",
        "lon": 98.22,
        "lat": 39.80,
        "tier": "pass",
        "role": "河西走廊西端明长城关城，内地与西域绿洲交通的门户象征。",
        "names": [{"from": 1372, "name": "嘉峪关"}],
    },
    {
        "id": "yumen",
        "modern": "玉门",
        "lon": 97.05,
        "lat": 40.29,
        "tier": "pass",
        "role": "汉代经营西域的西出门户之一，与阳关并称；走廊西端的烽燧与屯戍节点。",
        "names": [{"from": -120, "name": "玉门关"}],
    },
    {
        "id": "yangguan",
        "modern": "敦煌阳关",
        "lon": 94.15,
        "lat": 39.93,
        "tier": "pass",
        "role": "出敦煌南道门户，与玉门关分指西域南北道；文学地名背后是实在的绿洲补给点。",
        "names": [{"from": -120, "name": "阳关"}],
    },
    {
        "id": "hami",
        "modern": "哈密",
        "lon": 93.51,
        "lat": 42.83,
        "tier": "prefecture",
        "role": "天山南麓东端绿洲，内地进新疆的东大门；明清哈密卫与贡道关键站。",
        "names": [
            {"from": -100, "to": 1400, "name": "伊吾"},
            {"from": 1400, "name": "哈密"},
        ],
    },
    {
        "id": "kuqa",
        "modern": "库车",
        "lon": 82.96,
        "lat": 41.72,
        "tier": "prefecture",
        "role": "龟兹故地，天山南麓丝路北道重镇；佛教与绿洲城邦政治的交汇点。",
        "names": [{"from": -100, "name": "龟兹"}],
    },
    {
        "id": "hotan",
        "modern": "和田",
        "lon": 79.92,
        "lat": 37.11,
        "tier": "prefecture",
        "role": "于阗绿洲，丝路南道枢纽与玉石产地；汉唐经营西域的南翼支点。",
        "names": [{"from": -100, "name": "于阗"}],
    },
    {
        "id": "beitíng",
        "modern": "吉木萨尔北庭",
        "lon": 89.18,
        "lat": 44.00,
        "tier": "prefecture",
        "role": "唐北庭都护府驻地一带，天山北麓游牧—屯垦交接带的军政中心。",
        "names": [{"from": 640, "name": "北庭"}],
    },
    {
        "id": "huaián",
        "modern": "淮安",
        "lon": 119.15,
        "lat": 33.50,
        "tier": "metropolis",
        "role": "淮扬运河与黄河故道交汇带的漕运枢纽；明清漕船过淮常在此盘驳。",
        "names": [
            {"from": -200, "to": 960, "name": "淮阴"},
            {"from": 960, "name": "淮安"},
        ],
    },
    {
        "id": "jining",
        "modern": "济宁",
        "lon": 116.59,
        "lat": 35.41,
        "tier": "metropolis",
        "role": "会通河开通后的山东漕运中枢，南北水道与鲁西南陆路在此交会。",
        "names": [{"from": 1280, "name": "济宁"}],
    },
    {
        "id": "linqing",
        "modern": "临清",
        "lon": 115.71,
        "lat": 36.84,
        "tier": "metropolis",
        "role": "会通河与卫河交汇的钞关城市，明清运河商税与粮船最繁忙的节点之一。",
        "names": [{"from": 1280, "name": "临清"}],
    },
    {
        "id": "tongzhou",
        "modern": "通州",
        "lon": 116.66,
        "lat": 39.91,
        "tier": "metropolis",
        "role": "北运河终点，京师漕粮上岸码头；「北驾南漕」在地理上的最后一站。",
        "names": [{"from": 1200, "name": "通州"}],
    },
    {
        "id": "zhenjiang",
        "modern": "镇江",
        "lon": 119.45,
        "lat": 32.20,
        "tier": "metropolis",
        "role": "长江与大运河十字交汇的京口，控江防与漕运；南北军事对峙常盯住此处。",
        "names": [
            {"from": -200, "to": 589, "name": "京口"},
            {"from": 589, "name": "润州", "also": ["镇江"]},
        ],
    },
    {
        "id": "jiujiang",
        "modern": "九江",
        "lon": 115.99,
        "lat": 29.71,
        "tier": "prefecture",
        "role": "长江中游鄱阳湖口附近口岸，江防与赣江入江咽喉；控江西财赋出江通道。",
        "names": [
            {"from": -200, "to": 960, "name": "浔阳"},
            {"from": 960, "name": "江州", "also": ["九江"]},
        ],
    },
    {
        "id": "yueyang",
        "modern": "岳阳",
        "lon": 113.13,
        "lat": 29.37,
        "tier": "prefecture",
        "role": "洞庭湖入江口，荆湖粮米与湘江流域的出江门户。",
        "names": [
            {"from": -200, "to": 960, "name": "巴陵"},
            {"from": 960, "name": "岳州"},
        ],
    },
    {
        "id": "yichang",
        "modern": "宜昌",
        "lon": 111.29,
        "lat": 30.70,
        "tier": "prefecture",
        "role": "三峡东口、长江上游进入江汉平原的咽喉；夷陵之战与江防布局的地理锚点。",
        "names": [{"from": -200, "name": "夷陵", "also": ["峡州"]}],
    },
    {
        "id": "jingkou_caishi",
        "modern": "马鞍山采石",
        "lon": 118.48,
        "lat": 31.72,
        "tier": "pass",
        "role": "长江下游矶头渡口，历代南北争江的经典战场与渡江点。",
        "names": [{"from": 200, "name": "采石"}],
    },
    {
        "id": "dengzhou",
        "modern": "蓬莱",
        "lon": 120.75,
        "lat": 37.80,
        "tier": "prefecture",
        "role": "登州港，黄渤海航运与东方海上航线的北方口岸；岸防与漕海运节点。",
        "names": [{"from": -200, "name": "登州"}],
    },
    {
        "id": "mingzhou",
        "modern": "宁波",
        "lon": 121.55,
        "lat": 29.87,
        "tier": "metropolis",
        "role": "明州/庆元，唐宋以降东海贸易与对日航线要港；与泉州、广州并列的海上出口。",
        "names": [
            {"from": 738, "to": 1195, "name": "明州"},
            {"from": 1195, "name": "庆元", "also": ["宁波"]},
        ],
    },
    {
        "id": "jingzhou_jiangling",
        "modern": "荆州",
        "lon": 112.24,
        "lat": 30.33,
        "tier": "metropolis",
        "role": "江汉平原与长江中游军政枢纽，「兵争要地」；北上宛洛、东下建康、西入巴蜀的十字路口。",
        "names": [{"from": -300, "name": "江陵", "also": ["荆州"]}],
    },
    {
        "id": "xiangfan",
        "modern": "襄阳",
        "lon": 112.14,
        "lat": 32.04,
        "tier": "metropolis",
        "role": "汉水中游锁钥，南北对峙时中原与江淮之间的军事支点；水陆均可补给。",
        "names": [{"from": -200, "name": "襄阳"}],
    },
    {
        "id": "well_xing",
        "modern": "井陉",
        "lon": 114.14,
        "lat": 38.03,
        "tier": "pass",
        "role": "太行八陉之一，河北平原通往山西的窄道；韩信破赵一类战例的地理舞台。",
        "names": [{"from": -300, "name": "井陉"}],
    },
    {
        "id": "zijingguan",
        "modern": "易县紫荆关",
        "lon": 115.12,
        "lat": 39.42,
        "tier": "pass",
        "role": "太行东麓内三关之一，护京师西南侧；与居庸、倒马构成京西防线。",
        "names": [{"from": 500, "name": "紫荆关"}],
    },
    {
        "id": "ningyuan",
        "modern": "兴城",
        "lon": 120.71,
        "lat": 40.62,
        "tier": "pass",
        "role": "辽西走廊宁远卫一线，明末抗后金的前沿堡城；走廊战争的地理标本。",
        "names": [{"from": 1400, "name": "宁远"}],
    },
    {
        "id": "taiwan_fu",
        "modern": "台南",
        "lon": 120.21,
        "lat": 22.99,
        "tier": "prefecture",
        "role": "明郑—清代台湾府核心区，东南海上抗清基地转入省府行政后的岛上政治中心。",
        "names": [
            {"from": 1624, "to": 1683, "name": "热兰遮—承天"},
            {"from": 1683, "name": "台湾府"},
        ],
    },
    {
        "id": "ili",
        "modern": "伊宁",
        "lon": 81.32,
        "lat": 43.92,
        "tier": "prefecture",
        "role": "伊犁河谷，清乾隆后新疆军府重镇；天山北路农牧与卡伦体系的西端枢纽。",
        "names": [{"from": 1760, "name": "伊犁"}],
    },
    {
        "id": "urumqi",
        "modern": "乌鲁木齐",
        "lon": 87.62,
        "lat": 43.83,
        "tier": "prefecture",
        "role": "天山北麓后期军府与屯垦中心，近代新疆交通与行政的地理重心逐渐北移至此。",
        "names": [{"from": 1760, "name": "迪化", "also": ["乌鲁木齐"]}],
    },
    {
        "id": "xining",
        "modern": "西宁",
        "lon": 101.78,
        "lat": 36.62,
        "tier": "prefecture",
        "role": "河湟谷地门户，控青海路与藏区东北缘；边地军镇与茶马贸易节点。",
        "names": [
            {"from": -100, "to": 1100, "name": "湟中"},
            {"from": 1100, "name": "西宁"},
        ],
    },
    {
        "id": "chengde",
        "modern": "承德",
        "lon": 117.96,
        "lat": 40.97,
        "tier": "prefecture",
        "role": "清避暑山庄所在，木兰围场与蒙旗朝觐的塞外政治舞台，长城以外的第二种「京师」。",
        "names": [{"from": 1703, "name": "热河", "also": ["承德"]}],
    },
    {
        "id": "qiongzhou",
        "modern": "海口",
        "lon": 110.35,
        "lat": 20.02,
        "tier": "prefecture",
        "role": "琼州海峡北岸门户，岭南逾海经营海南岛的跳板。",
        "names": [{"from": 600, "name": "琼州"}],
    },
    {
        "id": "guilin",
        "modern": "桂林",
        "lon": 110.29,
        "lat": 25.27,
        "tier": "prefecture",
        "role": "岭南西部湘桂走廊枢纽，中原入广西的主要孔道与静江府治所。",
        "names": [
            {"from": -214, "to": 960, "name": "桂州"},
            {"from": 960, "name": "静江", "also": ["桂林"]},
        ],
    },
    {
        "id": "nanning",
        "modern": "南宁",
        "lon": 108.37,
        "lat": 22.82,
        "tier": "prefecture",
        "role": "邕州，岭南西道与左江流域军政中心，通往交趾方向的内地支点。",
        "names": [{"from": 600, "name": "邕州", "also": ["南宁"]}],
    },
    {
        "id": "zhaoqing",
        "modern": "肇庆",
        "lon": 112.47,
        "lat": 23.05,
        "tier": "prefecture",
        "role": "西江中游端州，两广总督常驻与岭南内河航运枢纽之一。",
        "names": [{"from": 600, "name": "端州", "also": ["肇庆"]}],
    },
    {
        "id": "wuhu",
        "modern": "芜湖",
        "lon": 118.38,
        "lat": 31.33,
        "tier": "prefecture",
        "role": "长江下游米市与江防节点，皖南与江淮之间的水运码头。",
        "names": [{"from": 200, "name": "芜湖"}],
    },
    {
        "id": "hankou",
        "modern": "武汉汉口",
        "lon": 114.29,
        "lat": 30.58,
        "tier": "metropolis",
        "role": "汉水入江口，近代崛起的长江中游总码头；「九省通衢」的地理含义在此落地。",
        "names": [
            {"from": -200, "to": 1861, "name": "夏口", "also": ["汉口"]},
            {"from": 1861, "name": "汉口"},
        ],
    },
]

# 给已有关键点补地理角色说明（不覆盖已有 role）
ROLE_PATCH: dict[str, str] = {
    "changan": "关中盆地核心都城，四塞形胜与渭河粮道交汇；帝国「形胜侧」政治中心的长期坐标。",
    "luoyang": "伊洛盆地「天下之中」，兼顾关中形胜与关东人力财赋的双都东端。",
    "jiankang": "长江下游石头城—秦淮河城市带，南渡法统与江南财赋的接合点。",
    "kaifeng": "汴河漕运帝都，运河补给型国家的空间标本。",
    "hangzhou": "钱塘江口与江南水网都市，南宋行在与海陆贸易腹地。",
    "dadu": "华北平原北缘帝都，漕运终点与长城前线之间的政治驻跸点。",
    "dunhuang": "河西走廊西端绿洲，丝路总枢纽与敦煌文书所代表的走廊社会。",
    "wuwei": "河西四郡东段，走廊屯田与驿站链的起点性节点。",
    "yangzhou": "运河与长江交汇的盐漕都会，「扬一益二」的江淮心脏。",
    "quanzhou": "刺桐港，印度洋—东海贸易的制度高峰口岸。",
    "guangzhou": "岭南港市，南海贸易与逾岭道路的南端汇聚点。",
    "xiangyang": "汉水中游南北对峙锁钥（与襄樊同址不同条目时互参）。",
    "chengdu": "成都平原天府粮仓，巴蜀盆地的政治与补给中心。",
    "yinchuan": "贺兰山东麓兴庆府，西夏立国的河套—宁夏地理底座。",
    "datong": "大同盆地云中/西京，农牧交接带的军镇与辽金西京传统。",
    "shanghai": "长江口条约口岸超级城市，近代经济地理的独立变量。",
    "hangu": "先秦至汉仰攻关中的经典关塞（与函谷叙事同线）。",
    "xianyang_pass_hangu": "函谷—潼关一线的关中东部门户示意点。",
}


def main() -> None:
    data = json.loads(ATLAS.read_text(encoding="utf-8"))
    data["_"] = (
        "九州图鉴。year 公元前为负；疆域见 territories.json（示意）。"
        "主轴七大政治秩序阶段（蒙元并入唐宋多元段）。深度：爱好者中高档。"
    )

    # --- 合并蒙元进唐宋 ---
    eras = data["eras"]
    yuan = next(e for e in eras if e["id"] == "yuan-reintegrate")
    tsp = next(e for e in eras if e["id"] == "tang-song-plural")
    tsp["title"] = "唐宋变革·多元与蒙元"
    tsp["to"] = yuan["to"]  # 1368
    tsp["blurb"] = (
        "科举、募兵与运河城市改变国家与社会接合；辽夏金与两宋并立之后，"
        "蒙元以行省、站赤与跨区域帝国机器完成再整合。多元并存与强制统一，"
        "同属这一长段的政治地理课题，而不是两个互不相关的故事。"
    )
    tsp["territoryId"] = "song-plural"  # App 按年切换到 yuan-empire
    data["eras"] = [e for e in eras if e["id"] != "yuan-reintegrate"]

    for ev in data["events"]:
        if ev.get("eraId") == "yuan-reintegrate":
            ev["eraId"] = "tang-song-plural"

    # --- 补 role ---
    by_id = {p["id"]: p for p in data["places"]}
    for pid, role in ROLE_PATCH.items():
        if pid in by_id and not by_id[pid].get("role"):
            by_id[pid]["role"] = role

    # --- 新地点 ---
    added = 0
    for p in NEW_PLACES:
        if p["id"] in by_id:
            # 已存在则只补 role
            if not by_id[p["id"]].get("role") and p.get("role"):
                by_id[p["id"]]["role"] = p["role"]
            continue
        data["places"].append(p)
        by_id[p["id"]] = p
        added += 1

    # 去重：ningbo 与 mingzhou 坐标接近，若已有 ningbo 则给 ningbo 补 role，不强制删 mingzhou
    if "ningbo" in by_id and not by_id["ningbo"].get("role"):
        by_id["ningbo"]["role"] = NEW_PLACES[[x["id"] for x in NEW_PLACES].index("mingzhou")]["role"]

    ATLAS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # --- territories：yuan 挂到合并后的时代；保留面供按年切换 ---
    terr = json.loads(TERR.read_text(encoding="utf-8"))
    for f in terr.get("features") or []:
        props = f.setdefault("properties", {})
        if props.get("id") == "yuan-empire":
            props["eraId"] = "tang-song-plural"
            props["name"] = "元疆域示意（唐宋·多元与蒙元段后半）"
        if props.get("id") == "song-plural":
            props["name"] = "两宋+并立政权框（示意，段前半）"
    TERR.write_text(json.dumps(terr, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        f"eras={len(data['eras'])} places={len(data['places'])} "
        f"(+{added}) events_yuan_remapped="
        f"{sum(1 for e in data['events'] if e['eraId']=='tang-song-plural')}"
    )


if __name__ == "__main__":
    main()
