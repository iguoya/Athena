import "dart:async";

import "package:athena_driver/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:athena_driver/sync.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  // 回归：首页只在启动时读一次本地库，而后台同步是启动之后才把数据拉下来的。
  // 旧行为：登录后界面一直是空的（数据其实早已在本地库里），要重开才看得见。
  testWidgets("后台同步拉到新数据后，首页自动重读，不用重开应用", (tester) async {
    late Bank bank;
    late ProgressStore store;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      store = await ProgressStore.open(suite: "home_sync_refresh");
    });
    final status = ValueNotifier(const SyncStatus());
    await tester.binding.setSurfaceSize(const Size(1600, 1000));
    final ready = Completer<void>();
    await tester.pumpWidget(MaterialApp(
      home: HomePage(bank: bank, store: store, syncStatus: status, onReady: ready.complete),
    ));
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue);
    expect(find.text("错题本"), findsOneWidget, reason: "本地库还是空的：错题本没有数字");

    // 后台同步把 3 道答错的科目一题拉进了本地库，并通知「拉到了 3 条」
    final wrong = bank.forSubject("subject1").where((q) => !q.isRare).take(3).toList();
    store.applyRemote("attempts", [
      for (var i = 0; i < wrong.length; i++)
        {
          "question_id": wrong[i].id, "topic_id": wrong[i].topicId, "subject_id": "subject1",
          "correct": 0, "hesitant": 0, "duration_ms": 5000, "at": "2026-10-01T09:0$i:00.000", "kind": "practice",
        },
    ]);
    status.value = const SyncStatus(pulled: 3);
    for (var i = 0; i < 2000 && find.text("错题本 3").evaluate().isEmpty; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(find.text("错题本 3"), findsOneWidget, reason: "拉到新数据后首页应自动重读");

    // 同步还在跑（running）时不重读；没有新拉到数据也不重读
    status.value = const SyncStatus(pulled: 3, running: true);
    await tester.pump();
    expect(tester.takeException(), isNull);

    await tester.pumpWidget(const SizedBox());
    status.dispose();
    await tester.runAsync(() => store.close());
  });
}
