import "dart:async";
import "dart:io";

import "package:athena_driver/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:athena_driver/session.dart";
import "package:athena_driver/sign.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  // 内容契约（ADR 0059）：json 的每条 id 都要画得出来，含义文案不能缺——
  // 漏画的标志会落到 painter 兜底的问号图，测试把它挡在 check 阶段。
  test("signs.json 的每条 id 都能画，每条都有含义文案", () async {
    final bank = await ContentLoader.load();
    for (final sign in bank.signs) {
      expect(paintableSignIds, contains(sign.id), reason: "${sign.id} 没有对应的绘制");
      expect(sign.meaning, isNotEmpty, reason: "${sign.id} 缺「看到之后怎么开」的文案");
      expect(sign.name, isNotEmpty);
    }
    // 名称与画法三方对齐（ADR 0059 决策 3）：一道斜杠是禁止停放车辆（可临时停靠），
    // 红叉是禁止停车（全禁）——题面 s1.signals.033/034 与国标都是这个语义。
    expect(bank.signs.firstWhere((s) => s.id == "no_parking").name, "禁止停放车辆");
    expect(bank.signs.firstWhere((s) => s.id == "no_stopping").name, "禁止停车");
  });

  // 标志速记页：用真实内容渲染一遍，布局溢出这类问题只在渲染时暴露。
  testWidgets("标志速记页用真实内容渲染不溢出，四组都在", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-signs-");
      store = await ProgressStore.open(suite: "signs_page_test");
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

    await tester.tap(find.text("标志速记").first);
    await tester.pump();
    expect(find.text("标志速记"), findsWidgets);
    // 高频标志有频次徽章（首屏的禁令组里就有）。
    expect(find.text("高频"), findsWidgets);
    // 一屏放不下四个分组，滚到底逐组检查都渲染出来了。
    for (final label in ["禁令标志", "警告标志", "指示标志", "指路标志"]) {
      await tester.scrollUntilVisible(find.text(label), 300, scrollable: find.byType(Scrollable).last);
      expect(find.text(label), findsOneWidget);
    }
    expect(tester.takeException(), isNull);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });

  // 组级练习入口：进页面首屏就是禁令组，「练这组」一点就起一轮练习。
  testWidgets("点「练这组」起一轮相关题练习", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-signs-");
      store = await ProgressStore.open(suite: "signs_page_test_practice");
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
    await tester.tap(find.text("标志速记").first);
    await tester.pump();
    await tester.tap(find.textContaining("练这组").first);
    await tester.pump();
    expect(find.byType(SessionStage), findsOneWidget);
    // SessionStage 挂着停留计时之类的 Timer；假时钟推走，不给收尾留 pending timer。
    await tester.pump(const Duration(seconds: 30));

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
