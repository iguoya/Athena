import "dart:async";
import "dart:io";
import "dart:math";

import "package:athena_driver/core/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:athena_driver/speed/recall_cards.dart";
import "package:athena_driver/speed/recall_status.dart";
import "package:athena_driver/study/reinforce.dart";
import "package:athena_driver/study/session.dart";
import "package:athena_driver/speed/speed_topics.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

import "nav_helpers.dart";

/// 自测（ADR 0094 并入作答记录，ADR 0118 改用做题界面、现场出题）：速记组的「自测」按这一组条目的内容
/// 现场出四选一，用错题本那套做题界面考，不弹对话框、不手输；答错还在错题库里的先出、没测过的其次，
/// 答对过的不再出；整组都答对了才给「再测一遍」整组重考。**作答就是普通作答记录**，题号沿用卡的。
void main() {
  Future<(Bank, ProgressStore, Directory)> boot(
    WidgetTester tester, {
    Future<void> Function(Bank bank, ProgressStore store)? seed,
  }) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-recall-");
      store = await ProgressStore.open(suite: "recall_test");
      await seed?.call(bank, store);
    });
    // 专题挂在各科目底下，侧栏高一点才都看得见（科目一的章节加专题）。
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
    return (bank, store, dir);
  }

  Future<void> teardown(WidgetTester tester, ProgressStore store, Directory dir) async {
    await tester.pump(const Duration(seconds: 30));
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  }

  Future<void> openTopic(WidgetTester tester, String page) async {
    await showTopic(tester, page);
    await tester.tap(find.text(page).first);
    await tester.pump();
  }

  /// 手势专题只有一组「8 个法定动作」：它的全部卡。
  List<RecallCard> gestureCards(Bank bank) => recallCardsOfTopic(speedTopicById("s1.gestures")!, bank);

  Future<void> record(ProgressStore store, RecallCard card, {required bool correct}) => store.recordAttempt(
    questionId: card.questionId,
    topicId: "$recallTopicPrefix${card.page}",
    subjectId: "subject1",
    correct: correct,
  );

  /// 点第一组的「自测」，返回起起来的这一轮的题。
  Future<List<Question>> startRecall(WidgetTester tester) async {
    final button = find.byType(GroupRecallButton).first;
    await tester.ensureVisible(button);
    await tester.pump();
    await tester.tap(button);
    await tester.pump();
    expect(find.byType(SessionStage), findsOneWidget, reason: "自测用做题界面，不弹对话框");
    return tester.widget<SessionStage>(find.byType(SessionStage)).launch.questions;
  }

  testWidgets("自测：点组里的「自测」直接起一轮做题，全是四选一，只考这一组没测过的卡", (tester) async {
    final (bank, store, dir) = await boot(tester);
    final cards = gestureCards(bank);
    await openTopic(tester, "手势速记");
    expect(find.text("自测 ${cards.length} 题"), findsOneWidget, reason: "一张没测过：整组都要考");
    final launched = await startRecall(tester);
    expect(launched.map((q) => q.id).toSet(), cards.map((c) => c.questionId).toSet(), reason: "题号沿用卡的");
    expect(launched.every((q) => q.kind == "single" && q.choices.length >= 2), isTrue, reason: "全是选择题，没有手输");
    expect(launched.every((q) => q.choices.where((c) => c.ok).length == 1), isTrue);
    final session = tester.widget<SessionStage>(find.byType(SessionStage)).launch;
    expect(session.recordChosen, isFalse, reason: "现场出的题选项每次不同，不记所选选项");
    await teardown(tester, store, dir);
  });

  testWidgets("自测：答错还在错题库里的先出、没测过的其次，答对过的不再出", (tester) async {
    late List<RecallCard> cards;
    final (_, store, dir) = await boot(tester, seed: (bank, store) async {
      cards = gestureCards(bank);
      await record(store, cards[0], correct: true); // 答对过：不再出
      await record(store, cards[1], correct: false); // 错 1 对 1：还在错题库里
      await record(store, cards[1], correct: true);
    });
    await openTopic(tester, "手势速记");
    expect(find.text("自测 ${cards.length - 1} 题"), findsOneWidget);
    final launched = await startRecall(tester);
    expect(launched.first.id, cards[1].questionId, reason: "错题库里的先出");
    expect(launched.any((q) => q.id == cards[0].questionId), isFalse, reason: "答对过的不再出");
    expect(launched, hasLength(cards.length - 1));
    await teardown(tester, store, dir);
  });

  testWidgets("自测：整组每张都答对了才给「再测一遍」，点了整组重考；按钮变绿", (tester) async {
    late List<RecallCard> cards;
    final (_, store, dir) = await boot(tester, seed: (bank, store) async {
      cards = gestureCards(bank);
      for (final c in cards) {
        await record(store, c, correct: true);
      }
    });
    await openTopic(tester, "手势速记");
    final again = find.text("再测一遍 ${cards.length} 题");
    expect(again, findsOneWidget);
    final button = tester.widget<FilledButton>(find.ancestor(of: again, matching: find.bySubtype<FilledButton>()).first);
    expect(button.style?.backgroundColor?.resolve(<WidgetState>{}), const Color(0xFF2ECC71), reason: "整组答对：绿");
    final launched = await startRecall(tester);
    expect(launched, hasLength(cards.length), reason: "再测一遍考整组");
    await teardown(tester, store, dir);
  });

  testWidgets("自测：15 个速记页每组都有「自测」，页头没有全页自测；记分证照第一组只考自己的条目", (tester) async {
    final (bank, store, dir) = await boot(tester);
    for (final page in ["易混数字", "标志速记", "标线速记", "仪表速记", "手势速记", "考点速记", "河南速记", "记分证照速记", "事故处理与时限", "停车与违停", "乘员与安全带", "信号灯与铁路道口", "超车会车与掉头倒车", "车辆基础与操作", "电动汽车"]) {
      await openTopic(tester, page);
      final buttons = find.byType(GroupRecallButton);
      expect(buttons, findsWidgets, reason: "$page 缺组内自测入口");
      expect(find.text("自测"), findsNothing, reason: "$page：页头不再有全页自测");
      final ids = tester.widget<GroupRecallButton>(buttons.first).ids;
      expect(ids, isNotEmpty, reason: "$page 第一组没有可自测的卡");
      expect(ids.every(isRecallQuestionId), isTrue, reason: "$page：自测只考速记卡");
    }
    final license = noteGroupsOf(bank, speedTopicById("s1.license-notes")!).first;
    await openTopic(tester, "记分证照速记");
    final launched = await startRecall(tester);
    expect(launched, hasLength(license.items.length), reason: "第一组「${license.title}」只考自己的条目");
    await teardown(tester, store, dir);
  });

  test("现场出题：每张卡都出得了题（没有题图的仪表卡改用文字问），正确项唯一", () async {
    final bank = await ContentLoader.load();
    for (final topic in speedTopics) {
      for (final card in recallCardsOfTopic(topic, bank)) {
        expect(askable(card), isTrue, reason: "${card.questionId}（${card.name}）出不了题");
      }
    }
    final gauges = recallCardsOfTopic(speedTopicById("s1.gauges")!, bank);
    final tire = gauges.firstWhere((c) => c.id == "tire_pressure");
    final q = freshRecallQuestionOf(tire, gauges, Random(1));
    expect(q.image, isNull);
    expect(q.prompt, contains("黄色蹄形加感叹号"), reason: "没有题图就用说明里的外观描述问");
    expect(q.choices.where((c) => c.ok).single.label, tire.name);
  });

  testWidgets("自测的速记题能进强化练习的题池：答错的速记题被强化练习抽到", (tester) async {
    late RecallCard missed;
    final (bank, store, dir) = await boot(tester, seed: (bank, store) async {
      missed = gestureCards(bank).first;
      await record(store, missed, correct: false);
    });
    await tester.runAsync(() async {
      final histories = HistorySet.build(await store.allAttempts());
      final plan = planReinforcement(
        pool: [for (final q in bank.questions) if (isRecallQuestionId(q.id) || q.topicId.startsWith("drive.s1.")) q],
        histories: histories,
        now: DateTime.now().add(const Duration(days: 1)),
        clusters: null,
        count: 20,
      );
      expect(plan.questions.any((q) => q.id == missed.questionId), isTrue);
    });
    await teardown(tester, store, dir);
  });
}
