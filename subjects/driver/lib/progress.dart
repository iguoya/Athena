import "dart:convert";
import "dart:io";

import "package:flutter/services.dart";
import "package:path/path.dart" as p;
import "package:sqflite_common_ffi/sqflite_ffi.dart";

import "app_root.dart";
import "models.dart";

class TopicStats {
  const TopicStats({required this.attempts, required this.correct});

  final int attempts;
  final int correct;

  double get rate => attempts == 0 ? 0 : correct / attempts;
}

/// 一场没交的模拟考——中途崩了或被重启，靠这个接着答，不用整场重来。
class ExamDraft {
  const ExamDraft({
    required this.subjectId,
    required this.title,
    required this.questionIds,
    required this.questionCount,
    required this.minutes,
    required this.passScore,
    required this.pointsPerQuestion,
    required this.mix,
    required this.fullBank,
    required this.picked,
    required this.startedAt,
  });

  final String subjectId;
  final String title;
  final List<String> questionIds;
  final int questionCount;
  final int minutes;
  final int passScore;
  final int pointsPerQuestion;
  final Map<String, int> mix;
  final bool fullBank;

  /// 题在卷子里的序号 -> 选了哪些选项 id。
  final Map<int, Set<String>> picked;
  final DateTime startedAt;
}

/// 一天的练习量——柱子高矮一眼看出手感有没有断（主仓库 ADR 0056）。
/// 练一把车的记录（ADR 0036）：哪一项、出了哪些错（同一个错可以出现多次）。
class DrillRun {
  const DrillRun({required this.itemId, required this.mistakes, required this.at});

  final String itemId;
  final List<String> mistakes;
  final DateTime at;
}

/// 点位卡某一步的文字（ADR 0037）。只追加，读最新的一行。
class PointNote {
  const PointNote({required this.itemId, required this.step, required this.text, required this.at});

  final String itemId;
  final int step;
  final String text;
  final DateTime at;
}

/// 点位卡上的一张照片。[file] 相对 [ProgressStore.pointsDir]。
class PointPhoto {
  const PointPhoto({
    required this.id,
    required this.itemId,
    required this.step,
    required this.file,
    required this.caption,
    required this.at,
  });

  final int id;
  final String itemId;
  final int step;
  final String file;
  final String caption;
  final DateTime at;
}

/// 一次默演（ADR 0037）：[missed] 是卡住的步骤下标。自评，不写掌握度。
class Rehearsal {
  const Rehearsal({required this.itemId, required this.missed, required this.total, required this.at});

  final String itemId;
  final List<int> missed;
  final int total;
  final DateTime at;
}

/// 教练的话（ADR 0039）：原始记录，和自己整理过的点位卡分开存。
class DrillNote {
  const DrillNote({required this.itemId, required this.text, required this.at});

  final String itemId;
  final String text;
  final DateTime at;
}

class DailyCount {
  const DailyCount({required this.day, required this.attempts, required this.correct});

  final DateTime day;
  final int attempts;
  final int correct;

  double get rate => attempts == 0 ? 0 : correct / attempts;
}

class Notice {
  const Notice({
    required this.id,
    required this.kind,
    required this.title,
    required this.body,
    required this.at,
    required this.read,
  });

  final int id;
  final String kind;
  final String title;
  final String body;
  final String at;
  final bool read;
}

class ProgressStore {
  ProgressStore(this._db);

  final Database _db;

  /// [seed] 为 false 时新库从空白开始，不铺随包的进度库——测试要一个跟使用者练到哪
  /// 无关的起点。
  static Future<ProgressStore> open({String? path, bool seed = true}) async {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
    final dbPath = path ?? _defaultPath();
    if (seed) await _seedIfMissing(dbPath);
    final db = await databaseFactory.openDatabase(
      dbPath,
      options: OpenDatabaseOptions(
        version: 8,
        onCreate: (db, version) async {
          await _createV1(db);
          await _createV2(db);
          await _createV5(db);
          await _createV6(db);
          await _createV7(db);
          await _createV8(db);
        },
        onUpgrade: (db, oldVersion, newVersion) async {
          if (oldVersion < 2) await _createV2(db);
          if (oldVersion < 3) await _createV3(db);
          if (oldVersion < 4) await _createV4(db);
          if (oldVersion < 5) await _createV5(db);
          if (oldVersion < 6) await _createV6(db);
          if (oldVersion < 7) await _createV7(db);
          if (oldVersion < 8) await _createV8(db);
        },
      ),
    );
    return ProgressStore(db);
  }

