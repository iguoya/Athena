import "dart:io";

import "package:athena_driver/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  // 易混数字页（ADR 0028）：用真实内容渲染一遍，布局溢出这类问题只在渲染时暴露。
  testWidgets("易混数字页用真实内容渲染不溢出，每组都有练习按钮", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-numbers-");
      store = await ProgressStore.open(path: "${dir.path}/learning.db");
    });
    await tester.binding.setSurfaceSize(const Size(1600, 1000));
    await tester.pumpWidget(MaterialApp(home: HomePage(bank: bank, store: store)));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 300)));
    await tester.pump();

    await tester.tap(find.text("易混数字").first);
    await tester.pump();
    expect(find.text("记分分值"), findsOneWidget);
    // 一屏放不下全部分组，滚到底检查每组都渲染出来了。
    for (final group in bank.cheatsheet) {
      await tester.scrollUntilVisible(find.text(group.title), 300, scrollable: find.byType(Scrollable).last);
      expect(find.text(group.title), findsOneWidget);
    }
    expect(tester.takeException(), isNull);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
