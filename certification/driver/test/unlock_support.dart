import "package:athena_driver/core/progress.dart";

/// 写入几场科目一满分模拟考。左侧目录不再用它当科目二的入口（ADR 0126）；
/// 需要模拟考记录的测试仍走这条，带精确时刻，跟真实交卷是同一条路。
Future<void> unlockSubject2(ProgressStore store) async {
  for (var i = 0; i < ProgressStore.steadyRuns; i++) {
    await store.recordExam(
      subjectId: "subject1",
      score: 100,
      passed: true,
      at: DateTime(2026, 1, 1, 9, i),
    );
  }
}
