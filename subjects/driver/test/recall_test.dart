import "dart:async";
import "dart:io";

import "package:athena_driver/core/content.dart";
import "package:athena_driver/ui/glyphs.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:athena_driver/speed/recall.dart";
import "package:athena_driver/speed/recall_cards.dart";
import "package:athena_driver/study/reinforce.dart";
import "package:athena_driver/study/session.dart";
import "package:athena_driver/speed/speed_topics.dart";
import "package:flutter/material.dart";
import "package:flutter/services.dart";
import "package:flutter_test/flutter_test.dart";

import "nav_helpers.dart";

/// 自测（ADR 0077 起，ADR 0094 并入作答记录，ADR 0095 易混数字重新规划）：卡片流检索练习——
/// 四选一 / 数值手输、对错当场判定、答错重现、答对的不再出现、随时退出。
/// **自测的每次作答就是一条作答记录**：错题本、考前复习、强化练习用同一份记录。
/// 选手势页跑完整流程；标线页（33 张）看版面；易混数字页看手输。
void main() {
  Future<(Bank, ProgressStore, Directory)> boot(WidgetTester tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-recall-");
      store = await ProgressStore.open(suite: "recall_test");
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

  /// 自测作答写成作答记录后，首页隔 0.8 秒重读进度（去抖）：等去抖到点，再给重读的异步查询一点真实时间。
  Future<void> reload(WidgetTester tester) async {
    await tester.pump(const Duration(milliseconds: 1000));
    for (var i = 0; i < 100; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
  }

  Future<void> closeDialog(WidgetTester tester) async {
    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pump(const Duration(milliseconds: 400));
  }

  Future<void> openRecall(WidgetTester tester, String page) async {
    await showTopic(tester, page);
    await tester.tap(find.text(page).first);
    await tester.pump();
    await showTopic(tester, "自测");
    await tester.tap(find.text("自测").first);
    await tester.pump();
  }

  /// 作答当前卡再进下一张：[remembered] 为真点正确项（`recall-correct`），答对 0.9 秒后自动切
  /// （ADR 0089）；否则点一个错项，答错不自动切，要点底部中间的「下一张」。
  Future<void> answer(WidgetTester tester, {required bool remembered}) async {
    await tester.tap(
      remembered
          ? find.byKey(const ValueKey("recall-correct"))
          : find.byWidgetPredicate((w) {
              final k = w.key;
              return k is ValueKey<String> && k.value.startsWith("recall-option-");
            }).first,
    );
    await tester.pump();
    if (remembered) {
      await tester.pump(const Duration(milliseconds: 1000));
    } else {
      final next = find.textContaining("下一张");
      await tester.ensureVisible(next);
      await tester.pump();
      await tester.tap(next);
    }
    await tester.pump();
  }

  /// 卡片头里「剩 N 张」的 N：自测没有张数上限，剩多少就是还要过多少。
  int remaining() {
    final re = RegExp(r"剩 (\d+) 张");
    for (final e in find.textContaining("剩 ").evaluate()) {
      final w = e.widget;
      if (w is Text && w.data != null) {
        final m = re.firstMatch(w.data!);
        if (m != null) return int.parse(m[1]!);
      }
    }
    throw StateError("卡片头里没有「剩 N 张」");
  }

  /// 当前卡上的错项（四个选项里除正确项外的那些：键以 `recall-option-` 开头）。
  Finder wrongOptions() => find.byWidgetPredicate((w) {
    final k = w.key;
    return k is ValueKey<String> && k.value.startsWith("recall-option-");
  });

  Future<List<AttemptView>> recallAttempts(ProgressStore store) async => [
    for (final a in await store.allAttempts())
      if (isRecallQuestionId(a.questionId)) a,
  ];

  testWidgets("自测：手势页逐张过完，答错的重现，每次作答记成作答记录；再开只考没答对够的，答对的不再出现", (tester) async {
    final (bank, store, dir) = await boot(tester);
    final n = recallCardsOfTopic(speedTopicById("s1.gestures")!, bank).length;
    final before = await store.allAttempts();

    await openRecall(tester, "手势速记");
    expect(find.textContaining("想一想"), findsOneWidget);
    expect(find.text("已答对 0 / $n"), findsOneWidget);
    expect(find.textContaining("剩 $n 张"), findsOneWidget, reason: "没有张数上限：$n 张都没考过，就排 $n 张");
    // 出的是四选一：一个正确项加三个错项。
    expect(find.byKey(const ValueKey("recall-correct")), findsOneWidget);
    expect(wrongOptions(), findsNWidgets(3));

    // 第一张答错，其余答对；答错的隔两张后重现，重现时答对。
    var gradedMiss = false;
    for (var i = 0; i < 30; i++) {
      if (find.text("考完了").evaluate().isNotEmpty) break;
      await answer(tester, remembered: gradedMiss);
      gradedMiss = true;
    }
    expect(find.text("考完了"), findsOneWidget);
    expect(find.textContaining("这次共 $n 张"), findsOneWidget);
    expect(find.textContaining("答错 1 次"), findsOneWidget);
    expect(find.textContaining("答错的："), findsOneWidget, reason: "收尾列出答错的");
    expect(find.text("已答对 ${n - 1} / $n"), findsOneWidget, reason: "答错后重现才答对的那张不算第一次就答对");
    expect(find.textContaining("认得"), findsNothing, reason: "界面里没有「认得」这个概念");
    expect(find.textContaining("再来"), findsNothing, reason: "没有「再来一轮」");
    expect(find.textContaining("去做这几个的题"), findsOneWidget);
    expect(find.text("再测一遍"), findsNothing, reason: "没有全部答对：不给整页重考（ADR 0115）");

    // 每次作答都是一条作答记录：8 张各一次，加上答错那张重现的一次，共 9 条，其中 1 条答错。
    final attempts = await recallAttempts(store);
    expect(attempts.length, n + 1);
    expect(attempts.where((a) => !a.correct).length, 1);
    expect(attempts.every((a) => a.questionId.startsWith("drive.recall.s1.gestures.")), isTrue);
    expect((await store.allAttempts()).length, before.length + n + 1, reason: "只多了自测的 ${n + 1} 条");

    // 答错的卡进了错题库：累计答错数、强化练习的错题库用的就是这份记录（重现答对一次，错题本里已经移出，
    // 但累计答对 1 次还没到答错 1 次的 2 倍，强化练习仍会抽它）。
    expect((await store.wrongCounts()).entries.where((e) => isRecallQuestionId(e.key) && e.value == 1), hasLength(1));

    // 再开：只剩答错过、还没答对到 2 倍的那 1 张；答对的 7 张不再出现。
    await closeDialog(tester);
    await reload(tester);
    await showTopic(tester, "自测");
    await tester.tap(find.text("自测").first);
    await tester.pump();
    expect(find.text("已答对 ${n - 1} / $n"), findsOneWidget);
    expect(find.textContaining("剩 1 张"), findsOneWidget, reason: "第二次只考答错的");
    await answer(tester, remembered: true);
    expect(find.text("这一组全部答对了"), findsOneWidget);
    expect(find.text("再测一遍"), findsOneWidget, reason: "错 1 对 2 移出错题库，整页都答对了才给再测一遍");

    // 又答对一次（累计答对 2 次 ≥ 答错 1 次的 2 倍）：移出错题库，再开已经没有要考的了。
    await closeDialog(tester);
    await reload(tester);
    await showTopic(tester, "自测");
    await tester.tap(find.text("自测").first);
    await tester.pump();
    expect(find.text("这一组全部答对了"), findsOneWidget);
    expect(find.textContaining("都已经答对过"), findsOneWidget, reason: "全部答对过：收尾说明没有自动要考的了");
    expect(find.text("已答对 $n / $n"), findsOneWidget);
    await closeDialog(tester);

    await teardown(tester, store, dir);
  });

  testWidgets("自测：答错的卡出现在错题本里，和真题的错题一样", (tester) async {
    final (_, store, dir) = await boot(tester);
    await openRecall(tester, "手势速记");
    await answer(tester, remembered: false);
    await closeDialog(tester);
    await reload(tester);

    // 错题本里能看到这道速记题（手势题的题干是「这是什么手势信号？」）。
    expect(find.text("错题本 1"), findsOneWidget, reason: "侧栏错题本多了这一道");
    await showTopic(tester, "错题本 1");
    await tester.tap(find.text("错题本 1").first);
    await tester.pump();
    for (var i = 0; i < 20; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(find.textContaining("这是什么手势信号"), findsWidgets, reason: "错题本带出了自测答错的速记题");
    await teardown(tester, store, dir);
  });

  testWidgets("自测：中途退出（按钮或 Esc）不丢已判的，再打开接着考没答对的", (tester) async {
    final (bank, store, dir) = await boot(tester);
    final n = recallCardsOfTopic(speedTopicById("s1.gestures")!, bank).length;
    await openRecall(tester, "手势速记");
    expect(find.text("已答对 0 / $n"), findsOneWidget);

    // 答对两张，用右上角退出按钮离开。
    await answer(tester, remembered: true);
    await answer(tester, remembered: true);
    expect(find.text("已答对 2 / $n"), findsOneWidget);
    await tester.tap(find.byIcon(Glyph.close));
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.textContaining("想一想"), findsNothing, reason: "退出按钮应关掉自测");
    await reload(tester);

    // 再打开：答对过的 2 张不再出现，只剩 6 张；再答一张后用 Esc 退出，同样记着。
    await showTopic(tester, "自测");
    await tester.tap(find.text("自测").first);
    await tester.pump();
    expect(find.text("已答对 2 / $n"), findsOneWidget);
    expect(remaining(), n - 2);
    await answer(tester, remembered: true);
    await closeDialog(tester);
    await reload(tester);
    await showTopic(tester, "自测");
    await tester.tap(find.text("自测").first);
    await tester.pump();
    expect(find.text("已答对 3 / $n"), findsOneWidget);
    expect(remaining(), n - 3);
    await closeDialog(tester);
    await teardown(tester, store, dir);
  });

  testWidgets("自测：解释在选项右侧，答对自动切下一张，答错留在解释上，「下一张」在底部中间（ADR 0089）", (tester) async {
    final (_, store, dir) = await boot(tester);
    await openRecall(tester, "标线速记");
    final total = remaining();
    expect(total, greaterThan(10), reason: "标线 33 条都没考过，就排 33 张，没有「一轮几张」的上限");

    // 版面：选项在左，解释在右（未作答时右栏是一句提示），选项不再拉满整行。
    final option = find.byKey(const ValueKey("recall-correct"));
    final hint = find.text("作答之后，这里给出解释。");
    expect(hint, findsOneWidget);
    expect(tester.getTopLeft(hint).dx, greaterThan(tester.getTopRight(option).dx), reason: "解释放在选项右侧");
    final session = find.byType(RecallSession);
    expect(
      tester.getTopRight(option).dx,
      lessThan(tester.getCenter(session).dx + tester.getSize(session).width * 0.15),
      reason: "选项只占左边一半多一点",
    );

    // 答对：右栏出解释，「下一张」在底部中间；等 0.9 秒自动切到下一张。
    await tester.tap(option);
    await tester.pump();
    expect(find.textContaining("答对了"), findsOneWidget);
    final next = find.textContaining("下一张");
    expect(next, findsOneWidget);
    expect((tester.getCenter(next).dx - tester.getCenter(session).dx).abs(), lessThan(4), reason: "下一张在底部中间");
    expect(tester.getTopLeft(next).dy, greaterThan(tester.getBottomLeft(option).dy), reason: "下一张在选项下方");
    expect(remaining(), total);
    await tester.pump(const Duration(milliseconds: 1000));
    await tester.pump();
    expect(remaining(), total - 1, reason: "答对自动切到下一张");

    // 答错：不自动切，停在解释上，点「下一张」才走。
    await tester.tap(wrongOptions().first);
    await tester.pump();
    expect(find.textContaining("答错了，正确答案："), findsOneWidget);
    await tester.pump(const Duration(seconds: 3));
    expect(find.textContaining("答错了，正确答案："), findsOneWidget, reason: "答错不自动切，留着看解释");
    await tester.ensureVisible(find.textContaining("下一张"));
    await tester.pump();
    await tester.tap(find.textContaining("下一张"));
    await tester.pump();
    expect(find.textContaining("答错了，正确答案："), findsNothing);
    expect(find.textContaining("想一想"), findsOneWidget);

    await closeDialog(tester);
    await teardown(tester, store, dir);
  });

  testWidgets("自测：侧栏里全部 15 个速记页每组都有入口，页头没有全页自测，组内自测只考这一组（ADR 0116）", (tester) async {
    final (bank, store, dir) = await boot(tester);
    for (final page in ["易混数字", "标志速记", "标线速记", "仪表速记", "手势速记", "考点速记", "河南速记", "记分证照速记", "事故处理与时限", "停车与违停", "乘员与安全带", "信号灯与铁路道口", "超车会车与掉头倒车", "车辆基础与操作", "电动汽车"]) {
      await showTopic(tester, page);
      await tester.tap(find.text(page).first);
      await tester.pump();
      expect(find.text("自测"), findsWidgets, reason: "$page 缺组内自测入口");
      await showTopic(tester, "自测");
      await tester.tap(find.text("自测").first);
      await tester.pump();
      expect(remaining(), greaterThanOrEqualTo(1), reason: "$page 应把这一组没考过的卡都排出来");
      expect(
        find.descendant(of: find.byType(RecallSession), matching: find.textContaining("认得")),
        findsNothing,
        reason: "$page：自测界面里没有「认得」这个概念",
      );
      await closeDialog(tester);
    }
    // 组内自测只考这一组：记分证照第一组有几条，就排几张。
    final license = noteGroupsOf(bank, speedTopicById("s1.license-notes")!).first;
    await showTopic(tester, "记分证照速记");
    await tester.tap(find.text("记分证照速记").first);
    await tester.pump();
    await showTopic(tester, "自测");
    await tester.tap(find.text("自测").first);
    await tester.pump();
    expect(find.textContaining("剩 ${license.items.length} 张"), findsOneWidget, reason: "第一组「${license.title}」只考自己的卡");
    await closeDialog(tester);
    await teardown(tester, store, dir);
  });

  testWidgets("自测：易混数字的数值题手输——填对答对、填错答错并给标准答案，作答记成记录", (tester) async {
    final (bank, store, dir) = await boot(tester);
    final cards = recallCardsOfNumbers("s1.numbers", cheatGroupsOf(bank, speedTopicById("s1.numbers")!));
    await openRecall(tester, "易混数字");
    expect(find.textContaining("认得"), findsNothing);

    String? stemShown() {
      final texts = tester
          .widgetList<Text>(find.descendant(of: find.byType(RecallSession), matching: find.byType(Text)))
          .where((t) => t.style?.fontSize == 24)
          .map((t) => t.data ?? "");
      return texts.isEmpty ? null : texts.first;
    }

    /// 翻到一张手输卡：不是手输的就答对（选择 / 反向题点正确项）跳过去。
    Future<RecallCard> toTyped() async {
      for (var i = 0; i < 80; i++) {
        if (find.byKey(const ValueKey("recall-typed")).evaluate().isNotEmpty) {
          final stem = stemShown();
          return cards.firstWhere((c) => c.typed != null && c.stem == stem, orElse: () => fail("找不到题干 $stem 对应的卡"));
        }
        await answer(tester, remembered: true);
      }
      fail("80 张里没翻到手输卡");
    }

    // 第一张手输卡：填错 → 答错、给标准答案、不自动切。
    var card = await toTyped();
    expect(find.text("确定（Enter）"), findsOneWidget);
    expect(wrongOptions(), findsNothing, reason: "手输题不出选项");
    await tester.enterText(find.byKey(const ValueKey("recall-typed")), "7777");
    await showTopic(tester, "确定（Enter）");
    await tester.tap(find.text("确定（Enter）"));
    await tester.pump();
    expect(find.textContaining("答错了，正确答案："), findsOneWidget);
    expect(find.textContaining("你填的：7777"), findsOneWidget);
    expect(find.text(card.name), findsWidgets, reason: "答后给出标准答案");
    await tester.pump(const Duration(seconds: 3));
    expect(find.textContaining("答错了，正确答案："), findsOneWidget, reason: "答错不自动切");
    await tester.ensureVisible(find.textContaining("下一张"));
    await tester.tap(find.textContaining("下一张"));
    await tester.pump();

    // 再翻到下一张手输卡：填对 → 答对、自动切。答案按卡里的数字序列敲（区间用「-」连接）。
    card = await toTyped();
    final right = card.typed!.numbers.map((n) => n == n.roundToDouble() ? n.round().toString() : n.toString()).join("-");
    await tester.enterText(find.byKey(const ValueKey("recall-typed")), right);
    await showTopic(tester, "确定（Enter）");
    await tester.tap(find.text("确定（Enter）"));
    await tester.pump();
    expect(find.textContaining("答对了"), findsOneWidget, reason: "填 $right 应判对：${card.stem}");
    await tester.pump(const Duration(milliseconds: 1000));

    // 作答都记下了：答错的 1 条在错题库里。
    final attempts = await recallAttempts(store);
    expect(attempts.where((a) => !a.correct).length, 1);
    // 累计答错数是确定的；错题本里是否还留着取决于答错的卡有没有在队列里重现并答对（顺序随机），不在这里断言。
    expect((await store.wrongCounts()).entries.where((e) => isRecallQuestionId(e.key) && e.value == 1), hasLength(1));

    await closeDialog(tester);
    await teardown(tester, store, dir);
  });

  testWidgets("自测：要点页（考点速记）情景 → 四选一，答后给完整要点", (tester) async {
    final (_, store, dir) = await boot(tester);
    await openRecall(tester, "考点速记");
    expect(find.textContaining("碰到这个情景该怎么做"), findsOneWidget);
    expect(find.byKey(const ValueKey("recall-correct")), findsOneWidget, reason: "出的是四选一");
    await tester.tap(find.byKey(const ValueKey("recall-correct")));
    await tester.pump();
    expect(find.text("要点"), findsOneWidget, reason: "答后显示完整要点");
    expect(find.textContaining("答对了"), findsOneWidget, reason: "对错当场判定");
    await closeDialog(tester);
    await teardown(tester, store, dir);
  });

  testWidgets("自测：收尾「去做这几个的题」把答错的卡关联的真题起一轮练习", (tester) async {
    final (_, store, dir) = await boot(tester);
    await openRecall(tester, "手势速记");
    // 第一张答错，其余答对，答错的重现时答对。
    var first = true;
    for (var i = 0; i < 30; i++) {
      if (find.text("考完了").evaluate().isNotEmpty) break;
      await answer(tester, remembered: !first);
      first = false;
    }
    await tester.tap(find.textContaining("去做这几个的题"));
    await tester.pump();
    expect(find.byType(SessionStage), findsOneWidget);
    await teardown(tester, store, dir);
  });

  testWidgets("自测的速记题能进强化练习的题池：答错的速记题被强化练习抽到", (tester) async {
    final (bank, store, dir) = await boot(tester);
    await openRecall(tester, "手势速记");
    await answer(tester, remembered: false);
    await closeDialog(tester);
    await tester.runAsync(() async {
      final histories = HistorySet.build(await store.allAttempts());
      final wrongRecall = [for (final q in bank.questions) if (isRecallQuestionId(q.id) && (histories.of(q.id)?.wrong ?? 0) > 0) q];
      expect(wrongRecall, hasLength(1));
      final plan = planReinforcement(
        pool: [for (final q in bank.questions) if (isRecallQuestionId(q.id) || q.topicId.startsWith("drive.s1.")) q],
        histories: histories,
        now: DateTime.now().add(const Duration(days: 1)),
        clusters: null,
        count: 20,
      );
      expect(plan.questions.any((q) => q.id == wrongRecall.single.id), isTrue);
    });
    await teardown(tester, store, dir);
  });
}
