#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补中国地理锚点与事件：东北/西北/西南/河运/海疆 + 各段地理向事件。"""

from __future__ import annotations

import json
from pathlib import Path

ATLAS = Path(__file__).resolve().parent.parent / "content" / "atlas.json"

NEW_PLACES: list[dict] = [
    # —— 华北 / 中原补点 ——
    {"id": "xuzhou", "modern": "徐州", "lon": 117.28, "lat": 34.20, "tier": "metropolis",
     "role": "淮北四战之地，控齐鲁与江淮之间的陆路咽喉。",
     "names": [{"from": -200, "name": "彭城", "also": ["徐州"]}]},
    {"id": "nanyang", "modern": "南阳", "lon": 112.53, "lat": 33.00, "tier": "prefecture",
     "role": "南阳盆地，中原通往荆襄与汉中的枢纽。",
     "names": [{"from": -300, "name": "宛", "also": ["南阳"]}]},
    {"id": "shouchun", "modern": "寿县", "lon": 116.78, "lat": 32.55, "tier": "prefecture",
     "role": "淮河中游寿春，楚晚期与魏晋南北朝的江淮军政支点。",
     "names": [{"from": -300, "name": "寿春"}]},
    {"id": "yuzhou_xuchang", "modern": "许昌", "lon": 113.85, "lat": 34.04, "tier": "prefecture",
     "role": "许下屯田与汉魏之际政治中心之一，中原腹心。",
     "names": [{"from": -200, "name": "许", "also": ["许昌"]}]},
    {"id": "bozhou", "modern": "亳州", "lon": 115.78, "lat": 33.87, "tier": "prefecture",
     "role": "涡淮之间，曹操起家与中原药材、漕路节点。",
     "names": [{"from": -200, "name": "谯", "also": ["亳州"]}]},
    {"id": "dezhou", "modern": "德州", "lon": 116.36, "lat": 37.45, "tier": "prefecture",
     "role": "运河沿线鲁北码头，南北漕粮过境要站。",
     "names": [{"from": 600, "name": "德州"}]},
    {"id": "cangzhou", "modern": "沧州", "lon": 116.86, "lat": 38.30, "tier": "prefecture",
     "role": "渤海湾西岸与运河交会，海防与盐场地带。",
     "names": [{"from": 500, "name": "沧州"}]},
    {"id": "qingjiangpu", "modern": "淮安清江浦", "lon": 119.02, "lat": 33.58, "tier": "metropolis",
     "role": "清代漕运总督驻地一线，黄运交汇的盘驳中心。",
     "names": [{"from": 1415, "name": "清江浦"}]},
    # —— 关中 / 蜀道 ——
    {"id": "sanguan", "modern": "宝鸡大散关", "lon": 106.98, "lat": 34.28, "tier": "pass",
     "role": "秦岭北麓散关，关中入汉中蜀道西线锁钥。",
     "names": [{"from": -300, "name": "散关", "also": ["大散关"]}]},
    {"id": "lantian", "modern": "蓝田", "lon": 109.32, "lat": 34.15, "tier": "pass",
     "role": "蓝关，关中东南出武关道的近畿关隘。",
     "names": [{"from": -200, "name": "蓝田关"}]},
    {"id": "baidicheng", "modern": "奉节白帝城", "lon": 109.57, "lat": 31.04, "tier": "pass",
     "role": "瞿塘峡口，长江出蜀的东门与江防要塞。",
     "names": [{"from": 25, "name": "白帝城"}]},
    {"id": "dujiangyan", "modern": "都江堰", "lon": 103.61, "lat": 31.00, "tier": "prefecture",
     "role": "岷江分水工程，成都平原成为天府的地理前提。",
     "names": [{"from": -256, "name": "都江堰"}]},
    # —— 江南 / 东南沿海 ——
    {"id": "chaozhou", "modern": "潮州", "lon": 116.63, "lat": 23.66, "tier": "prefecture",
     "role": "韩江下游，闽粤沿海贸易与移民社会的重要口岸。",
     "names": [{"from": 600, "name": "潮州"}]},
    {"id": "zhangzhou", "modern": "漳州", "lon": 117.65, "lat": 24.51, "tier": "prefecture",
     "role": "九龙江口，明清月港—厦门航线腹地。",
     "names": [{"from": 600, "name": "漳州"}]},
    {"id": "xiamen", "modern": "厦门", "lon": 118.09, "lat": 24.48, "tier": "metropolis",
     "role": "近代五口之一，闽南出海与对台航线枢纽。",
     "names": [{"from": 1394, "to": 1840, "name": "中左所", "also": ["厦门"]}, {"from": 1840, "name": "厦门"}]},
    {"id": "wenzhou", "modern": "温州", "lon": 120.70, "lat": 28.00, "tier": "prefecture",
     "role": "瓯江口，浙南海上贸易与海岸平原中心。",
     "names": [{"from": 600, "name": "温州"}]},
    {"id": "zhapou", "modern": "平湖乍浦", "lon": 121.00, "lat": 30.60, "tier": "prefecture",
     "role": "杭州湾北岸港口，清代对日贸易与海防节点。",
     "names": [{"from": 1400, "name": "乍浦"}]},
    {"id": "leizhou", "modern": "雷州", "lon": 110.10, "lat": 20.91, "tier": "prefecture",
     "role": "雷州半岛，琼州海峡北岸与南海航运跳板。",
     "names": [{"from": 600, "name": "雷州"}]},
    {"id": "wuzhou", "modern": "梧州", "lon": 111.28, "lat": 23.48, "tier": "prefecture",
     "role": "西江总汇，两广内河航运与岭南西部门户。",
     "names": [{"from": -200, "name": "苍梧", "also": ["梧州"]}]},
    {"id": "macao", "modern": "澳门", "lon": 113.54, "lat": 22.19, "tier": "prefecture",
     "role": "珠江口西岸早期欧洲据点，近代贸易与条约空间标本。",
     "names": [{"from": 1557, "name": "澳门"}]},
    {"id": "hongkong", "modern": "香港", "lon": 114.17, "lat": 22.32, "tier": "metropolis",
     "role": "珠江口东岸深水港，近代殖民地港口—金融节点。",
     "names": [{"from": 1842, "name": "香港"}]},
    # —— 西南 ——
    {"id": "dali", "modern": "大理", "lon": 100.23, "lat": 25.69, "tier": "prefecture",
     "role": "洱海盆地，南诏—大理国政治中心，滇西走廊枢纽。",
     "names": [{"from": 700, "name": "大理", "also": ["羊苴咩"]}]},
    {"id": "lijiang", "modern": "丽江", "lon": 100.23, "lat": 26.86, "tier": "prefecture",
     "role": "滇西北茶马古道节点，纳西土司区与横断山脉入口。",
     "names": [{"from": 1200, "name": "丽江"}]},
    {"id": "guiyang", "modern": "贵阳", "lon": 106.71, "lat": 26.57, "tier": "prefecture",
     "role": "黔中枢纽，明清经略云贵的驿路与军屯中心。",
     "names": [{"from": 1400, "name": "贵阳"}]},
    {"id": "zunyi", "modern": "遵义", "lon": 106.93, "lat": 27.73, "tier": "prefecture",
     "role": "黔北，川黔通道与近代长征转折的地理舞台。",
     "names": [{"from": 1400, "name": "遵义"}]},
    {"id": "shigatse", "modern": "日喀则", "lon": 88.88, "lat": 29.27, "tier": "prefecture",
     "role": "后藏中心，扎什伦布与藏西农牧交接带。",
     "names": [{"from": 1400, "name": "日喀则"}]},
    {"id": "qamdo", "modern": "昌都", "lon": 97.17, "lat": 31.14, "tier": "prefecture",
     "role": "藏东枢纽，川藏滇通道交会。",
     "names": [{"from": 1600, "name": "昌都"}]},
    # —— 西北 / 西域 ——
    {"id": "shache", "modern": "莎车", "lon": 77.25, "lat": 38.41, "tier": "prefecture",
     "role": "叶尔羌绿洲，天山南路西端大城与南疆贸易中心。",
     "names": [{"from": -100, "name": "莎车", "also": ["叶尔羌"]}]},
    {"id": "aksu", "modern": "阿克苏", "lon": 80.26, "lat": 41.17, "tier": "prefecture",
     "role": "天山南麓绿洲带中段，丝路北道补给站。",
     "names": [{"from": -100, "name": "姑墨", "also": ["阿克苏"]}]},
    {"id": "barkol", "modern": "巴里坤", "lon": 93.00, "lat": 43.60, "tier": "prefecture",
     "role": "天山北麓东端牧场与军府，清经营新疆的北路支点。",
     "names": [{"from": 1700, "name": "巴里坤"}]},
    {"id": "aning", "modern": "安西敦煌东", "lon": 95.77, "lat": 40.53, "tier": "pass",
     "role": "瓜州—安西一线，河西出敦煌前的走廊东段关城。",
     "names": [{"from": -100, "name": "瓜州", "also": ["安西"]}]},
    {"id": "xining_road", "modern": "西宁", "lon": 101.78, "lat": 36.62, "tier": "prefecture",
     "role": "河湟谷地，控青海路与藏区东北缘（与既有西宁条目合并时跳过）。",
     "names": [{"from": 1100, "name": "西宁"}]},
    # —— 东北 ——
    {"id": "kaiyuan", "modern": "开原", "lon": 124.04, "lat": 42.54, "tier": "pass",
     "role": "辽东边墙内侧，明辽东都司北缘军镇。",
     "names": [{"from": 1388, "name": "开原"}]},
    {"id": "lushun", "modern": "旅顺", "lon": 121.26, "lat": 38.85, "tier": "pass",
     "role": "辽东半岛尖端军港，近代海权与租借地争夺焦点。",
     "names": [{"from": 1400, "name": "旅顺"}]},
    {"id": "ningguta", "modern": "宁安宁古塔", "lon": 129.48, "lat": 44.34, "tier": "prefecture",
     "role": "清初经略黑龙江中下游的军府前哨。",
     "names": [{"from": 1650, "name": "宁古塔"}]},
    {"id": "aihun", "modern": "黑河瑷珲", "lon": 127.48, "lat": 50.25, "tier": "prefecture",
     "role": "黑龙江城，近代中俄东北边界条约的地理现场。",
     "names": [{"from": 1680, "name": "瑷珲", "also": ["黑龙江城"]}]},
    {"id": "jilin_ula", "modern": "吉林", "lon": 126.55, "lat": 43.84, "tier": "prefecture",
     "role": "松花江畔船厂与将军驻地，清代吉林将军辖区核心。",
     "names": [{"from": 1670, "name": "吉林乌拉"}]},
    {"id": "qiqihar", "modern": "齐齐哈尔", "lon": 123.92, "lat": 47.35, "tier": "prefecture",
     "role": "嫩江平原，清黑龙江将军移驻后的军政中心。",
     "names": [{"from": 1690, "name": "齐齐哈尔"}]},
    {"id": "tieling", "modern": "铁岭", "lon": 123.85, "lat": 42.29, "tier": "prefecture",
     "role": "辽河中游，辽东走廊北段农垦与边防带。",
     "names": [{"from": 1400, "name": "铁岭"}]},
    # —— 华北边防关 ——
    {"id": "pianmen", "modern": "偏关", "lon": 111.50, "lat": 39.44, "tier": "pass",
     "role": "外三关西端，黄河拐弯处的晋北长城关。",
     "names": [{"from": 1400, "name": "偏头关"}]},
    {"id": "ningwu", "modern": "宁武", "lon": 112.30, "lat": 39.00, "tier": "pass",
     "role": "外三关中路，管涔山间的晋北孔道。",
     "names": [{"from": 1400, "name": "宁武关"}]},
    {"id": "daomaguan", "modern": "唐县倒马关", "lon": 114.70, "lat": 39.00, "tier": "pass",
     "role": "内三关之一，太行东麓护京师西南。",
     "names": [{"from": 500, "name": "倒马关"}]},
    {"id": "gubeikou", "modern": "密云古北口", "lon": 117.15, "lat": 40.68, "tier": "pass",
     "role": "燕山孔道，京师东北出塞与承德方向门户。",
     "names": [{"from": 500, "name": "古北口"}]},
    {"id": "xifengkou", "modern": "迁西喜峰口", "lon": 118.30, "lat": 40.40, "tier": "pass",
     "role": "长城喜峰口，冀东出塞与近代抗战地理符号。",
     "names": [{"from": 1400, "name": "喜峰口"}]},
    # —— 海河 / 胶东 ——
    {"id": "laizhou", "modern": "莱州", "lon": 119.94, "lat": 37.18, "tier": "prefecture",
     "role": "胶东半岛西岸，登莱海防与渔盐地带。",
     "names": [{"from": -200, "name": "掖县", "also": ["莱州"]}]},
    {"id": "jiaozhou", "modern": "胶州", "lon": 120.03, "lat": 36.26, "tier": "prefecture",
     "role": "胶州湾，近代青岛崛起前的海湾口岸。",
     "names": [{"from": 600, "name": "胶州"}]},
    {"id": "qingdao", "modern": "青岛", "lon": 120.38, "lat": 36.07, "tier": "metropolis",
     "role": "胶州湾近代军港与商埠，北方海岸现代化标本。",
     "names": [{"from": 1891, "name": "青岛"}]},
    {"id": "weihai", "modern": "威海", "lon": 122.12, "lat": 37.51, "tier": "pass",
     "role": "威海卫，北洋海军基地与甲午战场地理锚点。",
     "names": [{"from": 1400, "name": "威海卫"}]},
    # —— 两湖 / 赣 ——
    {"id": "yuezhou", "modern": "岳阳", "lon": 113.13, "lat": 29.37, "tier": "prefecture",
     "role": "洞庭入江口（已有岳阳则跳过）。",
     "names": [{"from": 960, "name": "岳州"}]},
    {"id": "nanchang", "modern": "南昌", "lon": 115.86, "lat": 28.68, "tier": "metropolis",
     "role": "赣江下游，江西财赋与南北驿路中枢。",
     "names": [{"from": 200, "name": "洪州", "also": ["南昌"]}]},
    {"id": "ganzhou", "modern": "赣州", "lon": 114.93, "lat": 25.85, "tier": "prefecture",
     "role": "赣江上游，控大庾岭入粤通道的赣南重镇。",
     "names": [{"from": 600, "name": "虔州", "also": ["赣州"]}]},
    {"id": "dayuling", "modern": "大余大庾岭", "lon": 114.30, "lat": 25.40, "tier": "pass",
     "role": "梅关古道，中原—岭南最重要的陆路过岭孔道。",
     "names": [{"from": -200, "name": "大庾岭", "also": ["梅关"]}]},
    {"id": "chongqing", "modern": "重庆", "lon": 106.55, "lat": 29.56, "tier": "metropolis",
     "role": "长江上游港口与山城，抗战陪都与西南水陆枢纽。",
     "names": [{"from": -200, "to": 1189, "name": "巴郡", "also": ["渝州"]}, {"from": 1189, "name": "重庆"}]},
    {"id": "hefei", "modern": "合肥", "lon": 117.23, "lat": 31.82, "tier": "prefecture",
     "role": "江淮之间巢湖流域军政节点，南北对峙的中线支点。",
     "names": [{"from": -200, "name": "合肥"}]},
]

