import "dart:io";

import "package:athena_driver/exam.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/progress.dart";
import "package:athena_driver/session.dart";
import "package:flutter/material.dart";
import "package:flutter/services.dart";
import "package:flutter_test/flutter_test.dart";

Question _judge(int i) => Question(
      id: "q$i",
      topicId: "drive.s1.license",
      kind: "judge",
      prompt: "第 $i 句",
      choices: const [
        Choice(id: "T", label: "正确", ok: true),
        Choice(id: "F", label: "错误", ok: false),
      ],
      explain: "",
      sourceRefs: const [],
    );

void main() {
  // 模拟考按考场走（ADR 0023）：答一题交一题，交了不能改，错到第 11 道当场结束。
  testWidgets("模拟考答错第 11 道就结束，判不合格，没答的题不写作答记录", (tester) async {
    late Directory dir;
    late ProgressStore store;
    await tester.runAsync(() async {
      dir = await Directory.systemTemp.createTemp("athena-driver-session-");
      store = await ProgressStore.open(path: "${dir.path}/learning.db");
    });
    await tester.binding.setSurfaceSize(const Size(1600, 1000));
    final questions = [for (var i = 0; i < 100; i++) _judge(i)];
    const rules = ExamRules(questionCount: 100, minutes: 45, passScore: 90, pointsPerQuestion: 1);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SessionStage(
            launch: SessionLaunch(
              title: "科目一 模拟考试",
              subjectId: "subject1",
              questions: questions,
              timed: true,
              minutes: 45,
              revealImmediately: false,
              paper: Paper(questions: questions, rules: rules, fullBank: true),
            ),
            store: store,
            onClose: () {},
          ),
        ),
      ),
    );

    // 键盘 T/F 落在第一道还没交的题上；每交一题要等作答记录落盘。
    Future<void> answer(LogicalKeyboardKey key) async {
      await tester.sendKeyEvent(key);
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 30)));
      await tester.pump();
    }

    for (var i = 0; i < 5; i++) {
      await answer(LogicalKeyboardKey.keyT);
    }
    // 答对不提示：选项上不出现对勾。
    expect(find.byIcon(Icons.check_circle), findsNothing);
    for (var i = 0; i < 5; i++) {
      await answer(LogicalKeyboardKey.keyF);
    }
    // 本页最后一题答错：停在本页看正确答案，不自动翻；回车翻到下一组。
    expect(find.text("第11题"), findsNothing);
    await answer(LogicalKeyboardKey.enter);
    expect(find.text("第11题"), findsOneWidget);
    for (var i = 0; i < 5; i++) {
      await answer(LogicalKeyboardKey.keyF);
    }
    expect(find.text("考试结束"), findsNothing);
    expect(find.text("错 10 题（错到 11 题结束）"), findsOneWidget);
    await answer(LogicalKeyboardKey.keyF);
    await tester.pumpAndSettle();
    expect(find.text("考试结束"), findsOneWidget);

    await tester.tap(find.text("看结果"));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 100)));
    await tester.pumpAndSettle();
    expect(find.text("未及格"), findsOneWidget);
    expect(find.textContaining("提前结束"), findsOneWidget);
    expect(find.text("还有 84 题没答，按错计分。"), findsOneWidget);

    await tester.runAsync(() async {
      // 只交了 16 题，就只有 16 条作答记录；没见过的 84 题不算「答错」。
      // 新库会拿仓库里的进度库当底子，只数这场造的题。
      bool ours(String id) => RegExp(r"^q\d+$").hasMatch(id);
      expect((await store.wrongQuestionIds()).where(ours), hasLength(11));
      expect((await store.masteredQuestionIds()).where(ours), hasLength(5));
    });
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
