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
