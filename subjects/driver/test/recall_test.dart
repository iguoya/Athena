import "dart:async";
import "dart:io";

import "package:athena_driver/content.dart";
import "package:athena_driver/glyphs.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:athena_driver/recall.dart";
import "package:athena_driver/session.dart";
import "package:flutter/material.dart";
import "package:flutter/services.dart";
import "package:flutter_test/flutter_test.dart";

/// 自测模式（ADR 0077 起，ADR 0080 一轮 5 个，ADR 0082 改名并只考没认得的，ADR 0085 改四选一，
/// ADR 0089 答对自动切下一张、解释放选项右侧，ADR 0090 去掉「一轮几张」，没认得的逐张过完）：
/// 检索练习的卡片流——四选一作答、对错当场判定、答错重现、已认得的不再考、随时退出、
/// 收尾「再来 / 重新自测」。自测作答不写掌握度：自测之后进度库里的作答记录不应有任何变化。
/// 选手势页（8 个动作）跑完整流程；标线页（33 条）看版面与逐张过完。
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
    await tester.binding.setSurfaceSize(const Size(1600, 1000));
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

  /// 作答当前卡再进下一张：[remembered] 为真点正确项（`recall-correct`），答对 0.9 秒后自动切
  /// （ADR 0089）；否则点一个错项（选项键以 `recall-option-` 开头的都是错项），答错不自动切，
  /// 要点底部中间的「下一张」。
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
      // 答后内容可能超出可视区（整卡可滚动，ADR 0080），先滚到「下一张」再点。
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

  testWidgets("自测：四选一，没认得的逐张过完，答错的重现且不算认得，认得的不再考，考完给「重新自测」，作答不落库", (tester) async {
    final (_, store, dir) = await boot(tester);
    final before = await store.allAttempts();

    // 进手势速记页（8 个动作），打开自测。
    await tester.tap(find.text("手势速记").first);
    await tester.pump();
    await tester.tap(find.text("自测").first);
    await tester.pump();
    expect(find.textContaining("想一想"), findsOneWidget);
    expect(find.textContaining("已认得 0 / 8（以作答记录为准）"), findsOneWidget);
    // 出的是四选一：一个正确项加三个错项。
    expect(find.byKey(const ValueKey("recall-correct")), findsOneWidget);
    expect(wrongOptions(), findsNWidgets(3));

    // 第 1 轮：第一次答错，之后一直答对，直到收尾。
    var gradedMiss = false;
    expect(find.textContaining("剩 8 张"), findsOneWidget, reason: "没有张数上限：8 个动作都没认得，就排 8 张");
    for (var i = 0; i < 30; i++) {
      if (find.text("考完了").evaluate().isNotEmpty) break;
      await answer(tester, remembered: gradedMiss);
      gradedMiss = true;
    }
    expect(find.text("考完了"), findsOneWidget, reason: "8 张卡应在 30 次交互内考完（含答错的重现）");
    expect(find.textContaining("这次共 8 张"), findsOneWidget);
    expect(find.textContaining("答错 1 次"), findsOneWidget, reason: "第一次答错应计入");
    // 7 张第一次就答对 → 只是「自测答对」：认得以作答记录为准，没做题就还不算；
    // 答错后重现才答对的那张连自测答对都不算。
    expect(find.textContaining("已认得 0 / 8（以作答记录为准） · 自测答对 7，待做题确认"), findsOneWidget);
    expect(find.textContaining("答错的："), findsOneWidget, reason: "收尾反馈列出答错的");

    // 没有「再来一轮」，答对的以后不再出现：关掉再打开，第二次自测只考答错过的那 1 张。
    expect(find.textContaining("个没记住的"), findsNothing, reason: "不再有「再来一轮」这个收尾");
    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pump(const Duration(milliseconds: 400));
    await tester.tap(find.text("自测").first);
    await tester.pump();
    expect(find.textContaining("剩 1 张"), findsOneWidget, reason: "第二次只考答错过的，答对的不再出现");
    await answer(tester, remembered: true);

    // 全部只有自测答对、没有作答证明：不再硬出题，说清楚为什么，引导去做题确认，给「重新自测」。
    expect(find.text("这一页没有要再考的了"), findsOneWidget);
    expect(find.textContaining("自测答对 8，待做题确认"), findsOneWidget);
    expect(find.textContaining("作答记录还没证明"), findsOneWidget);
    expect(find.text("重新自测"), findsOneWidget);
    expect(find.textContaining("去做这几个的题"), findsOneWidget);

    // 重新自测：清空本页记录，8 个动作重新排队。
    await tester.tap(find.text("重新自测"));
    await tester.pump();
    expect(find.textContaining("已认得 0 / 8（以作答记录为准）"), findsOneWidget);
    expect(find.textContaining("剩 8 张"), findsOneWidget);
    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pump(const Duration(milliseconds: 400)); // 路由动画走完后还要多走几帧才摘掉对话框

    // 收尾深链：打开再答完一轮，去练这组起练习。
    await tester.tap(find.text("自测").first);
    await tester.pump();
    for (var i = 0; i < 8; i++) {
      await answer(tester, remembered: true);
    }
    await tester.tap(find.textContaining("去做这几个的题"));
    await tester.pump();
    expect(find.byType(SessionStage), findsOneWidget);

    // 自测作答不落库：作答记录与自测之前一致。
    final after = await store.allAttempts();
    expect(after.length, before.length);

    await teardown(tester, store, dir);
  });

  testWidgets("自测：认得以作答记录为准——答对掌握的不出，答错过的一定在第一轮", (tester) async {
    /// 给一个手势动作的相关题都记上同一种作答。
    Future<void> attempt(Bank bank, ProgressStore store, String gestureId, {required bool correct}) async {
      final g = bank.gestureList.firstWhere((x) => x.id == gestureId);
      final byId = {for (final q in bank.questions) q.id: q};
      for (final id in g.questions) {
        final q = byId[id]!;
        await store.recordAttempt(questionId: q.id, topicId: q.topicId, subjectId: "subject1", correct: correct);
      }
    }

    final (bank, store, dir) = await boot(
      tester,
      seed: (bank, store) async {
        await attempt(bank, store, "stop", correct: true);
        await attempt(bank, store, "straight", correct: true);
        await attempt(bank, store, "turn_left", correct: false);
      },
    );
    final wrongName = bank.gestureList.firstWhere((g) => g.id == "turn_left").name;
    final knownNames = {
      for (final id in ["stop", "straight"]) bank.gestureList.firstWhere((g) => g.id == id).name,
    };

    await tester.tap(find.text("手势速记").first);
    await tester.pump();
    await tester.tap(find.text("自测").first);
    await tester.pump();
    // 两个动作的相关题都答对并掌握：作答记录证明认得，8 个里只剩 6 个要考，一轮就是 6 张。
    expect(find.textContaining("已认得 2 / 8（以作答记录为准）"), findsOneWidget);
    expect(find.textContaining("剩 6 张"), findsOneWidget);

    // 一轮 6 张：看一遍抽到了谁。先答对，答后右栏才亮出条目名（22 号字标题）。
    final seen = <String>[];
    for (var i = 0; i < 6; i++) {
      await tester.tap(find.byKey(const ValueKey("recall-correct")));
      await tester.pump();
      final name = tester
          .widgetList<Text>(find.descendant(of: find.byType(RecallSession), matching: find.byType(Text)))
          .firstWhere((t) => t.style?.fontSize == 22 && t.style?.fontWeight == FontWeight.w700)
          .data!;
      seen.add(name);
      await tester.tap(find.textContaining("下一张"));
      await tester.pump();
    }
    expect(seen, contains(wrongName), reason: "作答记录里答错过的一定排在第一轮");
    expect(seen.toSet().intersection(knownNames), isEmpty, reason: "作答记录证明认得的不再出现");
    expect(seen.toSet().length, 6);

    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pump(const Duration(milliseconds: 400)); // 路由动画走完后还要多走几帧才摘掉对话框
    await teardown(tester, store, dir);
  });

  testWidgets("自测：中途退出（按钮或 Esc）不丢已评的，再打开接着考没认得的", (tester) async {
    // 选手势页：8 个动作都有相关题，自评只会得到「自评认得」；标志里有 9 个没有相关题，
    // 只能退回自评直接算认得，随机抽到它们结果会变，不适合做确定性断言。
    final (_, store, dir) = await boot(tester);
    await tester.tap(find.text("手势速记").first);
    await tester.pump();
    await tester.tap(find.text("自测").first);
    await tester.pump();
    expect(find.textContaining("已认得 0 / 8（以作答记录为准）"), findsOneWidget);

    // 一轮 8 张：答对两张，用右上角退出按钮离开。
    await answer(tester, remembered: true);
    await answer(tester, remembered: true);
    expect(find.textContaining("自测答对 2，待做题确认"), findsOneWidget);
    await tester.tap(find.byIcon(Glyph.close));
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pump(const Duration(milliseconds: 400)); // 路由动画走完后还要多走几帧才摘掉对话框
    expect(find.textContaining("想一想"), findsNothing, reason: "退出按钮应关掉自测");

    // 再打开：答对过的 2 张记着，不再出现；再答一张后用 Esc 退出，同样记着。
    await tester.tap(find.text("自测").first);
    await tester.pump();
    expect(find.textContaining("自测答对 2，待做题确认"), findsOneWidget);
    await answer(tester, remembered: true);
    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pump(const Duration(milliseconds: 400)); // 路由动画走完后还要多走几帧才摘掉对话框
    await tester.tap(find.text("自测").first);
    await tester.pump();
    expect(find.textContaining("自测答对 3，待做题确认"), findsOneWidget);
    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pump(const Duration(milliseconds: 400)); // 路由动画走完后还要多走几帧才摘掉对话框
    await teardown(tester, store, dir);
  });

  testWidgets("自测：解释在选项右侧，答对自动切下一张，答错留在解释上，「下一张」在底部中间（ADR 0089）", (tester) async {
    final (_, store, dir) = await boot(tester);
    await tester.tap(find.text("标线速记").first);
    await tester.pump();
    await tester.tap(find.text("自测").first);
    await tester.pump();
    final total = remaining();
    expect(total, greaterThan(10), reason: "标线 33 条都没认得，就排 33 张，没有「一轮 10 张」的上限");

    // 版面：选项在左，解释在右（未作答时右栏是一句提示），选项不再拉满整行。
    final option = find.byKey(const ValueKey("recall-correct"));
    final hint = find.text("选一个答案，这里给出解释。");
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

    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pump(const Duration(milliseconds: 400)); // 路由动画走完后还要多走几帧才摘掉对话框
    await teardown(tester, store, dir);
  });

  testWidgets("自测：侧栏里全部 8 个速记页都有入口，都把没认得的卡逐张排出来", (tester) async {
    final (_, store, dir) = await boot(tester);
    for (final page in ["易混数字", "标志速记", "标线速记", "仪表速记", "手势速记", "考点速记", "河南速记", "记分证照速记"]) {
      await tester.tap(find.text(page).first);
      await tester.pump();
      expect(find.text("自测"), findsOneWidget, reason: "$page 缺自测入口");
      await tester.tap(find.text("自测"));
      await tester.pump();
      // 没有张数上限：剩余张数写在卡片头里；手势页 8 个动作，其余页都不少于 8 条。
      expect(remaining(), greaterThanOrEqualTo(8), reason: "$page 应把没认得的卡都排出来");
      await tester.sendKeyEvent(LogicalKeyboardKey.escape);
      await tester.pump();
    }
    await teardown(tester, store, dir);
  });

  testWidgets("自测：易混数字与考点速记也有，文字卡正面是情形、选项是数字或单条要点", (tester) async {
    final (_, store, dir) = await boot(tester);

    // 易混数字：情形 → 数字四选一。
    await tester.tap(find.text("易混数字").first);
    await tester.pump();
    await tester.tap(find.text("自测").first);
    await tester.pump();
    expect(find.textContaining("括号里该填什么"), findsOneWidget);
    expect(find.byKey(const ValueKey("recall-correct")), findsOneWidget, reason: "出的是四选一");
    expect(wrongOptions(), findsNWidgets(3));
    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pump(const Duration(milliseconds: 400)); // 路由动画走完后还要多走几帧才摘掉对话框
    expect(find.text("自测").evaluate().length, 1, reason: "Esc 关掉卡片，只剩页面上的按钮");

    // 考点速记：情景 → 要点四选一，答后显示完整要点列表。
    await tester.tap(find.text("考点速记").first);
    await tester.pump();
    await tester.tap(find.text("自测").first);
    await tester.pump();
    expect(find.textContaining("碰到这个情景该怎么做"), findsOneWidget);
    expect(find.byKey(const ValueKey("recall-correct")), findsOneWidget, reason: "出的是四选一");
    await tester.tap(find.byKey(const ValueKey("recall-correct")));
    await tester.pump();
    expect(find.text("要点"), findsOneWidget, reason: "答后显示完整要点");
    expect(find.textContaining("答对了"), findsOneWidget, reason: "对错当场判定");

    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pump(const Duration(milliseconds: 400)); // 路由动画走完后还要多走几帧才摘掉对话框
    await teardown(tester, store, dir);
  });
}
