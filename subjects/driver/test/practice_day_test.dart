import "dart:async";
import "dart:io";

import "package:athena_driver/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:athena_driver/review.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

import "unlock_support.dart";

void main() {
  // 科目二围绕练车日（ADR 0039）：复盘今天一次录完整天，练车日、日志、考前各自看得到。
  testWidgets("复盘今天：格子表记错、实时算分、加一把、记教练的话；四个分区都跟着更新", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    late int before;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-day-");
      store = await ProgressStore.open(path: "${dir.path}/learning.db");
      await unlockSubject2(store);
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
    Future<void> settle() async {
      for (var i = 0; i < 40; i++) {
        await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
        await tester.pump();
      }
    }

    await tester.tap(find.text("科目二（C2）"));
    await tester.pump();
    // 默认就是练车日。
    expect(find.text("按最近的练车，整场能过的把握"), findsOneWidget);
    expect(find.text("今天练车的重点"), findsOneWidget);

    await tester.tap(find.text("复盘今天"));
    await tester.pumpAndSettle();
    Finder inReview(Finder f) => find.descendant(of: find.byType(DayReview), matching: f);
    await tester.tap(inReview(find.widgetWithText(FilterChip, "倒车入库")));
    await tester.pump();
    expect(inReview(find.text("第 3 把")), findsOneWidget);
    // 第 1 把中途停车两次 → 90 分；第 2 把车身出线 → 不合格。
    await tester.tap(find.byKey(const ValueKey("review-reverse-0-stop")));
    await tester.pump();
    await tester.tap(find.byKey(const ValueKey("review-reverse-0-stop")));
    await tester.pump();
    await tester.tap(find.byKey(const ValueKey("review-reverse-1-body_out")));
    await tester.pump();
    expect(inReview(find.text("90 分")), findsOneWidget);
    expect(inReview(find.text("不合格")), findsOneWidget);
    await tester.tap(inReview(find.byTooltip("多一把")));
    await tester.pump();
    expect(inReview(find.text("第 4 把")), findsOneWidget);
    await tester.enterText(inReview(find.byType(TextField)), "车尾到库角再打");
    await tester.tap(find.text("保存今天 4 把"));
    for (var i = 0; i < 300 && find.byType(DayReview).evaluate().isNotEmpty; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    await settle();

    await tester.runAsync(() async {
      final runs = await store.drillRuns();
      expect(runs.length, before + 4);
      final mine = runs.take(4).toList().reversed.toList();
      expect(mine.map((r) => r.itemId).toSet(), {"reverse"});
      expect(mine[0].mistakes, ["stop", "stop"]);
      expect(mine[1].mistakes, ["body_out"]);
      expect((await store.drillNotes()).first.text, "车尾到库角再打");
    });
    expect(find.text("今天已记下"), findsOneWidget);
    expect(find.textContaining("4 把能过 3 把"), findsOneWidget);

    await tester.tap(find.text("练车日志"));
    await tester.pump();
    expect(find.text("按练车日看每一项能过的比例"), findsOneWidget);
    expect(find.textContaining("教练：车尾到库角再打"), findsOneWidget);

    await tester.tap(find.text("考前"));
    await tester.pump();
    expect(find.textContaining("每一项最近的表现"), findsOneWidget);
    expect(find.text("规则自测"), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