  /// 发行包第一次启动时，把打包进来的那份进度库铺到用户数据目录。
  /// 不这么做的话，换成打包副本就等于从零开始——之前练的记录都在工作树里。
  static Future<void> _seedIfMissing(String dbPath) async {
    final file = File(dbPath);
    if (file.existsSync() && file.lengthSync() > 0) return;
    try {
      final seed = await rootBundle.load("progress/learning.db");
      file.parent.createSync(recursive: true);
      file.writeAsBytesSync(seed.buffer.asUint8List(seed.offsetInBytes, seed.lengthInBytes));
    } catch (_) {
      // 没有随包的种子库（开发时就是这样），照常建一个空库。
    }
  }

  /// 放用户数据的目录（发行包用；工作树里跑的时候进度在 progress/ 下）。
  static String userDataDir() {
    late final String root;
    if (Platform.isMacOS) {
      root = p.join(Platform.environment["HOME"]!, "Library", "Application Support");
    } else if (Platform.isWindows) {
      root = Platform.environment["APPDATA"] ?? Platform.environment["USERPROFILE"]!;
    } else {
      final home = Platform.environment["HOME"]!;
      root = Platform.environment["XDG_DATA_HOME"] ?? p.join(home, ".local", "share");
    }
    final folder = Directory(p.join(root, "AthenaDriver"));
    folder.createSync(recursive: true);
    return folder.path;
  }

  static String _defaultPath() {
    // 进度随仓库走（ADR 0053）：换一台机器 clone 下来，掌握度和战绩要还在。
    // `app.json` 只存在于工作树，Flutter 发行包里没有它——据此区分，不必判断
    // 路径是否可写。直接点开 build/ 下的调试包也要认得出工作树（ADR 0030）。
    final appRoot = workingTreeRoot();
    if (appRoot != null) {
      final inRepository = Directory(p.join(appRoot, "progress"));
      inRepository.createSync(recursive: true);
      return p.join(inRepository.path, "learning.db");
    }

    return p.join(userDataDir(), "learning.db");
  }

  static Future<void> _createV1(Database db) async {
    await db.execute("""
      CREATE TABLE attempts (
        id INTEGER PRIMARY KEY,
        question_id TEXT NOT NULL,
        topic_id TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        correct INTEGER NOT NULL,
        duration_ms INTEGER NOT NULL DEFAULT 0,
        hesitant INTEGER NOT NULL DEFAULT 0,
        at TEXT NOT NULL
      )
    """);
    await db.execute("""
      CREATE TABLE exams (
        id INTEGER PRIMARY KEY,
        subject_id TEXT NOT NULL,
        score INTEGER NOT NULL,
        passed INTEGER NOT NULL,
        at TEXT NOT NULL
      )
    """);
  }

  static Future<void> _createV2(Database db) async {
    await db.execute("""
      CREATE TABLE notices (
        id INTEGER PRIMARY KEY,
        kind TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        at TEXT NOT NULL,
        read INTEGER NOT NULL
      )
    """);
    await db.execute("""
      CREATE TABLE achievements (
        key TEXT PRIMARY KEY,
        at TEXT NOT NULL
      )
    """);
  }

  static Future<void> _createV3(Database db) async {
    await db.execute("ALTER TABLE attempts ADD COLUMN duration_ms INTEGER NOT NULL DEFAULT 0");
  }

  static Future<void> _createV4(Database db) async {
    await db.execute("ALTER TABLE attempts ADD COLUMN hesitant INTEGER NOT NULL DEFAULT 0");
  }

  /// 模拟考中途的答案只在内存里，中途崩了或被重启就整场白做——挪一份进库，
  /// 一个 key（科目 + 哪一种考）同时只留一份，交卷或放弃就删掉。
  /// 科目二练车记录（ADR 0036）。mistakes 是逗号连起来的错因 id，空串表示这把没毛病。
  static Future<void> _createV6(Database db) async {
    await db.execute("""
      CREATE TABLE drill_runs (
        id INTEGER PRIMARY KEY,
        item_id TEXT NOT NULL,
        mistakes TEXT NOT NULL,
        at TEXT NOT NULL
      )
    """);
  }

