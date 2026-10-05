import "dart:async";
import "dart:io";

import "package:athena_driver/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/look.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

import "nav_helpers.dart";

void main() {
  // 内容契约（ADR 0064）：每组条目非空、每条有情景与要点、出处可指——
  // 速记条目是引用条文的内容，出处断了就跟题库对不上。
  test("notes.json 每组都有条目，每条都有情景、要点与出处", () async {
    final bank = await ContentLoader.load();
    expect(bank.notes, isNotEmpty);
    for (final group in bank.notes) {
      expect(group.items, isNotEmpty, reason: "${group.id} 组没有条目");
      expect(group.related(bank.questions), isNotEmpty, reason: "${group.id} 组的 match 一道题都接不上");
      for (final item in group.items) {
        expect(item.scenario, isNotEmpty, reason: "${group.id} 有条目缺情景");
        expect(item.points, isNotEmpty, reason: "${group.id}「${item.scenario}」缺要点");
        expect(item.sourceId, isNotEmpty, reason: "${group.id}「${item.scenario}」缺出处");
      }
    }
    // 出处短名必须认得这些 source_id（认不得就会把原文 id 直接显示在界面上）。
    for (final group in bank.notes) {
      for (final item in group.items) {
        expect(Bs.sourceShort(item.sourceId), isNot(item.sourceId), reason: "未知出处 ${item.sourceId}");
      }
    }
  });

  // 考点速记页：用真实内容渲染一遍，布局溢出这类问题只在渲染时暴露。
  testWidgets("考点速记页用真实内容渲染不溢出，六组都在且能起练习", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-notes-");
      store = await ProgressStore.open(suite: "notes_page_test");
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
    expect(ready.isCompleted, isTrue, reason: "首页没在 20 秒内读完进度库");

    await showTopic(tester, "考点速记");
    await tester.tap(find.text("考点速记").first);
    await tester.pump();
    expect(find.text("考点速记"), findsWidgets);
    // 一屏放不下六组，滚到底逐组检查都渲染出来了。
    for (final group in bank.notes) {
      await tester.scrollUntilVisible(find.text(group.title), 300, scrollable: find.byType(Scrollable).last);
      expect(find.text(group.title), findsOneWidget);
    }
    // 组级练习入口可点，起一轮相关题练习。
    await tester.scrollUntilVisible(find.textContaining("练这组").first, 300, scrollable: find.byType(Scrollable).last);
    expect(find.textContaining("练这组"), findsWidgets);
    expect(tester.takeException(), isNull);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
