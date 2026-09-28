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
    // 不按固定时长等：机器忙时写库慢，等到「已答」计数真的变了再往下走。
    var answered = 0;
    Future<void> answer(LogicalKeyboardKey key) async {
      await tester.sendKeyEvent(key);
      answered++;
      for (var i = 0; i < 200 && find.textContaining("已答 $answered / 100").evaluate().isEmpty; i++) {
        await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
        await tester.pump();
      }
      expect(find.textContaining("已答 $answered / 100"), findsOneWidget);
    }

    for (var i = 0; i < 5; i++) {
      await answer(LogicalKeyboardKey.keyT);
    }
    // 答对不提示：选项上不出现对勾。
    expect(find.byIcon(Icons.check_circle), findsNothing);
    for (var i = 0; i < 5; i++) {
      await answer(LogicalKeyboardKey.keyF);
    }
    // 一页十题答完就翻（ADR 0025）：最后一题答错，先停 2.5 秒看清正确答案。
    expect(find.text("第11题"), findsNothing);
    await tester.pump(const Duration(milliseconds: 2000));
    expect(find.text("第11题"), findsNothing);
    await tester.pump(const Duration(milliseconds: 600));
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
  // 中途退出不交卷：答过的题交的时候已经落盘，退出不丢；这一卷不出分、不记一次考试，草稿留着续答。
  testWidgets("模拟考中途退出，答过的题照样记进作答记录，不记考试成绩", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late int examsBefore;
    await tester.runAsync(() async {
      dir = await Directory.systemTemp.createTemp("athena-driver-exit-");
      store = await ProgressStore.open(path: "${dir.path}/learning.db");
      examsBefore = (await store.recentExams(subjectId: "subject1", limit: 1000)).length;
    });
    await tester.binding.setSurfaceSize(const Size(1600, 1000));
    final questions = [for (var i = 0; i < 100; i++) _judge(i)];
    const rules = ExamRules(questionCount: 100, minutes: 45, passScore: 90, pointsPerQuestion: 1);
    var closed = false;
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
              draftKey: "subject1.exit-test",
            ),
            store: store,
            onClose: () => closed = true,
          ),
        ),
      ),
    );

    var answered = 0;
    Future<void> answer(LogicalKeyboardKey key) async {
      await tester.sendKeyEvent(key);
      answered++;
      for (var i = 0; i < 200 && find.textContaining("已答 $answered / 100").evaluate().isEmpty; i++) {
        await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
        await tester.pump();
      }
      expect(find.textContaining("已答 $answered / 100"), findsOneWidget);
    }

    await answer(LogicalKeyboardKey.keyT);
    await answer(LogicalKeyboardKey.keyT);
    await answer(LogicalKeyboardKey.keyF);

    await tester.tap(find.byTooltip("退出，不交卷"));
    await tester.pumpAndSettle();
    expect(find.textContaining("答过的 3 题已经记进作答记录"), findsOneWidget);
    await tester.tap(find.text("退出"));
    await tester.pumpAndSettle();
    expect(closed, isTrue);

    await tester.runAsync(() async {
      // 草稿是交题时顺手存的，等它写完再查。
      await Future<void>.delayed(const Duration(milliseconds: 100));
      bool ours(String id) => RegExp(r"^q\d+$").hasMatch(id);
      final counts = await store.attemptCounts();
      expect(counts.keys.where(ours).toSet(), {"q0", "q1", "q2"});
      expect((await store.masteredQuestionIds()).where(ours), hasLength(2));
      expect((await store.wrongQuestionIds()).where(ours), ["q2"]);
      expect((await store.recentExams(subjectId: "subject1", limit: 1000)).length, examsBefore);
      final draft = await store.loadExamDraft("subject1.exit-test");
      expect(draft?.picked.keys.toSet(), {0, 1, 2});
    });
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