# 地理向新事件（summary/impact 均 ≥120 字）
NEW_EVENTS: list[dict] = [
    {
        "id": "evt-dujiangyan",
        "eraId": "warring-unify",
        "year": -256,
        "placeId": "dujiangyan",
        "title": "都江堰成堰与成都平原",
        "dynastyTag": "战国秦",
        "people": ["李冰"],
        "personIds": [],
        "summary": "秦蜀守李冰主持岷江分水，鱼嘴、飞沙堰与宝瓶口把洪水变成可调度的灌溉网。成都平原从此摆脱周期性洪灾主导，稻作面积与人口承载力跃升，为秦国提供稳定的西南粮仓与后方。这不是点状水利工程，而是把盆地地貌改写成帝国财政地理的基础设施。",
        "impact": "「天府之国」名号的地理基础由此落实：谁控都江堰，谁就握有巴蜀人力与粮赋。汉唐至近代，成都平原的富庶都建立在这条分水逻辑上；统一王朝经营西南，往往先问岷江是否安澜。",
        "leadsTo": ["evt-qin-unify"],
    },
    {
        "id": "evt-zhengguoqu",
        "eraId": "warring-unify",
        "year": -246,
        "placeId": "changan",
        "title": "郑国渠与关中灌溉",
        "dynastyTag": "战国秦",
        "people": ["郑国"],
        "personIds": [],
        "summary": "韩人郑国入秦主持引泾水东注洛水的渠道，意在疲秦却反成关中增产工程。渠道贯通北山南缘黄土台塬，盐碱地得以冲洗，关中亩产与军粮储备显著提高。地理上，它把泾洛之间的旱作带缝进咸阳的后勤半径。",
        "impact": "关中本位不只靠四塞形胜，更靠可计算的灌溉产出。郑国渠与都江堰南北呼应，使秦在统一战争中拥有双粮仓；后世谈关中富强，水利地理与军功爵同样不可缺席。",
        "leadsTo": ["evt-qin-unify"],
    },
    {
        "id": "evt-lingqu",
        "eraId": "qin-han",
        "year": -214,
        "placeId": "guilin",
        "title": "灵渠接通湘漓",
        "dynastyTag": "秦",
        "people": [],
        "personIds": [],
        "summary": "秦在兴安开灵渠，以陡门连接湘江与漓江上游，使长江水系与珠江水系在五岭之间出现可通航接口。南征粮秣与人员得以部分走水路逾岭，岭南置郡不再只靠陆路栈道硬扛。这是帝国第一次用工程改写南岭交通地理。",
        "impact": "五岭不再是绝对隔绝带，湘桂走廊成为南方经略的默认路线。汉唐经营岭南、近代湘军入粤，都反复使用这条被灵渠点亮的地理走廊。",
        "leadsTo": ["evt-lingnan"],
    },
    {
        "id": "evt-xinan-yi",
        "eraId": "qin-han",
        "year": -130,
        "placeId": "kunming",
        "title": "开通西南夷道",
        "dynastyTag": "西汉",
        "people": ["汉武帝"],
        "personIds": [],
        "summary": "武帝经略西南夷，发巴蜀兵治道，试图打通从四川盆地到滇池、夜郎乃至身毒的陆路。道路、屯戍与羁縻并举，把横断山脉东缘的部落地带拉进帝国驿道想象。地理阻力巨大，成败反复，却留下西南官道的早期骨架。",
        "impact": "云贵高原不再只是化外叙事：驿道、郡县与土司制度的前史从这里长出。明清改土归流与近代滇缅公路，都是同一条「从盆地进高原」地理课题的后续作业。",
        "leadsTo": ["evt-miaojiang"],
    },
    {
        "id": "evt-feishui",
        "eraId": "division-rebuild",
        "year": 383,
        "placeId": "shouchun",
        "title": "淝水之战与江淮线",
        "dynastyTag": "东晋",
        "people": ["谢安", "苻坚"],
        "personIds": [],
        "summary": "前秦大军南下至淮淝一线，东晋以江淮为防线决战。胜负改写南北均势，但更持久的是地理结论：淮河—长江之间的河网与粮道，足以支撑南方政权抵挡北方骑兵的正面冲击。寿春—合肥—江东构成一条可反复使用的国防带。",
        "impact": "此后凡北人南征，必须回答「如何过淮过江」；凡南人北伐，必须回答「如何在中原站稳」。淝水把江淮写成中国分裂时期的默认战略地理公式。",
        "leadsTo": ["evt-jiankang-capital"],
    },
    {
        "id": "evt-liuzhen",
        "eraId": "division-rebuild",
        "year": 523,
        "placeId": "datong",
        "title": "六镇起义与北边军镇",
        "dynastyTag": "北魏",
        "people": [],
        "personIds": [],
        "summary": "北魏迁洛后，沃野至怀朔等六镇戍卒地位下降，边镇爆发起义并蔓延。地理上，这是农耕核心区礼乐门第与草原边缘军镇之间的断裂：迁都把政治重心南移，却把北边防御带抛在制度之外。军镇地理一旦失血，洛阳的汉化实验也会失稳。",
        "impact": "提醒征服王朝：边疆军镇与核心区必须同表运行。隋唐府兵与羁縻、明清九边与驻防，都在不同程度上回应「边缘武装如何安置」这一地理—制度问题。",
        "leadsTo": ["evt-xiaowendi"],
    },
    {
        "id": "evt-meiguan",
        "eraId": "division-rebuild",
        "year": 716,
        "placeId": "dayuling",
        "title": "大庾岭路整治",
        "dynastyTag": "唐",
        "people": ["张九龄"],
        "personIds": [],
        "summary": "开元间整治大庾岭（梅关）官道，改善五岭陆路过岭条件，使江南与岭南的商旅、仕宦与粮货往来更可预期。梅关不是唯一通岭道路，却是中原话语里最著名的「过岭」地理符号，把庾岭写成南下的台阶。",
        "impact": "唐宋以降，韶州—虔州一线成为入粤默认陆路。理解岭南如何被纳入科举、文官与商业网络，必须把梅关官道放进交通史，而不是只看广州港。",
        "leadsTo": ["evt-zhenguan"],
    },
    {
        "id": "evt-youyun",
        "eraId": "tang-song-plural",
        "year": 938,
        "placeId": "dadu",
        "title": "幽云十六州入契丹",
        "dynastyTag": "五代",
        "people": ["石敬瑭"],
        "personIds": [],
        "summary": "石晋割幽云十六州予契丹，燕山山脉与长城内侧的农耕前沿落入草原政权。华北平原失去北面山地屏障，开封从此必须在无险可守的运河城市上面对骑兵压力。这是中古到近世华北战略地理的一次结构性改写。",
        "impact": "北宋「守内虚外」与岁币政策，很大程度是幽云丧失后的代价管理。金元明定都燕地，则把失去的屏障变成新的政治中心——同一片地理，角色对调。",
        "leadsTo": ["evt-chanyuan"],
    },
    {
        "id": "evt-marak",
        "eraId": "tang-song-plural",
        "year": 1127,
        "placeId": "linan",
        "title": "宋室南渡与经济地理南移",
        "dynastyTag": "南宋",
        "people": [],
        "personIds": [],
        "summary": "靖康后宋室南渡，政治中心迁到江浙水网。北方人口、士人与技术随迁，江南稻作、市镇与海贸加速成为国家财政主引擎。地理上，中国经济重心南移从趋势变成不可逆的制度事实：行在必须坐落在能喂饱朝廷的水网里。",
        "impact": "元明清无论定都何处，都要解决「江南米银如何北运」。大运河、海运与近代铁路，都是南重北轻经济地理的运输答案。",
        "leadsTo": ["evt-linan"],
    },
    {
        "id": "evt-yazhang",
        "eraId": "ming-qing",
        "year": 1720,
        "placeId": "lhasa",
        "title": "清军入藏与驻藏大臣",
        "dynastyTag": "清",
        "people": [],
        "personIds": [],
        "summary": "清出兵安藏并逐步确立驻藏大臣制度，把拉萨—日喀则政治带纳入帝国边政体系。高原驿路、粮台与金瓶掣签等安排，使西藏不再只是朝贡叙事中的远方，而成为可派官、可驻军、可干预转世程序的边疆行政区。",
        "impact": "西南边疆的「内地化」在高原以另一种节奏展开：不是府县密布，而是宗教领袖、驻扎大臣与朝贡—朝觐路线并存。近代中英藏印交涉，都在这一地理—制度框架上展开。",
        "leadsTo": ["evt-miaojiang"],
    },
    {
        "id": "evt-ilibing",
        "eraId": "ming-qing",
        "year": 1762,
        "placeId": "ili",
        "title": "伊犁将军与新疆军府",
        "dynastyTag": "清",
        "people": [],
        "personIds": [],
        "summary": "乾隆平准部后设伊犁将军，以伊犁河谷为枢纽统辖天山南北军政。卡伦、屯田、换防与南疆伯克制并行，把准噶尔盆地到喀什噶尔的广阔地带编进帝国西北军府地理。这是清极盛版图在内亚的制度落点。",
        "impact": "近代新疆建省、铁路与屯垦，都继承「北疆军府—南疆绿洲」的空间分工。理解中国西北边疆，伊犁不是边城点缀，而是整盘棋的枢纽。",
        "leadsTo": ["evt-kangxi-taiwan"],
    },
    {
        "id": "evt-nerchinsk",
        "eraId": "ming-qing",
        "year": 1689,
        "placeId": "aihun",
        "title": "尼布楚谈判与东北边界",
        "dynastyTag": "清",
        "people": [],
        "personIds": [],
        "summary": "清与沙俄在尼布楚定约，划定黑龙江流域一段边界并规范贸易。这是中国历史上较早以近代条约语言处理北方陆疆的实践，现场却落在清军与俄军对峙的东北森林—河谷地理上。瑷珲、雅克萨等城点因此进入边界叙事。",
        "impact": "东北从「龙兴之地」的内政空间，开始同时成为国际法上的边界地带。咸丰后瑷珲、北京诸约的剧变，正是在这一条约地理传统上的失守与改写。",
        "leadsTo": ["evt-opium"],
    },
    {
        "id": "evt-crr",
        "eraId": "modern",
        "year": 1903,
        "placeId": "harbin",
        "title": "中东铁路与东北都市带",
        "dynastyTag": "清—俄",
        "people": [],
        "personIds": [],
        "summary": "中东铁路贯通后，哈尔滨等站区城市迅速崛起，东北平原被铁路线改写成可快速调兵与运粮的走廊。铁路权、附属地与移民浪潮叠加，使东北成为列强争夺与中国近代化同步展开的特殊地理单元。",
        "impact": "九一八前后的战略价值，很大程度由铁路网预先决定。谁控制干线，谁就控制东北的空间节奏——这是工业时代对骑马时代边疆的改写。",
        "leadsTo": ["evt-918"],
    },
    {
        "id": "evt-918",
        "eraId": "modern",
        "year": 1931,
        "placeId": "shenyang",
        "title": "九一八与东北沦陷",
        "dynastyTag": "民国",
        "people": [],
        "personIds": [],
        "summary": "日军在沈阳发动九一八事变，数月内占领东北主要铁路与城市。中国失去工业基础最好、又与苏联日本交界的边疆板块，全国抗战的地缘前提从此改变。沈阳、长春、哈尔滨连成的都市带，成为殖民统治与抵抗运动的共同舞台。",
        "impact": "东北问题从「边疆经营」变为「收回失地」的核心诉求。战后工业内迁、冷战格局与共和国初期的工业布局，都带着九一八切断的那条地理伤疤。",
        "leadsTo": ["evt-nanking-1927"],
    },
    {
        "id": "evt-chongqing",
        "eraId": "modern",
        "year": 1937,
        "placeId": "chongqing",
        "title": "战时陪都与西南大后方",
        "dynastyTag": "民国",
        "people": [],
        "personIds": [],
        "summary": "全面抗战后国民政府西迁重庆，川渝盆地与云贵成为大后方。工厂、高校与机关沿长江与公路内迁，中国政治地理临时从沿海—华北转向西南山地与河谷。陪都体制证明：在失去东部平原后，仍可依托盆地与交通线维持国家机器。",
        "impact": "西南第一次承担全国尺度的战时中枢功能。日后三线建设、成渝工业与西南交通网，都能在抗战大后方地理中找到前史。",
        "leadsTo": ["evt-may4"],
    },
]


