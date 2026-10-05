import "dart:async";

import "package:athena_driver/study/clusters.dart";
import "package:athena_driver/core/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  Future<void> openReinforce(WidgetTester tester, Bank bank, ProgressStore store) async {
    await tester.binding.setSurfaceSize(const Size(1600, 1400));
    final ready = Completer<void>();
    await tester.pumpWidget(MaterialApp(home: HomePage(bank: bank, store: store, onReady: ready.complete, clusterBuilder: (_) async => ClusterIndex.empty)));
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue, reason: "首页没在 20 秒内读完进度库");
    await tester.tap(find.text("强化练习").first);
    await tester.pump();
  }

  testWidgets("学习诊断：没有记录时每一块都老实说「还没有」，不编结论", (tester) async {
    late Bank bank;
    late ProgressStore store;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      store = await ProgressStore.open(suite: "diagnosis_page_empty");
    });
    await openReinforce(tester, bank, store);

    expect(find.text("学习诊断"), findsOneWidget);
    expect(find.textContaining("有结论的档位还少"), findsOneWidget);
    expect(find.textContaining("暂时没法判断「快」和「慢」"), findsOneWidget);
    expect(find.textContaining("还没有记了所选选项的答错记录"), findsOneWidget);
    expect(find.textContaining("还没有带全国错误率的题的作答记录"), findsOneWidget);
    expect(find.textContaining("还没有记了选题理由的强化练习作答"), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() => store.close());
  });

  testWidgets("学习诊断：有用时、所选选项、选题理由的记录时，各块给出统计", (tester) async {
    late Bank bank;
    late ProgressStore store;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      store = await ProgressStore.open(suite: "diagnosis_page_rich");
      // 取带全国错误率的单选题，才能同时验证「选错的方式」和「与全国比」。
      final pool = bank.forSubject("subject1").where((q) => !q.isRare && q.errorRate != null && !q.isMulti && q.kind == "single").take(30).toList();
      expect(pool.length, 30, reason: "题库里应有足够的带错误率的单选题");
      String wrongPick(Question q) => q.choices.firstWhere((c) => !c.ok).id;
      final day0 = DateTime(2026, 9, 28, 9);
      for (var i = 0; i < pool.length; i++) {
        final q = pool[i];
        // 第 0 天答对（用时 10 秒）；第 1 天：前 20 道答对，后 10 道答错且很慢（不会），选了同一个错选项
        await store.recordAttempt(
          questionId: q.id, topicId: q.topicId, subjectId: "subject1", correct: true, durationMs: 10000,
          chosen: q.choices.firstWhere((c) => c.ok).id, sessionId: "s0", at: day0.add(Duration(minutes: i)),
        );
        final ok = i < 20;
        await store.recordAttempt(
          questionId: q.id, topicId: q.topicId, subjectId: "subject1", correct: ok, durationMs: ok ? 10000 : 20000,
          chosen: ok ? q.choices.firstWhere((c) => c.ok).id : wrongPick(q), sessionId: "s1",
          at: day0.add(Duration(days: 1, minutes: i)),
        );
      }
      // 其中 3 道在第 2 天又错一次，选的还是同一个错选项 -> 「反复选同一个错误选项」
      for (final q in pool.skip(20).take(3)) {
        await store.recordAttempt(
          questionId: q.id, topicId: q.topicId, subjectId: "subject1", correct: false, durationMs: 20000,
          chosen: wrongPick(q), sessionId: "s2", at: day0.add(const Duration(days: 2)),
        );
      }
      // 强化练习：复测错题 2 道，一对一错
      await store.recordAttempt(
        questionId: pool[20].id, topicId: pool[20].topicId, subjectId: "reinforce", kind: "reinforce", correct: true,
        durationMs: 9000, chosen: pool[20].choices.firstWhere((c) => c.ok).id, sessionId: "s3", reason: "retest",
        at: day0.add(const Duration(days: 3)),
      );
      await store.recordAttempt(
        questionId: pool[21].id, topicId: pool[21].topicId, subjectId: "reinforce", kind: "reinforce", correct: false,
        durationMs: 9000, chosen: wrongPick(pool[21]), sessionId: "s3", reason: "retest",
        at: day0.add(const Duration(days: 3, minutes: 1)),
      );
    });
    await openReinforce(tester, bank, store);

    // 记忆保持：隔 1 天这一档有 30 对，前 20 对答对，所以是 67%
    expect(find.textContaining("67%（20/30）"), findsOneWidget);
    // 错因：答对 50 次、中位数 10 秒；10 次第二天慢而错 + 3 次第三天慢而错 = 13 次不会
    expect(find.textContaining("你答对一题通常用 10 秒"), findsOneWidget);
    expect(find.textContaining("不会 13"), findsOneWidget);
    // 选错的方式：3 道题反复选同一个错选项
    expect(find.text("反复选同一个错误选项的题："), findsOneWidget);
    expect(find.textContaining("你选了"), findsWidgets);
    // 与全国比：这些题都有错误率，覆盖率应是 100%
    expect(find.textContaining("带全国错误率的题占你全部作答的 100%"), findsOneWidget);
    // 强化练习成效：复测 2 次、1 次答对
    expect(find.text("复测错题 · 转正率"), findsOneWidget);
    expect(find.textContaining("50%（1/2）"), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() => store.close());
  });
}
