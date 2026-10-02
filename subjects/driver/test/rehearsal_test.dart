import "dart:async";
import "dart:io";

import "package:athena_driver/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:athena_driver/rehearsal.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

import "unlock_support.dart";

void main() {
  // 默演（ADR 0037）：先口述、再对照；卡住的步骤记下来，进练车前简报。
  testWidgets("默演：口述时讲解藏着，对照时亮出；卡住的步骤记进库、进简报", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-rehearsal-");
      store = await ProgressStore.open(suite: "rehearsal_test");
      await unlockSubject2(store);
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
    await tester.tap(find.text("科目二（C2）"));
    await tester.pump();
    await tester.tap(find.text("项目手册"));
    await tester.pump();
    await tester.tap(find.text("曲线行驶").first);
    await tester.pump();
    await tester.tap(find.text("默演一遍"));
    await tester.pumpAndSettle();

    Finder inView(Finder f) => find.descendant(of: find.byType(RehearsalView), matching: f);
    final item = bank.guide.item("curve")!;
    for (var i = 0; i < item.steps.length; i++) {
      expect(inView(find.text(item.steps[i].title)), findsWidgets);
      // 口述阶段：讲解藏着。
      expect(inView(find.text(item.steps[i].body)), findsNothing);
      await tester.tap(inView(find.text("说完了，对照")));
      await tester.pump();
      expect(inView(find.text(item.steps[i].body)), findsOneWidget);
      await tester.tap(inView(find.text(i == 1 ? "漏了或说错了" : "对上了")));
      for (var k = 0; k < 20; k++) {
        await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
        await tester.pump();
      }
    }
    expect(inView(find.text("4 步里对上 3 步")), findsOneWidget);
    expect(inView(find.text("第 2 步 · 第一个弯：左弯")), findsOneWidget);
    await tester.tap(inView(find.text("完成")).last);
    await tester.pumpAndSettle();

    await tester.runAsync(() async {
      final r = (await store.rehearsals()).first;
      expect(r.itemId, "curve");
      expect(r.missed, [1]);
      expect(r.total, 4);
    });
    // 单项简报带上卡住的步骤。
    expect(find.textContaining("上次默演卡在：第 2 步「第一个弯：左弯」"), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
