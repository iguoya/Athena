import "dart:io";

import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  late Directory dir;
  late ProgressStore store;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp("athena-driver-");
    store = await ProgressStore.open(suite: "progress_test");
  });

  tearDown(() async {
    await store.close();
    await dir.delete(recursive: true);
  });

  // 场合标记与用时封顶（ADR 0057）。
  test("作答记录带场合标记，默认平时练习；模拟考显式传 exam", () async {
    await store.recordAttempt(questionId: "k1", topicId: "t", subjectId: "s", correct: true);
    await store.recordAttempt(questionId: "k2", topicId: "t", subjectId: "s", correct: false, kind: "exam");
    final rows = {for (final r in store.debugAttempts()) r["question_id"]: r};
    expect(rows["k1"]!["kind"], "practice");
    expect(rows["k2"]!["kind"], "exam");
  });

  test("单题用时封顶 5 分钟：挂机十小时也按 300000 记", () async {
    await store.recordAttempt(
      questionId: "k3", topicId: "t", subjectId: "s", correct: true,
      durationMs: 36947433, at: DateTime(2026, 10, 3, 10),
    );
    final row = store.debugAttempts().single;
    expect(row["duration_ms"], 300000);
  });

  // 考前复习的进出（ADR 0033、0035）：答对比答错多 1～2 次、且最近一次答对才出；再错回来。
  test("考前复习：答对比答错多 1～2 次才移出，错多次的也能出，再错一次回来", () async {
    Future<void> answer(String id, List<bool> results) async {
      for (final ok in results) {
        await store.recordAttempt(questionId: id, topicId: "t", subjectId: "s", correct: ok);
      }
    }

    Future<bool> reviewing(String id) async {
      final wrongs = await store.wrongCounts();
      final streaks = await store.correctStreaksSinceWrong();
      final total = await store.attemptCounts();
      final wrong = wrongs[id] ?? 0;
      return inReview(wrongCount: wrong, correctCount: (total[id] ?? 0) - wrong, streak: streaks[id] ?? 0);
    }

    // 只错一次：不进。
    await answer("once", [false]);
    expect(await reviewing("once"), isFalse);

    // 错 2 次：要对 3 次。对 2 次还在，对第 3 次移出。
    await answer("two", [false, false, true, true]);
    expect(await reviewing("two"), isTrue);
    await answer("two", [true]);
    expect(await reviewing("two"), isFalse);
    // 移出后再错：累计错 3 次，要对 5 次；已经对 3 次，再对 2 次才出去。
    await answer("two", [false]);
    expect(await reviewing("two"), isTrue);
    expect((await store.correctStreaksSinceWrong())["two"], 0);
    await answer("two", [true]);
    expect(await reviewing("two"), isTrue);
    await answer("two", [true]);
    expect(await reviewing("two"), isFalse);

    // 错 8 次的顽固题：对 10 次也能出，不会永远困在里面。
    await answer("stubborn", List.filled(8, false));
    await answer("stubborn", List.filled(9, true));
    expect(await reviewing("stubborn"), isTrue);
    await answer("stubborn", [true]);
    expect(await reviewing("stubborn"), isFalse);

    // 累计答对早就够了，但刚答错：先留着，再答对一次才出去。
    await answer("late", [true, true, true, true, false, false]);
    expect(await reviewing("late"), isTrue);
    await answer("late", [true]);
    expect(await reviewing("late"), isFalse);
  });

  test("考前复习移出门槛：答对比答错多 1～2 次", () {
    expect(reviewExitCorrect(2), 3);
    expect(reviewExitCorrect(3), 5);
    expect(reviewExitCorrect(8), 10);
  });

  test("按作答时间认最近一次：后并进来的更早答错不盖掉现在的答对", () async {
    await store.recordAttempt(questionId: "q1", topicId: "t", subjectId: "s", correct: true);
    // 从旧库迁移进来的是早先的作答：入库晚、id 大，时间却更早（ADR 0030）。
    await store.recordAttempt(
      questionId: "q1",
      topicId: "t",
      subjectId: "s",
      correct: false,
      at: DateTime(2000, 1, 1),
    );
    expect(await store.masteredQuestionIds(), {"q1"});
    expect(await store.wrongQuestionIds(), isEmpty);
  });

  test("最近一次答对的题算已掌握，答错会从已掌握里拿掉", () async {
    await store.recordAttempt(
      questionId: "q1",
      topicId: "t",
      subjectId: "s",
      correct: true,
      durationMs: 18000,
    );
    await store.recordAttempt(
      questionId: "q2",
      topicId: "t",
      subjectId: "s",
      correct: false,
      durationMs: 1200,
    );
    expect(await store.masteredQuestionIds(), {"q1"});
    expect(await store.wrongQuestionIds(), ["q2"]);

    await store.recordAttempt(
      questionId: "q1",
      topicId: "t",
      subjectId: "s",
      correct: false,
    );
    expect(await store.masteredQuestionIds(), isEmpty);
    expect(await store.wrongQuestionIds(), containsAll(["q1", "q2"]));

    await store.recordAttempt(
      questionId: "q2",
      topicId: "t",
      subjectId: "s",
      correct: true,
    );
    expect(await store.masteredQuestionIds(), {"q2"});
    expect(await store.wrongQuestionIds(), ["q1"]);
  });
}
