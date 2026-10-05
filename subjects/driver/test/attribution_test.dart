import "dart:io";

import "package:athena_driver/study/exam.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:athena_driver/study/session.dart";
import "package:flutter/material.dart";
import "package:flutter/services.dart";
import "package:flutter_test/flutter_test.dart";
import "package:sqlite3/sqlite3.dart" as sqlite;

/// 主仓库 ADR 0076 阶段 1：作答与考试的归因字段（所选选项、会话、选题理由）和答错后看解析的停留。

Question _judge(int i) => Question(
      id: "q$i",
      topicId: "drive.s1.license",
      kind: "judge",
      prompt: "第 $i 句",
      choices: const [
        Choice(id: "T", label: "正确", ok: true),
        Choice(id: "F", label: "错误", ok: false),
      ],
      explain: "解析 $i",
      sourceRefs: const [],
    );

final _multi = Question(
  id: "m1",
  topicId: "drive.s4.crash",
  kind: "multi",
  prompt: "多选题",
  choices: const [
    Choice(id: "A", label: "甲", ok: true),
    Choice(id: "B", label: "乙", ok: false),
    Choice(id: "C", label: "丙", ok: true),
    Choice(id: "D", label: "丁", ok: false),
  ],
  explain: "",
  sourceRefs: const [],
);

