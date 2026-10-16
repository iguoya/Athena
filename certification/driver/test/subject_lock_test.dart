import "dart:async";
import "dart:io";

import "package:athena_driver/core/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  ExamRecord exam(int score, {String subject = "subject1"}) =>
      ExamRecord(subjectId: subject, score: score, passed: score >= 90, at: DateTime(2026));

  // 科目二的解锁线（ADR 0047）：最近 3 场科目一模拟考都不低于 95 分。
  test("科目二解锁线：连着 3 场 95 分以上才算稳", () {
    expect(ProgressStore.subject1Steady([]), isFalse);
    expect(ProgressStore.subject1Steady([exam(100), exam(98)]), isFalse, reason: "场次不够");
    expect(ProgressStore.subject1Steady([exam(95), exam(97), exam(100)]), isTrue);
    expect(ProgressStore.subject1Steady([exam(100), exam(94), exam(100)]), isFalse, reason: "中间掉了一场");
    expect(ProgressStore.subject1Steady([exam(96), exam(96), exam(96), exam(40)]), isTrue, reason: "只看最近 3 场");
    expect(
      ProgressStore.subject1Steady([exam(100), exam(60, subject: "subject4"), exam(100), exam(100)]),
      isTrue,
      reason: "别的科目的成绩不算",
    );
  });

  testWidgets("左侧目录不锁：没考过科目一也能进科目二和科目四", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-lock-");
      store = await ProgressStore.open(suite: "subject_lock_test");
    });
    await tester.binding.setSurfaceSize(const Size(1600, 2600));
    final ready = Completer<void>();
    await tester.pumpWidget(
      MaterialApp(home: HomePage(bank: bank, store: store, onReady: ready.complete)),
    );
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue);

    expect(find.textContaining("未解锁"), findsNothing);
    await tester.tap(find.text("科目二（C2）"));
    await tester.pump();
    expect(find.text("练车日"), findsWidgets);
    expect(find.text("项目手册"), findsWidgets);

    await tester.tap(find.text("科目四"));
    await tester.pump();
    expect(find.text("安全文明驾驶常识"), findsWidgets);
    expect(find.textContaining("未解锁"), findsNothing);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
