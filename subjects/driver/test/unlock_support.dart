import "package:athena_driver/progress.dart";

/// 科目二要等科目一模拟考连着几场 95 分以上才开（ADR 0047）。从主页点进科目二的测试
/// 先写进这几场成绩——带精确时刻，跟真实交卷的记录是同一条路。
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
