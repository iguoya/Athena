import "dart:async";
import "dart:io";

import "package:athena_driver/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:athena_driver/session.dart";
import "package:flutter/material.dart";
import "package:flutter/services.dart";
import "package:flutter_test/flutter_test.dart";

/// 自我测验模式（ADR 0077，ADR 0080 改名、一轮 5 个）：检索练习的卡片流——揭示、
/// 自评、没记住重现、收尾「再来 5 个」与深链。自评不写掌握度：考完进度库里的作答
/// 记录不应有任何变化。选手势页（8 个动作）跑完整流程。
void main() {
  Future<(Bank, ProgressStore, Directory)> boot(WidgetTester tester) async {
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
    return (bank, store, dir);
  }

  Future<void> teardown(WidgetTester tester, ProgressStore store, Directory dir) async {
    await tester.pump(const Duration(seconds: 30));
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  }

  testWidgets("自我测验：一轮 5 张，揭示、没记住重现、再来一轮、收尾「去练这组」起练习，自评不落库", (tester) async {
    final (_, store, dir) = await boot(tester);
    final before = await store.allAttempts();

    // 进手势速记页，打开自我测验。
    await tester.tap(find.text("手势速记").first);
    await tester.pump();
    await tester.tap(find.text("自我测验").first);
    await tester.pump();
    expect(find.textContaining("想一想"), findsOneWidget);

    // 一轮：揭示 → 第一次自评「没记住」，之后一直「记住了」，直到收尾。
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
    expect(find.text("考完了"), findsOneWidget, reason: "5 张卡应在 20 次交互内考完（含没记住的重现）");
    expect(find.textContaining("这一轮 5 个"), findsOneWidget, reason: "一轮固定 5 个");
    expect(find.textContaining("没记住 1"), findsOneWidget, reason: "第一次自评没记住应计入");

    // 再来 5 个：回到卡片流，第 2 轮。
    await tester.tap(find.text("再来 5 个"));
    await tester.pump();
    expect(find.textContaining("第 2 轮"), findsOneWidget);
    expect(find.textContaining("想一想"), findsOneWidget);
    // 第 2 轮全部记住；5 张刚好 5 次交互。
    for (var i = 0; i < 5; i++) {
      await tester.tap(find.text("揭示（空格）"));
      await tester.pump();
      await tester.tap(find.textContaining("记住了（1）"));
      await tester.pump();
    }
    expect(find.text("考完了"), findsOneWidget);
    expect(find.textContaining("没记住 0"), findsOneWidget);

    // 收尾深链：去练这组起一轮练习。
    await tester.tap(find.text("去练这组题"));
    await tester.pump();
    expect(find.byType(SessionStage), findsOneWidget);

    // 自评不落库：作答记录与自我测验之前一致。
    final after = await store.allAttempts();
    expect(after.length, before.length);

    await teardown(tester, store, dir);
  });

  testWidgets("自我测验：侧栏里全部 8 个速记页都有入口，一轮都是 5 张", (tester) async {
    final (_, store, dir) = await boot(tester);
    for (final page in ["易混数字", "标志速记", "标线速记", "仪表速记", "手势速记", "考点速记", "河南速记", "记分证照速记"]) {
      await tester.tap(find.text(page).first);
      await tester.pump();
      expect(find.text("自我测验"), findsOneWidget, reason: "$page 缺自我测验入口");
      await tester.tap(find.text("自我测验"));
      await tester.pump();
      // 一轮 5 张：剩余张数写在卡片头里。
      expect(find.textContaining("剩 5 张"), findsOneWidget, reason: "$page 一轮应抽 5 张");
      await tester.sendKeyEvent(LogicalKeyboardKey.escape);
      await tester.pump();
    }
    await teardown(tester, store, dir);
  });

  testWidgets("自我测验：易混数字与考点速记也有，文字卡正面是情形、揭示后是答案", (tester) async {
    final (_, store, dir) = await boot(tester);

    // 易混数字：情形 → 数字。
    await tester.tap(find.text("易混数字").first);
    await tester.pump();
    await tester.tap(find.text("自我测验").first);
    await tester.pump();
    expect(find.textContaining("这种情形对应的数字是多少"), findsOneWidget);
    await tester.tap(find.text("揭示（空格）"));
    await tester.pump();
    expect(find.textContaining("记住了（1）"), findsOneWidget);
    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pump();
    expect(find.text("自我测验").evaluate().length, 1, reason: "Esc 关掉卡片，只剩页面上的按钮");

    // 考点速记：情景 → 要点。
    await tester.tap(find.text("考点速记").first);
    await tester.pump();
    await tester.tap(find.text("自我测验").first);
    await tester.pump();
    expect(find.textContaining("碰到这个情景该怎么做"), findsOneWidget);
    await tester.tap(find.text("揭示（空格）"));
    await tester.pump();
    expect(find.text("要点"), findsOneWidget);

    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pump();
    await teardown(tester, store, dir);
  });
}
