import "dart:io";

import "package:flutter_test/flutter_test.dart";

/// 界面图标对照表（ADR 0049）的三条规矩，读源码检查：表是唯一来源，
/// 改表或在别处直接写图标，这里当场报出来。
void main() {
  final table = File("lib/glyphs.dart").readAsStringSync();
  final entries = [
    for (final m in RegExp(r"static const (\w+) = Icons\.(\w+);").allMatches(table)) (m[1]!, m[2]!),
  ];

  test("对照表读得出来", () {
    expect(entries.length, greaterThan(50));
  });

  test("一个图标只表示一个意思：表里没有两个概念共用一个图标", () {
    final byIcon = <String, List<String>>{};
    for (final (name, icon) in entries) {
      byIcon.putIfAbsent(icon, () => []).add(name);
    }
    final shared = {for (final e in byIcon.entries) if (e.value.length > 1) e.key: e.value};
    expect(shared, isEmpty);
  });

  test("统一实心风格：不混描边、圆角、尖角变体", () {
    final variants = [
      for (final (name, icon) in entries)
        if (RegExp(r"_(outlined|outline|rounded|sharp)$").hasMatch(icon)) "$name = $icon",
    ];
    expect(variants, isEmpty);
  });

  test("一个概念只用一个图标：界面代码只用 Glyph，不直接写 Icons.", () {
    final strays = <String>[];
    for (final file in Directory("lib").listSync(recursive: true).whereType<File>()) {
      if (!file.path.endsWith(".dart") || file.path.endsWith("glyphs.dart")) continue;
      final lines = file.readAsLinesSync();
      for (var i = 0; i < lines.length; i++) {
        if (lines[i].contains("Icons.")) strays.add("${file.path}:${i + 1}");
      }
    }
    expect(strays, isEmpty);
  });

  test("小汽车留给应用标志（ADR 0048），不当功能图标", () {
    expect(entries.where((e) => e.$2 == "directions_car"), isEmpty);
  });
}
