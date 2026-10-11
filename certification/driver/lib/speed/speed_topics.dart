import "package:flutter/widgets.dart";

import "../ui/glyphs.dart";
import "../core/models.dart";
// 速记专题的注册表（ADR 0096）：每个专题**属于一个科目**——科目一有科目一的专题，科目四有科目四自己的，
// 侧栏里挂在各自科目底下，相关题、自测作答记录、练习都只用本科目的，不混在一起。
//
// 内容共通的专题（手势、灯光与让行的考点）两个科目各有一份：内容是同一份文件，但各用各科目的题、
// 各记各的作答。某科目关联到的题不够多的组，不进它的专题（见 [NoteGroup.subjects]）。

enum SpeedKind { numbers, signs, markings, gauges, gestures, notes }

class SpeedTopic {
  const SpeedTopic(this.id, this.subjectId, this.title, this.icon, this.kind, {this.source, this.lead, this.footnote});

  /// 形如 `s1.signs`：兼作侧栏的位置键、自测速记题的页键（题号 `drive.recall.s1.signs.<哈希>`）。
  final String id;
  final String subjectId;
  final String title;
  final IconData icon;
  final SpeedKind kind;

  /// 要点类专题的内容来源：`notes` 考点速记、`henan` 河南速记、`license` 记分证照速记；
  /// 其余专题各有自己的内容文件，键就是专题 id（见 [Bank.topicNotes]）。
  final String? source;

  /// 页面开头的导语与页脚的出处说明；空则用页面组件自己的默认文字。
  final String? lead;
  final String? footnote;
}

