import "dart:async";
import "dart:io";

import "package:athena_driver/core/content.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/ui/glyphs.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/core/progress.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

/// 科目二侧栏按实操排（T-004）：默认落点是科目二，展开后不是笔试目录。
void main() {
  testWidgets("打开即科目二，展开后是练车日、四项、考前、日志、注意事项", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-s2-nav-");
      store = await ProgressStore.open(suite: "subject2_sidebar_test");
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

    expect(
      find.textContaining("场地驾驶技能"),
      findsOneWidget,
      reason: "默认落点是科目二练车日",
    );

    final sidebar = find.byWidgetPredicate(
      (w) => w is SizedBox && w.width == 312,
    );
    Finder inSidebar(Finder f) => find.descendant(of: sidebar, matching: f);
    expect(inSidebar(find.text("科目一")), findsOneWidget);
    expect(inSidebar(find.textContaining("待练")), findsWidgets);

    await tester.tap(
      find.descendant(of: sidebar, matching: find.byIcon(Glyph.expand)).first,
    );
    await tester.pump(const Duration(milliseconds: 500));

    final labels = [
      "练车日",
      "项目手册",
      "① 直角转弯",
      "② 曲线行驶",
      "③ 侧方停车",
      "④ 倒车入库",
      "考前",
      "练车日志",
      "注意事项 · 54 题",
    ];
    var previous = tester.getCenter(inSidebar(find.text("科目二（C2）"))).dy;
    for (final label in labels) {
      final found = inSidebar(find.text(label));
      expect(found, findsOneWidget, reason: label);
      final y = tester.getCenter(found).dy;
      expect(y, greaterThan(previous), reason: "$label 应排在上一项下面");
      previous = y;
    }
    expect(
      previous,
      lessThan(tester.getCenter(inSidebar(find.text("科目四"))).dy),
    );

    final subject2Top = tester.getTopLeft(inSidebar(find.text("科目二（C2）"))).dy;
    final subject4Top = tester.getTopLeft(inSidebar(find.text("科目四"))).dy;
    for (final banned in ["待练", "练新题"]) {
      final hits = inSidebar(find.textContaining(banned));
      for (var i = 0; i < hits.evaluate().length; i++) {
        final y = tester.getTopLeft(hits.at(i)).dy;
        expect(
          y < subject2Top || y > subject4Top,
          isTrue,
          reason: "科目二分支里不应出现$banned",
        );
      }
    }

    await tester.tap(inSidebar(find.text("考前")));
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.text("考试日怎么走"), findsOneWidget);

    // 一级章节不绑定实操内容：点「科目二（C2）」落到本章节概要，不是练车日。
    await tester.tap(inSidebar(find.text("科目二（C2）")));
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.text("C2 怎么开科目二"), findsOneWidget);

    await tester.tap(inSidebar(find.text("① 直角转弯")));
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.text("直角转弯"), findsWidgets);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
