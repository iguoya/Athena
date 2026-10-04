import "dart:async";
import "dart:io";

import "package:athena_driver/clusters.dart";
import "package:athena_driver/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

/// 交互闭环的守卫（ADR 0061）：空态有出口，不能把人晾在原地。用空进度库渲染真实首页。
void main() {
  testWidgets("错题本空态有「去强化练习」的出口，强化页空池有「去练新题」的出口", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-interact-");
      store = await ProgressStore.open(suite: "interaction_test");
    });
    await tester.binding.setSurfaceSize(const Size(1600, 1200));
    final ready = Completer<void>();
    await tester.pumpWidget(
      MaterialApp(
        home: HomePage(
          bank: bank,
          store: store,
          onReady: ready.complete,
          clusterBuilder: (_) async => ClusterIndex.empty,
        ),
      ),
    );
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue, reason: "首页没在 20 秒内读完进度库");

    // 空库进错题本：文案诚实，出口接强化练习。
    await tester.tap(find.text("错题本").first);
    await tester.pump();
    expect(find.text("最近一次都做对了。"), findsOneWidget);
    await tester.tap(find.text("去强化练习"));
    await tester.pump();

    // 强化页：错题库为空时按薄弱章节抽新题补满一轮（主仓库 ADR 0085），
    // 题单可直接开始——空态没有断头。
    expect(find.textContaining("开始强化练习"), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