  /// 点位卡与默演（ADR 0037）。照片文件在 [pointsDir]，这里只记元数据。
  static Future<void> _createV7(Database db) async {
    await db.execute("""
      CREATE TABLE point_notes (
        id INTEGER PRIMARY KEY,
        item_id TEXT NOT NULL,
        step INTEGER NOT NULL,
        text TEXT NOT NULL,
        at TEXT NOT NULL
      )
    """);
    await db.execute("""
      CREATE TABLE point_photos (
        id INTEGER PRIMARY KEY,
        item_id TEXT NOT NULL,
        step INTEGER NOT NULL,
        file TEXT NOT NULL,
        caption TEXT NOT NULL,
        at TEXT NOT NULL,
        removed INTEGER NOT NULL DEFAULT 0
      )
    """);
    await db.execute("""
      CREATE TABLE rehearsals (
        id INTEGER PRIMARY KEY,
        item_id TEXT NOT NULL,
        missed TEXT NOT NULL,
        total INTEGER NOT NULL,
        at TEXT NOT NULL
      )
    """);
  }

  /// 教练的话（ADR 0039）。
  static Future<void> _createV8(Database db) async {
    await db.execute("""
      CREATE TABLE drill_notes (
        id INTEGER PRIMARY KEY,
        item_id TEXT NOT NULL,
        text TEXT NOT NULL,
        at TEXT NOT NULL
      )
    """);
  }

  static Future<void> _createV5(Database db) async {
    await db.execute("""
      CREATE TABLE exam_drafts (
        draft_key TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL,
        title TEXT NOT NULL,
        question_ids TEXT NOT NULL,
        question_count INTEGER NOT NULL,
        minutes INTEGER NOT NULL,
        pass_score INTEGER NOT NULL,
        points_per_question INTEGER NOT NULL,
        mix TEXT NOT NULL,
        full_bank INTEGER NOT NULL,
        picked TEXT NOT NULL,
        started_at TEXT NOT NULL
      )
    """);
  }

  Future<List<Notice>> recordAttempt({
    required String questionId,
    required String topicId,
    required String subjectId,
    required bool correct,
    int durationMs = 0,
    String? topicTitle,
  }) async {
    final beforeWrong = (await wrongQuestionIds()).length;
    await _db.insert("attempts", {
      "question_id": questionId,
      "topic_id": topicId,
      "subject_id": subjectId,
      "correct": correct ? 1 : 0,
      "duration_ms": durationMs,
      "hesitant": 0,
      "at": DateTime.now().toIso8601String(),
    });
    final born = <Notice>[];
    if (correct) {
      born.addAll(await _maybeStreak());
      born.addAll(await _maybeTopic(topicId, topicTitle ?? topicId));
    }
    final afterWrong = (await wrongQuestionIds()).length;
    if (beforeWrong > 0 && afterWrong == 0) {
      born.add(await _notice(
        kind: "wrongbook",
        title: "错题本清空",
        body: "最近一次答错的题都订正了。",
      ));
    }
    return born;
  }

  Future<List<Notice>> recordExam({
    required String subjectId,
    required int score,
    required bool passed,
    String? subjectTitle,
  }) async {
    await _db.insert("exams", {
      "subject_id": subjectId,
      "score": score,
      "passed": passed ? 1 : 0,
      "at": DateTime.now().toIso8601String(),
    });
    final label = subjectTitle ?? subjectId;
    final born = <Notice>[
      await _notice(
        kind: passed ? "exam-pass" : "exam-fail",
        title: passed ? "$label 模拟考及格" : "$label 模拟考未及格",
        body: passed ? "折合 $score 分，达到 90 分线。" : "折合 $score 分。对照错题和条文再练。",
      ),
    ];
    if (passed) {
      final extra = await _unlock(
        "exam.pass.$subjectId",
        kind: "exam-pass",
        title: "首次及格：$label",
        body: "模拟考第一次站上 90 分。",
      );
      if (extra != null) born.add(extra);
    }
    return born;
  }

