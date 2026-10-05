import "dart:convert";
import "dart:io";

import "package:flutter/services.dart";
import "package:path/path.dart" as p;

import "app_root.dart";
import "gesture_index.dart";
import "guide.dart";
import "models.dart";
import "recall_cards.dart";

class ContentLoader {
  /// 读到内容的那个根目录；开发时是工作树，发行包里为空（走 assets）。
  static String? contentRoot;

  /// 题图要么在磁盘上（开发），要么打进 assets（发行）——两条路径都从这里给出。
  static String imagePath(String relative) {
    final root = contentRoot;
    return root == null ? "content/$relative" : p.join(root, "content", relative);
  }

  static bool get imagesOnDisk => contentRoot != null;

  /// 应用图标 `icon.png`（由 `icon.svg` 派生）在应用根，不在 content 下；
  /// 跟题图一样，开发时读工作树、发行包走 assets。
  static String get appIconPath {
    final root = contentRoot;
    return root == null ? "icon.png" : p.join(root, "icon.png");
  }

  static Future<Bank> load() async {
    final curriculum = Curriculum.fromJson(
      jsonDecode(await _read("curriculum.json")) as Map<String, dynamic>,
    );
    final signs = _signsOf(await _read("signs.json"));
    final markings = [
      for (final raw in (jsonDecode(await _read("markings.json")) as Map<String, dynamic>)["markings"] as List<dynamic>)
        Marking.fromJson(raw as Map<String, dynamic>),
    ];
    final gauges = [
      for (final raw in (jsonDecode(await _read("gauges.json")) as Map<String, dynamic>)["gauges"] as List<dynamic>)
        Gauge.fromJson(raw as Map<String, dynamic>),
    ];
    final gestureList = [
      for (final raw in (jsonDecode(await _read("gestures.json")) as Map<String, dynamic>)["gestures"] as List<dynamic>)
        TrafficGesture.fromJson(raw as Map<String, dynamic>),
    ];
    GestureIndex.load(gestureList);
    final henanGroups = [
      for (final raw in (jsonDecode(await _read("henan.json")) as Map<String, dynamic>)["groups"] as List<dynamic>)
        NoteGroup.fromJson(raw as Map<String, dynamic>),
    ];
    final licenseGroups = [
      for (final raw in (jsonDecode(await _read("license_notes.json")) as Map<String, dynamic>)["groups"] as List<dynamic>)
        NoteGroup.fromJson(raw as Map<String, dynamic>),
    ];
    final seen = <String>{};
    final questions = <Question>[
      for (final question in [
        ..._questionsOf(await _read("questions/subject1.json")),
        ..._questionsOf(await _read("questions/subject2.json")),
        ..._questionsOf(await _read("questions/subject4.json")),
      ])
        if (seen.add(question.id)) question,
    ];
    final cheatsheet = [
      for (final raw in (jsonDecode(await _read("cheatsheet.json")) as Map<String, dynamic>)["groups"] as List<dynamic>)
        CheatGroup.fromJson(raw as Map<String, dynamic>),
    ];
    final notes = [
      for (final raw in (jsonDecode(await _read("notes.json")) as Map<String, dynamic>)["groups"] as List<dynamic>)
        NoteGroup.fromJson(raw as Map<String, dynamic>),
    ];
    final guide = Subject2Guide.fromJson(jsonDecode(await _read("subject2.json")) as Map<String, dynamic>);
    // 速记题（ADR 0094）：每张速记卡一道有稳定编号的题，自测作答写成作答记录后，错题本、考前复习、强化练习
    // 按同一份记录带出。知识点号不在课表里，日常题、章节练习、模拟考、解锁判断都不会带上它。
    final catalog = jsonDecode(await _read("sources/catalog.json")) as Map<String, dynamic>;
    final sourceUrls = {
      for (final raw in catalog["sources"] as List<dynamic>)
        (raw as Map<String, dynamic>)["id"] as String: raw["url"] as String? ?? "",
    };
    final recall = recallQuestionsOf(
      signs: signs,
      markings: markings,
      gauges: gauges,
      gestures: gestureList,
      notes: notes,
      henan: henanGroups,
      licenseNotes: licenseGroups,
      numbers: cheatsheet,
      sourceUrls: sourceUrls,
    );
    return Bank(curriculum: curriculum, questions: [...questions, ...recall], signs: signs, markings: markings, gauges: gauges, gestureList: gestureList, cheatsheet: cheatsheet, notes: notes, henanGroups: henanGroups, licenseGroups: licenseGroups, guide: guide);
  }

  static List<RoadSign> _signsOf(String raw) {
    final data = jsonDecode(raw) as Map<String, dynamic>;
    return [
      for (final item in data["signs"] as List<dynamic>)
        RoadSign.fromJson(item as Map<String, dynamic>),
    ];
  }

  static List<Question> _questionsOf(String raw) {
    final data = jsonDecode(raw) as Map<String, dynamic>;
    return [
      for (final item in data["questions"] as List<dynamic>)
        Question.fromJson(item as Map<String, dynamic>),
    ];
  }

  static Future<String> _read(String relative) async {
    // 记的是应用根，不是 content 目录：relative 有一级也有两级，从文件路径倒推会算错。
    // 直接点开 build/ 下的调试包也读工作树里的题库，不读打包时的旧副本（ADR 0030）。
    final root = workingTreeRoot();
    final bases = <String>[?root];
    for (final base in bases) {
      try {
        final file = File(p.join(base, "content", relative));
        if (await file.exists()) {
          contentRoot = base;
          return await file.readAsString();
        }
      } on FileSystemException {
        // macOS 开着 App Sandbox 时文件看得到但读会被拒，改走下一候选或 assets。
        continue;
      }
    }
    return rootBundle.loadString("content/$relative");
  }
}
