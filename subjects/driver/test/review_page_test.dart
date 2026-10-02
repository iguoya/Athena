import "dart:async";
import "dart:io";

import "package:athena_driver/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  // 考前复习（ADR 0033、0035）：累计错够 2 次进来，答对比答错多 1～2 次才移出。
  testWidgets("考前复习收累计错 2 次的题，答对 1 次仍在、标对 1/3；只错 1 次的不收", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    late Question twice;
    late Question once;
    late Set<String> expected;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-review-");
      // 从空库开始：拿仓库进度库当底子的话，使用者把科目一答遍之后就挑不出没答过的题了。
      store = await ProgressStore.open(isolated: true);
      // 挑两道题干独一无二的科目一题来造记录，列表里才能按题干认出它。
      final pool = bank.forSubject("subject1");
      final prompts = <String, int>{};
      for (final q in pool) {
        prompts[q.prompt] = (prompts[q.prompt] ?? 0) + 1;
      }
      final fresh = [
        for (final q in pool)
          if (prompts[q.prompt] == 1 && !q.prompt.contains("\n")) q,
      ];
      twice = fresh[0];
      once = fresh[1];
      for (final correct in [false, false, true]) {
        await store.recordAttempt(questionId: twice.id, topicId: twice.topicId, subjectId: "subject1", correct: correct);
      }
      await store.recordAttempt(questionId: once.id, topicId: once.topicId, subjectId: "subject1", correct: false);
      final wrongs = await store.wrongCounts();
      final streaks = await store.correctStreaksSinceWrong();
      final totals = await store.attemptCounts();
      final s1Done = allMastered(bank.forSubject("subject1"), await store.masteredQuestionIds());
      expected = {
        for (final q in bank.questions)
          if (inReview(
                wrongCount: wrongs[q.id] ?? 0,
                correctCount: (totals[q.id] ?? 0) - (wrongs[q.id] ?? 0),
                streak: streaks[q.id] ?? 0,
              ) &&
              (s1Done || !q.topicId.startsWith("drive.s4.")))
            q.id,
      };
    });
    await tester.binding.setSurfaceSize(const Size(1600, 1000));
    final ready = Completer<void>();
    await tester.pumpWidget(
      MaterialApp(home: HomePage(bank: bank, store: store, onReady: ready.complete)),
    );
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue, reason: "首页没在 20 秒内读完进度库");

    await tester.tap(find.textContaining("考前复习").first);
    await tester.pump();
    expect(find.textContaining("全部复习"), findsOneWidget);

    final list = find.byType(Scrollable).last;
    await tester.scrollUntilVisible(find.textContaining(twice.prompt), 300, scrollable: list);
    final row = find.ancestor(of: find.textContaining(twice.prompt), matching: find.byType(Row)).first;
    expect(find.descendant(of: row, matching: find.text("对 1/3")), findsOneWidget);
    expect(find.descendant(of: row, matching: find.text("错 2 次")), findsOneWidget);

    // 总数按规则独立算一遍：只错过一次的那道不算在里面。
    expect(expected.contains(once.id), isFalse);
    expect(expected.contains(twice.id), isTrue);
    expect(find.text("共 ${expected.length} 道"), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
