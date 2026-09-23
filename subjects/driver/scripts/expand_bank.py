#!/usr/bin/env python3
"""按「过科目一」扩题：独立考点，不搬商业整库，不靠换皮凑数。"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "content/questions"
LAW = "https://www.gov.cn/banshi/2005-08/31/content_68700.htm"
REG = "https://www.gov.cn/zhengce/2020-12/25/content_5574205.htm"
ORD = "https://www.gov.cn/zhengce/2021-12/27/content_5712881.htm"
GB = "https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=15B1FC09EE1AE92F1A9EC97BA3C9E451"

DROP = {
    "drive.s1.signals.001",
    "drive.s1.signals.002",
    "drive.s1.signals.003",
    "drive.s1.signals.004",
    "drive.s1.signals.005",
    "drive.s1.signals.010",
    "drive.s1.signals.011",
    "drive.s1.signals.012",
}


def ref(source_id: str, locator: str, url: str, note: str, relation: str = "quoted") -> dict:
    return {
        "source_id": source_id,
        "relation": relation,
        "locator": locator,
        "url": url,
        "note": note,
    }


def law(locator: str, note: str) -> dict:
    return ref("road-safety-law", locator, LAW, note)


def reg(locator: str, note: str) -> dict:
    return ref("road-safety-regulation", locator, REG, note)


def gb(locator: str, note: str) -> dict:
    return ref("gb5768-2", locator, GB, note, "adapted")


def order(locator: str, note: str) -> dict:
    return ref("license-order-162", locator, ORD, note)


def judge(
    qid: str,
    topic: str,
    prompt: str,
    ok: bool,
    explain: str,
    source_refs: list,
    *,
    phase: int,
    band: str,
    difficulty: int = 1,
) -> dict:
    return {
        "id": qid,
        "topic_id": topic,
        "kind": "judge",
        "prompt": prompt,
        "choices": [
            {"id": "T", "label": "正确", "ok": ok},
            {"id": "F", "label": "错误", "ok": not ok},
        ],
        "explain": explain,
        "source_refs": source_refs,
        "phase": phase,
        "difficulty": difficulty,
        "band": band,
    }


def single(
    qid: str,
    topic: str,
    prompt: str,
    options: list[tuple[str, str, bool]],
    explain: str,
    source_refs: list,
    *,
    phase: int,
    band: str,
    difficulty: int = 2,
) -> dict:
    return {
        "id": qid,
        "topic_id": topic,
        "kind": "single",
        "prompt": prompt,
        "choices": [{"id": i, "label": label, "ok": ok} for i, label, ok in options],
        "explain": explain,
        "source_refs": source_refs,
        "phase": phase,
        "difficulty": difficulty,
        "band": band,
    }


LIC = "drive.s1.license"
RUL = "drive.s1.rules"
ALC = "drive.s1.alcohol"
SIG = "drive.s1.signals"
HWY = "drive.s1.highway"
OCC = "drive.s1.occupants"
CRASH = "drive.s4.crash"
LIGHT = "drive.s4.lights"
WX = "drive.s4.weather"
EMG = "drive.s4.emergency"
AID = "drive.s4.aid"

S1 = [
    judge("drive.s1.license.016", LIC, "驾驶机动车上道路行驶，应当悬挂机动车号牌，并随车携带机动车行驶证。", True, "号牌和行驶证是上路的标配，不是可选项。", [law("第11条", "驾驶机动车上道路行驶，应当悬挂机动车号牌，放置检验合格标志、保险标志，并随车携带机动车行驶证。")], phase=1, band="hot"),
    judge("drive.s1.license.017", LIC, "机动车号牌可以故意遮挡或者污损。", False, "第11条禁止故意遮挡、污损号牌。", [law("第11条", "机动车号牌应当按照规定悬挂并保持清晰、完整，不得故意遮挡、污损。")], phase=1, band="hot"),
    judge("drive.s1.license.018", LIC, "尚未登记的机动车需要临时上道路行驶的，应当取得临时通行牌证。", True, "纸质复印件顶不了临时牌证。", [law("第8条", "尚未登记的机动车，需要临时上道路行驶的，应当取得临时通行牌证。")], phase=1, band="common"),
    judge("drive.s1.license.019", LIC, "学习驾驶应当使用教练车，在教练员随车指导下进行。", True, "第20条：教练车、教练员随车，不是自己开私家车练。", [law("第20条", "在道路上学习驾驶，应当按照公安机关交通管理部门指定的路线、时间进行。在道路上学习机动车驾驶技能应当使用教练车，在教练员随车指导下进行。")], phase=1, band="common"),
    judge("drive.s1.license.020", LIC, "公安机关交通管理部门对机动车驾驶人违法行为实行累积记分制度，记分周期为12个月。", True, "记满12分会扣证学习，不是过了年自动清零就完事。", [law("第24条", "公安机关交通管理部门对机动车驾驶人违反道路交通安全法律、法规的行为，除依法给予行政处罚外，实行累积记分制度。记分周期为12个月。")], phase=1, band="hot"),
    single("drive.s1.license.021", LIC, "机动车驾驶人记分周期内累积记分达到多少分，公安机关交通管理部门将扣留驾驶证？", [("A", "6分", False), ("B", "9分", False), ("C", "12分", True), ("D", "24分", False)], "满12分扣证，不是满6分。", [law("第24条", "对记满12分的机动车驾驶人，扣留机动车驾驶证。")], phase=1, band="hot"),
    judge("drive.s1.license.022", LIC, "实习期内驾驶机动车，应当在车身后部粘贴或者悬挂实习标志。", True, "条例第22条。车上没有实习标，等于别人不知道你是新手。", [reg("第22条", "在实习期内驾驶机动车的，应当在车身后部粘贴或者悬挂统一式样的实习标志。")], phase=1, band="hot"),
    single("drive.s1.license.023", LIC, "实习期驾驶人驾驶机动车上高速公路，陪同人应当持相应或者包含其准驾车型驾驶证多少年以上？", [("A", "1年", False), ("B", "2年", False), ("C", "3年", True), ("D", "5年", False)], "陪同人要三年以上驾龄，不是随便一个有证的人。", [order("第65条", "实习期驾驶人驾驶机动车上高速公路，应当由持相应或者包含其准驾车型驾驶证三年以上的驾驶人陪同。")], phase=1, band="hot"),
    judge("drive.s1.license.024", LIC, "驾驶证丢失后，仍然可以继续驾驶机动车上道路行驶。", False, "没有合法驾驶证就不得驾驶。丢失应申请补证。", [law("第19条", "驾驶机动车，应当依法取得机动车驾驶证。")], phase=1, band="common"),
    judge("drive.s1.license.025", LIC, "把机动车交给没有驾驶证的人驾驶，是违法行为。", True, "第19条、第99条把将机动车交由未取得驾驶证的人驾驶列为禁止情形。", [law("第19条", "驾驶机动车，应当依法取得机动车驾驶证。"), law("第99条", "将机动车交由未取得机动车驾驶证的人驾驶的，由公安机关交通管理部门处二百元以上二千元以下罚款。")], phase=1, band="common"),
    judge("drive.s1.rules.017", RUL, "根据道路条件和通行需要划分机动车道、非机动车道和人行道的，应当分道通行。", True, "第36条：各走各的道。", [law("第36条", "根据道路条件和通行需要，道路划分为机动车道、非机动车道和人行道的，机动车、非机动车、行人实行分道通行。")], phase=2, band="hot"),
    judge("drive.s1.rules.018", RUL, "没有划分机动车道、非机动车道和人行道的，机动车应当在道路中间通行。", True, "机动车走中间，非机动车和行人走两侧。", [law("第36条", "没有划分机动车道、非机动车道和人行道的，机动车在道路中间通行，非机动车和行人在道路两侧通行。")], phase=2, band="common"),
    judge("drive.s1.rules.019", RUL, "遇有前方车辆停车排队等候时，可以从两侧穿插或者超越行驶。", False, "第45条禁止借道超车、占用对面车道和穿插等候车辆。", [law("第45条", "机动车遇有前方车辆停车排队等候或者缓慢行驶时，不得借道超车或者占用对面车道，不得穿插等候的车辆。")], phase=2, band="hot"),
    judge("drive.s1.rules.020", RUL, "机动车行经铁路道口，没有交通信号或者管理人员的，应当减速或者停车，确认安全后通过。", True, "第46条：看不清就停，不要抢过道口。", [law("第46条", "机动车通过铁路道口时，应当按照交通信号或者管理人员的指挥通行；没有交通信号或者管理人员的，应当减速或者停车，在确认安全后通过。")], phase=2, band="hot"),
    judge("drive.s1.rules.021", RUL, "机动车载人不得超过核定的人数。", True, "第49条，后排再挤也不行。", [law("第49条", "机动车载人不得超过核定的人数。")], phase=2, band="hot"),
    judge("drive.s1.rules.022", RUL, "货运机动车可以载客。", False, "第50条禁止货运机动车载客。", [law("第50条", "禁止货运机动车载客。")], phase=2, band="regular"),
    judge("drive.s1.rules.023", RUL, "警车、消防车、救护车、工程救险车执行紧急任务时，其他车辆和行人应当让行。", True, "第53条，听到警报先让，不是跟它抢。", [law("第53条", "警车、消防车、救护车、工程救险车执行紧急任务时，可以使用警报器、标志灯具；在确保安全的前提下，不受行驶路线、行驶方向、行驶速度和信号灯的限制，其他车辆和行人应当让行。")], phase=2, band="common"),
    single("drive.s1.rules.024", RUL, "没有道路中心线的城市道路，最高时速不得超过？", [("A", "30公里", True), ("B", "40公里", False), ("C", "50公里", False), ("D", "70公里", False)], "城市没中心线是30，公路才是40。", [reg("第45条", "没有道路中心线的道路，城市道路为每小时30公里，公路为每小时40公里。")], phase=2, band="hot"),
    single("drive.s1.rules.025", RUL, "没有道路中心线的公路，最高时速不得超过？", [("A", "30公里", False), ("B", "40公里", True), ("C", "50公里", False), ("D", "70公里", False)], "公路没中心线是40。", [reg("第45条", "没有道路中心线的道路，城市道路为每小时30公里，公路为每小时40公里。")], phase=2, band="hot"),
    single("drive.s1.rules.026", RUL, "同方向只有1条机动车道的城市道路，最高时速不得超过？", [("A", "30公里", False), ("B", "50公里", True), ("C", "70公里", False), ("D", "80公里", False)], "城市单车道50，不是70。", [reg("第45条", "同方向只有1条机动车道的道路，城市道路为每小时50公里，公路为每小时70公里。")], phase=2, band="hot"),
    single("drive.s1.rules.027", RUL, "同方向只有1条机动车道的公路，最高时速不得超过？", [("A", "50公里", False), ("B", "70公里", True), ("C", "80公里", False), ("D", "100公里", False)], "公路单车道70。", [reg("第45条", "同方向只有1条机动车道的道路，城市道路为每小时50公里，公路为每小时70公里。")], phase=2, band="hot"),
    single("drive.s1.rules.028", RUL, "同方向有2条以上机动车道的城市道路，最高时速不得超过？", [("A", "50公里", False), ("B", "60公里", False), ("C", "70公里", True), ("D", "80公里", False)], "城市多车道70，公路才是80。", [reg("第45条", "同方向有2条以上机动车道的道路，城市道路为每小时70公里，公路为每小时80公里。")], phase=2, band="hot"),
    single("drive.s1.rules.029", RUL, "同方向有2条以上机动车道的公路，最高时速不得超过？", [("A", "70公里", False), ("B", "80公里", True), ("C", "100公里", False), ("D", "120公里", False)], "公路多车道80，不是高速的120。", [reg("第45条", "同方向有2条以上机动车道的道路，城市道路为每小时70公里，公路为每小时80公里。")], phase=2, band="hot"),
    judge("drive.s1.rules.030", RUL, "道路上有限速标志的，应当按照限速标志标明的速度行驶。", True, "有牌子听牌子，条例第45条先写这一句。", [reg("第45条", "机动车在道路上行驶不得超过限速标志、标线标明的速度。")], phase=2, band="hot"),
    judge("drive.s1.rules.031", RUL, "通过急弯路、窄路、窄桥、铁路道口时，最高行驶速度不得超过每小时30公里。", True, "条例第46条把这些场面的上限写成30。", [reg("第46条", "进出非机动车道，通过铁路道口、急弯路、窄路、窄桥时，最高行驶速度不得超过每小时30公里。")], phase=2, band="hot"),
    judge("drive.s1.rules.032", RUL, "掉头、转弯、下陡坡时，最高行驶速度不得超过每小时30公里。", True, "条例第46条。", [reg("第46条", "掉头、转弯、下陡坡时，最高行驶速度不得超过每小时30公里。")], phase=2, band="common"),
    judge("drive.s1.rules.033", RUL, "在冰雪、泥泞的道路上行驶时，最高行驶速度不得超过每小时30公里。", True, "条例第46条。", [reg("第46条", "在冰雪、泥泞的道路上行驶时，最高行驶速度不得超过每小时30公里。")], phase=2, band="hot"),
    judge("drive.s1.rules.034", RUL, "在没有中心隔离设施或者没有中心线的道路上会车，应当减速靠右通行。", True, "会车先减速靠右，不要占中。", [reg("第48条", "在没有中心隔离设施或者没有中心线的道路上，机动车遇相对方向来车时应当减速靠右通行。")], phase=2, band="hot"),
    judge("drive.s1.rules.035", RUL, "机动车可以在铁路道口、人行横道、桥梁、急弯、陡坡、隧道掉头。", False, "条例第49条把这些地点列为不得掉头。", [reg("第49条", "机动车在有禁止掉头或者禁止左转弯标志、标线的地点以及在铁路道口、人行横道、桥梁、急弯、陡坡、隧道或者容易发生危险的路段，不得掉头。")], phase=2, band="hot"),
    judge("drive.s1.rules.036", RUL, "准备进入环形路口时，应当让已在路口内的机动车先行。", True, "进环岛让环内的车，条例第51条。", [reg("第51条", "准备进入环形路口的让已在路口内的机动车先行。")], phase=2, band="hot"),
    judge("drive.s1.rules.037", RUL, "在没有方向指示信号灯的交叉路口，转弯的机动车应当让直行的车辆、行人先行。", True, "转弯让直行。", [reg("第51条", "在没有方向指示信号灯的交叉路口，转弯的机动车让直行的车辆、行人先行。")], phase=2, band="hot"),
    judge("drive.s1.rules.038", RUL, "没有交通信号灯也没有交通警察指挥的交叉路口，没有标志标线控制时，应当让右方道路的来车先行。", True, "条例第52条：停一下，让右边的。", [reg("第52条", "没有交通标志、标线控制的，在进入路口前停车瞭望，让右方道路的来车先行。")], phase=2, band="hot"),
    judge("drive.s1.rules.039", RUL, "没有交通信号灯控制的交叉路口，转弯的机动车应当让直行的车辆先行。", True, "条例第52条同样写了转弯让直行。", [reg("第52条", "转弯的机动车让直行的车辆先行。")], phase=2, band="hot"),
    judge("drive.s1.rules.040", RUL, "前方交叉路口交通阻塞时，可以进入路口等候。", False, "应当停在路口以外，不要把路口堵死。", [reg("第53条", "机动车遇有前方交叉路口交通阻塞时，应当依次停在路口以外等候，不得进入路口。")], phase=2, band="hot"),
    judge("drive.s1.rules.041", RUL, "遇有前方机动车停车排队等候时，不得在人行横道、网状线区域内停车等候。", True, "黄网格和人行横道不是停车场。", [reg("第53条", "不得在人行横道、网状线区域内停车等候。")], phase=2, band="hot"),
    judge("drive.s1.rules.042", RUL, "车道减少的路段排队时，应当每车道一辆依次交替驶入。", True, "拉链通行，条例第53条。", [reg("第53条", "机动车在车道减少的路口、路段，遇有前方机动车停车排队等候或者缓慢行驶的，应当每车道一辆依次交替驶入车道减少后的路口、路段。")], phase=2, band="common"),
    judge("drive.s1.rules.043", RUL, "相对方向行驶时，右转弯的机动车应当让左转弯的车辆先行。", True, "条例第51、52条都写了这一句。", [reg("第52条", "相对方向行驶的右转弯的机动车让左转弯的车辆先行。")], phase=2, band="common"),
    judge("drive.s1.rules.044", RUL, "向左转弯时，应当靠路口中心点左侧转弯。", True, "条例第51条，不要大圈占对面。", [reg("第51条", "向左转弯时，靠路口中心点左侧转弯。")], phase=2, band="common"),
    judge("drive.s1.rules.045", RUL, "在划有导向车道的路口，可以随意选择车道再在路口内变道。", False, "按要去的方向提前进导向车道。", [reg("第51条", "在划有导向车道的路口，按所需行进方向驶入导向车道。")], phase=2, band="hot"),
    judge("drive.s1.alcohol.013", ALC, "连续驾驶机动车超过4小时未停车休息，或者停车休息时间少于20分钟，不得这样驾驶。", True, "条例第62条把超时驾驶写成禁止行为。", [reg("第62条", "连续驾驶机动车超过4小时未停车休息或者停车休息时间少于20分钟。")], phase=1, band="hot"),
    judge("drive.s1.alcohol.014", ALC, "在机动车驾驶室的前后窗范围内可以悬挂妨碍驾驶人视线的物品。", False, "条例第62条禁止悬挂、放置妨碍视线的物品。", [reg("第62条", "在机动车驾驶室的前后窗范围内悬挂、放置妨碍驾驶人视线的物品。")], phase=1, band="common"),
    judge("drive.s1.alcohol.015", ALC, "车门、车厢没有关好时，不得行车。", True, "条例第62条。", [reg("第62条", "在车门、车厢没有关好时行车。")], phase=1, band="common"),
    judge("drive.s1.alcohol.016", ALC, "可以向道路上抛撒物品。", False, "条例第62条禁止向道路上抛撒物品。", [reg("第62条", "向道路上抛撒物品。")], phase=1, band="regular"),
    single("drive.s1.alcohol.017", ALC, "饮酒后驾驶机动车，除暂扣驾驶证外，还应当并处多少罚款？", [("A", "二百元以上五百元以下", False), ("B", "五百元以上一千元以下", False), ("C", "一千元以上二千元以下", True), ("D", "二千元以上五千元以下", False)], "第91条：暂扣六个月，并处一千到二千。", [law("第91条", "饮酒后驾驶机动车的，处暂扣六个月机动车驾驶证，并处一千元以上二千元以下罚款。")], phase=1, band="hot"),
    single("drive.s1.alcohol.018", ALC, "饮酒后驾驶机动车，暂扣机动车驾驶证的期限是？", [("A", "一个月", False), ("B", "三个月", False), ("C", "六个月", True), ("D", "十二个月", False)], "饮酒暂扣六个月；醉酒是吊销。", [law("第91条", "饮酒后驾驶机动车的，处暂扣六个月机动车驾驶证。")], phase=1, band="hot"),
    judge("drive.s1.alcohol.019", ALC, "醉酒驾驶机动车的，由公安机关交通管理部门约束至酒醒，吊销机动车驾驶证。", True, "醉酒不是罚款了事。", [law("第91条", "醉酒驾驶机动车的，由公安机关交通管理部门约束至酒醒，吊销机动车驾驶证。")], phase=1, band="hot"),
    judge("drive.s1.alcohol.020", ALC, "患有妨碍安全驾驶机动车的疾病的，不得驾驶机动车。", True, "第22条和饮酒、疲劳写在一起。", [law("第22条", "患有妨碍安全驾驶机动车的疾病……不得驾驶机动车。")], phase=1, band="common"),
    judge("drive.s1.signals.014", SIG, "绿灯亮时，准许车辆通行，但转弯车辆不得妨碍被放行的直行车辆、行人通过。", True, "绿灯可以走，转弯仍要让直行和行人。", [reg("第38条", "绿灯亮时，准许车辆通行，但转弯的车辆不得妨碍被放行的直行车辆、行人通过。")], phase=3, band="hot"),
    judge("drive.s1.signals.015", SIG, "黄灯亮时，已越过停止线的车辆可以继续通行。", True, "还没过线就应当停；已经过线可以继续。", [reg("第38条", "黄灯亮时，已越过停止线的车辆可以继续通行。")], phase=3, band="hot"),
    judge("drive.s1.signals.016", SIG, "红灯亮时，禁止车辆通行。", True, "条例第38条。", [reg("第38条", "红灯亮时，禁止车辆通行。")], phase=3, band="hot"),
    judge("drive.s1.signals.017", SIG, "红灯亮时，右转弯的车辆在不妨碍被放行的车辆、行人通行的情况下，可以通行。", True, "可以右转，前提是不挡正在放行的车和人。", [reg("第38条", "红灯亮时，右转弯的车辆在不妨碍被放行的车辆、行人通行的情况下，可以通行。")], phase=3, band="hot"),
    judge("drive.s1.signals.018", SIG, "红灯亮时，只要路口没有行人，就可以直行通过。", False, "红灯禁止通行；不妨碍被放行对象时只允许右转。", [reg("第38条", "红灯亮时，禁止车辆通行。")], phase=3, band="hot"),
    judge("drive.s1.signals.019", SIG, "交通信号灯与交通警察指挥不一致时，应当按交通信号灯通行。", False, "有警察在现场，听警察的。", [law("第38条", "遇有交通警察现场指挥时，应当按照交通警察的指挥通行。")], phase=3, band="hot"),
    judge("drive.s1.signals.020", SIG, "路口设有停车让行标志时，应当停车瞭望，确认安全后再通行。", True, "停车让行是先停住，不是减速晃一眼。", [gb("停车让行", "停车让行：车辆应当停车瞭望，确认安全后才准许通行。")], phase=3, band="hot"),
    judge("drive.s1.signals.021", SIG, "路口设有减速让行标志时，应当减速瞭望；确认安全后可以不停车通过。", True, "减速让行不必一律停车；必须停车的是停车让行。", [gb("减速让行", "减速让行：车辆应当减速瞭望，确认安全后才准许通行。")], phase=3, band="hot"),
    single("drive.s1.signals.022", SIG, "停车让行和减速让行的关键差别是？", [("A", "前者必须停车确认安全，后者减速观察后安全可不停车", True), ("B", "两者都必须停车", False), ("C", "两者都可以不停车直接过", False), ("D", "只是颜色不同，做法一样", False)], "一个先停，一个先慢。认错了就会在路口抢行。", [gb("停车让行 / 减速让行", "停车让行须停车瞭望；减速让行减速瞭望，安全后可以不停车通过。")], phase=3, band="hot"),
    judge("drive.s1.signals.023", SIG, "路段设有限速标志时，最高行驶速度不得超过标志标明的数值。", True, "红圈里的数字就是上限。", [law("第42条", "机动车上道路行驶，不得超过限速标志标明的最高时速。"), gb("限制速度", "限制速度标志表示最高时速不得超过标志所示数值。")], phase=3, band="hot"),
    judge("drive.s1.signals.024", SIG, "道路入口设有禁止驶入标志时，可以从该方向驶入。", False, "禁止驶入就是这个方向不能进。", [gb("禁止驶入", "禁止驶入表示禁止车辆从该方向驶入。")], phase=3, band="hot"),
    judge("drive.s1.signals.025", SIG, "设有禁止超车标志的路段，对向没有来车时可以超车。", False, "有禁止超车标志就不得超。", [gb("禁止超车", "禁止超车表示该路段禁止超车。"), law("第43条", "行经没有超车条件的路段，不得超车。")], phase=3, band="hot"),
    judge("drive.s1.signals.026", SIG, "设有禁止掉头标志的地点，可以掉头。", False, "有禁止掉头标志就不得掉头。", [gb("禁止掉头", "禁止掉头表示该地点禁止机动车掉头。"), reg("第49条", "机动车在有禁止掉头或者禁止左转弯标志、标线的地点……不得掉头。")], phase=3, band="hot"),
    judge("drive.s1.signals.027", SIG, "路口设有禁止向左转弯标志时，可以向左转弯。", False, "禁令就是不准左拐。", [gb("禁止向左转弯", "禁止向左转弯表示该路口禁止机动车向左转弯。")], phase=3, band="common"),
    judge("drive.s1.signals.028", SIG, "路口设有直行标志时，只准直行，不得左右转弯。", True, "蓝底直行箭头是只准直行。", [gb("直行", "直行标志表示只准车辆直行。")], phase=3, band="hot"),
    judge("drive.s1.signals.029", SIG, "设有禁止鸣喇叭标志的路段，可以用鸣喇叭催促前车。", False, "禁鸣路段不得鸣喇叭。", [gb("禁止鸣喇叭", "禁止鸣喇叭表示禁止机动车鸣喇叭。"), reg("第62条", "在禁止鸣喇叭的区域或者路段鸣喇叭。")], phase=3, band="common"),
    judge("drive.s1.signals.030", SIG, "看到注意儿童、注意行人标志，应当减速行驶，注意观察。", True, "警告标志是提醒减速观察，不是加速抢过去。", [gb("注意儿童 / 注意行人", "表示前方注意儿童或行人，应当减速并注意观察。")], phase=3, band="hot"),
    judge("drive.s1.signals.031", SIG, "看到施工标志，应当减速慢行。", True, "施工路段按警告减速。", [gb("施工", "施工标志表示前方道路施工，应当减速慢行。")], phase=3, band="hot"),
    judge("drive.s1.signals.032", SIG, "看到急弯路标志，应当减速行驶，不得在弯道超车。", True, "弯道没有超车条件。", [gb("急弯路", "急弯路标志表示前方有急弯，应当减速。"), law("第43条", "行经弯道等没有超车条件的路段，不得超车。")], phase=3, band="common"),
    judge("drive.s1.signals.033", SIG, "设有禁止停放车辆标志的路段，可以临时停一下上下客。", False, "禁止停放连临时停也不行。", [gb("禁止停放车辆", "禁止停放车辆表示禁止车辆停放和临时停车。"), law("第56条", "在设有禁停标志、标线的路段，不得停车。")], phase=3, band="hot"),
    judge("drive.s1.signals.034", SIG, "设有禁止停车标志的路段，不得停车。", True, "有禁停标志就不要停。", [gb("禁止停车", "禁止停车表示禁止车辆停放。"), law("第56条", "在设有禁停标志、标线的路段，不得停车。")], phase=3, band="hot"),
    judge("drive.s1.highway.014", HWY, "在高速公路上行驶的小型载客汽车最高车速不得超过每小时120公里。", True, "条例第78条把小客车上限定在120。", [reg("第78条", "在高速公路上行驶的小型载客汽车最高车速不得超过每小时120公里。")], phase=4, band="hot"),
    judge("drive.s1.highway.015", HWY, "同方向有2条车道的高速公路，左侧车道的最低车速为每小时100公里。", True, "慢了请走右侧车道。", [reg("第78条", "同方向有2条车道的，左侧车道的最低车速为每小时100公里。")], phase=4, band="common"),
    judge("drive.s1.highway.016", HWY, "道路限速标志标明的车速与车道最低车速规定不一致时，按照道路限速标志标明的车速行驶。", True, "牌子优先。", [reg("第78条", "道路限速标志标明的车速与上述车道行驶车速的规定不一致的，按照道路限速标志标明的车速行驶。")], phase=4, band="common"),
    judge("drive.s1.highway.017", HWY, "从匝道驶入高速公路，应当开启左转向灯，在加速车道提高车速，在不妨碍已在高速公路内车辆通行的情况下驶入行车道。", True, "加速车道是用来加速的，不是直接插进去。", [reg("第79条", "机动车从匝道驶入高速公路，应当开启左转向灯，在不妨碍已在高速公路内的机动车正常行驶的情况下驶入车道。")], phase=4, band="hot"),
    judge("drive.s1.highway.018", HWY, "驶离高速公路，应当提前开启右转向灯，驶入减速车道，降低车速后驶离。", True, "先进入减速车道再下匝道。", [reg("第79条", "机动车驶离高速公路时，应当开启右转向灯，驶入减速车道，降低车速后驶离。")], phase=4, band="hot"),
    judge("drive.s1.highway.019", HWY, "机动车在高速公路上可以在应急车道内行驶、停车，以便更快到达出口。", False, "非紧急情况不得在应急车道行驶或停车。", [reg("第82条", "非紧急情况时在应急车道行驶或者停车。")], phase=4, band="hot"),
    judge("drive.s1.highway.020", HWY, "机动车不得在高速公路上试车或者学习驾驶机动车。", True, "条例第82条。", [reg("第82条", "不准在高速公路上试车或者学习驾驶机动车。")], phase=4, band="regular"),
    single("drive.s1.highway.021", HWY, "在高速公路上行驶，能见度小于200米时，车速不得超过每小时多少公里？", [("A", "20公里", False), ("B", "40公里", False), ("C", "60公里", True), ("D", "80公里", False)], "小于200米：开雾灯近光示廓前后位和双闪，不超过60。", [reg("第81条", "能见度小于200米时，开启雾灯、近光灯、示廓灯和前后位灯，车速不得超过每小时60公里，与同车道前车保持100米以上的距离。")], phase=4, band="hot"),
    single("drive.s1.highway.022", HWY, "在高速公路上行驶，能见度小于100米时，车速不得超过每小时多少公里？", [("A", "20公里", False), ("B", "40公里", True), ("C", "60公里", False), ("D", "80公里", False)], "小于100米不超过40，并从最近的出口离开。", [reg("第81条", "能见度小于100米时，开启雾灯、近光灯、示廓灯、前后位灯和危险报警闪光灯，车速不得超过每小时40公里，与同车道前车保持50米以上的距离。")], phase=4, band="hot"),
    single("drive.s1.highway.023", HWY, "在高速公路上行驶，能见度小于50米时，车速不得超过每小时多少公里？", [("A", "20公里", True), ("B", "40公里", False), ("C", "60公里", False), ("D", "80公里", False)], "小于50米不超过20，尽快从最近出口离开。", [reg("第81条", "能见度小于50米时，开启雾灯、近光灯、示廓灯、前后位灯和危险报警闪光灯，车速不得超过每小时20公里，并从最近的出口尽快驶离高速公路。")], phase=4, band="hot"),
    judge("drive.s1.highway.024", HWY, "高速公路能见度小于100米时，应当尽快从最近的出口驶离高速公路。", True, "条例第81条在小于100米、小于50米都要求从出口离开。", [reg("第81条", "能见度小于100米时……并从最近的出口尽快驶离高速公路。")], phase=4, band="common"),
    judge("drive.s1.highway.025", HWY, "机动车在高速公路上发生故障不能正常行驶时，可以由其他普通机动车拖曳、牵引。", False, "应当由救援车、清障车拖曳、牵引。", [law("第68条", "机动车在高速公路上发生故障或者交通事故，无法正常行驶的，应当由救援车、清障车拖曳、牵引。")], phase=4, band="common"),
    judge("drive.s1.occupants.013", OCC, "机动车应当在规定地点停放。", True, "第56条。", [law("第56条", "机动车应当在规定地点停放。")], phase=1, band="hot"),
    judge("drive.s1.occupants.014", OCC, "交叉路口、铁路道口、急弯路、宽度不足4米的窄路、桥梁、陡坡、隧道以及距离上述地点50米以内的路段不得停车。", True, "条例第63条，这些地方停下来就是堵人和挡视线。", [reg("第63条", "交叉路口、铁路道口、急弯路、宽度不足4米的窄路、桥梁、陡坡、隧道以及距离上述地点50米以内的路段，不得停车。")], phase=2, band="hot"),
    judge("drive.s1.occupants.015", OCC, "公共汽车站、急救站、加油站、消防栓或者消防队（站）门前以及距离上述地点30米以内的路段，除使用上述设施的以外不得停车。", True, "条例第63条。", [reg("第63条", "公共汽车站、急救站、加油站、消防栓或者消防队（站）门前以及距离上述地点30米以内的路段，除使用上述设施的以外，不得停车。")], phase=2, band="common"),
    judge("drive.s1.occupants.016", OCC, "车辆停稳前不得开车门和上下人员，开关车门不得妨碍其他车辆和行人通行。", True, "条例第63条。", [reg("第63条", "车辆停稳前不得开车门和上下人员，开关车门不得妨碍其他车辆和行人通行。")], phase=1, band="hot"),
    judge("drive.s1.occupants.017", OCC, "在设有禁停标志、标线的路段，人行横道、施工地段不得停车。", True, "条例第63条。", [reg("第63条", "在设有禁停标志、标线的路段，在机动车道与非机动车道、人行道之间设有隔离设施的路段以及人行横道、施工地段，不得停车。")], phase=1, band="hot"),
    judge("drive.s1.highway.026", HWY, "机动车在高速公路上不得在路肩上行驶。", True, "路肩不是行车道。", [reg("第82条", "骑、轧车行道分界线或者在路肩上行驶。")], phase=4, band="hot"),
    judge("drive.s1.occupants.019", OCC, "行人不得跨越、倚坐道路隔离设施。", True, "第63条。开车时也要预行人突然翻护栏。", [law("第63条", "行人不得跨越、倚坐道路隔离设施，不得扒车、强行拦车或者实施妨碍道路交通安全的其他行为。")], phase=1, band="regular"),
    judge("drive.s1.occupants.020", OCC, "机动车临时停车时，不得妨碍其他车辆和行人通行。", True, "第56条第二款。", [law("第56条", "在道路上临时停车的，不得妨碍其他车辆和行人通行。")], phase=1, band="hot"),
    judge("drive.s1.rules.046", RUL, "变更车道的机动车不得影响相关车道内行驶的机动车的正常行驶。", True, "先看后打灯，再变道，不能逼别人刹车。", [reg("第44条", "变更车道的机动车不得影响相关车道内行驶的机动车的正常行驶。")], phase=2, band="hot"),
    judge("drive.s1.rules.047", RUL, "在快速车道行驶未达到快速车道规定的行驶速度的，应当在慢速车道行驶。", True, "左侧不是用来慢悠悠占着。", [reg("第44条", "在快速车道行驶的机动车应当按照快速车道规定的速度行驶，未达到快速车道规定的行驶速度的，应当在慢速车道行驶。")], phase=2, band="common"),
    judge("drive.s1.rules.048", RUL, "摩托车应当在最右侧车道行驶。", True, "条例第44条。", [reg("第44条", "摩托车应当在最右侧车道行驶。")], phase=2, band="regular"),
    judge("drive.s1.rules.049", RUL, "会车有困难时，有让路条件的一方应当让对方先行。", True, "谁好让谁让。", [reg("第48条", "会车有困难的，有让路条件的一方让对方先行。")], phase=2, band="hot"),
    judge("drive.s1.rules.050", RUL, "在有障碍的路段会车，无障碍的一方应当让对方先行。", True, "你这边没挡，让对面先过障碍。", [reg("第48条", "在有障碍的路段，无障碍的一方让对方先行。")], phase=2, band="hot"),
    judge("drive.s1.rules.051", RUL, "在狭窄的坡路会车，下坡的一方一律先行。", False, "通常上坡先行；下坡车已到中途而上坡车还没上坡时，下坡先行。", [reg("第48条", "在狭窄的坡路，上坡的一方先行；但下坡的一方已行至中途而上坡的一方未上坡时，下坡的一方先行。")], phase=2, band="common"),
    judge("drive.s1.rules.052", RUL, "超车前应当提前开启左转向灯，变换使用远、近光灯或者鸣喇叭。", True, "条例第47条，先告诉前车你要超。", [reg("第47条", "机动车超车时，应当提前开启左转向灯、变换使用远、近光灯或者鸣喇叭。")], phase=2, band="hot"),
    judge("drive.s1.rules.053", RUL, "前车遇后车发出超车信号时，在条件许可的情况下，应当降低速度、靠右让路。", True, "被超也不要压着不让。", [reg("第47条", "在没有道路中心线或者同方向只有1条机动车道的道路上，前车遇后车发出超车信号时，在条件许可的情况下，应当降低速度、靠右让路。")], phase=2, band="common"),
    judge("drive.s1.rules.054", RUL, "后车应当在确认有充足的安全距离后，从前车的左侧超越。", True, "超完再合，不要别前车。", [reg("第47条", "后车应当在确认有充足的安全距离后，从前车的左侧超越，超越后在不影响被超越机动车正常行驶的情况下，改回原车道。")], phase=2, band="hot"),
    judge("drive.s1.signals.035", SIG, "遇停止信号时，应当依次停在停止线以外；没有停止线的，停在路口以外。", True, "车头不要压线、不要伸进路口。", [reg("第51条", "遇停止信号时，依次停在停止线以外。没有停止线的，停在路口以外。")], phase=3, band="hot"),
    judge("drive.s1.signals.036", SIG, "向右转弯遇有同车道前车正在等候放行信号时，可以从右侧绕过去。", False, "应当依次停车等候。", [reg("第51条", "向右转弯遇有同车道前车正在等候放行信号时，依次停车等候。")], phase=3, band="hot"),
    judge("drive.s1.highway.027", HWY, "在高速公路上行驶，车速超过每小时100公里时，应当与同车道前车保持100米以上的距离。", True, "跟车太近是高速追尾的主因。", [reg("第80条", "机动车在高速公路上行驶，车速超过每小时100公里时，应当与同车道前车保持100米以上的距离。")], phase=4, band="hot"),
    judge("drive.s1.highway.028", HWY, "在高速公路上行驶，车速低于每小时100公里时，与同车道前车距离不得少于50米。", True, "慢了也要留出50米。", [reg("第80条", "车速低于每小时100公里时，与同车道前车距离不得少于50米。")], phase=4, band="hot"),
    judge("drive.s1.highway.029", HWY, "机动车不得在高速公路匝道、加速车道或者减速车道上超车。", True, "加减速车道是用来变速的。", [reg("第82条", "在匝道、加速车道或者减速车道上超车。")], phase=4, band="hot"),
    judge("drive.s1.occupants.021", OCC, "机动车行驶时，乘坐人员可以不使用安全带，只要驾驶人系了即可。", False, "驾驶人和乘坐人员都要按规定使用安全带。", [law("第51条", "机动车行驶时，驾驶人、乘坐人员应当按规定使用安全带。")], phase=1, band="hot"),
]

S4 = [
    judge("drive.s4.crash.015", CRASH, "造成交通事故后逃逸的，由公安机关交通管理部门吊销机动车驾驶证，且终生不得重新取得机动车驾驶证。", True, "第101条，逃逸不是私事。", [law("第101条", "违反道路交通安全法律、法规的规定，发生重大交通事故，构成犯罪的，依法追究刑事责任，并由公安机关交通管理部门吊销机动车驾驶证。造成交通事故后逃逸的，由公安机关交通管理部门吊销机动车驾驶证，且终生不得重新取得机动车驾驶证。")], phase=1, band="hot"),
    judge("drive.s4.crash.016", CRASH, "未造成人身伤亡、事实清楚、无争议的事故，当事人应当在现场争吵清楚后再离开。", False, "可以即行撤离、恢复交通，自行协商赔偿。", [law("第70条", "未造成人身伤亡，当事人对事实及成因无争议的，可以即行撤离现场，恢复交通，自行协商处理损害赔偿事宜。")], phase=1, band="hot"),
    judge("drive.s4.crash.017", CRASH, "发生交通事故，仅造成轻微财产损失，并且基本事实清楚的，当事人应当先撤离现场再进行协商处理。", True, "第70条第三款，轻微财损先挪车。", [law("第70条", "在道路上发生交通事故，仅造成轻微财产损失，并且基本事实清楚的，当事人应当先撤离现场再进行协商处理。")], phase=1, band="common"),
    judge("drive.s4.lights.011", LIGHT, "夜间会车应当在距相对方向来车150米以外改用近光灯。", True, "条例第48条会车用近光，不要用远光晃对方。", [reg("第48条", "在没有中心隔离设施或者没有中心线的道路上，机动车遇相对方向来车时应当减速靠右通行，并与其他车辆、行人保持必要的安全距离。夜间会车应当在距相对方向来车150米以外改用近光灯。")], phase=1, band="hot"),
    judge("drive.s4.lights.012", LIGHT, "在窄路、窄桥与非机动车会车时应当使用近光灯。", True, "条例第48条。", [reg("第48条", "在窄路、窄桥与非机动车会车时应当使用近光灯。")], phase=1, band="common"),
    judge("drive.s4.lights.013", LIGHT, "机动车驶近急弯、坡道顶端等影响安全视距的路段，应当减速慢行，并鸣喇叭示意。", True, "看不清对面时先慢、先提醒。禁鸣路段除外。", [reg("第59条", "机动车驶近急弯、坡道顶端等影响安全视距的路段以及超车或者遇雾、雨、雪、沙尘、冰雹等低能见度情况时，应当减速慢行，并鸣喇叭示意。")], phase=1, band="common"),
    judge("drive.s4.lights.014", LIGHT, "夜间通过没有交通信号灯控制的路口，应当交替使用远近光灯示意。", True, "用灯光告诉对面你来了。", [reg("第59条", "机动车在夜间通过急弯、坡路、拱桥、人行横道或者没有交通信号灯控制的路口时，应当交替使用远近光灯示意。")], phase=1, band="hot"),
    judge("drive.s4.lights.015", LIGHT, "机动车倒车时，应当察明车后情况，确认安全后倒车。", True, "看不清后面就不要倒。", [reg("第50条", "机动车倒车时，应当察明车后情况，确认安全后倒车。")], phase=1, band="common"),
    judge("drive.s4.weather.009", WX, "能见度在50米以内的雾、雨、雪、沙尘、冰雹天气，最高行驶速度不得超过每小时30公里。", True, "条例第46条，普通道路也按30封顶。", [reg("第46条", "遇雾、雨、雪、沙尘、冰雹，能见度在50米以内时，最高行驶速度不得超过每小时30公里。")], phase=1, band="hot"),
    judge("drive.s4.weather.010", WX, "牵引发生故障的机动车时，最高行驶速度不得超过每小时30公里。", True, "条例第46条。", [reg("第46条", "牵引发生故障的机动车时，最高行驶速度不得超过每小时30公里。")], phase=1, band="regular"),
    judge("drive.s4.weather.011", WX, "高速公路能见度小于200米时，应当与同车道前车保持100米以上的距离。", True, "条例第81条。", [reg("第81条", "能见度小于200米时……与同车道前车保持100米以上的距离。")], phase=1, band="hot"),
    judge("drive.s4.weather.012", WX, "高速公路能见度小于100米时，应当与同车道前车保持50米以上的距离。", True, "条例第81条。", [reg("第81条", "能见度小于100米时……与同车道前车保持50米以上的距离。")], phase=1, band="common"),
    judge("drive.s4.weather.013", WX, "雾天在高速公路上可以开启远光灯以便看清更远。", False, "雾中远光会被散射，应当开雾灯、近光和双闪。", [reg("第81条", "能见度小于200米时，开启雾灯、近光灯、示廓灯和前后位灯。"), reg("第58条", "雾天行驶应当开启雾灯和危险报警闪光灯。")], phase=1, band="hot"),
    judge("drive.s4.emergency.010", EMG, "机动车不得在铁路道口、交叉路口、单行路、桥梁、急弯、陡坡或者隧道中倒车。", True, "条例第50条。", [reg("第50条", "不得在铁路道口、交叉路口、单行路、桥梁、急弯、陡坡或者隧道中倒车。")], phase=1, band="hot"),
    judge("drive.s4.emergency.011", EMG, "机动车在道路上发生故障，需要停车排除故障时，驾驶人应当立即开启危险报警闪光灯。", True, "先双闪，再下车。", [law("第52条", "机动车在道路上发生故障，需要停车排除故障时，驾驶人应当立即开启危险报警闪光灯。")], phase=1, band="hot"),
    single("drive.s4.emergency.012", EMG, "普通道路上发生故障难以移动时，警告标志应设在车后多少米处？", [("A", "10米至20米", False), ("B", "50米至100米", True), ("C", "150米以外", False), ("D", "200米以外", False)], "普通路50到100；150米以外是高速公路。", [reg("第60条", "机动车在道路上发生故障或者发生交通事故，妨碍交通又难以移动的，应当按照规定开启危险报警闪光灯并在车后50米至100米处设置警告标志。")], phase=1, band="hot"),
    single("drive.s4.emergency.013", EMG, "高速公路发生故障时，警告标志应当设置在来车方向多少米以外？", [("A", "50米", False), ("B", "100米", False), ("C", "150米", True), ("D", "200米", False)], "高速是150米以外。", [law("第68条", "并在故障车来车方向一百五十米以外设置警告标志。")], phase=1, band="hot"),
    judge("drive.s4.emergency.014", EMG, "高速公路发生故障后，车上人员应当迅速转移到右侧路肩上或者应急车道内，并且迅速报警。", True, "人先离开行车道。", [law("第68条", "车上人员应当迅速转移到右侧路肩上或者应急车道内，并且迅速报警。")], phase=1, band="hot"),
    judge("drive.s4.aid.009", AID, "过往车辆驾驶人、过往行人看到事故伤亡，应当予以协助。", True, "第70条写成义务，不是看热闹。", [law("第70条", "乘车人、过往车辆驾驶人、过往行人应当予以协助。")], phase=1, band="common"),
    judge("drive.s4.aid.010", AID, "抢救受伤人员需要变动现场时，可以不留痕迹直接把车开走。", False, "变动现场应当标明位置。", [law("第70条", "因抢救受伤人员变动现场的，应当标明位置。")], phase=1, band="hot"),
    judge("drive.s4.lights.016", LIGHT, "超车时应当提前开启左转向灯，变换使用远、近光灯或者鸣喇叭。", True, "夜间超车用变换灯光提醒前车。", [reg("第47条", "机动车超车时，应当提前开启左转向灯、变换使用远、近光灯或者鸣喇叭。")], phase=1, band="common"),
    judge("drive.s4.weather.014", WX, "雨天路面湿滑，应当降低行驶速度，并与前车保持安全距离。", True, "第42条把雨雪雾列为应当减速的情形。", [law("第42条", "遇有沙尘、冰雹、雨、雪、雾、结冰、交通拥堵等情形时，应当降低行驶速度。")], phase=1, band="hot"),
    judge("drive.s4.weather.015", WX, "冰雪道路可以沿用干燥路面的车速，只要抓地感觉还好。", False, "冰雪、泥泞路最高时速30公里。", [reg("第46条", "在冰雪、泥泞的道路上行驶时，最高行驶速度不得超过每小时30公里。")], phase=1, band="hot"),
    judge("drive.s4.emergency.015", EMG, "车辆发生故障后，可以在行车道内坐在车里等救援。", False, "人要转移到安全位置并报警，不要停在行车道里等。", [law("第68条", "车上人员应当迅速转移到右侧路肩上或者应急车道内，并且迅速报警。"), law("第52条", "难以移动的，应当持续开启危险报警闪光灯，并在来车方向设置警告标志等措施扩大示警距离。")], phase=1, band="hot"),
    judge("drive.s4.crash.018", CRASH, "机动车之间发生交通事故，双方都有过错的，按照各自过错的比例分担责任。", True, "不是谁车贵谁有理。", [law("第76条", "机动车之间发生交通事故的，由有过错的一方承担赔偿责任；双方都有过错的，按照各自过错的比例分担责任。")], phase=1, band="common"),
    judge("drive.s4.lights.017", LIGHT, "夜间通过急弯、坡路、拱桥、人行横道或者没有交通信号灯控制的路口，应当交替使用远近光灯示意。", True, "用变换灯光告诉对面你来了。", [reg("第59条", "机动车在夜间通过急弯、坡路、拱桥、人行横道或者没有交通信号灯控制的路口时，应当交替使用远近光灯示意。")], phase=1, band="hot"),
]


def _prompt_key(text: str) -> str:
    return "".join(text.split())


def merge(name: str, extra: list[dict]) -> None:
    path = ROOT / name
    data = json.loads(path.read_text(encoding="utf-8"))
    kept = [q for q in data["questions"] if q["id"] not in DROP]
    seen_id = {q["id"] for q in kept}
    seen_prompt = {_prompt_key(q["prompt"]) for q in kept}
    added = 0
    dropped = len(data["questions"]) - len(kept)
    for item in extra:
        key = _prompt_key(item["prompt"])
        if item["id"] in seen_id or key in seen_prompt:
            continue
        kept.append(item)
        seen_id.add(item["id"])
        seen_prompt.add(key)
        added += 1
    data["questions"] = kept
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{name}: {len(kept)} 题（去掉认名认类 {dropped}，新增 {added}）")


def main() -> None:
    merge("subject1.json", S1)
    merge("subject4.json", S4)


if __name__ == "__main__":
    main()
