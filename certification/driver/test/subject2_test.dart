import "dart:io";

import "package:athena_driver/core/content.dart";
import "package:athena_driver/subject2/drill.dart";
import "package:athena_driver/subject2/guide.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:athena_driver/subject2/subject2.dart";
import "package:flutter/material.dart";
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
    expect(guide.items.map((i) => i.id), [
      "reverse",
      "parallel",
      "curve",
      "corner",
    ]);
    for (final item in guide.items) {
      final scene = drillScenes[item.id];
      expect(scene, isNotNull, reason: item.id);
      expect(
        item.steps.length,
        scene!.steps.length,
        reason: "${item.id} 的讲解步骤和动画步骤对不上",
      );
      expect(
        bank.curriculum.topic(item.topicId),
        isNotNull,
        reason: item.topicId,
      );
      expect(
        bank.forTopic(item.topicId),
        isNotEmpty,
        reason: "${item.id} 没有评判题",
      );
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
        expect(
          excerpts,
          contains("- $clause：${ref.note}"),
          reason: "${q.id} 的 $clause 原句和摘录不一致",
        );
      }
    }
    final guide = bank.guide;
    final rules = [
      ...guide.generalRules,
      for (final i in guide.items) ...i.rules,
    ];
    for (final r in rules) {
      final clause = r.locator.substring("GA 1026—2022 ".length);
      expect(excerpts, contains("- $clause：${r.quote}"), reason: r.text);
    }
    final mistakes = [
      ...guide.generalMistakes,
      for (final i in guide.items) ...i.mistakes,
    ];
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
    final curveStop = guide
        .item("curve")!
        .mistakes
        .firstWhere((m) => m.id == "stop");
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
    final parallel = guide.score("parallel", const [
      "wheel_line",
      "wheel_line",
      "signal",
    ]);
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
    await store.recordDrillRun(
      "curve",
      const [],
      at: at.add(const Duration(minutes: 5)),
    );
    final mine = await store.drillRuns();
    expect(mine.first.itemId, "curve");
    expect(mine.first.mistakes, isEmpty);
    expect(mine.last.mistakes, ["stop", "stop"]);
    await store.close();
  });

  test("C2 卡片五条都指到摘录里的条款，手册按先易后难：直角、曲线、侧方、倒库", () {
    final guide = bank.guide;
    final c2 = guide.c2;
    expect(c2.blocks, hasLength(5));
    expect(c2.note, "经验要点，以教练和考场车型为准");
    expect(c2.order, ["corner", "curve", "parallel", "reverse"]);
    expect(guide.learnItems.map((i) => i.id), [
      "corner",
      "curve",
      "parallel",
      "reverse",
    ]);
    expect(guide.items.map((i) => i.id), [
      "reverse",
      "parallel",
      "curve",
      "corner",
    ]);
    for (final block in c2.blocks) {
      expect(block.body, isNot(contains("后视镜")));
      expect(block.body, isNot(contains("厘米")));
      expect(block.locators, isNotEmpty, reason: block.title);
      for (final l in block.locators) {
        expect(
          excerpts,
          contains("- ${l.substring("GA 1026—2022 ".length)}："),
          reason: "${block.title} $l",
        );
      }
    }
  });

  test("四项每一步都有同屏的车内参照和车外焦点", () {
    for (final id in ["corner", "curve", "parallel", "reverse"]) {
      final item = bank.guide.item(id)!;
      for (var i = 0; i < item.steps.length; i++) {
        final step = item.steps[i];
        final inside = step.inside;
        final outside = step.outside;
        expect(inside, isNotNull, reason: "${step.title} 缺车内");
        expect(outside, isNotNull, reason: "${step.title} 缺车外");
        expect(inside!.look, isNotEmpty);
        expect(inside.action, isNotEmpty);
        expect(outside!.focus, isNotEmpty);
        expect(outside.risk, isNotEmpty);
        expect(step.done, isNotEmpty);
        expect(inside.look, isNot(contains("厘米")));
        expect(inside.look, isNot(contains("门把手")));
        expect(inside.look, isNot(contains("转向灯开关")));
        final spoken = step.narration(i);
        expect(spoken.indexOf("车外："), lessThan(spoken.indexOf("车内看：")));
      }
    }
    expect(bank.guide.item("corner")!.steps[1].inside!.look, "视线保持在车道上，手摸开关");
    expect(bank.guide.item("parallel")!.steps[4].inside!.wrong, "低头找开关");
    expect(bank.guide.item("reverse")!.steps[5].inside!.look, "和第一次同一对关系，从另一侧");
  });

  test("理想走线是全程轨迹，实走余迹是走到一半的前缀", () {
    final timeline = Timeline(curveScene);
    final full = timeline.frame(timeline.total).trail;
    final mid = timeline.frame(timeline.total / 2).trail;
    expect(full.length, greaterThan(mid.length));
    expect(mid.first.dx, closeTo(full.first.dx, 1e-6));
    expect(mid.last.dx, isNot(closeTo(full.last.dx, 0.05)));
  });

  test("直角转弯五步都有方向盘和参照，注意事项不复述扣分", () {
    final item = bank.guide.item("corner")!;
    expect(item.steps, hasLength(5));
    expect(item.requirementLocator, "GA 1026—2022 5.2.7");
    expect(item.requirementQuote, startsWith("驾驶车辆按车道边线"));
    expect(item.rules.map((r) => r.locator), [
      "GA 1026—2022 6.2.3.6 a)",
      "GA 1026—2022 6.2.3.6 b)",
      "GA 1026—2022 6.2.3.6 c)",
      "GA 1026—2022 6.2.3.6 d)",
    ]);
    for (final step in item.steps) {
      expect(step.steer, isNotEmpty, reason: step.title);
      expect(step.reference, isNotEmpty, reason: step.title);
      final texts = [
        step.caution,
        step.steer,
        step.reference,
        step.skill,
        step.outside!.risk,
        for (final fix in step.fix) ...[fix.sign, fix.action],
      ];
      for (final text in texts) {
        expect(text, isNot(contains("扣")), reason: "${step.title}：$text");
        expect(text, isNot(contains("不合格")), reason: "${step.title}：$text");
      }
    }
    for (final tip in item.tips) {
      expect(tip, isNot(contains("扣")));
      expect(tip, isNot(contains("不合格")));
    }
    expect(item.steps[3].fix, hasLength(2));
    expect(item.steps[2].reference, contains("门把手"));
    expect(item.steps[2].inside!.look, isNot(contains("门把手")));
  });

  test("倒库、侧方、曲线每步都有方向盘和参照，四项修正合计不少于 8 条", () {
    var fixes = 0;
    for (final id in ["reverse", "parallel", "curve", "corner"]) {
      final item = bank.guide.item(id)!;
      var itemFixes = 0;
      for (final step in item.steps) {
        expect(step.steer, isNotEmpty, reason: "$id ${step.title}");
        expect(step.reference, isNotEmpty, reason: "$id ${step.title}");
        final texts = [
          step.caution,
          step.steer,
          step.reference,
          step.skill,
          step.outside!.risk,
          for (final fix in step.fix) ...[fix.sign, fix.action],
        ];
        for (final text in texts) {
          expect(text, isNot(contains("扣")), reason: "$id ${step.title}：$text");
          expect(
            text,
            isNot(contains("不合格")),
            reason: "$id ${step.title}：$text",
          );
        }
        itemFixes += step.fix.length;
      }
      for (final tip in item.tips) {
        expect(tip, isNot(contains("扣")), reason: id);
        expect(tip, isNot(contains("不合格")), reason: id);
      }
      expect(itemFixes, greaterThan(0), reason: id);
      fixes += itemFixes;
    }
    expect(fixes, greaterThanOrEqualTo(8));
    expect(bank.guide.item("curve")!.steps[1].title, "第一个弯：左弯");
  });

  testWidgets("车内格画出参照，并把错参照划掉", (tester) async {
    final step = bank.guide.item("curve")!.steps[1];
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SizedBox(
            width: 360,
            height: 480,
            child: CabinPanel(
              step: step,
              gear: Gear.drive,
              signal: Signal.none,
            ),
          ),
        ),
      ),
    );
    expect(find.text(step.inside!.look), findsOneWidget);
    expect(find.textContaining("别按这个：${step.inside!.wrong}"), findsOneWidget);
    expect(find.textContaining("做完：${step.done}"), findsOneWidget);
  });

  test("每一步都有注意事项，条款号能在摘录里找到；讲解稿带上注意事项（ADR 0040）", () {
    for (final item in bank.guide.items) {
      for (var i = 0; i < item.steps.length; i++) {
        final step = item.steps[i];
        expect(
          step.caution,
          isNotEmpty,
          reason: "${item.id} 第 ${i + 1} 步没有注意事项",
        );
        expect(step.cautionLocators, isNotEmpty);
        for (final l in step.cautionLocators) {
          // 场地尺寸的出处是 GB/T 30341—2013 的公式（与 GA 1029 同源），摘录按全条目核对；
          // 其余条款都是 GA 1026—2022，去掉标准号前缀后按条款号核对。
          final clause = l.startsWith("GA 1026—2022 ") ? l.substring("GA 1026—2022 ".length) : l;
          expect(
            excerpts,
            contains("- $clause："),
            reason: "${item.id} 第 ${i + 1} 步 $l",
          );
        }
        expect(
          step.narration(i),
          allOf(
            startsWith("第${i + 1}步，${step.title}。"),
            contains("注意：${step.caution}"),
          ),
        );
      }
    }
  });
}
