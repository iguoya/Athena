import "dart:async";

import "package:athena_driver/clusters.dart";
import "package:athena_driver/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:athena_driver/session.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  // 强化练习（主仓库 ADR 0076）：错题、薄弱章节、间隔到期合成一张题单；
  // 页面说明为什么这样选，开始后作答的场合标记是 reinforce，不是 practice 也不是 exam。
  testWidgets("强化练习页：题单构成、漏斗、通过概率与真实模拟考并列；开始后作答带 reinforce 标记", (tester) async {
    late Bank bank;
    late ProgressStore store;
    late List<Question> wrongOnes;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      store = await ProgressStore.open(suite: "reinforce_page_test");
      final pool = bank.forSubject("subject1").where((q) => !q.isRare).toList();
      wrongOnes = pool.take(6).toList();
      for (final q in wrongOnes) {
        await store.recordAttempt(questionId: q.id, topicId: q.topicId, subjectId: "subject1", correct: false);
      }
      await store.recordExam(subjectId: "subject1", score: 92, passed: true);
      await store.recordExam(subjectId: "subject1", score: 86, passed: false);
    });

    await tester.binding.setSurfaceSize(const Size(1600, 1200));
    final ready = Completer<void>();
    await tester.pumpWidget(MaterialApp(home: HomePage(bank: bank, store: store, onReady: ready.complete, clusterBuilder: (_) async => ClusterIndex.empty)));
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue, reason: "首页没在 20 秒内读完进度库");

    await tester.tap(find.text("强化练习").first);
    await tester.pump();

    // 题单构成：做错的 6 道进了复测，其余按薄弱章节补足
    expect(find.textContaining("复测错题 6"), findsOneWidget);
    expect(find.textContaining("薄弱章节"), findsWidgets);
    expect(find.textContaining("开始强化练习 20 题"), findsOneWidget);
    expect(find.textContaining("模拟考仍从整个题库按考场配比抽取"), findsOneWidget);

    // 掌握度漏斗
    expect(find.textContaining("学习中 6"), findsOneWidget);
    expect(find.textContaining("新题"), findsWidgets);

    // 真实模拟考与模型估计并列
    expect(find.textContaining("最近 2 场模拟考"), findsOneWidget);
    for (var i = 0; i < 3000 && find.textContaining("模型估计：").evaluate().isEmpty; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 20)));
      await tester.pump();
    }
    expect(find.textContaining("模型估计："), findsOneWidget, reason: "通过概率应在后台算完并显示");
    expect(find.textContaining("以真实模拟考为准"), findsOneWidget);

    // 优先章节
    expect(find.text("优先练哪几章"), findsOneWidget);

    // 开始：作答的场合标记是 reinforce，不计时（不是模拟考）
    await tester.tap(find.textContaining("开始强化练习"));
    await tester.pump();
    final stage = tester.widget<SessionStage>(find.byType(SessionStage));
    expect(stage.launch.attemptKind, "reinforce");
    expect(stage.launch.timed, isFalse);
    expect(stage.launch.questions, hasLength(20));
    expect({for (final q in stage.launch.questions) q.id}, hasLength(20), reason: "每题只出一次");
    expect(
      {for (final q in wrongOnes) q.id}.difference({for (final q in stage.launch.questions) q.id}),
      isEmpty,
      reason: "6 道错题都在复测里",
    );
    expect(tester.takeException(), isNull);

    // 做题台一出现，朗读模块就去问系统有哪些语音（起一个系统进程）；等它跑完再收场，
    // 免得测试结束时还挂着定时器。
    await tester.runAsync(() => Future<void>.delayed(const Duration(seconds: 6)));
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() => store.close());
  });

  testWidgets("有考点簇时，题单里出现「同考点变式」，并在后台算好簇后自动换题单（ADR 0079）", (tester) async {
    late Bank bank;
    late ProgressStore store;
    late List<Question> wrong;
    late List<Question> mates;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      store = await ProgressStore.open(suite: "reinforce_page_variants");
      final pool = bank.forSubject("subject1").where((q) => !q.isRare).toList();
      wrong = pool.take(6).toList();
      mates = pool.skip(100).take(6).toList();
      for (final q in wrong) {
        await store.recordAttempt(questionId: q.id, topicId: q.topicId, subjectId: "subject1", correct: false);
      }
    });
    final clusters = ClusterIndex([
      for (var i = 0; i < 6; i++) [wrong[i].id, mates[i].id],
    ], {
      for (var i = 0; i < 6; i++) ...{wrong[i].id: i, mates[i].id: i},
    });
    await tester.binding.setSurfaceSize(const Size(1600, 1200));
    final ready = Completer<void>();
    await tester.pumpWidget(MaterialApp(
      home: HomePage(bank: bank, store: store, onReady: ready.complete, clusterBuilder: (_) async => clusters),
    ));
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue);
    await tester.tap(find.text("强化练习").first);
    for (var i = 0; i < 300 && find.textContaining("同考点变式").evaluate().isEmpty; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(find.textContaining("同考点变式"), findsWidgets, reason: "簇算好后题单里应有变式");
    expect(find.textContaining("复测错题 6"), findsOneWidget, reason: "6 道错题照样都在复测里");

    await tester.tap(find.textContaining("开始强化练习"));
    await tester.pump();
    final stage = tester.widget<SessionStage>(find.byType(SessionStage));
    final reasons = stage.launch.reasons!;
    final variantIds = [for (final e in reasons.entries) if (e.value == "variant") e.key];
    expect(variantIds, isNotEmpty);
    expect(variantIds.toSet().difference({for (final q in mates) q.id}), isEmpty, reason: "变式都是错题的同簇题");
    await tester.runAsync(() => Future<void>.delayed(const Duration(seconds: 6)));
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() => store.close());
  });
}
