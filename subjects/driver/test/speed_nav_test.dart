import "dart:async";
import "dart:io";

import "package:athena_driver/core/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/ui/look.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:athena_driver/speed/recall_cards.dart";
import "package:athena_driver/speed/speed_topics.dart";
import "package:flutter/material.dart";
import "package:flutter/services.dart";
import "package:flutter_test/flutter_test.dart";

import "nav_helpers.dart";

/// 侧栏专题分组折叠与状态圆、速记组「练这组」按钮的三色（ADR 0109）。
void main() {
  Future<(Bank, ProgressStore, Directory)> boot(WidgetTester tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-speednav-");
      store = await ProgressStore.open(suite: "speed_nav_test");
    });
    await tester.binding.setSurfaceSize(const Size(1600, 2600));
    final ready = Completer<void>();
    await tester.pumpWidget(MaterialApp(home: HomePage(bank: bank, store: store, onReady: ready.complete)));
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
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

  test("每个专题都归到一个分组，科目一的分组不为空", () {
    for (final topic in speedTopics) {
      expect(speedGroups.map((g) => g.id), contains(speedGroupIdOf(topic)), reason: topic.id);
    }
    final groups = speedTopicGroupsOf("subject1");
    expect(groups.expand((g) => g.topics).length, speedTopicsOf("subject1").length);
  });

  testWidgets("专题默认折叠在分组下，点分组展开，点专题时它所在的组自动展开", (tester) async {
    final (_, store, dir) = await boot(tester);
    expect(find.text("易混数字"), findsNothing, reason: "默认折叠");
    expect(find.textContaining("速记对照 · "), findsOneWidget);
    await tester.tap(find.textContaining("速记对照 · "));
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.text("易混数字"), findsOneWidget);
    await tester.tap(find.textContaining("速记对照 · "));
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.text("易混数字"), findsNothing, reason: "再点收起");
    await teardown(tester, store, dir);
  });

  testWidgets("专题与分组左边的状态圆：没测完灰、答错红、只答对一张仍是灰", (tester) async {
    final (_, store, dir) = await boot(tester);
    const gray = "这个专题还没测完";
    const red = "这个专题的自测题最近答错过，还没掌握";
    const green = "这个专题的自测题全部答对过";

    Future<void> reload() async {
      await tester.pump(const Duration(milliseconds: 1000));
      for (var i = 0; i < 100; i++) {
        await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
        await tester.pump();
      }
    }

    Future<void> closeDialog() async {
      await tester.sendKeyEvent(LogicalKeyboardKey.escape);
      await tester.pump(const Duration(milliseconds: 400));
      await tester.pump(const Duration(milliseconds: 400));
    }

    Future<void> openRecall(String page) async {
      await showTopic(tester, page);
      await tester.tap(find.text(page).first);
      await tester.pump();
      await tester.tap(find.text("自测").first);
      await tester.pump();
    }

    await showTopic(tester, "手势速记");
    expect(find.byTooltip(gray), findsWidgets);
    expect(find.byTooltip(red), findsNothing);
    expect(find.byTooltip(green), findsNothing);

    // 手势自测答错一张：专题和它所在的分组都变红。
    await openRecall("手势速记");
    await tester.tap(
      find
          .byWidgetPredicate((w) => w.key is ValueKey<String> && (w.key! as ValueKey<String>).value.startsWith("recall-option-"))
          .first,
    );
    await tester.pump();
    await closeDialog();
    await reload();
    expect(find.byTooltip(red), findsWidgets, reason: "答错过的专题与分组变红");

    // 标志自测答对一张：标志专题还没测完，仍是灰。
    await openRecall("标志速记");
    await tester.tap(find.byKey(const ValueKey("recall-correct")));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 1000));
    await closeDialog();
    await reload();
    // 只答对一张不算测完（ADR 0113）：标志专题仍是灰，不能写「已掌握」。
    expect(find.byTooltip(green), findsNothing, reason: "只测了一部分：不变绿");
    await teardown(tester, store, dir);
  });

  testWidgets("速记组「练这组」按钮（跟自测卡走）：没做过灰、有答错红（全部掌握为绿，见 statusOf）", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-speednav2-");
      store = await ProgressStore.open(suite: "speed_nav_btn_test");
      // 只有「禁止驶入」这张自测卡答错一次（相关真题一道没碰）：按钮也跟自测卡走，禁令组变红（ADR 0110）。
      await store.recordAttempt(
        questionId: recallQuestionId("s1.signs", "no_entry"),
        topicId: "${recallTopicPrefix}s1.signs",
        subjectId: "subject1",
        correct: false,
        kind: "recall",
      );
    });
    await tester.binding.setSurfaceSize(const Size(1600, 2600));
    final ready = Completer<void>();
    await tester.pumpWidget(MaterialApp(home: HomePage(bank: bank, store: store, onReady: ready.complete)));
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    await showTopic(tester, "标志速记");
    await tester.tap(find.text("标志速记").first);
    await tester.pump();
    Color? colorOf(Finder button) =>
        (tester.widget<FilledButton>(button).style?.backgroundColor)?.resolve(<WidgetState>{});
    final buttons = find.ancestor(of: find.textContaining("练这组"), matching: find.bySubtype<FilledButton>());
    expect(buttons.evaluate().length, greaterThan(1));
    // 禁令组（第一组）有答错：红；其余组没做过：灰。
    expect(colorOf(buttons.first), Bs.danger, reason: "禁令组的自测卡答错 → 红");
    expect(colorOf(buttons.at(1)), const Color(0xFF8A939B), reason: "警告组没做过 → 灰");
    await tester.pump(const Duration(seconds: 30));
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
