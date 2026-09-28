import "package:athena_driver/brief.dart";
import "package:athena_driver/content.dart";
import "package:athena_driver/guide.dart";
import "package:athena_driver/progress.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  late Subject2Guide guide;

  setUpAll(() async {
    guide = (await ContentLoader.load()).guide;
  });

  // 新的在前，跟 ProgressStore.drillRuns 一致。
  List<DrillRun> runs(String item, List<List<String>> mistakes, {DateTime? from}) {
    final start = from ?? DateTime(2026, 9, 28, 20);
    return [
      for (var i = 0; i < mistakes.length; i++)
        DrillRun(itemId: item, mistakes: mistakes[i], at: start.subtract(Duration(minutes: 10 * i))),
    ];
  }

  test("没有记录就不给建议：只提示每项还没记过", () {
    final brief = buildBrief(guide, const []);
    expect(brief.empty, isTrue);
    expect(brief.focus.every((f) => f.kind == FocusKind.untried), isTrue);
    expect(brief.focus, hasLength(briefFocusLimit));
  });

  test("只看最近 5 把；在其中 ≥ 2 把出现的错算反复出现，同一把里出现多次只算一把", () {
    final reverse = runs("reverse", [
      ["stop", "stop", "stop"],
      [],
      ["stop"],
      ["body_out"],
      [],
      // 第 6 把起不在窗口里
      ["body_out"],
      ["body_out"],
    ]);
    final b = buildBrief(guide, reverse).item("reverse")!;
    expect(b.recent, 5);
    expect(b.recurring.map((r) => r.mistake.id), ["stop"]);
    expect(b.recurring.single.runs, 2);
    // 5 把里：第 1 把 85 分能过，第 2、3、5 把能过，第 4 把车身出线不合格 → 4 把能过。
    expect(b.passes, 4);
    expect(b.weak, isFalse);
  });

  test("重点排序：不合格的反复错排在扣分前面；能过不到 60% 的项要关注；同一项只留最重的一条", () {
    final all = [
      ...runs("curve", [
        ["stop"],
        ["stop"],
        ["stop"],
      ]),
      ...runs("corner", [
        ["wheel_line"],
        ["wheel_line"],
        [],
      ], from: DateTime(2026, 9, 28, 19)),
    ]..sort((a, b) => b.at.compareTo(a.at));
    final brief = buildBrief(guide, all);
    // 直角转弯压线（不合格）先于曲线行驶中途停车（扣 5 分），尽管后者出现得更多。
    expect(brief.focus.first.itemId, "corner");
    expect(brief.focus.first.kind, FocusKind.mistake);
    expect(brief.focus[1].itemId, "curve");
    // 直角转弯 3 把能过 1 把，是 weak，但它已经有一条更重的重点，不再重复列。
    expect(brief.item("corner")!.weak, isTrue);
    expect(brief.focus.where((f) => f.itemId == "corner"), hasLength(1));
    expect(brief.focus, hasLength(briefFocusLimit));
    expect(brief.focus.last.kind, FocusKind.untried);
    expect(brief.lastAt, DateTime(2026, 9, 28, 20));
  });

  test("默演卡住的步骤进简报", () {
    final brief = buildBrief(guide, runs("reverse", [[], []]), missedSteps: const {"reverse": [2, 3]});
    expect(brief.item("reverse")!.missedSteps, [2, 3]);
    final line = brief.focus.firstWhere((f) => f.kind == FocusKind.rehearsal);
    expect(line.text, contains("第 3 步、第 4 步"));
  });
}