void main() {
  group("存储层", () {
    test("作答带归因字段：存本地、进队列；不带的不进载荷", () async {
      final store = await ProgressStore.open(suite: "attribution_a");
      addTearDown(store.close);
      await store.recordAttempt(
        questionId: "q1", topicId: "t", subjectId: "reinforce", correct: false, kind: "reinforce",
        chosen: "A,C", sessionId: "sess1", reason: "retest", at: DateTime(2026, 10, 3, 9),
      );
      await store.recordAttempt(
        questionId: "q2", topicId: "t", subjectId: "subject1", correct: true, at: DateTime(2026, 10, 3, 9, 1),
      );
      final rows = store.debugAttempts();
      expect((rows[0]["chosen"], rows[0]["session_id"], rows[0]["reason"]), ("A,C", "sess1", "retest"));
      expect((rows[1]["chosen"], rows[1]["session_id"], rows[1]["reason"]), (null, null, null));
      final batch = store.outboxBatch("attempts");
      expect(batch[0].payload["chosen"], "A,C");
      expect(batch[0].payload["reason"], "retest");
      for (final key in ["chosen", "session_id", "reason"]) {
        expect(batch[1].payload.containsKey(key), isFalse, reason: "$key 没有就不带，服务端存为空");
      }
    });

    test("考试带会话与用时", () async {
      final store = await ProgressStore.open(suite: "attribution_b");
      addTearDown(store.close);
      await store.recordExam(subjectId: "subject1", score: 92, passed: true, sessionId: "sess1", usedMs: 1800000);
      final row = store.debugExams().single;
      expect((row["session_id"], row["used_ms"]), ("sess1", 1800000));
      expect(store.outboxBatch("exams").single.payload["used_ms"], 1800000);
      await store.recordExam(subjectId: "subject4", score: 80, passed: false, at: DateTime(2026, 10, 3, 10));
      expect(store.outboxBatch("exams").last.payload.containsKey("session_id"), isFalse);
    });

    test("解析停留：本地去重、封顶 5 分钟、进队列", () async {
      final store = await ProgressStore.open(suite: "attribution_c");
      addTearDown(store.close);
      await store.recordExplainView(questionId: "q1", attemptAt: "2026-10-03T09:00:00.000", dwellMs: 6200);
      await store.recordExplainView(questionId: "q1", attemptAt: "2026-10-03T09:00:00.000", dwellMs: 9999);
      await store.recordExplainView(questionId: "q2", attemptAt: "2026-10-03T09:01:00.000", dwellMs: 99999999);
      final rows = store.debugExplainViews();
      expect(rows, hasLength(2), reason: "同一次作答只留一条");
      expect(rows.map((r) => r["dwell_ms"]), [6200, 300000]);
      expect(store.outboxBatch("explain-views"), hasLength(3), reason: "队列照发，服务端按去重键跳过重复");
    });

    test("草稿带会话：存取一致，覆盖保存也不丢", () async {
      final store = await ProgressStore.open(suite: "attribution_d");
      addTearDown(store.close);
      ExamDraft draft(String? session) => ExamDraft(
            subjectId: "subject1", title: "模拟考", questionIds: const ["a", "b"], questionCount: 2, minutes: 45,
            passScore: 90, pointsPerQuestion: 1, mix: const {}, fullBank: true, picked: const {0: {"T"}},
            startedAt: DateTime(2026, 10, 3, 9), sessionId: session,
          );
      await store.saveExamDraft(draft("sessX"), draftKey: "subject1.exam");
      expect((await store.loadExamDraft("subject1.exam"))!.sessionId, "sessX");
      await store.saveExamDraft(draft("sessX"), draftKey: "subject1.exam");
      expect((await store.loadExamDraft("subject1.exam"))!.sessionId, "sessX");
      await store.saveExamDraft(draft(null), draftKey: "subject1.exam");
      expect((await store.loadExamDraft("subject1.exam"))!.sessionId, isNull, reason: "老草稿没有会话，读出来是空");
      expect(store.outboxBatch("exam-draft").last.payload["session_id"], isNull);
    });

    test("老库升级：自动补列和新表，老行为空、新写入可用", () async {
      final dir = await Directory.systemTemp.createTemp("athena-attribution-old-");
      addTearDown(() => dir.delete(recursive: true));
      final path = "${dir.path}${Platform.pathSeparator}local.db";
      final old = sqlite.sqlite3.open(path);
      old.execute("CREATE TABLE attempts (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id TEXT NOT NULL, topic_id TEXT NOT NULL, "
          "subject_id TEXT NOT NULL, correct INTEGER NOT NULL, duration_ms INTEGER NOT NULL DEFAULT 0, hesitant INTEGER NOT NULL DEFAULT 0, "
          "at TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'practice')");
      old.execute("CREATE TABLE exams (id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id TEXT NOT NULL, score INTEGER NOT NULL, passed INTEGER NOT NULL, at TEXT NOT NULL)");
      old.execute("CREATE TABLE exam_drafts (draft_key TEXT PRIMARY KEY, subject_id TEXT NOT NULL, title TEXT NOT NULL, question_ids TEXT NOT NULL, "
          "question_count INTEGER NOT NULL, minutes INTEGER NOT NULL, pass_score INTEGER NOT NULL, points_per_question INTEGER NOT NULL, "
          "mix TEXT NOT NULL, full_bank INTEGER NOT NULL, picked TEXT NOT NULL, started_at TEXT NOT NULL, saved_at TEXT)");
      old.execute("INSERT INTO attempts (question_id, topic_id, subject_id, correct, at) VALUES ('q0', 't', 'subject1', 1, '2026-09-01T09:00:00')");
      old.dispose();

      final store = await ProgressStore.open(path: path);
      addTearDown(store.close);
      expect(store.debugAttempts().single["chosen"], isNull, reason: "老行归因为空");
      await store.recordAttempt(questionId: "q1", topicId: "t", subjectId: "subject1", correct: true, chosen: "T", sessionId: "s");
      await store.recordExam(subjectId: "subject1", score: 90, passed: true, sessionId: "s", usedMs: 1);
      await store.recordExplainView(questionId: "q1", attemptAt: "2026-10-03T09:00:00.000", dwellMs: 1000);
      expect(store.debugAttempts().last["chosen"], "T");
      expect(store.debugExams().single["used_ms"], 1);
      expect(store.debugExplainViews(), hasLength(1));
    });

    test("拉回的别处记录：带归因字段的照收，不带的（老记录）也收", () async {
      final store = await ProgressStore.open(suite: "attribution_f");
      addTearDown(store.close);
      store.applyRemote("attempts", [
        {"question_id": "q1", "topic_id": "t", "subject_id": "s", "correct": true, "at": "2026-10-03T09:00:00.000",
          "chosen": "B", "session_id": "r1", "reason": "due", "kind": "reinforce"},
        {"question_id": "q2", "topic_id": "t", "subject_id": "s", "correct": false, "at": "2026-10-03T09:01:00.000"},
      ]);
      store.applyRemote("exams", [
        {"subject_id": "subject1", "score": 91, "passed": true, "at": "2026-10-03T10:00:00.000", "session_id": "r1", "used_ms": 5},
        {"subject_id": "subject1", "score": 70, "passed": false, "at": "2026-10-03T11:00:00.000"},
      ]);
      store.applyRemote("explain-views", [
        {"question_id": "q2", "attempt_at": "2026-10-03T09:01:00.000", "dwell_ms": 7000},
      ]);
      final rows = store.debugAttempts();
      expect((rows[0]["chosen"], rows[0]["reason"], rows[1]["chosen"]), ("B", "due", null));
      expect(store.debugExams().map((r) => r["used_ms"]), [5, null]);
      expect(store.debugExplainViews().single["dwell_ms"], 7000);
    });

    test("服务端的标志位是 0/1 整数：拉回来的作答、通知、草稿都认（对着真实服务端会崩的老毛病）", () async {
      final store = await ProgressStore.open(suite: "attribution_g");
      addTearDown(store.close);
      store.applyRemote("attempts", [
        {"question_id": "q1", "topic_id": "t", "subject_id": "s", "correct": 1, "hesitant": 0, "at": "2026-10-03T09:00:00.000"},
        {"question_id": "q2", "topic_id": "t", "subject_id": "s", "correct": 0, "hesitant": 1, "at": "2026-10-03T09:01:00.000"},
      ]);
      store.applyRemote("notices", [
        {"kind": "k", "title": "t1", "body": "b", "at": "2026-10-03T09:00:00.000", "read": 1},
        {"kind": "k", "title": "t2", "body": "b", "at": "2026-10-03T09:01:00.000", "read": 0},
      ]);
      store.applyRemote("exams", [
        {"subject_id": "subject1", "score": 91, "passed": 1, "at": "2026-10-03T10:00:00.000"},
      ]);
      expect(store.debugAttempts().map((r) => (r["correct"], r["hesitant"])), [(1, 0), (0, 1)]);
      expect(store.debugExams().single["passed"], 1);
      final draft = ExamDraft.fromApi({
        "subject_id": "subject1", "title": "模拟考", "question_ids": '["a"]', "question_count": 1, "minutes": 45,
        "pass_score": 90, "points_per_question": 1, "mix": "{}", "full_bank": 1, "picked": "{}",
        "started_at": "2026-10-03T09:00:00.000", "saved_at": null, "session_id": null,
      });
      expect(draft.fullBank, isTrue);
      expect(asFlag(0), isFalse);
      expect(asFlag(null), isFalse);
      expect(asFlag(true), isTrue);
    });

    test("会话 id：16 位十六进制，彼此不同，不含个人信息", () {
      final ids = {for (var i = 0; i < 50; i++) newSessionId()};
      expect(ids, hasLength(50));
      expect(ids, everyElement(matches(RegExp(r"^[0-9a-f]{16}$"))));
    });
  });

  group("做题台", () {
    late ProgressStore store;
    var seq = 0;

    Future<void> open(
      WidgetTester tester,
      SessionLaunch launch,
    ) async {
      await tester.runAsync(() async => store = await ProgressStore.open(suite: "attribution_session_${seq++}"));
      await tester.binding.setSurfaceSize(const Size(1600, 1000));
      await tester.pumpWidget(MaterialApp(home: Scaffold(body: SessionStage(launch: launch, store: store, onClose: () {}))));
    }

    /// 按键作答，等到作答记录真的落盘（机器忙时写库慢，不赌固定时长）。
    Future<void> answer(WidgetTester tester, LogicalKeyboardKey key, int expectedRows) async {
      await tester.sendKeyEvent(key);
      for (var i = 0; i < 300 && store.debugAttempts().length < expectedRows; i++) {
        await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
        await tester.pump();
      }
      expect(store.debugAttempts().length, expectedRows);
    }

    /// 离开做题台（会触发解析停留的结算）。
    Future<void> leave(WidgetTester tester) async {
      // 做题台一出现，朗读模块就去问系统有哪些语音（起一个系统进程）；等它跑完再收场，
      // 免得测试结束时还挂着定时器。
      await tester.runAsync(() => Future<void>.delayed(const Duration(seconds: 3)));
      await tester.pump(const Duration(seconds: 1));
      await tester.pumpWidget(const SizedBox());
    }

    Future<void> close(WidgetTester tester) async {
      await leave(tester);
      await tester.runAsync(() => store.close());
    }

    testWidgets("强化练习：作答记下所选选项、同一会话、选题理由、场合标记", (tester) async {
      await open(
        tester,
        SessionLaunch(
          title: "强化练习",
          subjectId: "reinforce",
          questions: [for (var i = 0; i < 3; i++) _judge(i)],
          timed: false,
          revealImmediately: true,
          attemptKind: "reinforce",
          reasons: const {"q0": "retest", "q1": "weak", "q2": "due"},
        ),
      );
      await answer(tester, LogicalKeyboardKey.keyT, 1);
      await answer(tester, LogicalKeyboardKey.keyF, 2);
      await answer(tester, LogicalKeyboardKey.keyT, 3);

      final rows = store.debugAttempts();
      expect(rows.map((r) => r["chosen"]), ["T", "F", "T"]);
      expect(rows.map((r) => r["reason"]), ["retest", "weak", "due"]);
      expect(rows.map((r) => r["kind"]).toSet(), {"reinforce"});
      expect(rows.map((r) => r["subject_id"]).toSet(), {"reinforce"});
      final sessions = rows.map((r) => r["session_id"]).toSet();
      expect(sessions, hasLength(1), reason: "一次强化练习是一个会话");
      expect(sessions.single, matches(RegExp(r"^[0-9a-f]{16}$")));
      await close(tester);
    });

    testWidgets("答错后看解析的停留只记答错的那一题，对上那次作答", (tester) async {
      await open(
        tester,
        SessionLaunch(
          title: "练习", subjectId: "subject1", questions: [for (var i = 0; i < 3; i++) _judge(i)],
          timed: false, revealImmediately: true,
        ),
      );
      await answer(tester, LogicalKeyboardKey.keyT, 1); // 答对
      await answer(tester, LogicalKeyboardKey.keyF, 2); // 答错：解析显示在右栏
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 700)));
      await answer(tester, LogicalKeyboardKey.keyT, 3); // 答对：焦点移到第三题，结算第二题的停留
      await leave(tester); // 离开做题台，结算剩余

      final views = store.debugExplainViews();
      expect(views, hasLength(1), reason: "答对的题不记");
      expect(views.single["question_id"], "q1");
      expect(views.single["dwell_ms"] as int, inInclusiveRange(500, 300000));
      final wrong = store.debugAttempts().firstWhere((r) => r["question_id"] == "q1");
      expect(views.single["attempt_at"], wrong["at"], reason: "对上那次作答的时刻");
      await tester.runAsync(() => store.close());
    });

    testWidgets("多选题：所选选项排序后逗号拼接", (tester) async {
      await open(
        tester,
        SessionLaunch(title: "练习", subjectId: "subject4", questions: [_multi], timed: false, revealImmediately: true),
      );
      await tester.sendKeyEvent(LogicalKeyboardKey.keyC);
      await tester.sendKeyEvent(LogicalKeyboardKey.keyA);
      await tester.pump();
      await tester.tap(find.text("确认作答"));
      for (var i = 0; i < 300 && store.debugAttempts().isEmpty; i++) {
        await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
        await tester.pump();
      }
      expect(store.debugAttempts().single["chosen"], "A,C", reason: "先点 C 再点 A，也记成 A,C");
      expect(store.debugAttempts().single["correct"], 1);
      await close(tester);
    });

    testWidgets("续答沿用草稿里的会话 id", (tester) async {
      await open(
        tester,
        SessionLaunch(
          title: "练习", subjectId: "subject1", questions: [for (var i = 0; i < 2; i++) _judge(i)],
          timed: false, revealImmediately: true, sessionId: "resumed-session-1",
        ),
      );
      await answer(tester, LogicalKeyboardKey.keyT, 1);
      expect(store.debugAttempts().single["session_id"], "resumed-session-1");
      await close(tester);
    });

    testWidgets("模拟考：作答、考试记录、草稿共用同一个会话，并记整场用时", (tester) async {
      const rules = ExamRules(questionCount: 3, minutes: 45, passScore: 90, pointsPerQuestion: 1);
      final questions = [for (var i = 0; i < 3; i++) _judge(i)];
      await open(
        tester,
        SessionLaunch(
          title: "模拟考", subjectId: "subject1", questions: questions, timed: true, minutes: 45,
          revealImmediately: false, draftKey: "subject1.exam",
          paper: Paper(questions: questions, rules: rules, fullBank: true),
        ),
      );
      await answer(tester, LogicalKeyboardKey.keyT, 1);
      // 交一题存一次草稿（不 await 的写入）：等它落盘，草稿里应带着同一个会话。
      ExamDraft? draft;
      for (var i = 0; i < 300 && draft == null; i++) {
        await tester.runAsync(() async => draft = await store.loadExamDraft("subject1.exam"));
        if (draft == null) await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      }
      final session = store.debugAttempts().single["session_id"] as String;
      expect(draft!.sessionId, session);

      await answer(tester, LogicalKeyboardKey.keyT, 2);
      await answer(tester, LogicalKeyboardKey.keyT, 3);
      await tester.tap(find.text("交卷"));
      await tester.pumpAndSettle();
      await tester.tap(find.text("确定交卷"));
      for (var i = 0; i < 300 && store.debugExams().isEmpty; i++) {
        await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
        await tester.pump();
      }
      await tester.pumpAndSettle();

      final exam = store.debugExams().single;
      expect(exam["session_id"], session, reason: "考试记录与作答同一个会话：这就是作答属于哪场考试的关联键");
      expect(exam["used_ms"] as int, greaterThanOrEqualTo(0));
      expect(store.debugAttempts().map((r) => r["session_id"]).toSet(), {session});
      expect(store.debugAttempts().map((r) => r["kind"]).toSet(), {"exam"});
      await close(tester);
    });
  });
}
