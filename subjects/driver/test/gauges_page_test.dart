import "dart:async";
import "dart:io";

import "package:athena_driver/core/content.dart";
import "package:athena_driver/speed/gauge.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:athena_driver/study/session.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

import "nav_helpers.dart";

void main() {
  // 内容契约（ADR 0067）：json 的每条 id 都要画得出来，含义文案不能缺——
  // 漏画的符号会落到 painter 兜底的问号图，测试把它挡在 check 阶段。
  test("gauges.json 的每条 id 都能画，每条都有含义文案", () async {
    final bank = await ContentLoader.load();
    expect(bank.gauges, isNotEmpty);
    for (final gauge in bank.gauges) {
      expect(paintableGaugeIds, contains(gauge.id), reason: "${gauge.id} 没有对应的绘制");
      expect(gauge.meaning, isNotEmpty, reason: "${gauge.id} 缺「亮了怎么办」的文案");
      expect(gauge.name, isNotEmpty);
      expect(["alarm", "indicate", "dial", "control"], contains(gauge.kind),
          reason: "${gauge.id} 的 kind 不在四分法里");
    }
    final labels = {for (final g in bank.gauges) g.kind: g.kindLabel};
    expect(labels.length, 4);
  });

  // 反向映射契约（ADR 0067 决策 3）：映射里的题 id 都真实存在，每条至少挂一道
  // 题，「练这组」才有得练；题库 JSON 不因此加字段。
  test("反向映射的题 id 都存在，每条符号都挂着题", () async {
    final bank = await ContentLoader.load();
    final byId = {for (final q in bank.questions) q.id: q};
    for (final gauge in bank.gauges) {
      expect(gauge.questions, isNotEmpty, reason: "${gauge.id} 一道相关题都没挂");
      for (final id in gauge.questions) {
        expect(byId, contains(id), reason: "${gauge.id} 映射的题 $id 不在题库里");
      }
    }
    // vehicle 块的核心题大部分有归属：131 道左右挂着。
    final referenced = {for (final g in bank.gauges) ...g.questions};
    expect(referenced.length, greaterThan(120));
  });

  // 仪表速记页：用真实内容渲染一遍，布局溢出这类问题只在渲染时暴露。
  testWidgets("仪表速记页用真实内容渲染不溢出，四组都在", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-gauges-");
      store = await ProgressStore.open(suite: "gauges_page_test");
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

    await showTopic(tester, "仪表速记");
    await tester.tap(find.text("仪表速记").first);
    await tester.pump();
    expect(find.text("仪表速记"), findsWidgets);
    expect(find.text("高频"), findsWidgets);
    for (final label in ["报警灯", "指示灯", "仪表表盘", "开关与操纵件"]) {
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

  // 组级练习入口：进页面首屏就是报警灯组，「练这组」一点就起一轮练习。
  testWidgets("点「练这组」起一轮相关题练习", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-gauges-");
      store = await ProgressStore.open(suite: "gauges_page_test_practice");
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
    await showTopic(tester, "仪表速记");
    await tester.tap(find.text("仪表速记").first);
    await tester.pump();
    await tester.tap(find.textContaining("练这组").first);
    await tester.pump();
    expect(find.byType(SessionStage), findsOneWidget);
    await tester.pump(const Duration(seconds: 30));

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
