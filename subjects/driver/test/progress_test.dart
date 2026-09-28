import "dart:io";

import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  late Directory dir;
  late ProgressStore store;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp("athena-driver-");
    store = await ProgressStore.open(path: "${dir.path}/learning.db");
  });

  tearDown(() async {
    await store.close();
    await dir.delete(recursive: true);
  });

  // 考前复习的进出（ADR 0033、0034）：错几次就要连对几次，封顶 4 次；再错清零回来。
  test("考前复习：连对够次数移出，错多次的封顶 4 次也能出，再错一次回来", () async {
    Future<void> answer(String id, List<bool> results) async {
      for (final ok in results) {
        await store.recordAttempt(questionId: id, topicId: "t", subjectId: "s", correct: ok);
      }
    }

    Future<bool> reviewing(String id) async {
      final wrongs = await store.wrongCounts();
      final streaks = await store.correctStreaksSinceWrong();
      return inReview(wrongCount: wrongs[id] ?? 0, streak: streaks[id] ?? 0);
    }

    // 只错一次：不进。
    await answer("once", [false]);
    expect(await reviewing("once"), isFalse);

    // 错 2 次：连对 1 次还在，连对 2 次移出。
    await answer("two", [false, false, true]);
    expect(await reviewing("two"), isTrue);
    await answer("two", [true]);
    expect(await reviewing("two"), isFalse);
    // 移出后再错：连对清零、累计错 3 次，要连对 3 次才再出去。
    await answer("two", [false]);
    expect(await reviewing("two"), isTrue);
    expect((await store.correctStreaksSinceWrong())["two"], 0);
    await answer("two", [true, true]);
    expect(await reviewing("two"), isTrue);
    await answer("two", [true]);
    expect(await reviewing("two"), isFalse);

    // 错 8 次的顽固题：连对 4 次就能出，不会永远困在里面。
    await answer("stubborn", List.filled(8, false));
    await answer("stubborn", [true, true, true]);
    expect(await reviewing("stubborn"), isTrue);
    await answer("stubborn", [true]);
    expect(await reviewing("stubborn"), isFalse);

    // 答对在前、答错在后的不算连对：只数最后一次错之后的。
    await answer("late", [true, true, true, false, false]);
    expect((await store.correctStreaksSinceWrong())["late"], 0);
    expect(await reviewing("late"), isTrue);
  });

  test("考前复习移出门槛：错几次连对几次，最少 2 次、最多 4 次", () {
    expect(reviewExitStreak(2), 2);
    expect(reviewExitStreak(3), 3);
    expect(reviewExitStreak(4), 4);
    expect(reviewExitStreak(8), 4);
  });

  test("按作答时间认最近一次：后并进来的更早答错不盖掉现在的答对", () async {
    await store.recordAttempt(questionId: "q1", topicId: "t", subjectId: "s", correct: true);
    // 同步或合并带回来的是早先在别处的作答：入库晚、id 大，时间却更早。
    await store.importEvents([
      {
        "kind": "attempt",
        "question_id": "q1",
        "topic_id": "t",
        "subject_id": "s",
        "correct": 0,
        "at": "2000-01-01T00:00:00.000",
      },
    ]);
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