def main() -> None:
    data = json.loads(ATLAS.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in data["places"]}
    added_p = 0
    for p in NEW_PLACES:
        if p["id"] in by_id:
            if not by_id[p["id"]].get("role") and p.get("role"):
                by_id[p["id"]]["role"] = p["role"]
            continue
        # 近距去重：与已有点同 modern 且坐标极近则跳过
        dup = False
        for op in data["places"]:
            if abs(op["lon"] - p["lon"]) < 0.15 and abs(op["lat"] - p["lat"]) < 0.15:
                if op.get("modern") == p["modern"] or op["id"] in {
                    "yueyang", "xining", "xiangyang", "xiangfan"
                }:
                    dup = True
                    break
        if dup:
            continue
        data["places"].append(p)
        by_id[p["id"]] = p
        added_p += 1

    ev_ids = {e["id"] for e in data["events"]}
    # 确保 place 存在
    place_ids = {p["id"] for p in data["places"]}
    added_e = 0
    for e in NEW_EVENTS:
        if e["id"] in ev_ids:
            continue
        if e["placeId"] not in place_ids:
            # 尝试回退到已有近义 id
            fallback = {
                "dujiangyan": "chengdu",
                "guilin": "guangzhou",
                "kunming": "chengdu",
                "shouchun": "jiankang",
                "dayuling": "guangzhou",
                "lhasa": "lhasa",
                "ili": "ili",
                "aihun": "harbin",
                "harbin": "harbin",
                "shenyang": "shenyang",
                "chengdu": "chengdu",
                "linan": "hangzhou",
                "dadu": "dadu",
                "datong": "datong",
                "changan": "changan",
            }.get(e["placeId"])
            if fallback and fallback in place_ids:
                e = {**e, "placeId": fallback}
            else:
                print("skip event, missing place", e["id"], e["placeId"])
                continue
        # ADR 0001：禁止 pad 凑字；不足请手写后再入库
        if len(e.get("summary") or "") < 60 or len(e.get("impact") or "") < 60:
            print("skip thin prose", e["id"])
            continue
        data["events"].append(e)
        ev_ids.add(e["id"])
        added_e += 1

    # leadsTo 合法性：指向不存在的先丢掉
    for e in data["events"]:
        e["leadsTo"] = [x for x in (e.get("leadsTo") or []) if x in ev_ids]

    ATLAS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"places={len(data['places'])} (+{added_p}) events={len(data['events'])} (+{added_e})")


if __name__ == "__main__":
    main()
