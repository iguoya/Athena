import "dart:async";

import "package:athena_driver/study/clusters.dart";
import "package:athena_driver/core/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  // 回归：强化练习的题单跟错题直接挂钩（主仓库 ADR 0076）。
  // 旧行为：在做题台里直接点侧栏离开（没点结果页的「回到章节」），不会走 onClose，作答早已一题题写进库，
  // 可题单、错题数、掌握度还是进做题台之前的旧数据，刚错的题进不了「复测」。
  testWidgets("在做题台里直接点侧栏回到强化练习，刚答错的题要进复测", (tester) async {
    late Bank bank;
    late ProgressStore store;
    late Question freshWrong;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      store = await ProgressStore.open(suite: "reinforce_refresh");
      final pool = bank.forSubject("subject1").where((q) => !q.isRare).toList();
      for (final q in pool.take(6)) {
        await store.recordAttempt(questionId: q.id, topicId: q.topicId, subjectId: "subject1", correct: false);
      }
      freshWrong = pool[6];
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
    expect(ready.isCompleted, isTrue, reason: "首页没在 20 秒内读完进度库");

    await tester.tap(find.text("强化练习").first);
    await tester.pump();
    expect(find.textContaining("复测错题 6"), findsOneWidget);

    // 开始强化练习，进入做题台
    await tester.tap(find.textContaining("开始强化练习"));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.textContaining("开始强化练习"), findsNothing, reason: "应该已经在做题台里了");

    // 在做题台里又答错了一道新题（作答一题一题写进库）
    await tester.runAsync(() => store.recordAttempt(
          questionId: freshWrong.id,
          topicId: freshWrong.topicId,
          subjectId: "subject1",
          correct: false,
        ));

    // 不点结果页的按钮，直接点侧栏的「强化练习」离开
    await tester.tap(find.text("强化练习").first);
    for (var i = 0; i < 2000 && find.textContaining("复测错题 7").evaluate().isEmpty; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(find.textContaining("复测错题 7"), findsOneWidget, reason: "刚答错的那道应该进复测，题单要跟着错题更新");

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() => store.close());
  });
}