/// 全部速记专题，按科目、再按侧栏里的先后顺序排。
const speedTopics = [
  // ---- 科目一 ----
  SpeedTopic(
    "s1.numbers",
    "subject1",
    "易混数字",
    Glyph.numbers,
    SpeedKind.numbers,
    lead: "科目一丢分多在硬数字上。同类数字放在一起看，记住的是它们之间的区别；每组都能直接自测。",
  ),
  SpeedTopic("s1.signs", "subject1", "标志速记", Glyph.signs, SpeedKind.signs),
  SpeedTopic("s1.markings", "subject1", "标线速记", Glyph.markings, SpeedKind.markings),
  SpeedTopic("s1.gauges", "subject1", "仪表速记", Glyph.gauges, SpeedKind.gauges),
  SpeedTopic("s1.gestures", "subject1", "手势速记", Glyph.gestures, SpeedKind.gestures),
  SpeedTopic("s1.keypoints", "subject1", "考点速记", Glyph.notes, SpeedKind.notes, source: "notes"),
  SpeedTopic(
    "s1.henan",
    "subject1",
    "河南速记",
    Glyph.henan,
    SpeedKind.notes,
    source: "henan",
    lead: "模拟考固定抽 10 道河南地方题。罚款档次、高速规矩、赔偿比例都是河南条例自定的，"
        "跟全国规定对照着记——先看速记，再按组自测。",
    footnote: "条目依据《河南省道路交通安全条例》与《河南省高速公路条例》，罚款数字均指到条款。",
  ),
  SpeedTopic(
    "s1.license-notes",
    "subject1",
    "记分证照速记",
    Glyph.licenseNotes,
    SpeedKind.notes,
    source: "license",
    lead: "记分分档、证照期限、罚款档位、禁考年限、号牌登记——科目一最容易丢分的这几块，"
        "按作答记录里错得最多的点整理。先看对照，再按组自测。",
    footnote: "条目依据《道路交通安全违法行为记分管理办法》《机动车驾驶证申领和使用规定》《机动车登记规定》"
        "《道路交通安全法》及其实施条例，每条指到条款。",
  ),
  SpeedTopic(
    "s1.accident",
    "subject1",
    "事故处理与时限",
    Glyph.accident,
    SpeedKind.notes,
    lead: "事故处理在科目一占一整块：现场先做什么、能私了还是必须报警、十日五日三日各是哪个时限、逃逸和刑责怎么算。"
        "按事情发生的先后对照着记，再按组自测。",
    footnote: "条目依据《道路交通安全法》及其实施条例、《道路交通事故处理程序规定》（公安部令第146号）、"
        "《道路交通安全违法行为记分管理办法》《刑法》，每条指到条款。",
  ),
  SpeedTopic(
    "s1.parking",
    "subject1",
    "停车与违停",
    Glyph.parkingRules,
    SpeedKind.notes,
    lead: "哪里不能停（站 30 口 50）、临时停车怎么停、违停罚多少、故障夜间怎么示警、高速上能不能停——"
        "停车的规矩散在各章，这里按「一件事」收在一起，对照着记，再按组自测。",
    footnote: "条目依据《道路交通安全法》及其实施条例、《河南省道路交通安全条例》《河南省高速公路条例》，每条指到条款。",
  ),
  SpeedTopic(
    "s1.occupant",
    "subject1",
    "乘员与安全带",
    Glyph.occupants,
    SpeedKind.notes,
    lead: "安全带、载人超员、乘车人的规矩、儿童座椅与头枕——车里坐的人的事，散在好几章，这里收在一起，"
        "对照着记，再按组自测。",
    footnote: "条目依据《道路交通安全法》及其实施条例、《道路交通安全违法行为记分管理办法》《未成年人保护法》，每条指到条款。",
  ),
  SpeedTopic(
    "s1.signal-rail",
    "subject1",
    "信号灯与铁路道口",
    Glyph.signalRail,
    SpeedKind.notes,
    lead: "每种灯的意思、路口怎么走、铁路道口怎么过——这三块的口诀最容易记混，按场景对照着记，再按组自测。",
    footnote: "条目依据《道路交通安全法》及其实施条例、记分办法与 GB 5768.3，每条指到条款。",
  ),
  SpeedTopic(
    "s1.maneuver",
    "subject1",
    "超车会车与掉头倒车",
    Glyph.maneuvers,
    SpeedKind.notes,
    lead: "超车、会车、变更车道与转向灯、掉头倒车——科目一最大的一块通行规则，口诀和例外最多。"
        "按场景对照着记，再按组自测。",
    footnote: "条目依据《道路交通安全法》及其实施条例、《河南省道路交通安全条例》、GB 5768.3 与记分办法，每条指到条款。",
  ),
  SpeedTopic(
    "s1.vehicle",
    "subject1",
    "车辆基础与操作",
    Glyph.vehicleCare,
    SpeedKind.notes,
    lead: "ABS 与制动、轮胎胎压与爆胎、下长坡与油耗、自动挡操作——机动车基础知识里最常考的几块，"
        "按场景对照着记，再按组自测。",
    footnote: "条目依据 GB 7258、GB 26149、《道路交通安全法实施条例》与 2022 版考试大纲，每条指到条款或章节。",
  ),
  SpeedTopic(
    "s1.people",
    "subject1",
    "避让行人非机动车校车",
    Glyph.people,
    SpeedKind.notes,
    lead: "行人、非机动车、校车、特种车、牲畜——谁该让谁、怎么让，规矩都在「让」字上，按场景对照着记，再按组自测。",
    footnote: "条目依据《道路交通安全法》及其实施条例、记分办法与 2022 版考试大纲，每条指到条款或章节。",
  ),
  SpeedTopic(
    "s1.hill",
    "subject1",
    "山区坡道与弯道",
    Glyph.hill,
    SpeedKind.notes,
    lead: "急弯、山区弯道、上下坡、颠簸路、塌方路段——「进弯前减速、鸣喇叭、靠右行」，按场景对照着记，再按组自测。",
    footnote: "条目依据《道路交通安全法实施条例》与 2022 版考试大纲，每条指到条款或章节。",
  ),
  SpeedTopic(
    "s1.ev",
    "subject1",
    "电动汽车",
    Glyph.electric,
    SpeedKind.notes,
    lead: "出行前查电量、规范充电、能量回收不能当刹车、低速声音小要更小心——新能源汽车的基础知识，对照着记，再按组自测。",
    footnote: "条目依据 2022 版考试大纲与《道路交通安全法》，每条指到条款或章节。",
  ),
  // ---- 科目四 ----
  SpeedTopic(
    "s4.numbers",
    "subject4",
    "易混数字",
    Glyph.numbers,
    SpeedKind.numbers,
    lead: "科目四也考这几组数字：限速、距离、高速低能见度。同类数字放在一起看，记住的是它们之间的区别；每组都能直接练科目四的相关题。",
  ),
  SpeedTopic("s4.gestures", "subject4", "手势速记", Glyph.gestures, SpeedKind.gestures),
  SpeedTopic("s4.keypoints", "subject4", "考点速记", Glyph.notes, SpeedKind.notes, source: "notes"),
  SpeedTopic(
    "s4.crash",
    "subject4",
    "事故处置",
    Glyph.accident,
    SpeedKind.notes,
    lead: "科目四考的是出事之后怎么处置：现场先防二次事故，高速、隧道、铁路道口各有各的顺序，责任和赔偿也要分清。"
        "按顺序对照着记，再练科目四的相关题。",
    footnote: "条目依据《道路交通安全法》及其实施条例、《机动车交通事故责任强制保险条例》与 2022 版考试大纲，每条指到条款。",
  ),
  SpeedTopic(
    "s4.occupant",
    "subject4",
    "安全带与乘员安全",
    Glyph.occupants,
    SpeedKind.notes,
    lead: "科目四的乘员题偏安全：安全带与气囊、座椅头枕怎么调、碰撞时怎么保护自己、停车后提醒乘客开门。"
        "按场景对照着记，再练科目四的相关题。",
    footnote: "条目依据《道路交通安全法》及其实施条例与 2022 版考试大纲，每条指到条款。",
  ),
  SpeedTopic(
    "s4.signal-rail",
    "subject4",
    "信号灯与铁路道口",
    Glyph.signalRail,
    SpeedKind.notes,
    lead: "科目四的信号灯与铁路道口：绿灯不等于优先、堵车不进路口、道口一停二看三通过、熄火先重启再离轨。"
        "按场景对照着记，再练科目四的相关题。",
    footnote: "条目依据《道路交通安全法》及其实施条例，每条指到条款。",
  ),
  SpeedTopic(
    "s4.maneuver",
    "subject4",
    "超车会车与变道倒车",
    Glyph.maneuvers,
    SpeedKind.notes,
    lead: "科目四的超车、会车、变道、倒车：不超的情形、被超怎么让、窄路怎么会车、转向灯怎么开。"
        "按场景对照着记，再练科目四的相关题。",
    footnote: "条目依据《道路交通安全法》及其实施条例与 2022 版考试大纲，每条指到条款。",
  ),
  SpeedTopic(
    "s4.failure",
    "subject4",
    "车辆故障与紧急处置",
    Glyph.vehicleCare,
    SpeedKind.notes,
    lead: "爆胎、制动失效、转向失控、侧滑水滑、熄火起火——科目四最常考的险情处置，"
        "一条一个险情，先做什么、不能做什么，对照着记，再练科目四的相关题。",
    footnote: "条目依据 2022 版考试大纲与 GB 26149，每条指到章节。",
  ),
  SpeedTopic(
    "s4.people",
    "subject4",
    "避让行人非机动车校车",
    Glyph.people,
    SpeedKind.notes,
    lead: "科目四的避让题：别穿插别绕前别鸣喇叭催行人、非机动车违法占道也不逼让、校车停靠后方和相邻车道都停。"
        "按场景对照着记，再练科目四的相关题。",
    footnote: "条目依据《道路交通安全法》及其实施条例与 2022 版考试大纲，每条指到条款或章节。",
  ),
  SpeedTopic(
    "s4.hill",
    "subject4",
    "山区坡道与弯道",
    Glyph.hill,
    SpeedKind.notes,
    lead: "科目四的山区、坡道、弯道：进弯前减速、坡底提前减挡、山区不紧跟前车、颠簸挂低挡。"
        "按场景对照着记，再练科目四的相关题。",
    footnote: "条目依据《道路交通安全法实施条例》与 2022 版考试大纲，每条指到条款或章节。",
  ),
  SpeedTopic(
    "s4.expressway",
    "subject4",
    "高速公路驾驶",
    Glyph.expressway,
    SpeedKind.notes,
    lead: "科目四的高速题：加速车道汇入、减速车道驶出、不骑线不走路肩、险情先避人后避物、碰护栏握稳方向。"
        "按场景对照着记，再练科目四的相关题。",
    footnote: "条目依据《道路交通安全法实施条例》第七十八至八十二条与 2022 版考试大纲，每条指到条款或章节。",
  ),
  SpeedTopic(
    "s4.fatigue",
    "subject4",
    "疲劳与驾驶状态",
    Glyph.fatigue,
    SpeedKind.notes,
    lead: "疲劳驾驶的程度与预防（八小时、四小时、二十分钟）、情绪与药物对驾驶的影响。按场景对照着记，再练科目四的相关题。",
    footnote: "条目依据《道路交通安全法》及其实施条例与 2022 版考试大纲，每条指到条款或章节。",
  ),
  SpeedTopic(
    "s4.fire",
    "subject4",
    "起火逃生与危险物品",
    Glyph.fire,
    SpeedKind.notes,
    lead: "车辆起火怎么停、怎么逃，倾翻别跳车，危险物品运输要批准、定路线、挂标志。按场景对照着记，再练科目四的相关题。",
    footnote: "条目依据《道路交通安全法》与 2022 版考试大纲，每条指到条款或章节。",
  ),
  SpeedTopic(
    "s4.stopping",
    "subject4",
    "停车与停放",
    Glyph.parkingRules,
    SpeedKind.notes,
    lead: "科目四的停车题偏安全：临时停车怎么停、夜间和雨雾天怎么示警、坡道和山区怕溜车、高速上要停只去服务区。"
        "按场景对照着记，再练科目四的相关题。",
    footnote: "条目依据《道路交通安全法》及其实施条例与 2022 版考试大纲，每条指到条款。",
  ),
];

