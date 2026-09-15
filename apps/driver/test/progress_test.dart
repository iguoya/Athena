import "dart:io";

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

  test("迟疑只在明显慢于自己节奏时才成立", () {
    const pace = [4000, 5000, 4500, 5200, 4800, 5100];
    expect(lingeredVsPace(8000, pace), isFalse);
    expect(lingeredVsPace(16000, pace), isFalse);
    expect(lingeredVsPace(22000, pace), isTrue);
    expect(lingeredVsPace(60000, pace.take(5)), isFalse);
  });

  test("按平时节奏答对算掌握，明显停更久的答对还会再练", () async {
    for (var i = 0; i < 6; i++) {
      await store.recordAttempt(
        questionId: "pace$i",
        topicId: "t",
        subjectId: "s",
        correct: true,
        durationMs: 5000,
      );
    }
    await store.recordAttempt(
      questionId: "solid",
      topicId: "t",
      subjectId: "s",
      correct: true,
      durationMs: 6000,
    );
    await store.recordAttempt(
      questionId: "slow",
      topicId: "t",
      subjectId: "s",
      correct: true,
      durationMs: 25000,
      hesitant: true,
    );
    final mastered = await store.masteredQuestionIds();
    expect(mastered, contains("solid"));
    expect(mastered, isNot(contains("slow")));
  });
}
