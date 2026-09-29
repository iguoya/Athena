import "package:athena_driver/progress.dart";

/// 科目二要等科目一模拟考连着几场 95 分以上才开（ADR 0047）。从主页点进科目二的测试
/// 先写进这几场成绩；走同步导入的入口，跟换机器合并进来的记录是同一条路。
Future<void> unlockSubject2(ProgressStore store) async {
  await store.importEvents([
    for (var i = 0; i < ProgressStore.steadyRuns; i++)
      {
        "kind": "exam",
        "subject_id": "subject1",
        "score": 100,
        "passed": 1,
        "at": DateTime(2026, 1, 1, 9, i).toIso8601String(),
      },
  ]);
}
