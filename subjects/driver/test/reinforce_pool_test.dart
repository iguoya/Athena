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
  // 强化练习从历史上全部错题里按权重抽取（主仓库 ADR 0085）：
  // 页面写明错题池有多大；错题池够大时整轮都来自它；「换一批」重新抽，抽到的是另一批。
  testWidgets("错题池很大：整轮都从历史错题里抽，写明池子大小；换一批抽到另一批", (tester) async {
    late Bank bank;
    late ProgressStore store;
    late Set<String> wrongIds;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      store = await ProgressStore.open(suite: "reinforce_pool");
      final pool = bank.forSubject("subject1").where((q) => !q.isRare).toList();
      final wrong = pool.take(60).toList();
      wrongIds = {for (final q in wrong) q.id};
      for (final q in wrong) {
        await store.recordAttempt(questionId: q.id, topicId: q.topicId, subjectId: "subject1", correct: false);
      }
      // 其中 20 道后来又答对了：旧规则里它们早就掉出复测池，现在仍在错题池里
      for (final q in wrong.take(20)) {
        await store.recordAttempt(questionId: q.id, topicId: q.topicId, subjectId: "subject1", correct: true);
      }
    });

    await tester.binding.setSurfaceSize(const Size(1600, 1200));
    final ready = Completer<void>();
    await tester.pumpWidget(MaterialApp(
      home: HomePage(bank: bank, store: store, onReady: ready.complete, clusterBuilder: (_) async => ClusterIndex.empty),
    ));
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue);

    await tester.tap(find.text("强化练习").first);
    await tester.pump();
    expect(find.textContaining("历史上答错过的全部 60 题"), findsOneWidget, reason: "后来答对过的 20 道也在池子里");
    expect(find.textContaining("复测错题 20"), findsOneWidget, reason: "错题池够大：整轮 20 题都来自它");
    expect(find.text("换一批"), findsOneWidget);

    Set<String> started() => {for (final q in tester.widget<SessionStage>(find.byType(SessionStage)).launch.questions) q.id};

    await tester.tap(find.textContaining("开始强化练习"));
    await tester.pump();
    final first = started();
    expect(first, hasLength(20));
    expect(first.difference(wrongIds), isEmpty, reason: "整轮都来自历史错题");

    // 在做题台里直接回到强化练习页，点「换一批」，再开始：抽到的是另一批
    await tester.tap(find.text("强化练习").first);
    for (var i = 0; i < 300 && find.text("换一批").evaluate().isEmpty; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    await tester.tap(find.text("换一批"));
    await tester.pump();
    await tester.tap(find.textContaining("开始强化练习"));
    await tester.pump();
    final second = started();
    expect(second.difference(wrongIds), isEmpty);
    expect(second, isNot(equals(first)), reason: "换一批要抽到另一批题，不能总是同一批");

    await tester.runAsync(() => Future<void>.delayed(const Duration(seconds: 6)));
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() => store.close());
  });

  testWidgets("还没有答错过的题：页面说明先练薄弱章节的新题，错题池为空", (tester) async {
    late Bank bank;
    late ProgressStore store;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      store = await ProgressStore.open(suite: "reinforce_pool_empty");
    });
    await tester.binding.setSurfaceSize(const Size(1600, 1200));
    final ready = Completer<void>();
    await tester.pumpWidget(MaterialApp(
      home: HomePage(bank: bank, store: store, onReady: ready.complete, clusterBuilder: (_) async => ClusterIndex.empty),
    ));
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    await tester.tap(find.text("强化练习").first);
    await tester.pump();
    expect(find.textContaining("还没有答错过的题"), findsOneWidget);
    expect(find.textContaining("历史上答错过的全部"), findsNothing);
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() => store.close());
  });
}