/// 侧栏里专题的分组（ADR 0109）：专题多了，按内容归成几组折叠起来。分组按专题 id 点号后的部分归，
/// 科目一、科目四同名专题归同一组；同一科目里只列出该科目有的专题。
const speedGroups = [
  (id: "recite", title: "速记对照", suffixes: ["numbers", "signs", "markings", "gauges", "gestures", "keypoints", "henan", "license-notes"]),
  (id: "accident", title: "事故与停车", suffixes: ["accident", "crash", "parking", "stopping"]),
  (id: "traffic", title: "通行规则", suffixes: ["maneuver", "signal-rail", "people", "hill", "expressway"]),
  (id: "safety", title: "车辆与安全", suffixes: ["occupant", "vehicle", "failure", "ev", "fire", "fatigue"]),
];

/// 专题所在分组的 id。
String speedGroupIdOf(SpeedTopic topic) {
  final suffix = topic.id.substring(topic.id.indexOf(".") + 1);
  return speedGroups.firstWhere((g) => g.suffixes.contains(suffix)).id;
}

/// 一个科目的专题按 [speedGroups] 分好组（空组不出现，组内保持注册表里的先后）。
List<({String id, String title, List<SpeedTopic> topics})> speedTopicGroupsOf(String subjectId) {
  final topics = speedTopicsOf(subjectId);
  return [
    for (final g in speedGroups)
      (
        id: g.id,
        title: g.title,
        topics: [for (final t in topics) if (g.suffixes.contains(t.id.substring(t.id.indexOf(".") + 1))) t],
      ),
  ].where((g) => g.topics.isNotEmpty).toList();
}

