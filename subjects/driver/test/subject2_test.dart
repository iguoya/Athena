import "dart:io";

import "package:athena_driver/content.dart";
import "package:athena_driver/drill.dart";
import "package:athena_driver/guide.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  late Bank bank;
  late String excerpts;

  setUpAll(() async {
    bank = await ContentLoader.load();
    excerpts = File("content/sources/reference/excerpts.md").readAsStringSync();
  });

  test("科目二四项都有动画，讲解步骤数和动画步骤数一致（ADR 0036）", () {
    final guide = bank.guide;
    expect(guide.items.map((i) => i.id), ["reverse", "parallel", "curve", "corner"]);
    for (final item in guide.items) {
      final scene = drillScenes[item.id];
      expect(scene, isNotNull, reason: item.id);
      expect(item.steps.length, scene!.steps.length, reason: "${item.id} 的讲解步骤和动画步骤对不上");
      expect(bank.curriculum.topic(item.topicId), isNotNull, reason: item.topicId);
      expect(bank.forTopic(item.topicId), isNotEmpty, reason: "${item.id} 没有评判题");
    }
  });

  test("科目二的题目、评判条目、错因都指到 GA 1026—2022 条款，原句能在摘录里逐字找到", () {
    final questions = bank.forSubject("subject2");
    expect(questions.length, greaterThanOrEqualTo(40));
    for (final q in questions) {
      for (final ref in q.sourceRefs) {
        expect(ref.sourceId, "ga-1026", reason: q.id);
        expect(ref.locator, startsWith("GA 1026—2022 "), reason: q.id);
        final clause = ref.locator.substring("GA 1026—2022 ".length);
        expect(excerpts, contains("- $clause：${ref.note}"), reason: "${q.id} 的 $clause 原句和摘录不一致");
      }
    }
    final guide = bank.guide;
    final rules = [...guide.generalRules, for (final i in guide.items) ...i.rules];
    for (final r in rules) {
      final clause = r.locator.substring("GA 1026—2022 ".length);
      expect(excerpts, contains("- $clause：${r.quote}"), reason: r.text);
    }
    final mistakes = [...guide.generalMistakes, for (final i in guide.items) ...i.mistakes];
    for (final m in mistakes) {
      final clause = m.locator.substring("GA 1026—2022 ".length);
      expect(excerpts, contains("- $clause："), reason: m.label);
    }
  });

  test("评判数字对得上原文：C2 80 分合格，倒车入库 3.5 分钟，侧方停车 1.5 分钟，曲线行驶中途停车扣 5 分", () {
    final guide = bank.guide;
    expect(guide.passScore, 80);
    expect(guide.item("reverse")!.limitText, "3.5 分钟");
    expect(guide.item("parallel")!.limitText, "1.5 分钟");
    final curveStop = guide.item("curve")!.mistakes.firstWhere((m) => m.id == "stop");
    expect(curveStop.level.fails, isFalse);
    expect(curveStop.level.deduct, 5);
  });

  test("按考场规则给一把练车打分：不合格压过分数，扣分累计，按次计的可以扣多次", () {
    final guide = bank.guide;
    expect(guide.score("reverse", const []).label, "100 分");
    expect(guide.score("reverse", const []).passed, isTrue);
    // 中途停车两次：100 - 5 - 5。
    expect(guide.score("reverse", const ["stop", "stop"]).score, 90);
    // 侧方停车：车轮压线两次 + 出库没开灯 = 扣 30，70 分不及格。
    final parallel = guide.score("parallel", const ["wheel_line", "wheel_line", "signal"]);
    expect(parallel.score, 70);
    expect(parallel.failed, isFalse);
    expect(parallel.passed, isFalse);
    // 通用错因也能勾：没系安全带直接不合格。
    final belt = guide.score("curve", const ["seatbelt"]);
    expect(belt.failed, isTrue);
    expect(belt.failReasons, ["没系安全带"]);
    // 认不出的旧 id 忽略，不让统计崩掉。
    expect(guide.score("corner", const ["no_such_mistake"]).score, 100);
    expect(Level.parse("-10").label, "扣 10 分");
  });

  test("练车记录能存能读，新的在前", () async {
    final store = await ProgressStore.open(suite: "subject2_test");
    final at = DateTime(2026, 9, 28, 20, 0);
    await store.recordDrillRun("reverse", const ["stop", "stop"], at: at);
    await store.recordDrillRun("curve", const [], at: at.add(const Duration(minutes: 5)));
    final mine = await store.drillRuns();
    expect(mine.first.itemId, "curve");
    expect(mine.first.mistakes, isEmpty);
    expect(mine.last.mistakes, ["stop", "stop"]);
    await store.close();
  });

  test("每一步都有注意事项，条款号能在摘录里找到；讲解稿带上注意事项（ADR 0040）", () {
    for (final item in bank.guide.items) {
      for (var i = 0; i < item.steps.length; i++) {
        final step = item.steps[i];
        expect(step.caution, isNotEmpty, reason: "${item.id} 第 ${i + 1} 步没有注意事项");
        expect(step.cautionLocators, isNotEmpty);
        for (final l in step.cautionLocators) {
          expect(excerpts, contains("- ${l.substring("GA 1026—2022 ".length)}："), reason: "${item.id} 第 ${i + 1} 步 $l");
        }
        expect(step.narration(i), allOf(startsWith("第${i + 1}步，${step.title}。"), contains("注意：${step.caution}")));
      }
    }
  });
}
