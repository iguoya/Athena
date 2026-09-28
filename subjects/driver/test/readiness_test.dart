import "package:athena_driver/content.dart";
import "package:athena_driver/guide.dart";
import "package:athena_driver/progress.dart";
import "package:athena_driver/readiness.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  late Subject2Guide guide;

  setUpAll(() async {
    guide = (await ContentLoader.load()).guide;
  });

  var clock = DateTime(2026, 9, 28, 20);
  // 新的在前。
  List<DrillRun> runs(String item, List<List<String>> mistakes) => [
        for (final m in mistakes) DrillRun(itemId: item, mistakes: m, at: clock = clock.subtract(const Duration(minutes: 1))),
      ];
  List<DrillRun> all(Map<String, List<List<String>>> byItem) =>
      [for (final e in byItem.entries) ...runs(e.key, e.value)]..sort((a, b) => b.at.compareTo(a.at));

  test("有一项少于 3 把：数据不够，不给整场结论", () {
    final r = computeReadiness(guide, all({"reverse": [[], [], []], "parallel": [[], [], []], "curve": [[], [], []], "corner": [[], []]}));
    expect(r.enough, isFalse);
    expect(r.rate, isNull);
    expect(r.missing.map((i) => i.item.id), ["corner"]);
  });

  test("四项最近都干净：整场 100%", () {
    final clean = [<String>[], <String>[], <String>[]];
    final r = computeReadiness(guide, all({"reverse": clean, "parallel": clean, "curve": clean, "corner": clean}));
    expect(r.combos, 81);
    expect(r.rate, 1.0);
    expect(r.culprits, isEmpty);
  });

  test("一项 5 把里 1 把不合格、其余干净：整场 80%，罪魁就是那个错", () {
    final clean = [<String>[], <String>[], <String>[]];
    final r = computeReadiness(guide, all({
      "reverse": [[], [], ["body_out"], [], []],
      "parallel": clean,
      "curve": clean,
      "corner": clean,
    }));
    expect(r.combos, 5 * 27);
    expect(r.rate, closeTo(0.8, 1e-9));
    expect(r.culprits.first.itemId, "reverse");
    expect(r.culprits.first.mistake.id, "body_out");
  });

  test("扣分四项累计：每项单独都是 90 分能过，合起来扣 40 分整场过不了", () {
    final twoStops = [["stop", "stop"], ["stop", "stop"], ["stop", "stop"]];
    final r = computeReadiness(guide, all({"reverse": twoStops, "parallel": twoStops, "curve": twoStops, "corner": twoStops}));
    for (final i in r.items) {
      expect(i.passRate, 1.0, reason: "${i.item.id} 单项每把 90 分，能过");
      expect(i.avgDeduct, 10);
    }
    expect(r.rate, 0.0);
    expect(r.culprits.first.mistake.id, "stop");
  });

  test("只看最近 5 把：更早的不合格不影响", () {
    final clean = [<String>[], <String>[], <String>[]];
    final r = computeReadiness(guide, all({
      "reverse": [[], [], [], [], [], ["body_out"], ["body_out"]],
      "parallel": clean,
      "curve": clean,
      "corner": clean,
    }));
    expect(r.items.first.recent, hasLength(readinessWindow));
    expect(r.rate, 1.0);
  });
}
