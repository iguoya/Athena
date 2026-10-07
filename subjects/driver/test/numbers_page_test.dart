import "dart:async";
import "dart:io";

import "package:athena_driver/speed/cloze.dart";
import "package:athena_driver/core/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/speed/numbers_page.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:athena_driver/speed/recall_status.dart";
import "package:athena_driver/speed/recall_cards.dart";
import "package:athena_driver/speed/speed_topics.dart";
import "package:athena_driver/study/reinforce.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

import "nav_helpers.dart";

void main() {
  // 易混数字页（ADR 0028）：用真实内容渲染一遍，布局溢出这类问题只在渲染时暴露。
  test("掌握 a/b 按条目数：一行名下的卡都答对才算掌握一条（ADR 0119）", () async {
    final bank = await ContentLoader.load();
    final topic = speedTopicById("s1.numbers")!;
    final entries = recallEntriesOfTopic(topic, bank);
    final rows = [for (final g in cheatGroupsOf(bank, topic)) ...g.rows];
    expect(entries, hasLength(rows.length), reason: "条目数就是行数");
    final multi = entries.firstWhere((e) => e.length > 1);
    final t0 = DateTime(2026, 10, 7);
    // 只答对这一行的一张卡：这一行还不算掌握。
    var m = masteryOf(entries: [multi], histories: HistorySet.build([AttemptView(questionId: multi.first, topicId: "t", correct: true, at: t0)]));
    expect(m, (done: 0, total: 1));
    m = masteryOf(entries: [multi], histories: HistorySet.build([for (final id in multi) AttemptView(questionId: id, topicId: "t", correct: true, at: t0)]));
    expect(m, (done: 1, total: 1));
  });

  test("还要再对几次：最近一次答错的卡各差一次，答对过的、没答过的不算（ADR 0120、0121）", () {
    final t0 = DateTime(2026, 10, 7);
    AttemptView at(String id, bool ok, int m) => AttemptView(questionId: id, topicId: "t", correct: ok, at: t0.add(Duration(minutes: m)));
    final h = HistorySet.build([at("a", false, 0), at("a", true, 1), at("b", true, 2), at("b", false, 3), at("c", false, 4)]);
    expect(recallRetireGap(["a"], h), 0, reason: "错过一次但最近答对了：不用再对");
    expect(recallRetireGap(["b", "c"], h), 2, reason: "两张最近一次都错：各差一次");
    expect(recallRetireGap(["a", "x"], h), 0, reason: "没答过的卡不算差几次");
  });

  test("专题掌握只认自测里的作答：普通做题（记了所选选项）里答速记卡不算（ADR 0119）", () {
    final t0 = DateTime(2026, 10, 7);
    const card = "drive.recall.s1.numbers.deadbeef";
    final inPractice = AttemptView(questionId: card, topicId: "t", correct: false, at: t0, chosen: "B");
    final inSelfTest = AttemptView(questionId: card, topicId: "t", correct: true, at: t0.add(const Duration(minutes: 1)));
    expect(isSelfTestAttempt(inPractice), isFalse);
    expect(isSelfTestAttempt(inSelfTest), isTrue);
    expect(isSelfTestAttempt(AttemptView(questionId: "drive.s1.rules.1", topicId: "t", correct: true, at: t0)), isFalse, reason: "真题不是自测");
    final h = selfTestHistories([inPractice, inSelfTest]);
    expect(statusOfIds(ids: [card], histories: h), SymbolStatus.mastered, reason: "错题本里答错那次不拖累专题掌握");
  });

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
    // 「掌握 a/b」按页面上的行数计，不按背后的卡数（ADR 0119）：记分分值有几行就是 /几。
    final score = cheatGroupsOf(bank, speedTopicById("s1.numbers")!).firstWhere((g) => g.title == "记分分值");
    expect(find.text("掌握 0/${score.rows.length}"), findsWidgets, reason: "分母是行数 ${score.rows.length}");
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

  testWidgets("易混数字每行按自测卡的作答记录标状态点：答错红、全部答对绿、没测完灰", (tester) async {
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
    expect(dots[1].status, SymbolStatus.fresh, reason: "第二行只答对了一部分卡：没测完不算掌握（ADR 0113）");
    expect(dots[2].status, SymbolStatus.fresh, reason: "第三行没作答过");

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });

  // 急救数字只有两个值，不出反向卡；行的状态点不能去等一张不存在的卡，否则整行答对也永远灰。
  testWidgets("易混数字：整个专题的卡都答对后，急救数字这类没有反向卡的行也是绿点", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-numbers-all-");
      store = await ProgressStore.open(suite: "numbers_page_all_test");
      final topic = speedTopics.firstWhere((t) => t.id == "s1.numbers");
      for (final card in recallCardsOfNumbers(topic.id, cheatGroupsOf(bank, topic))) {
        await store.recordAttempt(
          questionId: card.questionId,
          topicId: "drive.recall.${topic.id}",
          subjectId: "subject1",
          correct: true,
        );
      }
    });
    await tester.binding.setSurfaceSize(const Size(1600, 2600));
    final ready = Completer<void>();
    await tester.pumpWidget(MaterialApp(home: HomePage(bank: bank, store: store, onReady: ready.complete)));
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue);

    await showTopic(tester, "易混数字");
    await tester.tap(find.text("易混数字").first);
    await tester.pump();
    await tester.scrollUntilVisible(find.text("急救数字"), 600, scrollable: find.byType(Scrollable).last);
    await tester.pump();

    final dots = tester.widgetList<RecallRowDot>(find.byType(RecallRowDot)).toList();
    expect(dots, isNotEmpty);
    expect(
      dots.every((d) => d.status == SymbolStatus.mastered),
      isTrue,
      reason: "每张卡都答对了，所有已渲染的行都该是绿点",
    );

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
