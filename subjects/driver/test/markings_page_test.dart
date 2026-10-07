import "dart:async";
import "dart:io";

import "package:athena_driver/core/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/speed/marking.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

import "nav_helpers.dart";

void main() {
  // 内容契约（ADR 0065）：json 的每条 id 都要画得出来，含义文案不能缺——
  // 漏画的标线会落到 painter 兜底的问号图，测试把它挡在 check 阶段。
  test("markings.json 的每条 id 都能画，每条都有含义文案", () async {
    final bank = await ContentLoader.load();
    expect(bank.markings, isNotEmpty);
    for (final marking in bank.markings) {
      expect(paintableMarkingIds, contains(marking.id), reason: "${marking.id} 没有对应的绘制");
      expect(marking.meaning, isNotEmpty, reason: "${marking.id} 缺「看到之后怎么开」的文案");
      expect(marking.name, isNotEmpty);
      expect(["indicative", "prohibit", "warning"], contains(marking.kind),
          reason: "${marking.id} 的 kind 不在 GB 5768.3 三分法里");
    }
    // 分组别混：同 kind 的 kindLabel 一致，三组的标签互不相同。
    final labels = {for (final m in bank.markings) m.kind: m.kindLabel};
    expect(labels.length, 3);
  });

  // 挂题契约（ADR 0065 决策 3）：每条标线都挂着科目一的题，「自测答错后去做题」才有得练；
  // 挂出来的题必须真实存在，marking id 必须是 markings.json 里的条目。
  test("每条标线都挂着题，题上的 marking id 都有效", () async {
    final bank = await ContentLoader.load();
    final markingIds = {for (final m in bank.markings) m.id};
    final subject1 = bank.forSubject("subject1");
    final byMarking = <String, int>{};
    for (final q in subject1) {
      final marking = q.marking;
      if (marking == null) continue;
      expect(markingIds, contains(marking), reason: "${q.id} 挂了不存在的标线 $marking");
      byMarking[marking] = (byMarking[marking] ?? 0) + 1;
    }
    for (final marking in bank.markings) {
      expect(byMarking[marking.id], greaterThan(0), reason: "${marking.id} 一道相关题都没挂");
    }
    expect(byMarking.values.reduce((a, b) => a + b), greaterThan(80));
  });

  // 标线速记页：用真实内容渲染一遍，布局溢出这类问题只在渲染时暴露。
  testWidgets("标线速记页用真实内容渲染不溢出，三组都在", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-markings-");
      store = await ProgressStore.open(suite: "markings_page_test");
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

    await showTopic(tester, "标线速记");
    await tester.tap(find.text("标线速记").first);
    await tester.pump();
    expect(find.text("标线速记"), findsWidgets);
    // 高频标线有频次徽章（首屏的指示组里就有）。
    expect(find.text("高频"), findsWidgets);
    // 一屏放不下三个分组，滚到底逐组检查都渲染出来了。
    for (final label in ["指示标线", "禁止标线", "警告标线"]) {
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

}
