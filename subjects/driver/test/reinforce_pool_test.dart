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
  testWidgets("错题库很大：整轮都从还没验收的错题里抽，写明库的大小；换一批抽到另一批", (tester) async {
    late Bank bank;
    late ProgressStore store;
    late Set<String> wrongIds;
    late Set<String> retiredIds;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      store = await ProgressStore.open(suite: "reinforce_pool");
      final pool = bank.forSubject("subject1").where((q) => !q.isRare).toList();
      final wrong = pool.take(150).toList();
      wrongIds = {for (final q in wrong) q.id};
      for (final q in wrong) {
        await store.recordAttempt(questionId: q.id, topicId: q.topicId, subjectId: "subject1", correct: false);
      }
      // 前 20 道后来在练习里又答对了：在别处答对不算验收，仍在备选库里
      for (final q in wrong.take(20)) {
        await store.recordAttempt(questionId: q.id, topicId: q.topicId, subjectId: "subject1", correct: true);
      }
      // 中间 15 道在强化练习里测过，而且没有出错 → 已经移出备选库
      retiredIds = {for (final q in wrong.skip(20).take(15)) q.id};
      for (final q in wrong.skip(20).take(15)) {
        await store.recordAttempt(
            questionId: q.id, topicId: q.topicId, subjectId: "subject1", correct: true, kind: "reinforce");
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
    expect(find.textContaining("历史上答错过 150 题，其中还要练 135 题"), findsOneWidget);
    expect(find.textContaining("135 题还没在强化练习里测过"), findsOneWidget);
    expect(find.textContaining("测过且没有出错的 15 题已移出"), findsOneWidget);
    expect(find.textContaining("复测错题 50"), findsOneWidget, reason: "备选库够大：整轮 50 题都来自它");
    // 备选库的大小直接用大号数字摆出来
    expect(find.text("135"), findsWidgets, reason: "备选库 135 题，大号数字");
    expect(find.textContaining("还要练的错题（备选库）"), findsOneWidget);
    expect(find.text("换一批"), findsOneWidget);

    Set<String> started() => {for (final q in tester.widget<SessionStage>(find.byType(SessionStage)).launch.questions) q.id};

    await tester.tap(find.textContaining("开始强化练习"));
    await tester.pump();
    final first = started();
    expect(first, hasLength(50));
    expect(first.difference(wrongIds), isEmpty, reason: "整轮都来自历史错题");
    expect(first.intersection(retiredIds), isEmpty, reason: "已经移出的 15 道不再出现");

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
    expect(second.intersection(retiredIds), isEmpty);
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
