import "dart:io";

import "package:athena_driver/core/content.dart";
import "package:athena_driver/core/progress.dart";
import "package:athena_driver/subject2/brief.dart";
import "package:athena_driver/subject2/guide.dart";
import "package:athena_driver/subject2/rehearsal.dart";
import "package:athena_driver/subject2/review.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  late Directory dir;
  late ProgressStore store;
  late Subject2Guide guide;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp("athena-driver-time-");
    store = await ProgressStore.open(suite: "drill_time_test");
  });

  setUpAll(() async {
    guide = (await ContentLoader.load()).guide;
  });

  tearDown(() async {
    await store.close();
    if (dir.existsSync()) await dir.delete(recursive: true);
  });

  group("练车用时", () {
    test("用时写进练车记录但不进同步队列；拉回同一把不冲掉本地用时", () async {
      final at = DateTime.utc(2026, 10, 22, 1, 2, 3);
      await store.recordDrillRun("reverse", const [], at: at, seconds: 205);
      await store.recordDrillRun("reverse", const [], at: at.add(const Duration(milliseconds: 1)), seconds: 250);

      final runs = await store.drillRuns();
      expect(runs[0].seconds, 250);
      expect(runs[1].seconds, 205);

      final queued = store.outboxBatch("drill-runs");
      for (final entry in queued) {
        expect(entry.payload.containsKey("seconds"), isFalse);
      }

      store.applyRemote("drill-runs", [
        {"item_id": "reverse", "mistakes": "", "at": at.toIso8601String()},
      ]);
      final again = await store.drillRuns();
      expect(again.last.seconds, 205);
    });

    test("简报汇总窗口里填了用时的把，新的在前；没填的把不算", () {
      final at = DateTime(2026, 9, 28, 20);
      final brief = buildBrief(guide, [
        DrillRun(itemId: "reverse", mistakes: const [], at: at, seconds: 190),
        DrillRun(itemId: "reverse", mistakes: const [], at: at.subtract(const Duration(minutes: 5))),
        DrillRun(itemId: "reverse", mistakes: const [], at: at.subtract(const Duration(minutes: 10)), seconds: 240),
      ]);
      expect(brief.item("reverse")!.times, [190, 240]);
    });
  });

  group("复盘录入页", () {
    testWidgets("填了超时限的用时提示超时与条款，没超不提示；保存后用时进库", (tester) async {
      await tester.pumpWidget(MaterialApp(home: DayReview(guide: guide, store: store)));
      await tester.pumpAndSettle();

      await tester.tap(find.text("倒车入库"));
      await tester.pumpAndSettle();

      final box = find.byKey(const ValueKey("review-seconds-reverse-0"));
      expect(box, findsOneWidget);

      // 3.5 分钟 = 210 秒；250 超时、200 不超。
      await tester.enterText(box, "250");
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey("review-overtime-reverse-0")), findsOneWidget);
      expect(find.textContaining("6.2.3.1 d)"), findsOneWidget);

      await tester.enterText(box, "200");
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey("review-overtime-reverse-0")), findsNothing);

      await tester.tap(find.text("保存今天 3 把"));
      await tester.pumpAndSettle();

      final runs = await store.drillRuns();
      expect(runs.where((r) => r.seconds == 200), hasLength(1));
    });

    testWidgets("没有时限的项不判超时", (tester) async {
      await tester.pumpWidget(MaterialApp(home: DayReview(guide: guide, store: store)));
      await tester.pumpAndSettle();

      await tester.tap(find.text("曲线行驶"));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(const ValueKey("review-seconds-curve-0")), "999");
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey("review-overtime-curve-0")), findsNothing);
    });
  });

  group("默演计时器", () {
    testWidgets("可选开；开着只计时，做完停在总用时", (tester) async {
      await tester.binding.setSurfaceSize(const Size(1600, 2600));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RehearsalView(
              item: guide.item("curve")!,
              store: store,
              notes: const {},
              photos: const [],
              onChanged: () async {},
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      final timer = find.byKey(const ValueKey("rehearsal-timer"));
      expect(timer, findsOneWidget);
      expect(find.text("计时"), findsOneWidget);

      await tester.tap(timer);
      await tester.pump();
      expect(find.text("0:00"), findsOneWidget);
      await tester.pump(const Duration(seconds: 2));
      expect(find.text("0:02"), findsOneWidget);

      // 停表后读数留在原地，再点是从头计。
      await tester.tap(timer);
      await tester.pump();
      expect(find.textContaining("0:02"), findsOneWidget);

      await tester.tap(timer);
      await tester.pump();
      expect(find.text("0:00"), findsOneWidget);

      final item = guide.item("curve")!;
      for (var i = 0; i < item.steps.length; i++) {
        await tester.tap(find.text("说完了，对照"));
        await tester.pumpAndSettle();
        await tester.tap(find.text("对上了"));
        await tester.pumpAndSettle();
      }
      expect(find.textContaining("本次默演用时"), findsOneWidget);
      expect(find.textContaining("本次默演用时 0:"), findsOneWidget);
    });
  });
}
