import "package:flutter/widgets.dart";

import "glyphs.dart";
import "models.dart";

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
    lead: "科目一丢分多在硬数字上。同类数字放在一起看，记住的是它们之间的区别；每组都能直接练相关的题。",
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
        "跟全国规定对照着记——先看速记，再练相关的题。",
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
        "按作答记录里错得最多的点整理。先看对照，再练相关的题。",
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
        "按事情发生的先后对照着记，再练相关的题。",
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
        "停车的规矩散在各章，这里按「一件事」收在一起，对照着记，再练相关的题。",
    footnote: "条目依据《道路交通安全法》及其实施条例、《河南省道路交通安全条例》《河南省高速公路条例》，每条指到条款。",
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