  /// 存/覆盖一份模拟考草稿——一个 key 同时只留一份，答一题存一次。
  Future<void> saveExamDraft(ExamDraft draft, {required String draftKey}) async {
    await _db.insert("exam_drafts", {
      "draft_key": draftKey,
      "subject_id": draft.subjectId,
      "title": draft.title,
      "question_ids": jsonEncode(draft.questionIds),
      "question_count": draft.questionCount,
      "minutes": draft.minutes,
      "pass_score": draft.passScore,
      "points_per_question": draft.pointsPerQuestion,
      "mix": jsonEncode(draft.mix),
      "full_bank": draft.fullBank ? 1 : 0,
      "picked": jsonEncode({
        for (final entry in draft.picked.entries) "${entry.key}": entry.value.toList(),
      }),
      "started_at": draft.startedAt.toIso8601String(),
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<ExamDraft?> loadExamDraft(String draftKey) async {
    final rows = await _db.query("exam_drafts", where: "draft_key = ?", whereArgs: [draftKey]);
    if (rows.isEmpty) return null;
    final row = rows.first;
    final pickedRaw = jsonDecode(row["picked"] as String) as Map<String, dynamic>;
    return ExamDraft(
      subjectId: row["subject_id"] as String,
      title: row["title"] as String,
      questionIds: [for (final id in jsonDecode(row["question_ids"] as String) as List<dynamic>) id as String],
      questionCount: row["question_count"] as int,
      minutes: row["minutes"] as int,
      passScore: row["pass_score"] as int,
      pointsPerQuestion: row["points_per_question"] as int,
      mix: {
        for (final entry in (jsonDecode(row["mix"] as String) as Map<String, dynamic>).entries) entry.key: entry.value as int,
      },
      fullBank: (row["full_bank"] as int) == 1,
      picked: {
        for (final entry in pickedRaw.entries)
          int.parse(entry.key): {for (final id in entry.value as List<dynamic>) id as String},
      },
      startedAt: DateTime.tryParse(row["started_at"] as String? ?? "") ?? DateTime.now(),
    );
  }

  Future<void> clearExamDraft(String draftKey) async {
    await _db.delete("exam_drafts", where: "draft_key = ?", whereArgs: [draftKey]);
  }

  Future<int> currentStreak() async {
    final rows = await _db.rawQuery(
      "SELECT correct FROM attempts ORDER BY at DESC, id DESC LIMIT 40",
    );
    var n = 0;
    for (final row in rows) {
      if ((row["correct"] as int?) == 1) {
        n += 1;
      } else {
        break;
      }
    }
    return n;
  }

  Future<int> unreadCount() async {
    final rows = await _db.rawQuery("SELECT COUNT(*) AS n FROM notices WHERE read = 0");
    return (rows.first["n"] as int?) ?? 0;
  }

  Future<List<Notice>> notices({int limit = 30}) async {
    final rows = await _db.query("notices", orderBy: "id DESC", limit: limit);
    return [for (final row in rows) _noticeFrom(row)];
  }

  Future<void> markAllRead() async {
    await _db.update("notices", {"read": 1}, where: "read = 0");
  }

  Future<Map<String, TopicStats>> topicStats() async {
    final rows = await _db.rawQuery("""
      SELECT topic_id, COUNT(*) AS attempts, SUM(correct) AS correct
      FROM attempts GROUP BY topic_id
    """);
    return {
      for (final row in rows)
        row["topic_id"] as String: TopicStats(
          attempts: row["attempts"] as int,
          correct: (row["correct"] as int?) ?? 0,
        ),
    };
  }

  /// 最近 N 天每天的练习量，没练的天数补 0——柱子连不上就是断更了。
  Future<List<DailyCount>> dailyAttempts({int days = 14}) async {
    final today = DateTime.now();
    final since = DateTime(today.year, today.month, today.day).subtract(Duration(days: days - 1));
    final rows = await _db.rawQuery(
      "SELECT at, correct FROM attempts WHERE at >= ?",
      [since.toIso8601String()],
    );
    String key(DateTime d) =>
        "${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}";
    final counts = <String, List<int>>{};
    for (final row in rows) {
      final at = DateTime.tryParse(row["at"] as String? ?? "");
      if (at == null) continue;
      final entry = counts.putIfAbsent(key(at), () => [0, 0]);
      entry[0] += 1;
      if ((row["correct"] as int?) == 1) entry[1] += 1;
    }
    return [
      for (var i = 0; i < days; i++)
        () {
          final day = since.add(Duration(days: i));
          final entry = counts[key(day)] ?? const [0, 0];
          return DailyCount(day: day, attempts: entry[0], correct: entry[1]);
        }(),
    ];
  }

  /// 每道题按作答时间取最近一次。不能按自增 id 取：同步和合并进来的是别处早先的作答，
  /// 入库晚、id 大，按 id 会把几小时前的一次答错当成最新，盖掉后来的答对（ADR 0030）。
  static const _latestAttempts = """
    SELECT question_id, correct, at, id FROM (
      SELECT question_id, correct, at, id,
        ROW_NUMBER() OVER (PARTITION BY question_id ORDER BY at DESC, id DESC) AS rn
      FROM attempts
    ) WHERE rn = 1
  """;

  Future<List<String>> wrongQuestionIds() async {
    final rows = await _db.rawQuery("""
      SELECT a.question_id
      FROM ($_latestAttempts) a
      WHERE a.correct = 0
      ORDER BY a.at DESC, a.id DESC
    """);
    return [for (final row in rows) row["question_id"] as String];
  }

  /// 每道答错过的题，最后一次答错之后又连着答对了几次（考前复习的移出判据，ADR 0034）。
  /// 「最后一次」跟 `_latestAttempts` 同一个排序：先按时间，时间相同按行号。
  Future<Map<String, int>> correctStreaksSinceWrong() async {
    final rows = await _db.rawQuery("""
      WITH last_wrong AS (
        SELECT question_id, at, id FROM (
          SELECT question_id, at, id,
            ROW_NUMBER() OVER (PARTITION BY question_id ORDER BY at DESC, id DESC) AS rn
          FROM attempts WHERE correct = 0
        ) WHERE rn = 1
      )
      SELECT w.question_id, COUNT(a.id) AS n
      FROM last_wrong w
      LEFT JOIN attempts a
        ON a.question_id = w.question_id AND a.correct = 1
        AND (a.at > w.at OR (a.at = w.at AND a.id > w.id))
      GROUP BY w.question_id
    """);
    return {
      for (final row in rows) row["question_id"] as String: row["n"] as int,
    };
  }

  /// 每道题累计答错过几次。考前最该刷的是反复栽跟头的题，不是最近错的那一道。
  Future<Map<String, int>> wrongCounts() async {
    final rows = await _db.rawQuery(
      "SELECT question_id, COUNT(*) AS n FROM attempts WHERE correct = 0 GROUP BY question_id",
    );
    return {
      for (final row in rows) row["question_id"] as String: row["n"] as int,
    };
  }

  /// 最近几次模拟考的成绩，新的在前——记了不给人看，等于没记（主仓库 ADR 0052）。
  Future<List<ExamRecord>> recentExams({String? subjectId, int limit = 12}) async {
    final rows = await _db.rawQuery(
      """
      SELECT subject_id, score, passed, at FROM exams
      ${subjectId == null ? "" : "WHERE subject_id = ?"}
      ORDER BY id DESC LIMIT ?
      """,
      [?subjectId, limit],
    );
    return [
      for (final row in rows)
        ExamRecord(
          subjectId: row["subject_id"] as String,
          score: row["score"] as int,
          passed: (row["passed"] as int) == 1,
          at: DateTime.tryParse(row["at"] as String? ?? "") ?? DateTime.now(),
        ),
    ];
  }

  /// 最近一次开始往前数，连着及格了几次。
  static int passStreak(List<ExamRecord> exams) {
    var n = 0;
    for (final exam in exams) {
      if (!exam.passed) break;
      n++;
    }
    return n;
  }

  /// 最近一次答对、且没有明显慢于平时节奏。迟疑答对的题练习里还会再出。
  Future<Set<String>> masteredQuestionIds() async {
    final rows = await _db.rawQuery("""
      SELECT a.question_id
      FROM ($_latestAttempts) a
      WHERE a.correct = 1
    """);
    return {for (final row in rows) row["question_id"] as String};
  }

  Future<int> averageDurationMs() async {
    final rows = await _db.rawQuery(
      "SELECT AVG(duration_ms) AS ms FROM attempts WHERE duration_ms > 0",
    );
    final value = rows.first["ms"];
    if (value is int) return value;
    if (value is double) return value.round();
    return 0;
  }

  Future<Map<String, int>> attemptCounts() async {
    final rows = await _db.rawQuery(
      "SELECT question_id, COUNT(*) AS n FROM attempts GROUP BY question_id",
    );
    return {
      for (final row in rows) row["question_id"] as String: row["n"] as int,
    };
  }

  Future<List<Notice>> _maybeStreak() async {
    final n = await currentStreak();
    final born = <Notice>[];
    for (final mark in const [5, 10, 20]) {
      if (n == mark) {
        final item = await _unlock(
          "streak.$mark",
          kind: "streak",
          title: "连对 $mark 题",
          body: "连续答对 $mark 道。规则记牢了，不是蒙的。",
        );
        if (item != null) born.add(item);
      }
    }
    return born;
  }

  Future<List<Notice>> _maybeTopic(String topicId, String title) async {
    final stats = (await topicStats())[topicId];
    if (stats == null || stats.attempts < 3 || stats.rate < 0.9) return const [];
    final item = await _unlock(
      "topic.$topicId",
      kind: "topic",
      title: "章节过关：$title",
      body: "正确率 ${(stats.rate * 100).round()}%（${stats.attempts} 次）。",
    );
    return item == null ? const [] : [item];
  }

  Future<Notice?> _unlock(
    String key, {
    required String kind,
    required String title,
    required String body,
  }) async {
    final existing = await _db.query("achievements", where: "key = ?", whereArgs: [key]);
    if (existing.isNotEmpty) return null;
    final at = DateTime.now().toIso8601String();
    await _db.insert("achievements", {"key": key, "at": at});
    return _notice(kind: kind, title: title, body: body, at: at);
  }

  Future<Notice> _notice({
    required String kind,
    required String title,
    required String body,
    String? at,
  }) async {
    final stamp = at ?? DateTime.now().toIso8601String();
    final id = await _db.insert("notices", {
      "kind": kind,
      "title": title,
      "body": body,
      "at": stamp,
      "read": 0,
    });
    return Notice(id: id, kind: kind, title: title, body: body, at: stamp, read: false);
  }

  Notice _noticeFrom(Map<String, Object?> row) {
    return Notice(
      id: row["id"] as int,
      kind: row["kind"] as String,
      title: row["title"] as String,
      body: row["body"] as String,
      at: row["at"] as String,
      read: (row["read"] as int) == 1,
    );
  }

  /// 导出成事件流：作答、模拟考、里程碑都是只追加的记录，设备之间按并集合并
  /// 就行，不需要冲突解决（ADR 0010）。notices 是由这些记录派生的，不导。
  Future<List<Map<String, Object?>>> exportEvents({String? since}) async {
    final events = <Map<String, Object?>>[];
    final attempts = await _db.rawQuery(
      since == null
          ? "SELECT * FROM attempts ORDER BY at"
          : "SELECT * FROM attempts WHERE at > ? ORDER BY at",
      [?since],
    );
    for (final row in attempts) {
      events.add({
        "kind": "attempt",
        "question_id": row["question_id"],
        "topic_id": row["topic_id"],
        "subject_id": row["subject_id"],
        "correct": row["correct"],
        "duration_ms": row["duration_ms"] ?? 0,
        "hesitant": row["hesitant"] ?? 0,
        "at": row["at"],
      });
    }
    final exams = await _db.rawQuery(
      since == null
          ? "SELECT * FROM exams ORDER BY at"
          : "SELECT * FROM exams WHERE at > ? ORDER BY at",
      [?since],
    );
    for (final row in exams) {
      events.add({
        "kind": "exam",
        "subject_id": row["subject_id"],
        "score": row["score"],
        "passed": row["passed"],
        "at": row["at"],
      });
    }
    final drills = await _db.rawQuery(
      since == null
          ? "SELECT * FROM drill_runs ORDER BY at"
          : "SELECT * FROM drill_runs WHERE at > ? ORDER BY at",
      [?since],
    );
    for (final row in drills) {
      events.add({"kind": "drill", "item_id": row["item_id"], "mistakes": row["mistakes"], "at": row["at"]});
    }
    final drillNotes = await _db.rawQuery(
      since == null
          ? "SELECT * FROM drill_notes ORDER BY at"
          : "SELECT * FROM drill_notes WHERE at > ? ORDER BY at",
      [?since],
    );
    for (final row in drillNotes) {
      events.add({"kind": "drill_note", "item_id": row["item_id"], "text": row["text"], "at": row["at"]});
    }
    // 点位卡文字与默演记录跟着事件同步；照片不同步，跨机器靠仓库（ADR 0037）。
    final notes = await _db.rawQuery(
      since == null
          ? "SELECT * FROM point_notes ORDER BY at"
          : "SELECT * FROM point_notes WHERE at > ? ORDER BY at",
      [?since],
    );
    for (final row in notes) {
      events.add({"kind": "point", "item_id": row["item_id"], "step": row["step"], "text": row["text"], "at": row["at"]});
    }
    final rehearsals = await _db.rawQuery(
      since == null
          ? "SELECT * FROM rehearsals ORDER BY at"
          : "SELECT * FROM rehearsals WHERE at > ? ORDER BY at",
      [?since],
    );
    for (final row in rehearsals) {
      events.add({
        "kind": "rehearsal",
        "item_id": row["item_id"],
        "missed": row["missed"],
        "total": row["total"],
        "at": row["at"],
      });
    }
    final achievements = await _db.rawQuery("SELECT * FROM achievements ORDER BY at");
    for (final row in achievements) {
      events.add({"kind": "achievement", "key": row["key"], "at": row["at"]});
    }
    events.sort((a, b) => (a["at"] as String).compareTo(b["at"] as String));
    return events;
  }

  /// 把别的设备的事件并进来，已有的跳过。返回真正写进去的条数。
  Future<int> importEvents(List<Map<String, Object?>> events) async {
    var written = 0;
    await _db.transaction((txn) async {
      for (final event in events) {
        switch (event["kind"]) {
          case "attempt":
            final exists = await txn.rawQuery(
              "SELECT 1 FROM attempts WHERE question_id = ? AND at = ? LIMIT 1",
              [event["question_id"], event["at"]],
            );
            if (exists.isNotEmpty) continue;
            await txn.insert("attempts", {
              "question_id": event["question_id"],
              "topic_id": event["topic_id"],
              "subject_id": event["subject_id"],
              "correct": event["correct"],
              "duration_ms": event["duration_ms"] ?? 0,
              "hesitant": event["hesitant"] ?? 0,
              "at": event["at"],
            });
            written++;
          case "exam":
            final exists = await txn.rawQuery(
              "SELECT 1 FROM exams WHERE subject_id = ? AND at = ? LIMIT 1",
              [event["subject_id"], event["at"]],
            );
            if (exists.isNotEmpty) continue;
            await txn.insert("exams", {
              "subject_id": event["subject_id"],
              "score": event["score"],
              "passed": event["passed"],
              "at": event["at"],
            });
            written++;
          case "drill":
            final exists = await txn.rawQuery(
              "SELECT 1 FROM drill_runs WHERE item_id = ? AND at = ? LIMIT 1",
              [event["item_id"], event["at"]],
            );
            if (exists.isNotEmpty) continue;
            await txn.insert("drill_runs", {
              "item_id": event["item_id"],
              "mistakes": event["mistakes"] ?? "",
              "at": event["at"],
            });
            written++;
          case "drill_note":
            final exists = await txn.rawQuery(
              "SELECT 1 FROM drill_notes WHERE item_id = ? AND at = ? LIMIT 1",
              [event["item_id"], event["at"]],
            );
            if (exists.isNotEmpty) continue;
            await txn.insert("drill_notes", {
              "item_id": event["item_id"],
              "text": event["text"] ?? "",
              "at": event["at"],
            });
            written++;
          case "point":
            final exists = await txn.rawQuery(
              "SELECT 1 FROM point_notes WHERE item_id = ? AND step = ? AND at = ? LIMIT 1",
              [event["item_id"], event["step"], event["at"]],
            );
            if (exists.isNotEmpty) continue;
            await txn.insert("point_notes", {
              "item_id": event["item_id"],
              "step": event["step"],
              "text": event["text"] ?? "",
              "at": event["at"],
            });
            written++;
          case "rehearsal":
            final exists = await txn.rawQuery(
              "SELECT 1 FROM rehearsals WHERE item_id = ? AND at = ? LIMIT 1",
              [event["item_id"], event["at"]],
            );
            if (exists.isNotEmpty) continue;
            await txn.insert("rehearsals", {
              "item_id": event["item_id"],
              "missed": event["missed"] ?? "",
              "total": event["total"] ?? 0,
              "at": event["at"],
            });
            written++;
          case "achievement":
            final exists = await txn.rawQuery(
              "SELECT 1 FROM achievements WHERE key = ? LIMIT 1",
              [event["key"]],
            );
            if (exists.isNotEmpty) continue;
            await txn.insert("achievements", {"key": event["key"], "at": event["at"]});
            written++;
        }
      }
    });
    return written;
  }

  /// 记一把练车。不写掌握度——掌握度只由答题写入（ADR 0036）。
  Future<void> recordDrillRun(String itemId, List<String> mistakes, {DateTime? at}) async {
    await _db.insert("drill_runs", {
      "item_id": itemId,
      "mistakes": mistakes.join(","),
      "at": (at ?? DateTime.now()).toIso8601String(),
    });
  }

  /// 练车记录，新的在前。
  Future<List<DrillRun>> drillRuns() async {
    final rows = await _db.rawQuery("SELECT * FROM drill_runs ORDER BY at DESC, id DESC");
    return [
      for (final row in rows)
        DrillRun(
          itemId: row["item_id"] as String,
          mistakes: [
            for (final id in (row["mistakes"] as String).split(","))
              if (id.isNotEmpty) id,
          ],
          at: DateTime.parse(row["at"] as String),
        ),
    ];
  }

  /// 点位卡照片放在进度库旁边的 `points/`：工作树里随仓库走，发行副本在用户数据目录。
  String get pointsDir => p.join(p.dirname(_db.path), "points");

  Future<void> savePointNote(String itemId, int step, String text, {DateTime? at}) async {
    await _db.insert("point_notes", {
      "item_id": itemId,
      "step": step,
      "text": text,
      "at": (at ?? DateTime.now()).toIso8601String(),
    });
  }

  /// 每一步最新的一版文字，键是（项目, 步骤）。
  Future<Map<(String, int), PointNote>> pointNotes() async {
    final rows = await _db.rawQuery("""
      SELECT item_id, step, text, at FROM (
        SELECT item_id, step, text, at,
          ROW_NUMBER() OVER (PARTITION BY item_id, step ORDER BY at DESC, id DESC) AS rn
        FROM point_notes
      ) WHERE rn = 1
    """);
    return {
      for (final row in rows)
        (row["item_id"] as String, row["step"] as int): PointNote(
          itemId: row["item_id"] as String,
          step: row["step"] as int,
          text: row["text"] as String,
          at: DateTime.parse(row["at"] as String),
        ),
    };
  }

  Future<void> addPointPhoto(String itemId, int step, String file, String caption) async {
    await _db.insert("point_photos", {
      "item_id": itemId,
      "step": step,
      "file": file,
      "caption": caption,
      "at": DateTime.now().toIso8601String(),
    });
  }

  Future<List<PointPhoto>> pointPhotos() async {
    final rows = await _db.rawQuery("SELECT * FROM point_photos WHERE removed = 0 ORDER BY at, id");
    return [
      for (final row in rows)
        PointPhoto(
          id: row["id"] as int,
          itemId: row["item_id"] as String,
          step: row["step"] as int,
          file: row["file"] as String,
          caption: row["caption"] as String,
          at: DateTime.parse(row["at"] as String),
        ),
    ];
  }

  /// 删照片：删文件，记录标记删除。
  Future<void> removePointPhoto(PointPhoto photo) async {
    await _db.update("point_photos", {"removed": 1}, where: "id = ?", whereArgs: [photo.id]);
    final file = File(p.join(pointsDir, photo.file));
    if (await file.exists()) await file.delete();
  }

  Future<void> recordRehearsal(String itemId, List<int> missed, int total, {DateTime? at}) async {
    await _db.insert("rehearsals", {
      "item_id": itemId,
      "missed": missed.join(","),
      "total": total,
      "at": (at ?? DateTime.now()).toIso8601String(),
    });
  }

  /// 默演记录，新的在前。
  Future<List<Rehearsal>> rehearsals() async {
    final rows = await _db.rawQuery("SELECT * FROM rehearsals ORDER BY at DESC, id DESC");
    return [
      for (final row in rows)
        Rehearsal(
          itemId: row["item_id"] as String,
          missed: [
            for (final s in (row["missed"] as String).split(","))
              if (s.isNotEmpty) int.parse(s),
          ],
          total: row["total"] as int,
          at: DateTime.parse(row["at"] as String),
        ),
    ];
  }

  Future<void> recordDrillNote(String itemId, String text, {DateTime? at}) async {
    await _db.insert("drill_notes", {
      "item_id": itemId,
      "text": text,
      "at": (at ?? DateTime.now()).toIso8601String(),
    });
  }

  /// 教练的话，新的在前。
  Future<List<DrillNote>> drillNotes() async {
    final rows = await _db.rawQuery("SELECT * FROM drill_notes ORDER BY at DESC, id DESC");
    return [
      for (final row in rows)
        DrillNote(itemId: row["item_id"] as String, text: row["text"] as String, at: DateTime.parse(row["at"] as String)),
    ];
  }

  Future<int> attemptTotal() async {
    final rows = await _db.rawQuery("SELECT COUNT(*) AS n FROM attempts");
    return (rows.first["n"] as int?) ?? 0;
  }

  Future<void> close() => _db.close();
}
