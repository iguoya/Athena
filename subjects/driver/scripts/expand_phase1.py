#!/usr/bin/env python3
"""把第一阶段基础题并进题库。只写能指到现行法条/标准的题，不搬商业题库原题。"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "content/questions"
LAW = "https://www.gov.cn/banshi/2005-08/31/content_68700.htm"
REG = "https://www.gov.cn/zhengce/2020-12/25/content_5574205.htm"
ORD = "https://www.gov.cn/zhengce/2021-12/27/content_5712881.htm"
GB = "https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=15B1FC09EE1AE92F1A9EC97BA3C9E451"
GA = "http://jj.ga.zhuhai.gov.cn/ConvenienceGuide/Details/173"


def ref(source_id: str, locator: str, url: str, note: str, relation: str = "quoted") -> dict:
    return {
        "source_id": source_id,
        "relation": relation,
        "locator": locator,
        "url": url,
        "note": note,
    }


def judge(qid: str, topic: str, prompt: str, ok: bool, explain: str, source_refs: list, difficulty: int = 1) -> dict:
    return {
        "id": qid,
        "topic_id": topic,
        "kind": "judge",
        "difficulty": difficulty,
        "phase": 1,
        "prompt": prompt,
        "choices": [
            {"id": "T", "label": "正确", "ok": ok},
            {"id": "F", "label": "错误", "ok": not ok},
        ],
        "explain": explain,
        "source_refs": source_refs,
    }


def single(qid: str, topic: str, prompt: str, options: list[tuple[str, str, bool]], explain: str, source_refs: list, difficulty: int = 1) -> dict:
    return {
        "id": qid,
        "topic_id": topic,
        "kind": "single",
        "difficulty": difficulty,
        "phase": 1,
        "prompt": prompt,
        "choices": [{"id": i, "label": label, "ok": ok} for i, label, ok in options],
        "explain": explain,
        "source_refs": source_refs,
    }


S1 = [
    judge("drive.s1.license.009", "drive.s1.license", "未取得机动车驾驶证，不得驾驶机动车。", True, "第19条把取得驾驶证规定为驾驶机动车的前提。", [ref("road-safety-law", "第19条", LAW, "驾驶机动车，应当依法取得机动车驾驶证。")]),
    judge("drive.s1.license.010", "drive.s1.license", "驾驶人可以驾驶驾驶证载明准驾车型以外的机动车。", False, "第19条要求按照驾驶证载明的准驾车型驾驶。", [ref("road-safety-law", "第19条", LAW, "驾驶人应当按照驾驶证载明的准驾车型驾驶机动车。")]),
    judge("drive.s1.license.011", "drive.s1.license", "机动车经公安机关交通管理部门登记后，方可上道路行驶。", True, "第8条把登记作为上道路行驶的条件。", [ref("road-safety-law", "第8条", LAW, "国家对机动车实行登记制度。机动车经公安机关交通管理部门登记后，方可上道路行驶。")]),
    single("drive.s1.license.012", "drive.s1.license", "初次申领机动车驾驶证后，实习期是多久？", [("A", "6个月", False), ("B", "12个月", True), ("C", "24个月", False), ("D", "没有实习期", False)], "公安部令第162号规定初次申请和增加准驾车型后的12个月为实习期。", [ref("license-order-162", "第64条", ORD, "机动车驾驶人初次申请机动车驾驶证和增加准驾车型后的12个月为实习期。")]),
    judge("drive.s1.license.013", "drive.s1.license", "实习期驾驶人驾驶机动车上高速公路，可以由任何持证驾驶人陪同。", False, "陪同人须持相应或者包含其准驾车型驾驶证三年以上。", [ref("license-order-162", "第65条", ORD, "实习期驾驶人驾驶机动车上高速公路，应当由持相应或者包含其准驾车型驾驶证三年以上的驾驶人陪同。")], 2),
    judge("drive.s1.license.014", "drive.s1.license", "科目一考试满分100分，90分合格。", True, "公安部令第162号第38条。", [ref("license-order-162", "第38条", ORD, "科目一、科目二、科目三道路驾驶技能和安全文明驾驶常识考试满分为100分，科目一、科目三安全文明驾驶常识考试合格标准为90分。")]),
    judge("drive.s1.license.015", "drive.s1.license", "小型汽车科目一考试为100道题、45分钟。", True, "GA 1026 对小型汽车科目一题量和时长的规定。", [ref("ga-1026", "小型汽车科目一", GA, "小型汽车科目一 100 题、45 分钟。")]),
    judge("drive.s1.rules.010", "drive.s1.rules", "机动车、非机动车实行右侧通行。", True, "道路交通安全法第35条。", [ref("road-safety-law", "第35条", LAW, "机动车、非机动车实行右侧通行。")]),
    judge("drive.s1.rules.011", "drive.s1.rules", "没有交通信号的交叉路口，机动车可以不减速直接通过。", False, "第44条要求减速慢行，并让行人和优先通行的车辆先行。", [ref("road-safety-law", "第44条", LAW, "通过没有交通信号灯、交通标志、交通标线或者交通警察指挥的交叉路口时，应当减速慢行，并让行人和优先通行的车辆先行。")]),
    single("drive.s1.rules.012", "drive.s1.rules", "机动车通过有交通信号灯的交叉路口，应当按什么通行？", [("A", "只看旁边车辆", False), ("B", "交通信号灯、交通标志、交通标线或者交通警察的指挥", True), ("C", "谁快谁先", False), ("D", "一律停车等待", False)], "第44条把信号、标志、标线和警察指挥并列。", [ref("road-safety-law", "第44条", LAW, "机动车通过交叉路口，应当按照交通信号灯、交通标志、交通标线或者交通警察的指挥通过。")]),
    judge("drive.s1.rules.013", "drive.s1.rules", "机动车行经人行横道，应当减速行驶；遇行人正在通过，应当停车让行。", True, "第47条。", [ref("road-safety-law", "第47条", LAW, "机动车行经人行横道时，应当减速行驶；遇行人正在通过人行横道，应当停车让行。")]),
    judge("drive.s1.rules.014", "drive.s1.rules", "没有道路中心线的城市道路，最高时速为30公里。", True, "实施条例第45条。", [ref("road-safety-regulation", "第45条", REG, "没有道路中心线的道路，城市道路为每小时30公里。")]),
    judge("drive.s1.rules.015", "drive.s1.rules", "同方向只有1条机动车道的城市道路，最高时速为70公里。", False, "城市道路为每小时50公里，公路才是70公里。", [ref("road-safety-regulation", "第45条", REG, "同方向只有1条机动车道的道路，城市道路为每小时50公里，公路为每小时70公里。")], 2),
    judge("drive.s1.rules.016", "drive.s1.rules", "机动车超车应当从左侧超越。", True, "实施条例对超车路径的基本要求。", [ref("road-safety-regulation", "第47条", REG, "机动车超车时，应当提前开启左转向灯、变换使用远、近光灯或者鸣喇叭。在没有道路中心线或者同方向只有1条机动车道的道路上，前车遇后车发出超车信号时，在条件许可的情况下，应当降低速度、靠右让路。后车应当在确认有充足的安全距离后，从前车的左侧超越。")]),
    judge("drive.s1.alcohol.008", "drive.s1.alcohol", "饮酒后不得驾驶机动车。", True, "第22条。", [ref("road-safety-law", "第22条", LAW, "饮酒、服用国家管制的精神药品或者麻醉药品，或者患有妨碍安全驾驶机动车的疾病，或者过度疲劳影响安全驾驶的，不得驾驶机动车。")]),
    judge("drive.s1.alcohol.009", "drive.s1.alcohol", "服用国家管制的精神药品后，只要自我感觉良好就可以开车。", False, "第22条直接禁止，不以自我感觉为准。", [ref("road-safety-law", "第22条", LAW, "服用国家管制的精神药品或者麻醉药品……不得驾驶机动车。")]),
    judge("drive.s1.alcohol.010", "drive.s1.alcohol", "过度疲劳影响安全驾驶的，不得驾驶机动车。", True, "第22条把过度疲劳与饮酒并列。", [ref("road-safety-law", "第22条", LAW, "过度疲劳影响安全驾驶的，不得驾驶机动车。")]),
    judge("drive.s1.alcohol.011", "drive.s1.alcohol", "不得驾驶安全设施不全或者机件不符合技术标准等具有安全隐患的机动车。", True, "第21条。", [ref("road-safety-law", "第21条", LAW, "不得驾驶安全设施不全或者机件不符合技术标准等具有安全隐患的机动车。")]),
    judge("drive.s1.alcohol.012", "drive.s1.alcohol", "醉酒驾驶机动车只会罚款，不会吊销驾驶证。", False, "第91条对醉酒驾驶规定吊销机动车驾驶证等处罚。", [ref("road-safety-law", "第91条", LAW, "醉酒驾驶机动车的，由公安机关交通管理部门约束至酒醒，吊销机动车驾驶证。")], 2),
    judge("drive.s1.signals.009", "drive.s1.signals", "车辆、行人应当按照交通信号通行；遇交通警察现场指挥时，应当按照交通警察的指挥通行。", True, "第38条。", [ref("road-safety-law", "第38条", LAW, "车辆、行人应当按照交通信号通行；遇有交通警察现场指挥时，应当按照交通警察的指挥通行。")]),
    judge("drive.s1.signals.010", "drive.s1.signals", "禁令标志的基本形状是圆形，颜色以红圈白底为主。", True, "GB 5768.2 对禁令标志形状与颜色的分类。", [ref("gb5768-2", "禁令标志", GB, "禁令标志一般为圆形、白底、红圈红杠。", "adapted")]),
    judge("drive.s1.signals.011", "drive.s1.signals", "警告标志的基本形状是等边三角形，黄底黑边。", True, "GB 5768.2 对警告标志的分类。", [ref("gb5768-2", "警告标志", GB, "警告标志为等边三角形、黄底黑边黑图案。", "adapted")]),
    judge("drive.s1.signals.012", "drive.s1.signals", "指示标志通常是黄底黑边三角形。", False, "指示标志是蓝底白图案；黄底三角形是警告标志。", [ref("gb5768-2", "指示标志", GB, "指示标志一般为圆形、矩形，蓝底白图案。", "adapted")]),
    judge("drive.s1.signals.013", "drive.s1.signals", "没有交通信号的道路，应当在确保安全、畅通的原则下通行。", True, "第38条后半句。", [ref("road-safety-law", "第38条", LAW, "在没有交通信号的道路上，应当在确保安全、畅通的原则下通行。")]),
    judge("drive.s1.highway.009", "drive.s1.highway", "行人不得进入高速公路。", True, "第67条。", [ref("road-safety-law", "第67条", LAW, "行人、非机动车、拖拉机、轮式专用机械车、铰接式客车、全挂拖斗车以及其他设计最高时速低于七十公里的机动车，不得进入高速公路。")]),
    judge("drive.s1.highway.010", "drive.s1.highway", "非机动车可以进入高速公路行驶。", False, "第67条明确非机动车不得进入。", [ref("road-safety-law", "第67条", LAW, "行人、非机动车……不得进入高速公路。")]),
    judge("drive.s1.highway.011", "drive.s1.highway", "高速公路限速标志标明的最高时速不得超过120公里。", True, "第67条。", [ref("road-safety-law", "第67条", LAW, "高速公路限速标志标明的最高时速不得超过一百二十公里。")]),
    judge("drive.s1.highway.012", "drive.s1.highway", "在高速公路上行驶，最低时速不得低于60公里。", True, "实施条例第78条。", [ref("road-safety-regulation", "第78条", REG, "高速公路应当标明车道的行驶速度，最高车速不得超过每小时120公里，最低车速不得低于每小时60公里。")]),
    judge("drive.s1.highway.013", "drive.s1.highway", "机动车在高速公路上发生故障时，警告标志应当设置在故障车来车方向150米以外。", True, "第68条。", [ref("road-safety-law", "第68条", LAW, "机动车在高速公路上发生故障时……并在故障车来车方向一百五十米以外设置警告标志。")]),
    judge("drive.s1.occupants.008", "drive.s1.occupants", "机动车行驶时，驾驶人、乘坐人员应当按规定使用安全带。", True, "第51条。", [ref("road-safety-law", "第51条", LAW, "机动车行驶时，驾驶人、乘坐人员应当按规定使用安全带。")]),
    judge("drive.s1.occupants.009", "drive.s1.occupants", "摩托车驾驶人应当按规定戴安全头盔。", True, "第51条。", [ref("road-safety-law", "第51条", LAW, "摩托车驾驶人及乘坐人员应当按规定戴安全头盔。")]),
    judge("drive.s1.occupants.010", "drive.s1.occupants", "在设有禁停标志的路段，只要停一会儿上下客就可以。", False, "第56条禁止在禁停路段停车。", [ref("road-safety-law", "第56条", LAW, "机动车应当在规定地点停放。禁止在人行道上停放机动车；在设有禁停标志、标线的路段，不得停车。")]),
    judge("drive.s1.occupants.011", "drive.s1.occupants", "行人通过路口或者横过道路，应当走人行横道或者过街设施。", True, "第62条。", [ref("road-safety-law", "第62条", LAW, "行人通过路口或者横过道路，应当走人行横道或者过街设施。")]),
    judge("drive.s1.occupants.012", "drive.s1.occupants", "机动车可以在人行道上停放。", False, "第56条禁止在人行道上停放机动车。", [ref("road-safety-law", "第56条", LAW, "禁止在人行道上停放机动车。")]),
]

S4 = [
    judge("drive.s4.crash.011", "drive.s4.crash", "在道路上发生交通事故，车辆驾驶人应当立即停车，保护现场。", True, "第70条。", [ref("road-safety-law", "第70条", LAW, "在道路上发生交通事故，车辆驾驶人应当立即停车，保护现场。")]),
    judge("drive.s4.crash.012", "drive.s4.crash", "造成人身伤亡的，车辆驾驶人应当立即抢救受伤人员，并迅速报告执勤的交通警察或者公安机关交通管理部门。", True, "第70条。", [ref("road-safety-law", "第70条", LAW, "造成人身伤亡的，车辆驾驶人应当立即抢救受伤人员，并迅速报告执勤的交通警察或者公安机关交通管理部门。")]),
    judge("drive.s4.crash.013", "drive.s4.crash", "未造成人身伤亡，事实清楚、无争议的，当事人可以先撤离现场再自行协商处理损害赔偿。", True, "第70条第二款。", [ref("road-safety-law", "第70条", LAW, "在道路上发生交通事故，未造成人身伤亡，当事人对事实及成因无争议的，可以即行撤离现场，恢复交通，自行协商处理损害赔偿事宜。")]),
    judge("drive.s4.crash.014", "drive.s4.crash", "机动车发生故障难以移动时，应当持续开启危险报警闪光灯，并在来车方向设置警告标志。", True, "第52条。", [ref("road-safety-law", "第52条", LAW, "难以移动的，应当持续开启危险报警闪光灯，并在来车方向设置警告标志等措施扩大示警距离。")]),
    judge("drive.s4.lights.007", "drive.s4.lights", "向左转弯、向左变更车道、准备超车、驶离停车地点或者掉头时，应当提前开启左转向灯。", True, "实施条例第57条。", [ref("road-safety-regulation", "第57条", REG, "向左转弯、向左变更车道、准备超车、驶离停车地点或者掉头时，应当提前开启左转向灯。")]),
    judge("drive.s4.lights.008", "drive.s4.lights", "向右转弯、向右变更车道、超车完毕驶回原车道、靠路边停车时，应当提前开启右转向灯。", True, "实施条例第57条。", [ref("road-safety-regulation", "第57条", REG, "向右转弯、向右变更车道、超车完毕驶回原车道、靠路边停车时，应当提前开启右转向灯。")]),
    judge("drive.s4.lights.009", "drive.s4.lights", "在雾天行驶，应当开启雾灯、示廓灯、前照灯、危险报警闪光灯和后雾灯。", True, "实施条例第58条。", [ref("road-safety-regulation", "第58条", REG, "在雾天行驶时，应当开启雾灯和危险报警闪光灯。")]),
    judge("drive.s4.lights.010", "drive.s4.lights", "夜间没有路灯、照明不良时，应当开启前照灯、示廓灯和后位灯。", True, "实施条例第58条。", [ref("road-safety-regulation", "第58条", REG, "夜间没有路灯、照明不良或者遇有雾、雨、雪、沙尘、冰雹等低能见度情况下，应当开启前照灯、示廓灯和后位灯。")]),
    judge("drive.s4.weather.006", "drive.s4.weather", "能见度低时，应当按规定开启灯光并降低行驶速度。", True, "第42条要求根据能见度降低速度；第58条要求开启相应灯光。", [ref("road-safety-law", "第42条", LAW, "机动车上道路行驶，不得超过限速标志标明的最高时速。在没有限速标志的路段，应当保持安全车速。夜间行驶或者在容易发生危险的路段行驶，以及遇有沙尘、冰雹、雨、雪、雾、结冰、交通拥堵等情形时，应当降低行驶速度。"), ref("road-safety-regulation", "第58条", REG, "雾、雨、雪、沙尘、冰雹等低能见度情况下应当开启前照灯、示廓灯和后位灯。")]),
    judge("drive.s4.weather.007", "drive.s4.weather", "夜间行驶应当降低行驶速度。", True, "第42条。", [ref("road-safety-law", "第42条", LAW, "夜间行驶或者在容易发生危险的路段行驶……应当降低行驶速度。")]),
    judge("drive.s4.weather.008", "drive.s4.weather", "遇有交通拥堵时，可以不降低行驶速度抢行。", False, "第42条把交通拥堵列为应当降低行驶速度的情形。", [ref("road-safety-law", "第42条", LAW, "遇有沙尘、冰雹、雨、雪、雾、结冰、交通拥堵等情形时，应当降低行驶速度。")]),
    judge("drive.s4.emergency.007", "drive.s4.emergency", "机动车在道路上发生故障，需要停车排除故障时，驾驶人应当立即开启危险报警闪光灯。", True, "第52条。", [ref("road-safety-law", "第52条", LAW, "机动车在道路上发生故障，需要停车排除故障时，驾驶人应当立即开启危险报警闪光灯。")]),
    judge("drive.s4.emergency.008", "drive.s4.emergency", "在道路上发生故障难以移动时，警告标志应设在来车方向。", True, "第52条要求在来车方向设置警告标志。", [ref("road-safety-law", "第52条", LAW, "并在来车方向设置警告标志等措施扩大示警距离。")]),
    judge("drive.s4.emergency.009", "drive.s4.emergency", "机动车在道路上发生故障或者事故，妨碍交通又难以移动的，应当按照规定开启危险报警闪光灯并在车后50米至100米处设置警告标志。", True, "实施条例第60条（普通道路）。", [ref("road-safety-regulation", "第60条", REG, "机动车在道路上发生故障或者发生交通事故，妨碍交通又难以移动的，应当按照规定开启危险报警闪光灯并在车后50米至100米处设置警告标志。")], 2),
    judge("drive.s4.aid.005", "drive.s4.aid", "造成人身伤亡的交通事故，驾驶人应当立即抢救受伤人员。", True, "第70条。", [ref("road-safety-law", "第70条", LAW, "造成人身伤亡的，车辆驾驶人应当立即抢救受伤人员。")]),
    judge("drive.s4.aid.006", "drive.s4.aid", "因抢救受伤人员变动现场的，应当标明位置。", True, "第70条。", [ref("road-safety-law", "第70条", LAW, "因抢救受伤人员变动现场的，应当标明位置。")]),
    judge("drive.s4.aid.007", "drive.s4.aid", "安全文明驾驶常识考试满分100分，合格标准为90分。", True, "公安部令第162号第38条。", [ref("license-order-162", "第38条", ORD, "科目三安全文明驾驶常识考试合格标准为90分。")]),
    judge("drive.s4.aid.008", "drive.s4.aid", "小型汽车安全文明驾驶常识考试为50道题、45分钟。", True, "GA 1026。", [ref("ga-1026", "安全文明驾驶常识", GA, "小型汽车安全文明驾驶常识 50 题、45 分钟。")]),
]


def stamp_existing(item: dict) -> dict:
    item.setdefault("phase", 1)
    if "difficulty" not in item:
        item["difficulty"] = 1 if item.get("kind") == "judge" else 2
    return item


def merge(name: str, extra: list[dict]) -> None:
    path = ROOT / name
    data = json.loads(path.read_text(encoding="utf-8"))
    data["questions"] = [stamp_existing(q) for q in data["questions"]]
    seen = {q["id"] for q in data["questions"]}
    added = 0
    for item in extra:
        if item["id"] not in seen:
            data["questions"].append(item)
            seen.add(item["id"])
            added += 1
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{name}: 现有 {len(data['questions'])} 题（新增 {added}）")


def main() -> None:
    merge("subject1.json", S1)
    merge("subject4.json", S4)


if __name__ == "__main__":
    main()
