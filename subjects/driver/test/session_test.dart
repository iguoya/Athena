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
  // 模拟考答一题交一题，交了不能改（ADR 0023）；错到不可能及格也不提前结束（ADR 0041）。
  testWidgets("模拟考错到不可能及格也继续答，交卷判不合格，没答的题不写作答记录", (tester) async {
    late Directory dir;
    late ProgressStore store;
    await tester.runAsync(() async {
      dir = await Directory.systemTemp.createTemp("athena-driver-session-");
      store = await ProgressStore.open(suite: "session_test");
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

    // 每道题都带稳定编号（合成题的 id 就是编号本身）。
    expect(find.text("q0"), findsWidgets);
    for (var i = 0; i < 5; i++) {
      await answer(LogicalKeyboardKey.keyT);
    }
    // 答对不提示：选项上不出现对勾。
    expect(find.byIcon(Icons.check_circle), findsNothing);
    for (var i = 0; i < 5; i++) {
      await answer(LogicalKeyboardKey.keyF);
    }
    // 一页十题答完就翻（ADR 0025），但至少停 5 秒看清正确答案（ADR 0038）。
    expect(find.text("第11题"), findsNothing);
    await tester.pump(const Duration(milliseconds: 4500));
    expect(find.text("第11题"), findsNothing);
    await tester.pump(const Duration(milliseconds: 600));
    expect(find.text("第11题"), findsOneWidget);
    for (var i = 0; i < 5; i++) {
      await answer(LogicalKeyboardKey.keyF);
    }
    expect(find.text("错 10 题（错到 11 题不及格）"), findsOneWidget);
    // 错到第 11 道已不可能及格，但不提前结束，照样往下答（ADR 0041）。
    await answer(LogicalKeyboardKey.keyF);
    await tester.pumpAndSettle();
    expect(find.text("考试结束"), findsNothing);
    expect(find.text("错 11 题（已不及格，继续答完）"), findsOneWidget);
    await answer(LogicalKeyboardKey.keyT);

    // 过了 45 分钟也不收卷，还停在答题页（ADR 0042）。
    await tester.pump(const Duration(minutes: 46));
    expect(find.text("未及格"), findsNothing);
    expect(find.text("交卷"), findsOneWidget);

    // 自己交卷。出结果前要走 recordExam 真实写库；同上，等到结果页真的出来，不赌固定时长——
    // Windows runner 上 100ms 经常不够。
    await tester.tap(find.text("交卷"));
    await tester.pumpAndSettle();
    await tester.tap(find.text("确定交卷"));
    for (var i = 0; i < 200 && find.text("未及格").evaluate().isEmpty; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    await tester.pumpAndSettle();
    expect(find.text("未及格"), findsOneWidget);
    expect(find.textContaining("提前结束"), findsNothing);
    expect(find.text("还有 83 题没答，按错计分。"), findsOneWidget);

    await tester.runAsync(() async {
      // 只交了 17 题，就只有 17 条作答记录；没见过的 83 题不算「答错」。
      // 新库会拿仓库里的进度库当底子，只数这场造的题。
      bool ours(String id) => RegExp(r"^q\d+$").hasMatch(id);
      expect((await store.wrongQuestionIds()).where(ours), hasLength(11));
      expect((await store.masteredQuestionIds()).where(ours), hasLength(6));
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
      store = await ProgressStore.open(suite: "session_test");
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
      // 草稿是交题时顺手存的、不被等待；轮询到它写全再查，不赌固定时长。
      for (var i = 0; i < 200; i++) {
        final draft = await store.loadExamDraft("subject1.exit-test");
        if (draft != null && draft.picked.length == 3) break;
        await Future<void>.delayed(const Duration(milliseconds: 10));
      }
      bool ours(String id) => RegExp(r"^q\d+$").hasMatch(id);
      final counts = await store.attemptCounts();
      expect(counts.keys.where(ours).toSet(), {"q0", "q1", "q2"});
      expect((await store.masteredQuestionIds()).where(ours), hasLength(2));
      expect((await store.wrongQuestionIds()).where(ours), ["q2"]);
      expect((await store.recentExams(subjectId: "subject1", limit: 1000)).length, examsBefore);
      final draft = await store.loadExamDraft("subject1.exit-test");
      expect(draft?.picked.keys.toSet(), {0, 1, 2});
      // 续答时用时只算到最后一次存草稿（ADR 0043）：saved_at 要存下来。
      expect(draft?.savedAt, isNotNull);
      expect(draft!.spent, greaterThanOrEqualTo(Duration.zero));
    });
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });

  // 模拟考答错当场讲：右栏答题卡下面出依据，题干旁有「解析」；答对仍不提示（ADR 0052）。
  testWidgets("模拟考答错在右栏讲为什么错，答对不讲", (tester) async {
    late Directory dir;
    late ProgressStore store;
    await tester.runAsync(() async {
      dir = await Directory.systemTemp.createTemp("athena-driver-exam-explain-");
      store = await ProgressStore.open(suite: "session_test");
    });
    await tester.binding.setSurfaceSize(const Size(1600, 1000));
    final questions = [
      for (var i = 0; i < 100; i++)
        Question(
          id: "q$i",
          topicId: "drive.s1.license",
          kind: "judge",
          prompt: "第 $i 句",
          choices: const [
            Choice(id: "T", label: "正确", ok: true),
            Choice(id: "F", label: "错误", ok: false),
          ],
          explain: "第 $i 句为什么对",
          sourceRefs: const [],
        ),
    ];
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

    expect(find.text("简短解释"), findsNothing);
    await answer(LogicalKeyboardKey.keyT);
    // 答对：不讲，也没有「解析」可点。
    expect(find.text("简短解释"), findsNothing);
    expect(find.text("第 0 句为什么对"), findsNothing);
    await answer(LogicalKeyboardKey.keyF);
    // 答错：右栏讲这一题，可以手动再听。
    expect(find.text("简短解释"), findsOneWidget);
    expect(find.text("第 1 句为什么对"), findsOneWidget);
    expect(find.text("答错"), findsOneWidget);
    expect(find.text("系统朗读"), findsOneWidget);
    expect(find.text("答题卡"), findsOneWidget);
    // 接着答对下一题，右栏回到只有答题卡；答错那题的「解析」能把依据调回来。
    await answer(LogicalKeyboardKey.keyT);
    expect(find.text("简短解释"), findsNothing);
    // 没讲的题「解析」按钮只是藏着（保留占位、不可点），可点的只有答错那题的；
    // 答下一题时页面已经把下一道滚到正中，先滚回来再点。
    final explain = find.ancestor(
      of: find.text("解析"),
      matching: find.byWidgetPredicate((w) => w is ButtonStyleButton && w.enabled),
    );
    expect(explain, findsOneWidget);
    await tester.ensureVisible(explain);
    await tester.pumpAndSettle();
    await tester.tap(explain);
    await tester.pump();
    expect(find.text("第 1 句为什么对"), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });

  // 一页答完自动翻：最后一题答对只停 1 秒（ADR 0053）；答错至少停 5 秒，看清正确答案和解释（ADR 0038）。
  Future<void> pageTurn(WidgetTester tester, {required bool lastCorrect, required int waitMs, required int turnMs}) async {
    late Directory dir;
    late ProgressStore store;
    await tester.runAsync(() async {
      dir = await Directory.systemTemp.createTemp("athena-driver-dwell-");
      store = await ProgressStore.open(suite: "session_test");
    });
    await tester.binding.setSurfaceSize(const Size(1600, 1000));
    final questions = [for (var i = 0; i < 20; i++) _judge(i)];
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SessionStage(
            launch: SessionLaunch(
              title: "科目一 · 练习",
              subjectId: "subject1",
              questions: questions,
              timed: false,
              revealImmediately: true,
            ),
            store: store,
            onClose: () {},
          ),
        ),
      ),
    );
    for (var n = 1; n <= 10; n++) {
      final key = n == 10 && !lastCorrect ? LogicalKeyboardKey.keyF : LogicalKeyboardKey.keyT;
      await tester.sendKeyEvent(key);
      for (var i = 0; i < 200 && find.textContaining("已答 $n").evaluate().isEmpty; i++) {
        await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
        await tester.pump();
      }
    }
    expect(find.text("第11题"), findsNothing);
    await tester.pump(Duration(milliseconds: waitMs));
    expect(find.text("第11题"), findsNothing);
    await tester.pump(Duration(milliseconds: turnMs));
    await tester.pump();
    expect(find.text("第11题"), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  }

  testWidgets("练习一页答完、最后一题答对，1 秒就翻页", (tester) async {
    await pageTurn(tester, lastCorrect: true, waitMs: 600, turnMs: 600);
  });

  testWidgets("练习一页答完、最后一题答错，至少停 5 秒再翻页", (tester) async {
    await pageTurn(tester, lastCorrect: false, waitMs: 4500, turnMs: 600);
  });
}
