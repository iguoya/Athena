import "dart:async";
import "dart:io";

import "package:athena_driver/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:athena_driver/session.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  // 内容契约（ADR 0068）：每组至少一条目，每条目都有河南条例的条款定位——
  // 罚款与赔偿比例是硬规定，条目出处必须指到条文。
  test("henan.json 五组齐备，条目都挂河南条例条款", () async {
    final bank = await ContentLoader.load();
    expect(bank.henanGroups.length, 5);
    for (final group in bank.henanGroups) {
      expect(group.items, isNotEmpty, reason: "${group.id} 没有条目");
      for (final item in group.items) {
        expect(["henan-road-safety", "henan-expressway"], contains(item.sourceId),
            reason: "${group.id} 的「${item.scenario}」出处不是河南条例");
        expect(item.locator, isNotEmpty, reason: "${group.id} 的「${item.scenario}」缺条款号");
        expect(item.points, isNotEmpty);
      }
    }
  });

  // match 抓取面（ADR 0068 决策 3）：各组正则以「在河南」锚定，要在地方题上
  // 抓得到、不误抓全国题；合起来覆盖绝大多数河南题。
  test("组 match 覆盖河南题且不误抓全国题", () async {
    final bank = await ContentLoader.load();
    final subject1 = bank.forSubject("subject1");
    final henan = [for (final q in subject1) if (q.topicId == "drive.s1.henan") q];
    expect(henan.length, greaterThan(90));
    final covered = <String>{};
    for (final group in bank.henanGroups) {
      final related = group.related(subject1);
      for (final q in related) {
        if (q.topicId == "drive.s1.henan") {
          covered.add(q.id);
        } else {
          // 通行与借道组抓到的 rules.028 内容就是河南限速档，算正确收录；
          // 其余全国题都算误抓。
          expect(q.id, "drive.s1.rules.028", reason: "${group.id} 误抓 ${q.id}");
        }
      }
      expect(related.where((q) => q.topicId == "drive.s1.henan"), isNotEmpty,
          reason: "${group.id} 一道河南题都抓不到");
    }
    expect(covered.length, greaterThan(88), reason: "组 match 对河南题覆盖不足");
  });

  // 河南速记页：用真实内容渲染一遍，五组都在。
  testWidgets("河南速记页用真实内容渲染不溢出，五组都在", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-henan-");
      store = await ProgressStore.open(suite: "henan_page_test");
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

    await tester.tap(find.text("河南速记").first);
    await tester.pump();
    expect(find.text("河南速记"), findsWidgets);
    for (final label in ["罚款对照（河南档次）", "高速公路（河南规矩）", "通行与借道", "车辆与牵引", "事故责任与赔偿"]) {
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

  // 组级练习入口：进页面首屏就是罚款组，「练这组」一点就起一轮河南题练习。
  testWidgets("点「练这组」起一轮河南题练习", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-henan-");
      store = await ProgressStore.open(suite: "henan_page_test_practice");
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
    await tester.tap(find.text("河南速记").first);
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
