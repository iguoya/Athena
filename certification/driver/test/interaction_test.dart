import "dart:async";
import "dart:io";

import "package:athena_driver/study/clusters.dart";
import "package:athena_driver/core/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:athena_driver/study/session.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

/// 交互闭环的守卫（ADR 0061）：空态有出口，不能把人晾在原地。用空进度库渲染真实首页。
void main() {
  testWidgets("错题本空态有「去强化练习」的出口，强化页空池有「去练新题」的出口", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-interact-");
      store = await ProgressStore.open(suite: "interaction_test");
    });
    await tester.binding.setSurfaceSize(const Size(1600, 1200));
    final ready = Completer<void>();
    await tester.pumpWidget(
      MaterialApp(
        home: HomePage(
          bank: bank,
          store: store,
          onReady: ready.complete,
          clusterBuilder: (_) async => ClusterIndex.empty,
        ),
      ),
    );
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue, reason: "首页没在 20 秒内读完进度库");

    // 空库进错题本：文案诚实，出口接强化练习。
    await tester.tap(find.text("错题本").first);
    await tester.pump();
    expect(find.text("最近一次都做对了。"), findsOneWidget);
    await tester.tap(find.text("去强化练习"));
    await tester.pump();

    // 强化页：错题库为空时按薄弱章节抽新题补满一轮（主仓库 ADR 0085），
    // 题单可直接开始——空态没有断头。
    expect(find.textContaining("开始强化练习"), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });

  testWidgets("章节下有「练新题」行，点起的一轮全是没答过的题（ADR 0070）", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-fresh-");
      store = await ProgressStore.open(suite: "interaction_fresh_test");
      // 第一章里先答几道，它们不该再出现在「练新题」里。
      final topic = bank.curriculum.subject("subject1").topics.first;
      final some = bank.forTopic(topic.id).where((q) => !q.isRare).take(3).toList();
      for (final q in some) {
        await store.recordAttempt(questionId: q.id, topicId: q.topicId, subjectId: "subject1", correct: false);
      }
    });
    await tester.binding.setSurfaceSize(const Size(1600, 1400));
    final ready = Completer<void>();
    await tester.pumpWidget(
      MaterialApp(
        home: HomePage(
          bank: bank,
          store: store,
          onReady: ready.complete,
          clusterBuilder: (_) async => ClusterIndex.empty,
        ),
      ),
    );
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue);

    final topic = bank.curriculum.subject("subject1").topics.first;
    await tester.tap(find.textContaining("练新题").first);
    await tester.pump(const Duration(seconds: 1));
    final stage = tester.widget<SessionStage>(find.byType(SessionStage));
    final answered = {
      for (final q in bank.forTopic(topic.id).where((q) => !q.isRare).take(3)) q.id,
    };
    expect(
      answered.intersection({for (final q in stage.launch.questions) q.id}),
      isEmpty,
      reason: "刚答过的 3 道不该混进新题轮",
    );
    expect(stage.launch.attemptKind ?? "practice", "practice", reason: "章节练习不是强化练习场合");
    expect(stage.launch.timed, isFalse);

    await tester.runAsync(() => Future<void>.delayed(const Duration(seconds: 6)));
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });

  testWidgets("专题全部掌握后仍可重练：入口不再点不了，确认后整章再练一遍（ADR 0125）", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-repractice-");
      store = await ProgressStore.open(suite: "interaction_repractice_test");
      // 第一个专题的全部日常题各答对一次：专题练完，其余专题照旧有待练。
      final topic = bank.curriculum.subject("subject1").topics.first;
      for (final q in bank.forTopic(topic.id).where((q) => !q.isRare)) {
        await store.recordAttempt(questionId: q.id, topicId: q.topicId, subjectId: "subject1", correct: true);
      }
    });
    await tester.binding.setSurfaceSize(const Size(1600, 2600));
    final ready = Completer<void>();
    await tester.pumpWidget(
      MaterialApp(home: HomePage(bank: bank, store: store, onReady: ready.complete)),
    );
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue);

    Finder inSidebar(Finder f) => find.descendant(of: find.byType(ListView).first, matching: f);
    final topic = bank.curriculum.subject("subject1").topics.first;
    final daily = bank.forTopic(topic.id).where((q) => !q.isRare).toList();

    // 入口活着：标签变成「（重练）」，点了先问，不直接起会话。
    await tester.tap(inSidebar(find.textContaining("（重练）").first));
    await tester.pump();
    expect(find.text("全部掌握，重新练习？"), findsOneWidget);
    expect(find.byType(SessionStage), findsNothing);

    // 取消：什么都不发生。
    await tester.tap(find.text("先不用"));
    await tester.pump();
    expect(find.byType(SessionStage), findsNothing);

    // 确认：起一轮，题单正好是这一章的全部日常题。
    await tester.tap(inSidebar(find.textContaining("（重练）").first));
    await tester.pump();
    await tester.tap(find.text("重新练习"));
    await tester.pump(const Duration(seconds: 1));
    final stage = tester.widget<SessionStage>(find.byType(SessionStage));
    expect(
      {for (final q in stage.launch.questions) q.id},
      {for (final q in daily) q.id},
      reason: "重练不过滤待练：已掌握的整章题全在题单里",
    );
    expect(stage.launch.timed, isFalse);

    await tester.runAsync(() => Future<void>.delayed(const Duration(seconds: 6)));
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });

  testWidgets("科目一全部掌握后：侧栏入口变「重新练习（全部 n 题）」，概览按钮变「重新练习全部题」（ADR 0125）", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-repractice-all-");
      store = await ProgressStore.open(suite: "interaction_repractice_all_test");
      // 科目一全部日常题各答对一次：待练清零，科目四随之解锁。
      for (final q in bank.forSubject("subject1").where((q) => !q.isRare)) {
        await store.recordAttempt(questionId: q.id, topicId: q.topicId, subjectId: "subject1", correct: true);
      }
    });
    await tester.binding.setSurfaceSize(const Size(1600, 2600));
    final ready = Completer<void>();
    await tester.pumpWidget(
      MaterialApp(home: HomePage(bank: bank, store: store, onReady: ready.complete)),
    );
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue);

    final daily = bank.forSubject("subject1").where((q) => !q.isRare).toList();

    // 侧栏入口不再是灰死的「全部练习（已掌握）」。
    Finder inSidebar(Finder f) => find.descendant(of: find.byType(ListView).first, matching: f);
    final entry = inSidebar(find.textContaining("重新练习（全部 ${daily.length} 题）"));
    expect(entry, findsOneWidget);

    // 概览页按钮也能重练。
    await tester.tap(inSidebar(find.text("科目一")).first);
    await tester.pump();
    expect(find.text("重新练习全部题"), findsOneWidget);

    // 确认后起一轮，全部日常题都在。
    await tester.tap(find.text("重新练习全部题"));
    await tester.pump();
    await tester.tap(find.text("重新练习"));
    await tester.pump(const Duration(seconds: 1));
    final stage = tester.widget<SessionStage>(find.byType(SessionStage));
    expect(stage.launch.questions.length, daily.length);
    // 解锁状态不受重练影响：科目四照常可进，没有重新锁上。
    expect(find.textContaining("科目四"), findsWidgets);

    await tester.runAsync(() => Future<void>.delayed(const Duration(seconds: 6)));
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
