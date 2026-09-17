import "dart:io";

import "package:flutter/services.dart";
import "package:path/path.dart" as p;
import "package:sqflite_common_ffi/sqflite_ffi.dart";

import "models.dart";

/// 相对自己平时的答题节奏：样本不够不下结论；必须明显停更久才算迟疑。
bool lingeredVsPace(int durationMs, Iterable<int> otherDurations) {
  final samples = [
    for (final ms in otherDurations)
      if (ms > 0) ms,
  ]..sort();
  if (samples.length < 6) return false;
  final median = samples[samples.length ~/ 2];
  return durationMs >= median * 2.5 && durationMs >= median + 12000;
}

class TopicStats {
  const TopicStats({required this.attempts, required this.correct});

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

  static Future<ProgressStore> open({String? path}) async {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
    final dbPath = path ?? _defaultPath();
    await _seedIfMissing(dbPath);
    final db = await databaseFactory.openDatabase(
      dbPath,
      options: OpenDatabaseOptions(
        version: 4,
        onCreate: (db, version) async {
          await _createV1(db);
          await _createV2(db);
        },
        onUpgrade: (db, oldVersion, newVersion) async {
          if (oldVersion < 2) await _createV2(db);
          if (oldVersion < 3) await _createV3(db);
          if (oldVersion < 4) await _createV4(db);
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
    // 路径是否可写，也不必问自己「是不是在仓库里」。
    final env = Platform.environment["ATHENA_DRIVER_ROOT"];
    final appRoot = (env != null && env.isNotEmpty) ? env : Directory.current.path;
    if (File(p.join(appRoot, "app.json")).existsSync()) {
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

  Future<List<Notice>> recordAttempt({
    required String questionId,
    required String topicId,
    required String subjectId,
    required bool correct,
    int durationMs = 0,
    bool? hesitant,
    String? topicTitle,
  }) async {
    final lingering = hesitant ?? lingeredVsPace(durationMs, await recentDurations());
    final beforeWrong = (await wrongQuestionIds()).length;
    await _db.insert("attempts", {
      "question_id": questionId,
      "topic_id": topicId,
      "subject_id": subjectId,
      "correct": correct ? 1 : 0,
      "duration_ms": durationMs,
      "hesitant": lingering ? 1 : 0,
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

  Future<List<String>> wrongQuestionIds() async {
    final rows = await _db.rawQuery("""
      SELECT a.question_id
      FROM attempts a
      INNER JOIN (
        SELECT question_id, MAX(id) AS last_id
        FROM attempts
        GROUP BY question_id
      ) latest ON a.id = latest.last_id
      WHERE a.correct = 0
      ORDER BY a.id DESC
    """);
    return [for (final row in rows) row["question_id"] as String];
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
      FROM attempts a
      INNER JOIN (
        SELECT question_id, MAX(id) AS last_id
        FROM attempts
        GROUP BY question_id
      ) latest ON a.id = latest.last_id
      WHERE a.correct = 1 AND a.hesitant = 0
    """);
    return {for (final row in rows) row["question_id"] as String};
  }

  Future<List<int>> recentDurations({int limit = 24}) async {
    final rows = await _db.rawQuery(
      """
      SELECT duration_ms FROM attempts
      WHERE duration_ms > 0
      ORDER BY id DESC
      LIMIT ?
      """,
      [limit],
    );
    return [for (final row in rows) row["duration_ms"] as int];
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

  Future<int> attemptTotal() async {
    final rows = await _db.rawQuery("SELECT COUNT(*) AS n FROM attempts");
    return (rows.first["n"] as int?) ?? 0;
  }

  Future<void> close() => _db.close();
}
