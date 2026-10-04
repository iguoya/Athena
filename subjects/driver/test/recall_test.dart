import "dart:async";
import "dart:io";

import "package:athena_driver/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:athena_driver/session.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

/// 考我模式（ADR 0077）：检索练习的卡片流——揭示、自评、没记住重现、收尾深链。
/// 自评不写掌握度：考完进度库里的作答记录不应有任何变化。选手势页（9 条）
/// 跑完整流程。
void main() {
  testWidgets("考我：揭示、没记住重现、收尾「去练这组」起练习，自评不落库", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-recall-");
      store = await ProgressStore.open(suite: "recall_test");
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
    expect(ready.isCompleted, isTrue);

    final before = await store.allAttempts();

    // 进手势速记页（9 条），打开考我。
    await tester.tap(find.text("手势速记").first);
    await tester.pump();
    await tester.tap(find.text("考我").first);
    await tester.pump();
    expect(find.textContaining("想一想"), findsOneWidget);

    // 揭示 → 第一次自评「没记住」，之后一直「记住了」，直到收尾。
    var gradedMiss = false;
    for (var i = 0; i < 20; i++) {
      if (find.text("考完了").evaluate().isNotEmpty) break;
      await tester.tap(find.text("揭示（空格）"));
      await tester.pump();
      if (!gradedMiss) {
        await tester.tap(find.textContaining("没记住（2）"));
        gradedMiss = true;
      } else {
        await tester.tap(find.textContaining("记住了（1）"));
      }
      await tester.pump();
    }
    expect(find.text("考完了"), findsOneWidget, reason: "9 张卡应在 20 次交互内考完（含没记住的重现）");
    expect(find.textContaining("共考"), findsOneWidget);
    expect(find.textContaining("没记住 1"), findsOneWidget, reason: "第一次自评没记住应计入");

    // 收尾深链：去练这组起一轮练习。
    await tester.tap(find.text("去练这组题"));
    await tester.pump();
    expect(find.byType(SessionStage), findsOneWidget);

    // 自评不落库：作答记录与考我之前一致。
    final after = await store.allAttempts();
    expect(after.length, before.length);

    await tester.pump(const Duration(seconds: 30));
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
