import "dart:async";
import "dart:io";

import "package:athena_driver/core/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/subject2/field_map.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

import "unlock_support.dart";

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
      store = await ProgressStore.open(suite: "subject2_page_test");
      await unlockSubject2(store);
      before = (await store.drillRuns()).length;
    });
    await tester.binding.setSurfaceSize(const Size(1600, 2600));
    final ready = Completer<void>();
    await tester.pumpWidget(
      MaterialApp(
        home: HomePage(bank: bank, store: store, onReady: ready.complete),
      ),
    );
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 10)),
      );
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue);

    await tester.tap(find.text("科目二（C2）"));
    await tester.pump();
    await tester.tap(find.text("项目手册").last);
    await tester.pump();
    expect(find.text("C2 怎么开科目二"), findsOneWidget);
    expect(find.text("先学哪一项"), findsOneWidget);
    for (final title in ["倒车入库", "侧方停车", "曲线行驶", "直角转弯"]) {
      expect(find.text(title), findsWidgets);
    }
    Offset at(String id) =>
        tester.getTopLeft(find.byKey(ValueKey("handbook-item-$id")));
    int reading(Offset a, Offset b) =>
        (a.dy - b.dy).abs() > 40 ? a.dy.compareTo(b.dy) : a.dx.compareTo(b.dx);
    final learn = ["corner", "curve", "parallel", "reverse"];
    for (var i = 0; i < learn.length - 1; i++) {
      expect(
        reading(at(learn[i]), at(learn[i + 1])),
        lessThan(0),
        reason: "${learn[i]} 应排在 ${learn[i + 1]} 前面",
      );
    }

    // 曲线行驶：一张俯视图，参照写成一句，不再另开「车内」卡。
    await tester.tap(find.text("曲线行驶").first);
    await tester.pump();
    expect(find.byType(FieldMapAnimated), findsOneWidget);
    expect(find.text("车内"), findsNothing);
    expect(find.text("车外 · 盯哪"), findsNothing);
    expect(find.text("入口在挡风玻璃里偏外侧"), findsWidgets);
    expect(tester.takeException(), isNull);
    await tester.tap(find.widgetWithText(TextButton, "科目二"));
    await tester.pump();
    await tester.tap(find.text("项目手册").last);
    await tester.pump();

    // 打开倒车入库：动画、步骤、评判、要点都在。
    await tester.tap(find.text("倒车入库").first);
    await tester.pump();
    expect(find.byType(FieldMapAnimated), findsOneWidget);
    expect(find.text("车内"), findsNothing);
    expect(find.text("车外 · 盯哪"), findsNothing);
    expect(find.byTooltip("只播这一步"), findsOneWidget);
    expect(find.textContaining("练这一项的评判题"), findsNothing);
    expect(find.text("我的点位卡"), findsOneWidget);
    final itemPage = find
        .descendant(
          of: find.byKey(const ValueKey("subject2-item")),
          matching: find.byType(Scrollable),
        )
        .first;
    await tester.scrollUntilVisible(
      find.text("车身出线"),
      300,
      scrollable: itemPage,
    );
    expect(find.text("操作要求（标准原文）"), findsOneWidget);
    expect(find.text("车身出线"), findsOneWidget);
    await tester.drag(itemPage, const Offset(0, 5000));
    await tester.pumpAndSettle();
    expect(find.text("两个前轮已经在控制线外侧"), findsWidgets);

    // 单步播第 2 步：步骤条选中后只播这一步，停在第 2 步末尾。
    await tester.tap(
      find.descendant(
        of: find.byType(SegmentedButton<int>),
        matching: find.text("2"),
      ),
    );
    await tester.pump();
    await tester.tap(find.byTooltip("只播这一步"));
    for (var i = 0; i < 80; i++) {
      await tester.pump(const Duration(milliseconds: 100));
    }
    expect(find.text("后视镜里车尾接近库口，车身还是直的"), findsWidgets);
    await tester.tap(find.byTooltip("下一步"));
    await tester.pump();
    expect(find.textContaining("同时能看到库角"), findsWidgets);

    // 记一把：中途停车两次 → 90 分，能过。
    await tester.ensureVisible(find.text("记一把练车"));
    await tester.pump();
    await tester.tap(find.text("记一把练车"));
    await tester.pumpAndSettle();
    Finder inDialog(Finder f) =>
        find.descendant(of: find.byType(AlertDialog), matching: f);
    await tester.tap(inDialog(find.textContaining("中途停车")).first);
    await tester.pump();
    await tester.tap(inDialog(find.textContaining("中途停车 ×1")).first);
    await tester.pump();
    expect(inDialog(find.text("90 分")), findsOneWidget);
    await tester.tap(find.text("记下这一把"));
    for (
      var i = 0;
      i < 200 && find.textContaining("上次练：今天").evaluate().isEmpty;
      i++
    ) {
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 10)),
      );
      await tester.pump();
    }
    await tester.scrollUntilVisible(
      find.text("这一项的练车记录"),
      300,
      scrollable: itemPage,
    );
    expect(find.text("这一项的练车记录"), findsOneWidget);
    expect(find.textContaining("中途停车 ×2"), findsWidgets);
    // 简报跟着记录走（ADR 0037）。
    await tester.scrollUntilVisible(
      find.textContaining("上次练：今天"),
      -300,
      scrollable: itemPage,
    );
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

  // 考前分区（ADR 0039）：就绪度之外，考试日的流程与兜底规则（当场补考、终止）要在场。
  testWidgets("科目二：考前分区显示考试日流程与当场补考规则", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-s2-exam-");
      store = await ProgressStore.open(suite: "subject2_page_exam");
      await unlockSubject2(store);
    });
    await tester.binding.setSurfaceSize(const Size(1600, 2600));
    final ready = Completer<void>();
    await tester.pumpWidget(
      MaterialApp(
        home: HomePage(bank: bank, store: store, onReady: ready.complete),
      ),
    );
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 10)),
      );
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue);

    await tester.tap(find.text("科目二（C2）"));
    await tester.pump();
    await tester.tap(find.text("考前").last);
    await tester.pump();
    expect(find.text("考试日怎么走"), findsOneWidget);
    expect(find.textContaining("当场补考一次"), findsOneWidget);
    expect(find.textContaining("本次考试终止"), findsOneWidget);
    expect(find.textContaining("不系安全带"), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
