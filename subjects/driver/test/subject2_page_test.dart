import "dart:async";
import "dart:io";

import "package:athena_driver/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  // 科目二页面（ADR 0036）：用真实内容渲染，布局溢出、动画驱动、记一把练车都走一遍。
  testWidgets("科目二：四项卡片、动画单步、记一把练车后统计出现", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    late int before;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-s2-");
      store = await ProgressStore.open(path: "${dir.path}/learning.db");
      before = (await store.drillRuns()).length;
    });
    await tester.binding.setSurfaceSize(const Size(1600, 1000));
    final ready = Completer<void>();
    await tester.pumpWidget(
      MaterialApp(home: HomePage(bank: bank, store: store, autoSync: false, onReady: ready.complete)),
    );
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue);

    await tester.tap(find.text("科目二（C2）"));
    await tester.pump();
    await tester.tap(find.text("项目手册"));
    await tester.pump();
    for (final title in ["倒车入库", "侧方停车", "曲线行驶", "直角转弯"]) {
      expect(find.text(title), findsWidgets);
    }

    // 打开倒车入库：动画、步骤、评判、要点都在。
    await tester.tap(find.text("倒车入库").first);
    await tester.pump();
    expect(find.text("我的点位卡"), findsOneWidget);
    final itemPage = find.descendant(of: find.byKey(const ValueKey("subject2-item")), matching: find.byType(Scrollable)).first;
    await tester.scrollUntilVisible(find.text("车身出线"), 300, scrollable: itemPage);
    expect(find.text("操作要求（标准原文）"), findsOneWidget);
    expect(find.text("车身出线"), findsOneWidget);
    await tester.drag(itemPage, const Offset(0, 5000));
    await tester.pumpAndSettle();
    expect(find.textContaining("系好安全带"), findsOneWidget);
    expect(find.textContaining("系好安全带"), findsOneWidget); // 第 1 步展开着

    // 单步播第 2 步：播完停在第 2 步末尾，步骤列表跟着高亮到第 2 步。
    await tester.tap(find.byTooltip("播这一步").at(1));
    for (var i = 0; i < 80; i++) {
      await tester.pump(const Duration(milliseconds: 100));
    }
    expect(find.textContaining("松手刹、挂 R 挡"), findsOneWidget);
    await tester.tap(find.byTooltip("下一步"));
    await tester.pump();
    expect(find.textContaining("向库的一侧打满方向"), findsOneWidget);

    // 记一把：中途停车两次 → 90 分，能过。
    await tester.ensureVisible(find.text("记一把练车"));
    await tester.pump();
    await tester.tap(find.text("记一把练车"));
    await tester.pumpAndSettle();
    Finder inDialog(Finder f) => find.descendant(of: find.byType(AlertDialog), matching: f);
    await tester.tap(inDialog(find.textContaining("中途停车")).first);
    await tester.pump();
    await tester.tap(inDialog(find.textContaining("中途停车 ×1")).first);
    await tester.pump();
    expect(inDialog(find.text("90 分")), findsOneWidget);
    await tester.tap(find.text("记下这一把"));
    for (var i = 0; i < 200 && find.textContaining("上次练：今天").evaluate().isEmpty; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    await tester.scrollUntilVisible(find.text("这一项的练车记录"), 300, scrollable: itemPage);
    expect(find.text("这一项的练车记录"), findsOneWidget);
    expect(find.textContaining("中途停车 ×2"), findsWidgets);
    // 简报跟着记录走（ADR 0037）。
    await tester.scrollUntilVisible(find.textContaining("上次练：今天"), -300, scrollable: itemPage);
    expect(find.textContaining("上次练：今天"), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.runAsync(() async {
      final runs = await store.drillRuns();
      expect(runs.length, before + 1);
      expect(runs.first.itemId, "reverse");
      expect(runs.first.mistakes, ["stop", "stop"]);
    });

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
