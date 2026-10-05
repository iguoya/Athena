import "dart:async";
import "dart:io";

import "package:athena_driver/cloze.dart";
import "package:athena_driver/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:athena_driver/recall.dart";
import "package:athena_driver/recall_cards.dart";
import "package:athena_driver/speed_topics.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

import "nav_helpers.dart";

void main() {
  // 易混数字页（ADR 0028）：用真实内容渲染一遍，布局溢出这类问题只在渲染时暴露。
  testWidgets("易混数字页用真实内容渲染不溢出，每组都有练习按钮", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-numbers-");
      store = await ProgressStore.open(suite: "numbers_page_test");
    });
    await tester.binding.setSurfaceSize(const Size(1600, 2600));
    // 关掉自动同步：首页一启动就会按本机 sync.json 去读写真实的云盘目录，测试不能碰它。
    final ready = Completer<void>();
    await tester.pumpWidget(
      MaterialApp(home: HomePage(bank: bank, store: store, onReady: ready.complete)),
    );
    // 等首页从进度库读完统计再往下走，免得关库时还有查询在跑。查询的后续步骤要靠 pump
    // 推进，所以边让真实时间走一点、边 pump，直到就绪回调触发。
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue, reason: "首页没在 20 秒内读完进度库");

    await showTopic(tester, "易混数字");
    await tester.tap(find.text("易混数字").first);
    await tester.pump();
    expect(find.text("记分分值"), findsOneWidget);
    // 一屏放不下全部分组，滚到底检查每组都渲染出来了（页面的组来自专题，ADR 0097）。
    for (final group in cheatGroupsOf(bank, speedTopics.firstWhere((t) => t.id == "s1.numbers"))) {
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

  testWidgets("易混数字每行按自测卡的作答记录标状态点：答错红、答对过绿、没做过灰", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-numbers-dot-");
      store = await ProgressStore.open(suite: "numbers_page_dot_test");

      // 前三行造三种状态：第一行答错（红）、第二行答对但反向卡没答（黄）、第三行不动（灰）。
      // 卡题号由行数据直接构造，与 [recallCardsOfNumbers] 的合成规则一致；页键是专题 id（ADR 0097）。
      final topic = speedTopics.firstWhere((t) => t.id == "s1.numbers");
      final group = cheatGroupsOf(bank, topic).first;
      final rows = group.rows;
      Future<void> attempt(String entryKey, {required bool correct}) async {
        await store.recordAttempt(
          questionId: recallQuestionId(topic.id, entryKey),
          topicId: "drive.recall.${topic.id}",
          subjectId: "subject1",
          correct: correct,
        );
      }

      final firstCases = splitCase(rows[0].caseText);
      await attempt("f/${group.id}/${firstCases.first}|${rows[0].value}", correct: false);
      final secondCases = splitCase(rows[1].caseText);
      await attempt("f/${group.id}/${secondCases.first}|${rows[1].value}", correct: true);
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
    expect(ready.isCompleted, isTrue);

    await showTopic(tester, "易混数字");
    await tester.tap(find.text("易混数字").first);
    await tester.pump();
    expect(find.text("记分分值"), findsOneWidget);

    // 页面顶上是第一组，前三行的微点按文档序排：红、绿、灰（三态，ADR 0101）。
    final dots = tester.widgetList<RecallRowDot>(find.byType(RecallRowDot)).toList();
    expect(dots.length, greaterThanOrEqualTo(3), reason: "每行左侧都该有状态点");
    expect(dots[0].status, SymbolStatus.wrong, reason: "第一行最近答错过");
    expect(dots[1].status, SymbolStatus.mastered, reason: "第二行答对过（哪怕只答了一部分卡）");
    expect(dots[2].status, SymbolStatus.fresh, reason: "第三行没作答过");

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
