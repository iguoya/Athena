import "dart:async";
import "dart:io";

import "package:athena_driver/core/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:athena_driver/study/session.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

import "nav_helpers.dart";

void main() {
  const groupIds = [
    "score-pairs",
    "score-cycle",
    "license-terms",
    "license-types",
    "license-fines",
    "license-bans",
    "plates-registration",
  ];

  // 内容契约（ADR 0076）：七组齐备；每条有情景、要点与指到条款的出处——
  // 记分分值、罚款档位、期限都是硬规定，出处必须到条（沿用 0028、0064）。
  test("license_notes.json 七组齐备，每条都有情景、要点与条款定位", () async {
    final bank = await ContentLoader.load();
    expect([for (final g in bank.licenseGroups) g.id], groupIds);
    const sources = {
      "penalty-order-163",
      "license-order-162",
      "registration-order-164",
      "road-safety-law",
      "road-safety-regulation",
    };
    for (final group in bank.licenseGroups) {
      expect(group.items, isNotEmpty, reason: "${group.id} 没有条目");
      expect(group.items.length, lessThanOrEqualTo(10), reason: "${group.id} 条目过多，速记页每组不超过 10 条");
      for (final item in group.items) {
        expect(sources, contains(item.sourceId), reason: "${group.id} 的「${item.scenario}」出处不在登记过的法规里");
        expect(item.locator, isNotEmpty, reason: "${group.id} 的「${item.scenario}」缺条款号");
        expect(item.scenario, isNotEmpty);
        expect(item.points, isNotEmpty, reason: "${group.id} 的「${item.scenario}」没有要点");
      }
    }
  });

  // 按题面找相关题的正则（ADR 0076 决策 3）：每组都要抓得到题，合起来覆盖
  // 记分、证照、登记三个知识点的绝大多数题；不能是空壳。
  test("组 match 都抓得到题，合起来覆盖记分、证照、登记题的八成以上", () async {
    final bank = await ContentLoader.load();
    final subject1 = bank.forSubject("subject1");
    const topics = {"drive.s1.penalty", "drive.s1.license", "drive.s1.registration"};
    final topicQuestions = [for (final q in subject1) if (topics.contains(q.topicId)) q];
    final covered = <String>{};
    for (final group in bank.licenseGroups) {
      final related = group.related(subject1);
      expect(related.length, greaterThanOrEqualTo(30), reason: "${group.id} 抓到的题太少");
      covered.addAll([for (final q in related) if (topics.contains(q.topicId)) q.id]);
    }
    expect(covered.length / topicQuestions.length, greaterThan(0.8), reason: "组 match 对三个知识点的覆盖不足");
  });

  // 页面：用真实内容渲染，七组标题都在，不溢出。
  testWidgets("记分证照速记页用真实内容渲染不溢出，七组都在", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-license-notes-");
      store = await ProgressStore.open(suite: "license_notes_page_test");
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

    await showTopic(tester, "记分证照速记");
    await tester.tap(find.text("记分证照速记").first);
    await tester.pump();
    for (final group in bank.licenseGroups) {
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

  // 组级练习入口：点「练这组」起一轮相关题的练习。
  testWidgets("点「练这组」起一轮练习", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-license-notes-");
      store = await ProgressStore.open(suite: "license_notes_page_test_practice");
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
    await showTopic(tester, "记分证照速记");
    await tester.tap(find.text("记分证照速记").first);
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