SpeedTopic? speedTopicById(String id) {
  for (final t in speedTopics) {
    if (t.id == id) return t;
  }
  return null;
}

List<SpeedTopic> speedTopicsOf(String subjectId) => [for (final t in speedTopics) if (t.subjectId == subjectId) t];

/// 速记题的题号 / 知识点号属于哪个科目：`drive.recall.s4.gestures.1a2b3c4d` → `subject4`。
String? recallSubjectOf(String idOrTopic) {
  const prefix = "drive.recall.";
  if (!idOrTopic.startsWith(prefix)) return null;
  return switch (idOrTopic.substring(prefix.length, prefix.length + 2)) {
    "s1" => "subject1",
    "s4" => "subject4",
    _ => null,
  };
}

/// 要点类专题的分组：考点速记按各组标的科目筛，河南、记分证照只在科目一，新专题取自己的内容。
List<NoteGroup> noteGroupsOf(Bank bank, SpeedTopic topic) => switch (topic.source) {
  "notes" => [for (final g in bank.notes) if (g.subjects.contains(topic.subjectId)) g],
  "henan" => bank.henanGroups,
  "license" => bank.licenseGroups,
  _ => bank.topicNotes[topic.id] ?? const [],
};

/// 手势专题的条目：只留本科目有题可考的手势（每个条目都要有题，ADR 0091）——「示意靠边停车」只有科目四的题，
/// 就不进科目一的手势专题。
List<TrafficGesture> gesturesOf(Bank bank, SpeedTopic topic) {
  final prefix = topic.subjectId == "subject1" ? "drive.s1." : "drive.s4.";
  return [for (final g in bank.gestureList) if (g.questions.any((id) => id.startsWith(prefix))) g];
}

/// 易混数字专题的分组：按各组标的科目筛。
List<CheatGroup> cheatGroupsOf(Bank bank, SpeedTopic topic) => [
  for (final g in bank.cheatsheet) if (g.subjects.contains(topic.subjectId)) g,
];
