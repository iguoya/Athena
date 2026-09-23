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
}
