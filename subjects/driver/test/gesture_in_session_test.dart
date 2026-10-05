import "dart:io";

import "package:athena_driver/cheat_image.dart";
import "package:athena_driver/content.dart";
import "package:athena_driver/gesture_animation.dart";
import "package:athena_driver/gesture_index.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:athena_driver/session.dart";
import "package:flutter/material.dart";
import "package:flutter/services.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  // ADR 0078：手势题答完，右栏放这个动作的完整动画；非手势题没有。
  test("反向索引：29 道手势题里有动画的动作都能查到，非手势题查不到", () async {
    final bank = await ContentLoader.load();
    var animated = 0;
    for (final g in bank.gestureList) {
      for (final id in g.questions) {
        final hit = GestureIndex.of(id);
        expect(hit, isNotNull, reason: "$id 查不到手势动作");
        expect(hit!.$1, g.id);
        if (gestureClips.containsKey(g.id)) animated++;
      }
    }
    expect(animated, 26, reason: "29 道手势题里，除 3 道手势效力题外都有动画");
    expect(GestureIndex.of("drive.s1.license.001"), isNull);
  });

  testWidgets("答完手势题，右栏出现该动作的动画；答完非手势题没有", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-gesture-session-");
      store = await ProgressStore.open(suite: "gesture_in_session_test");
    });
    await tester.binding.setSurfaceSize(const Size(1600, 1000));
    final byId = {for (final q in bank.questions) q.id: q};
    final gestureQuestion = byId["drive.s1.signals.339"]!; // 左转弯信号
    final plainQuestion = byId["drive.s1.license.001"]!;
    for (final (question, expectAnimation) in [(gestureQuestion, true), (plainQuestion, false)]) {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SessionStage(
              launch: SessionLaunch(
                title: "测试",
                subjectId: "subject1",
                questions: [question],
                timed: false,
                revealImmediately: true,
              ),
              store: store,
              onClose: () {},
            ),
          ),
        ),
      );
      await tester.pump(const Duration(milliseconds: 500));
      // 故意答错（解析一定会出现）：单选按 A、B、C、D，判断题按 T、F。
      final wrong = question.choices.indexWhere((c) => !c.ok);
      final key = question.kind == "judge"
          ? (question.choices[wrong].id == "T" ? LogicalKeyboardKey.keyT : LogicalKeyboardKey.keyF)
          : [LogicalKeyboardKey.keyA, LogicalKeyboardKey.keyB, LogicalKeyboardKey.keyC, LogicalKeyboardKey.keyD][wrong];
      await tester.sendKeyEvent(key);
      for (var i = 0; i < 200 && find.textContaining("简短解释").evaluate().isEmpty; i++) {
        await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
        await tester.pump();
      }
      expect(find.textContaining("简短解释"), findsOneWidget, reason: "答错后右栏没出解析");
      expect(tester.takeException(), isNull);
      // 规范 GIF（ADR 0080）：用 CheatImage 放；非手势题右栏没有它。
      expect(find.byType(CheatImage), expectAnimation ? findsOneWidget : findsNothing);
      await tester.pumpWidget(const SizedBox());
    }
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
