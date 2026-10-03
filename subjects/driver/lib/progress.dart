import "dart:convert";
import "dart:io";
import "dart:math";

import "package:flutter/foundation.dart";
import "package:path/path.dart" as p;
import "package:sqlite3/sqlite3.dart";

import "app_root.dart";
import "models.dart";
import "reinforce.dart";

/// 新会话的标识：16 位随机十六进制，不含任何个人信息或设备信息（主仓库 ADR 0076 决策 3）。
String newSessionId() {
  final random = Random.secure();
  return List.generate(16, (_) => random.nextInt(16).toRadixString(16)).join();
}

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
    this.savedAt,
    this.sessionId,
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

  /// 最后一次存草稿（最后交一题）的时刻。续答时用时只算到这里，挂起的那段不算
  /// （ADR 0043）。更早版本存的草稿没有这一列，读出来是 null。
  final DateTime? savedAt;

  /// 这场考试所属的会话（主仓库 ADR 0076）。续答沿用它，不另起新会话；老草稿没有，读出来是 null。
  final String? sessionId;

  /// 上次停下之前已经答了多久。老草稿不知道，按 0 算——宁可少算，不把挂起的几天算进去。
  Duration get spent {
    final end = savedAt;
    if (end == null || end.isBefore(startedAt)) return Duration.zero;
    return end.difference(startedAt);
  }

  /// 上传给中心 API 的字段形态（ADR 0068 的接口契约：question_ids/mix/picked 是
  /// JSON 字符串，started_at/saved_at 是 ISO 时间串）。
  Map<String, Object?> toApi() => {
        "subject_id": subjectId,
        "title": title,
        "question_ids": jsonEncode(questionIds),
        "question_count": questionCount,
        "minutes": minutes,
        "pass_score": passScore,
        "points_per_question": pointsPerQuestion,
        "mix": jsonEncode(mix),
        "full_bank": fullBank,
        "picked": jsonEncode({
          for (final entry in picked.entries) "${entry.key}": entry.value.toList(),
        }),
        "started_at": startedAt.toIso8601String(),
        "saved_at": savedAt?.toIso8601String(),
        "session_id": sessionId,
      };

  static ExamDraft fromApi(Map<String, Object?> row) => ExamDraft(
        subjectId: row["subject_id"]! as String,
        title: row["title"]! as String,
        questionIds: [
          for (final id in jsonDecode(row["question_ids"]! as String) as List<dynamic>) id as String,
        ],
        questionCount: row["question_count"]! as int,
        minutes: row["minutes"]! as int,
        passScore: row["pass_score"]! as int,
        pointsPerQuestion: row["points_per_question"]! as int,
        mix: {
          for (final entry in (jsonDecode(row["mix"]! as String) as Map<String, dynamic>).entries)
            entry.key: entry.value as int,
        },
        fullBank: (row["full_bank"]! as bool),
        picked: {
          for (final entry in (jsonDecode(row["picked"]! as String) as Map<String, dynamic>).entries)
            int.parse(entry.key): {for (final id in entry.value as List<dynamic>) id as String},
        },
        startedAt: DateTime.tryParse(row["started_at"]! as String? ?? "") ?? DateTime.now(),
        savedAt: DateTime.tryParse(row["saved_at"] as String? ?? ""),
        sessionId: row["session_id"] as String?,
      );
}

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

/// 点位卡上的一张照片。[file] 相对 [ProgressStore.pointsDir]。登记随仓库走
/// （photos.json，ADR 0070），file 名里带时间戳，本身就是唯一键。
class PointPhoto {
  const PointPhoto({
    required this.itemId,
    required this.step,
    required this.file,
    required this.caption,
    required this.at,
  });

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

/// 待发送队列里的一条。追加型资源的 payload 是那一行业务字段；可变数据
/// （成就、草稿、已读）的 payload 是动作参数（ADR 0068 决策 4）。
class OutboxEntry {
  const OutboxEntry({required this.id, required this.kind, required this.key, required this.payload});

  final int id;
  final String kind;
  final String? key;
  final Map<String, Object?> payload;
}

/// 本地进度库打不开（磁盘错误、文件损坏）。本地库是界面的唯一数据面，打不开
/// 就是不能用；中心同步的成败不在此层——那是 SyncEngine 的状态，不拦做题。
class ProgressUnavailable implements Exception {
  ProgressUnavailable(this.detail);

  final String detail;

  @override
  String toString() => "本地学习记录库打不开：$detail";
}

class ProgressStore {
  ProgressStore._(this._db, this._tempDir);

  final Database _db;

  /// suite 模式（测试专用）下持有临时目录，close 时连库一起清掉。
  final Directory? _tempDir;

  /// 有记录进队列后回调一次（同步器接上做防抖触发，ADR 0070）；没人接就是
  /// 纯离线模式，队列安静地攒着。测试不接。
  void Function()? onEnqueued;

  /// 本地 SQLite 是唯一数据面（ADR 0070）：打开必成功（最多抛
  /// [ProgressUnavailable]），做题不再以「连上中心」为前提。
  ///
  /// [user] 是学习者名字（ADR 0071）：本地按用户分库文件 `local-<用户>.db`，
  /// 换人就是换一份空白历史；本地表不建 `user` 列——分文件已隔离，中心侧才有该列。
  /// [suite] 供测试：每个测试文件一个独立的临时库（隔离语义自 ADR 0068 决策 5
  /// 延续），close 时自动删除；[path] 显式指定文件（测试用）。
  static Future<ProgressStore> open({String? path, String? suite, String? user}) async {
    Directory? tempDir;
    late final String file;
    if (suite != null) {
      tempDir = Directory.systemTemp.createTempSync("athena-driver-");
      final safe = suite.replaceAll(RegExp(r"[^a-zA-Z0-9_]"), "_");
      file = p.join(tempDir.path, "$safe.db");
    } else if (user != null) {
      file = p.join(userDataDir(), "local-${_fileSafe(user)}.db");
    } else {
      file = path ?? p.join(userDataDir(), "local.db");
    }
    final Database db;
    try {
      Directory(p.dirname(file)).createSync(recursive: true);
      db = sqlite3.open(file);
      _ensureSchema(db);
    } catch (error) {
      tempDir?.deleteSync(recursive: true);
      throw ProgressUnavailable("$error");
    }
    final store = ProgressStore._(db, tempDir);
    store._user = user;
    return store;
  }

  /// 表结构与中心 PG 同名同列（ADR 0070：方言差异关在本文件）；id 是本地自增，
  /// 只作排序断路器，业务键唯一索引承担「拉回来的重复行不再插一遍」的幂等合并。
  /// outbox 与业务表同库，写入在同一事务里落两边——记了题必有队列。
  static void _ensureSchema(Database db) {
    db.execute("PRAGMA journal_mode = WAL");
    db.execute("""
      CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id TEXT NOT NULL,
        topic_id TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        correct INTEGER NOT NULL,
        duration_ms INTEGER NOT NULL DEFAULT 0,
        hesitant INTEGER NOT NULL DEFAULT 0,
        at TEXT NOT NULL,
        kind TEXT NOT NULL DEFAULT 'practice'
      )
    """);
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_attempts ON attempts (question_id, at)");
    // 老库升级：CREATE IF NOT EXISTS 不会给已有的表补列，手动加（ADR 0057）。
    final columns = db.select("PRAGMA table_info(attempts)").map((r) => r["name"] as String).toSet();
    if (!columns.contains("kind")) {
      db.execute("ALTER TABLE attempts ADD COLUMN kind TEXT NOT NULL DEFAULT 'practice'");
    }
    db.execute("""
      CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id TEXT NOT NULL,
        score INTEGER NOT NULL,
        passed INTEGER NOT NULL,
        at TEXT NOT NULL
      )
    """);
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_exams ON exams (subject_id, at)");
    db.execute("""
      CREATE TABLE IF NOT EXISTS notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        at TEXT NOT NULL,
        read INTEGER NOT NULL
      )
    """);
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_notices ON notices (kind, title, at)");
    db.execute("CREATE TABLE IF NOT EXISTS achievements (key TEXT PRIMARY KEY, at TEXT NOT NULL)");
    db.execute("""
      CREATE TABLE IF NOT EXISTS exam_drafts (
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
        started_at TEXT NOT NULL,
        saved_at TEXT
      )
    """);
    db.execute("""
      CREATE TABLE IF NOT EXISTS drill_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id TEXT NOT NULL,
        mistakes TEXT NOT NULL,
        at TEXT NOT NULL
      )
    """);
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_drill_runs ON drill_runs (item_id, at)");
    db.execute("""
      CREATE TABLE IF NOT EXISTS point_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id TEXT NOT NULL,
        step INTEGER NOT NULL,
        text TEXT NOT NULL,
        at TEXT NOT NULL
      )
    """);
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_point_notes ON point_notes (item_id, step, at)");
    db.execute("""
      CREATE TABLE IF NOT EXISTS rehearsals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id TEXT NOT NULL,
        missed TEXT NOT NULL,
        total INTEGER NOT NULL,
        at TEXT NOT NULL
      )
    """);
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_rehearsals ON rehearsals (item_id, at)");
    db.execute("""
      CREATE TABLE IF NOT EXISTS drill_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id TEXT NOT NULL,
        text TEXT NOT NULL,
        at TEXT NOT NULL
      )
    """);
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_drill_notes ON drill_notes (item_id, at)");
    db.execute("""
      CREATE TABLE IF NOT EXISTS outbox (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,
        key TEXT,
        payload TEXT NOT NULL,
        created_at TEXT NOT NULL
      )
    """);
    db.execute("CREATE TABLE IF NOT EXISTS sync_state (name TEXT PRIMARY KEY, value INTEGER NOT NULL)");
    // 归因字段与解析停留（主仓库 ADR 0076）：CREATE IF NOT EXISTS 不会给已有的表补列，手动加。
    void addColumn(String table, String column, String type) {
      final existing = db.select("PRAGMA table_info($table)").map((r) => r["name"] as String).toSet();
      if (!existing.contains(column)) db.execute("ALTER TABLE $table ADD COLUMN $column $type");
    }

    addColumn("attempts", "chosen", "TEXT");
    addColumn("attempts", "session_id", "TEXT");
    addColumn("attempts", "reason", "TEXT");
    addColumn("exams", "session_id", "TEXT");
    addColumn("exams", "used_ms", "INTEGER");
    addColumn("exam_drafts", "session_id", "TEXT");
    db.execute("""
      CREATE TABLE IF NOT EXISTS explain_views (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id TEXT NOT NULL,
        attempt_at TEXT NOT NULL,
        dwell_ms INTEGER NOT NULL
      )
    """);
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_explain_views ON explain_views (question_id, attempt_at)");
  }

  /// 点位卡照片与进度同住一处：工作树里在 `progress/points`（随仓库走），
  /// 发行副本在用户数据目录。照片文件与登记清单（photos.json）都不进数据库，
  /// 跨机器靠仓库（ADR 0037、0069）。
  /// 测试把照片目录重定向到自己的临时目录；生产为 null。
  static String? pointsDirOverride;

  static String get pointsDir {
    final overridden = pointsDirOverride;
    if (overridden != null) return overridden;
    final appRoot = workingTreeRoot();
    final base = appRoot != null ? p.join(appRoot, "progress") : userDataDir();
    final folder = Directory(p.join(base, "points"));
    folder.createSync(recursive: true);
    return folder.path;
  }

  /// 放用户数据的目录（本地进度库 local.db 与发行副本的照片都在这里）。
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
    return p.join(root, "AthenaDriver");
  }

  // ---------------------------------------------------------------- 写入（业务表 + outbox 同事务）

  /// 队列入队。可变数据按 key 折叠——同 key 只留最新一条（草稿每答一题存一次，
  /// 一场考试能排出一百条 PUT，而服务端本来就整份覆盖；save 与 delete 也靠折叠
  /// 互斥，最新意图生效）。read-all 是全局动作，只留一条。追加型资源每条都要
  /// 发，永不折叠。
  void _enqueue(String kind, {String? key, required Map<String, Object?> payload}) {
    if (key != null) {
      _db.execute("DELETE FROM outbox WHERE key = ?", [key]);
    } else if (kind == "read-all") {
      _db.execute("DELETE FROM outbox WHERE kind = 'read-all'");
    }
    _db.execute(
      "INSERT INTO outbox (kind, key, payload, created_at) VALUES (?, ?, ?, ?)",
      [kind, key, jsonEncode(payload), DateTime.now().toIso8601String()],
    );
    onEnqueued?.call();
  }

  /// 仅供测试：绕过正常写入路径直接入队一条（构造服务端必拒的记录，验证
  /// invalid 标死逻辑，ADR 0070）。生产代码不调用。
  @visibleForTesting
  void debugEnqueue(String kind, Map<String, Object?> payload) => _enqueue(kind, payload: payload);

  /// 仅供测试：attempts 原始行（断言 kind 场合标记与用时封顶，ADR 0057）。
  @visibleForTesting
  List<Map<String, Object?>> debugAttempts() =>
      _db.select("SELECT * FROM attempts ORDER BY at");

  @visibleForTesting
  List<Map<String, Object?>> debugExams() => _db.select("SELECT * FROM exams ORDER BY at");

  @visibleForTesting
  List<Map<String, Object?>> debugExplainViews() => _db.select("SELECT * FROM explain_views ORDER BY id");

  Future<List<Notice>> recordAttempt({
    required String questionId,
    required String topicId,
    required String subjectId,
    required bool correct,
    int durationMs = 0,
    String kind = "practice",
    String? chosen,
    String? sessionId,
    String? reason,
    String? topicTitle,
    DateTime? at,
  }) async {
    final stamp = (at ?? DateTime.now()).toIso8601String();
    // 单题用时封顶 5 分钟（ADR 0057）：中途挂机的时间不是答题时间，截断而非记天文值。
    final cappedMs = durationMs < 300000 ? durationMs : 300000;
    final beforeWrong = (await wrongQuestionIds()).length;
    _db.execute(
      "INSERT OR IGNORE INTO attempts (question_id, topic_id, subject_id, correct, duration_ms, hesitant, at, kind, "
      "chosen, session_id, reason) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)",
      [questionId, topicId, subjectId, correct ? 1 : 0, cappedMs, stamp, kind, chosen, sessionId, reason],
    );
    _enqueue("attempts", payload: {
      "question_id": questionId,
      "topic_id": topicId,
      "subject_id": subjectId,
      "correct": correct,
      "duration_ms": cappedMs,
      "hesitant": false,
      "at": stamp,
      "kind": kind,
      // 归因字段（主仓库 ADR 0076）：没有就不带，服务端存为空。
      "chosen": ?chosen,
      "session_id": ?sessionId,
      "reason": ?reason,
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

  /// 答错后看解析的停留（主仓库 ADR 0076 决策 4）。作答在判定时刻写入、停留在之后才知道，
  /// 所以单独成一个事件，按 (question_id, attempt_at) 对上那次作答；封顶 5 分钟，同 driver ADR 0057。
  Future<void> recordExplainView({
    required String questionId,
    required String attemptAt,
    required int dwellMs,
  }) async {
    final capped = dwellMs.clamp(0, 300000);
    _db.execute(
      "INSERT OR IGNORE INTO explain_views (question_id, attempt_at, dwell_ms) VALUES (?, ?, ?)",
      [questionId, attemptAt, capped],
    );
    _enqueue("explain-views", payload: {
      "question_id": questionId,
      "attempt_at": attemptAt,
      "dwell_ms": capped,
    });
  }

  Future<List<Notice>> recordExam({
    required String subjectId,
    required int score,
    required bool passed,
    String? sessionId,
    int? usedMs,
    String? subjectTitle,
    DateTime? at,
  }) async {
    final stamp = (at ?? DateTime.now()).toIso8601String();
    // 整场用时同样封顶在服务端的 24 小时上限内（挂机恢复的极端情形）。
    final cappedUsed = usedMs?.clamp(0, 24 * 3600 * 1000);
    _db.execute(
      "INSERT OR IGNORE INTO exams (subject_id, score, passed, at, session_id, used_ms) VALUES (?, ?, ?, ?, ?, ?)",
      [subjectId, score, passed ? 1 : 0, stamp, sessionId, cappedUsed],
    );
    _enqueue("exams", payload: {
      "subject_id": subjectId,
      "score": score,
      "passed": passed,
      "at": stamp,
      "session_id": ?sessionId,
      "used_ms": ?cappedUsed,
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
    // 调用方不关心存草稿的时刻（session 只填题目内容），这里统一落当前时间：
    // saved_at 是续答计时的截止线（ADR 0043），也是同步覆盖的判据（ADR 0068）。
    if (draft.savedAt == null) {
      draft = ExamDraft(
        subjectId: draft.subjectId,
        title: draft.title,
        questionIds: draft.questionIds,
        questionCount: draft.questionCount,
        minutes: draft.minutes,
        passScore: draft.passScore,
        pointsPerQuestion: draft.pointsPerQuestion,
        mix: draft.mix,
        fullBank: draft.fullBank,
        picked: draft.picked,
        startedAt: draft.startedAt,
        savedAt: DateTime.now(),
        sessionId: draft.sessionId,
      );
    }
    final row = draft.toApi();
    _db.execute(
      "INSERT INTO exam_drafts (draft_key, subject_id, title, question_ids, question_count, minutes, "
      "pass_score, points_per_question, mix, full_bank, picked, started_at, saved_at, session_id) "
      "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
      "ON CONFLICT (draft_key) DO UPDATE SET subject_id = excluded.subject_id, title = excluded.title, "
      "question_ids = excluded.question_ids, question_count = excluded.question_count, "
      "minutes = excluded.minutes, pass_score = excluded.pass_score, "
      "points_per_question = excluded.points_per_question, mix = excluded.mix, "
      "full_bank = excluded.full_bank, picked = excluded.picked, started_at = excluded.started_at, "
      "saved_at = excluded.saved_at, session_id = excluded.session_id",
      [
        draftKey, row["subject_id"], row["title"], row["question_ids"], row["question_count"],
        row["minutes"], row["pass_score"], row["points_per_question"], row["mix"],
        (row["full_bank"] as bool) ? 1 : 0, row["picked"], row["started_at"], row["saved_at"],
        row["session_id"],
      ],
    );
    _enqueue("exam-draft", key: draftKey, payload: row);
  }

  Future<ExamDraft?> loadExamDraft(String draftKey) async {
    final rows = _db.select("SELECT * FROM exam_drafts WHERE draft_key = ?", [draftKey]);
    if (rows.isEmpty) return null;
    final row = rows.first;
    return ExamDraft.fromApi({
      "subject_id": row["subject_id"],
      "title": row["title"],
      "question_ids": row["question_ids"],
      "question_count": row["question_count"],
      "minutes": row["minutes"],
      "pass_score": row["pass_score"],
      "points_per_question": row["points_per_question"],
      "mix": row["mix"],
      "full_bank": (row["full_bank"] as int) == 1,
      "picked": row["picked"],
      "started_at": row["started_at"],
      "saved_at": row["saved_at"],
      "session_id": row["session_id"],
    });
  }

  Future<void> clearExamDraft(String draftKey) async {
    _db.execute("DELETE FROM exam_drafts WHERE draft_key = ?", [draftKey]);
    _enqueue("exam-draft-delete", key: draftKey, payload: {});
  }

  Future<int> currentStreak() async {
    final rows = _db.select("SELECT correct FROM attempts ORDER BY at DESC, id DESC LIMIT 40");
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
    final rows = _db.select("SELECT COUNT(*) AS n FROM notices WHERE read = 0");
    return rows.first["n"] as int;
  }

  Future<List<Notice>> notices({int limit = 30}) async {
    final rows = _db.select("SELECT * FROM notices ORDER BY id DESC LIMIT ?", [limit]);
    return [for (final row in rows) _noticeFrom(row)];
  }

  Future<void> markAllRead() async {
    _db.execute("UPDATE notices SET read = 1 WHERE read = 0");
    // 服务端是「全部标已读」的动作语义，重复执行没有额外效果，全局折叠成一条。
    _enqueue("read-all", payload: {});
  }

  Future<Map<String, TopicStats>> topicStats() async {
    final rows = _db.select(
      "SELECT topic_id, COUNT(*) AS attempts, CAST(SUM(correct) AS INTEGER) AS correct "
      "FROM attempts GROUP BY topic_id",
    );
    return {
      for (final row in rows)
        row["topic_id"] as String: TopicStats(
          attempts: row["attempts"] as int,
          correct: row["correct"] as int,
        ),
    };
  }

  /// 最近 N 天每天的练习量，没练的天数补 0——柱子连不上就是断更了。
  Future<List<DailyCount>> dailyAttempts({int days = 14}) async {
    final today = DateTime.now();
    final since = DateTime(today.year, today.month, today.day).subtract(Duration(days: days - 1));
    final rows = _db.select("SELECT at, correct FROM attempts WHERE at >= ?", [since.toIso8601String()]);
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

  /// 每道题按作答时间取最近一次。不能按自增 id 取：并进来的是别处早先的作答，
  /// 入库晚、id 大，按 id 会把几小时前的一次答错当成最新，盖掉后来的答对（ADR 0030）。
  /// 本地 id 是各机自增，只在 at 完全相同时当并列断路器——极端并列下两台机器的
  /// 判定可能不同，但统计不受影响（ADR 0070 的已知取舍）。
  static const _latestAttempts = """
    SELECT question_id, correct, at, id FROM (
      SELECT question_id, correct, at, id,
        ROW_NUMBER() OVER (PARTITION BY question_id ORDER BY at DESC, id DESC) AS rn
      FROM attempts
    ) t WHERE rn = 1
  """;

  Future<List<String>> wrongQuestionIds() async {
    final rows = _db.select("""
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
    final rows = _db.select("""
      WITH last_wrong AS (
        SELECT question_id, at, id FROM (
          SELECT question_id, at, id,
            ROW_NUMBER() OVER (PARTITION BY question_id ORDER BY at DESC, id DESC) AS rn
          FROM attempts WHERE correct = 0
        ) t WHERE rn = 1
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
    final rows = _db.select(
      "SELECT question_id, COUNT(*) AS n FROM attempts WHERE correct = 0 GROUP BY question_id",
    );
    return {
      for (final row in rows) row["question_id"] as String: row["n"] as int,
    };
  }

  /// 全部作答（强化练习选题与学习建议用）。只取需要的四列；时间解析不了的行跳过。
  Future<List<AttemptView>> allAttempts() async {
    final rows = _db.select("SELECT question_id, topic_id, correct, at FROM attempts ORDER BY at, id");
    return [
      for (final row in rows)
        if (DateTime.tryParse(row["at"] as String? ?? "") case final at?)
          AttemptView(
            questionId: row["question_id"] as String,
            topicId: row["topic_id"] as String,
            correct: (row["correct"] as int?) == 1,
            at: at,
          ),
    ];
  }

  /// 最近几次模拟考的成绩，新的在前——记了不给人看，等于没记（主仓库 ADR 0052）。
  Future<List<ExamRecord>> recentExams({String? subjectId, int limit = 12}) async {
    final rows = subjectId == null
        ? _db.select("SELECT subject_id, score, passed, at FROM exams ORDER BY id DESC LIMIT ?", [limit])
        : _db.select(
            "SELECT subject_id, score, passed, at FROM exams WHERE subject_id = ? ORDER BY id DESC LIMIT ?",
            [subjectId, limit],
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

  /// 科目二的解锁线：最近 [steadyRuns] 场科目一模拟考都不低于 [steadyScore] 分（ADR 0047）。
  /// 百分制折合分就是正确率；只看最近几场而不看最高分——考过一次 95 不算稳，
  /// 连着几场都在 95 以上才算。[exams] 新的在前，可以混着别的科目。
  static const steadyScore = 95;
  static const steadyRuns = 3;

  static bool subject1Steady(List<ExamRecord> exams) {
    final recent = [for (final e in exams) if (e.subjectId == "subject1") e].take(steadyRuns).toList();
    return recent.length == steadyRuns && recent.every((e) => e.score >= steadyScore);
  }

  /// 最近一次答对、且没有明显慢于平时节奏。迟疑答对的题练习里还会再出。
  Future<Set<String>> masteredQuestionIds() async {
    final rows = _db.select("""
      SELECT a.question_id
      FROM ($_latestAttempts) a
      WHERE a.correct = 1
    """);
    return {for (final row in rows) row["question_id"] as String};
  }

  Future<int> averageDurationMs() async {
    final rows = _db.select("SELECT AVG(duration_ms) AS ms FROM attempts WHERE duration_ms > 0");
    final value = rows.first["ms"];
    if (value is num) return value.round();
    return 0;
  }

  Future<Map<String, int>> attemptCounts() async {
    final rows = _db.select("SELECT question_id, COUNT(*) AS n FROM attempts GROUP BY question_id");
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
    final existing = _db.select("SELECT 1 FROM achievements WHERE key = ?", [key]);
    if (existing.isNotEmpty) return null;
    final at = DateTime.now().toIso8601String();
    _db.execute("INSERT OR IGNORE INTO achievements (key, at) VALUES (?, ?)", [key, at]);
    _enqueue("achievement", key: key, payload: {"at": at});
    return _notice(kind: kind, title: title, body: body, at: at);
  }

  Future<Notice> _notice({
    required String kind,
    required String title,
    required String body,
    String? at,
  }) async {
    final stamp = at ?? DateTime.now().toIso8601String();
    _db.execute(
      "INSERT OR IGNORE INTO notices (kind, title, body, at, read) VALUES (?, ?, ?, ?, 0)",
      [kind, title, body, stamp],
    );
    final id = _db.select("SELECT id FROM notices WHERE kind = ? AND title = ? AND at = ?", [kind, title, stamp]);
    _enqueue("notices", payload: {"kind": kind, "title": title, "body": body, "at": stamp, "read": false});
    return Notice(id: id.isEmpty ? 0 : id.first["id"] as int, kind: kind, title: title, body: body, at: stamp, read: false);
  }

  Notice _noticeFrom(Row row) {
    return Notice(
      id: row["id"] as int,
      kind: row["kind"] as String,
      title: row["title"] as String,
      body: row["body"] as String,
      at: row["at"] as String,
      read: (row["read"] as int) == 1,
    );
  }

  /// 记一把练车。不写掌握度——掌握度只由答题写入（ADR 0036）。
  Future<void> recordDrillRun(String itemId, List<String> mistakes, {DateTime? at}) async {
    final stamp = (at ?? DateTime.now()).toIso8601String();
    _db.execute(
      "INSERT OR IGNORE INTO drill_runs (item_id, mistakes, at) VALUES (?, ?, ?)",
      [itemId, mistakes.join(","), stamp],
    );
    _enqueue("drill-runs", payload: {"item_id": itemId, "mistakes": mistakes.join(","), "at": stamp});
  }

  /// 练车记录，新的在前。
  Future<List<DrillRun>> drillRuns() async {
    final rows = _db.select("SELECT * FROM drill_runs ORDER BY at DESC, id DESC");
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

  Future<void> savePointNote(String itemId, int step, String text, {DateTime? at}) async {
    final stamp = (at ?? DateTime.now()).toIso8601String();
    _db.execute(
      "INSERT OR IGNORE INTO point_notes (item_id, step, text, at) VALUES (?, ?, ?, ?)",
      [itemId, step, text, stamp],
    );
    _enqueue("point-notes", payload: {"item_id": itemId, "step": step, "text": text, "at": stamp});
  }

  /// 每一步最新的一版文字，键是（项目, 步骤）。
  Future<Map<(String, int), PointNote>> pointNotes() async {
    final rows = _db.select("""
      SELECT item_id, step, text, at FROM (
        SELECT item_id, step, text, at,
          ROW_NUMBER() OVER (PARTITION BY item_id, step ORDER BY at DESC, id DESC) AS rn
        FROM point_notes
      ) t WHERE rn = 1
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

  // ---------------------------------------------------------------- 照片：清单文件随仓库走（ADR 0070），按用户一份（ADR 0071）

  /// 名字进文件名（本地库、照片清单）：替换路径非法字符。名字本身仍按原名存进
  /// 注册表与请求头，safe 名只做磁盘文件名。
  static String _fileSafe(String user) => user.replaceAll(RegExp(r'[/\\:*?"<>|]'), "_");

  /// 单用户时代（ADR 0070 落地当天）的 local.db / photos.json 收编为首用户的文件
  /// （ADR 0071）。本地优先版本尚未发行过，这只是防御：存在旧名且新名不存在时改名。
  static void adoptLegacyFiles(String user) {
    final legacy = File(p.join(userDataDir(), "local.db"));
    final modern = File(p.join(userDataDir(), "local-${_fileSafe(user)}.db"));
    if (legacy.existsSync() && !modern.existsSync()) legacy.renameSync(modern.path);
    final legacyPhotos = File(p.join(pointsDir, "photos.json"));
    final modernPhotos = File(p.join(pointsDir, "photos-${_fileSafe(user)}.json"));
    if (legacyPhotos.existsSync() && !modernPhotos.existsSync()) legacyPhotos.renameSync(modernPhotos.path);
  }

  String? _user;

  String get _photosManifest {
    final user = _user;
    return user == null
        ? p.join(pointsDir, "photos.json")
        : p.join(pointsDir, "photos-${_fileSafe(user)}.json");
  }

  List<PointPhoto> _loadPhotos() {
    final file = File(_photosManifest);
    if (!file.existsSync()) return const [];
    try {
      final list = jsonDecode(file.readAsStringSync()) as List<dynamic>;
      return [
        for (final entry in list)
          PointPhoto(
            itemId: entry["item_id"] as String,
            step: entry["step"] as int,
            file: entry["file"] as String,
            caption: entry["caption"] as String? ?? "",
            at: DateTime.tryParse(entry["at"] as String? ?? "") ?? DateTime.now(),
          ),
      ];
    } on FormatException {
      return const [];
    }
  }

  void _savePhotos(List<PointPhoto> photos) {
    final file = File(_photosManifest);
    file.createSync(recursive: true);
    file.writeAsStringSync(const JsonEncoder.withIndent("  ").convert([
      for (final photo in photos)
        {"item_id": photo.itemId, "step": photo.step, "file": photo.file, "caption": photo.caption, "at": photo.at.toIso8601String()},
    ]));
  }

  Future<void> addPointPhoto(String itemId, int step, String file, String caption) async {
    final photos = [..._loadPhotos()];
    photos.add(PointPhoto(itemId: itemId, step: step, file: file, caption: caption, at: DateTime.now()));
    _savePhotos(photos);
  }

  Future<List<PointPhoto>> pointPhotos() async => _loadPhotos();

  /// 删照片：删文件，登记行从清单里移除（清单随仓库走，删除对 git 可见）。
  Future<void> removePointPhoto(PointPhoto photo) async {
    _savePhotos([for (final entry in _loadPhotos()) if (entry.file != photo.file) entry]);
    final file = File(p.join(pointsDir, photo.file));
    if (await file.exists()) await file.delete();
  }

  Future<void> recordRehearsal(String itemId, List<int> missed, int total, {DateTime? at}) async {
    final stamp = (at ?? DateTime.now()).toIso8601String();
    _db.execute(
      "INSERT OR IGNORE INTO rehearsals (item_id, missed, total, at) VALUES (?, ?, ?, ?)",
      [itemId, missed.join(","), total, stamp],
    );
    _enqueue("rehearsals", payload: {"item_id": itemId, "missed": missed.join(","), "total": total, "at": stamp});
  }

  /// 默演记录，新的在前。
  Future<List<Rehearsal>> rehearsals() async {
    final rows = _db.select("SELECT * FROM rehearsals ORDER BY at DESC, id DESC");
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
    final stamp = (at ?? DateTime.now()).toIso8601String();
    _db.execute(
      "INSERT OR IGNORE INTO drill_notes (item_id, text, at) VALUES (?, ?, ?)",
      [itemId, text, stamp],
    );
    _enqueue("drill-notes", payload: {"item_id": itemId, "text": text, "at": stamp});
  }

  /// 教练的话，新的在前。
  Future<List<DrillNote>> drillNotes() async {
    final rows = _db.select("SELECT * FROM drill_notes ORDER BY at DESC, id DESC");
    return [
      for (final row in rows)
        DrillNote(itemId: row["item_id"] as String, text: row["text"] as String, at: DateTime.parse(row["at"] as String)),
    ];
  }

  Future<int> attemptTotal() async {
    final rows = _db.select("SELECT COUNT(*) AS n FROM attempts");
    return rows.first["n"] as int;
  }

  /// 全部成就（key -> 解锁时间串）。同步合并与测试用；界面将来展示成就也走这里。
  Map<String, String> achievements() {
    final rows = _db.select("SELECT key, at FROM achievements");
    return {for (final row in rows) row["key"] as String: row["at"] as String};
  }

  // ---------------------------------------------------------------- 同步器的协作面（ADR 0068 决策 4、ADR 0070）

  /// outbox 里待发送的条数（dead 除外）——界面显示「N 条待同步」的数据源。
  int pendingCount() {
    final rows = _db.select("SELECT COUNT(*) AS n FROM outbox WHERE kind != 'dead'");
    return rows.first["n"] as int;
  }

  /// 上传被服务端判 invalid 的条目单独标死：那是程序缺陷不是网络问题，
  /// 停止重试并显式暴露（ADR 0070 决策 4）。
  int deadCount() {
    final rows = _db.select("SELECT COUNT(*) AS n FROM outbox WHERE kind = 'dead'");
    return rows.first["n"] as int;
  }

  List<String> pendingKinds() {
    final rows = _db.select("SELECT DISTINCT kind FROM outbox WHERE kind != 'dead' ORDER BY id");
    return [for (final row in rows) row["kind"] as String];
  }

  /// 取某资源的头一批（≤[limit]，服务端批量上限 500）。按 id 単调保序：草稿的
  /// save 与 delete 不能乱序。同 key 已在 `_enqueue` 里折叠，这里只会拿到最新一条。
  List<OutboxEntry> outboxBatch(String kind, {int limit = 500}) {
    final rows = _db.select(
      "SELECT id, kind, key, payload FROM outbox WHERE kind = ? ORDER BY id LIMIT ?",
      [kind, limit],
    );
    return [
      for (final row in rows)
        OutboxEntry(
          id: row["id"] as int,
          kind: row["kind"] as String,
          key: row["key"] as String?,
          payload: (jsonDecode(row["payload"] as String) as Map<String, dynamic>).cast<String, Object?>(),
        ),
    ];
  }

  void outboxDelete(List<int> ids) {
    if (ids.isEmpty) return;
    final placeholders = List.filled(ids.length, "?").join(",");
    _db.execute("DELETE FROM outbox WHERE id IN ($placeholders)", ids);
  }

  void outboxMarkDead(int id) {
    _db.execute("UPDATE outbox SET kind = 'dead' WHERE id = ?", [id]);
  }

  /// 上传成功一条成就后：本地没有就带上，已有且本地更早就保留本地（服务端同样
  /// 取更早，两端收敛一致——ADR 0068「成就取更早时间」）。
  void applyRemoteAchievement(String key, String at) {
    _db.execute(
      "INSERT INTO achievements (key, at) VALUES (?, ?) "
      "ON CONFLICT (key) DO UPDATE SET at = excluded.at WHERE excluded.at < achievements.at",
      [key, at],
    );
  }

  /// 拉回的草稿合并：服务端 `saved_at` 更新才覆盖本地；[draft] 为 null 表示服务端
  /// 已没有这份草稿（别处交卷后删除），本地也删——但本地还有未上传的保存时不删，
  /// 那份更新很快会推上去。
  void applyRemoteDraft(String draftKey, ExamDraft? draft) {
    if (draft == null) {
      final pending = _db.select(
        "SELECT 1 FROM outbox WHERE kind = 'exam-draft' AND key = ?", [draftKey]);
      if (pending.isEmpty) {
        _db.execute("DELETE FROM exam_drafts WHERE draft_key = ?", [draftKey]);
      }
      return;
    }
    final rows = _db.select("SELECT saved_at FROM exam_drafts WHERE draft_key = ?", [draftKey]);
    final remoteAt = draft.savedAt;
    if (rows.isEmpty) {
      final row = draft.toApi();
      _db.execute(
        "INSERT OR REPLACE INTO exam_drafts (draft_key, subject_id, title, question_ids, question_count, "
        "minutes, pass_score, points_per_question, mix, full_bank, picked, started_at, saved_at, session_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
          draftKey, row["subject_id"], row["title"], row["question_ids"], row["question_count"],
          row["minutes"], row["pass_score"], row["points_per_question"], row["mix"],
          (row["full_bank"] as bool) ? 1 : 0, row["picked"], row["started_at"], row["saved_at"],
          row["session_id"],
        ],
      );
      return;
    }
    final localSaved = DateTime.tryParse(rows.first["saved_at"] as String? ?? "");
    if (remoteAt != null && (localSaved == null || remoteAt.isAfter(localSaved))) {
      final row = draft.toApi();
      _db.execute(
        "UPDATE exam_drafts SET subject_id = ?, title = ?, question_ids = ?, question_count = ?, "
        "minutes = ?, pass_score = ?, points_per_question = ?, mix = ?, full_bank = ?, "
        "picked = ?, started_at = ?, saved_at = ?, session_id = ? WHERE draft_key = ?",
        [
          row["subject_id"], row["title"], row["question_ids"], row["question_count"], row["minutes"],
          row["pass_score"], row["points_per_question"], row["mix"], (row["full_bank"] as bool) ? 1 : 0,
          row["picked"], row["started_at"], row["saved_at"], row["session_id"], draftKey,
        ],
      );
    }
  }

  /// 拉回的追加型记录并集合并：业务键唯一索引 + INSERT OR IGNORE，本机已有的
  /// 行（含自己刚上传的）自动跳过。各资源列名与中心一致，直接按表分发。
  void applyRemote(String resource, List<Map<String, Object?>> items) {
    switch (resource) {
      case "attempts":
        for (final item in items) {
          _db.execute(
            "INSERT OR IGNORE INTO attempts (question_id, topic_id, subject_id, correct, duration_ms, hesitant, at, kind, "
            "chosen, session_id, reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
              item["question_id"], item["topic_id"], item["subject_id"],
              (item["correct"] is bool) ? ((item["correct"]! as bool) ? 1 : 0) : item["correct"],
              item["duration_ms"] ?? 0,
              ((item["hesitant"] ?? false) as bool) ? 1 : 0,
              item["at"],
              item["kind"] ?? "practice",
              item["chosen"], item["session_id"], item["reason"],
            ],
          );
        }
      case "exams":
        for (final item in items) {
          _db.execute(
            "INSERT OR IGNORE INTO exams (subject_id, score, passed, at, session_id, used_ms) VALUES (?, ?, ?, ?, ?, ?)",
            [
              item["subject_id"], item["score"],
              (item["passed"] is bool) ? ((item["passed"]! as bool) ? 1 : 0) : item["passed"], item["at"],
              item["session_id"], item["used_ms"],
            ],
          );
        }
      case "explain-views":
        for (final item in items) {
          _db.execute(
            "INSERT OR IGNORE INTO explain_views (question_id, attempt_at, dwell_ms) VALUES (?, ?, ?)",
            [item["question_id"], item["attempt_at"], item["dwell_ms"]],
          );
        }
      case "notices":
        for (final item in items) {
          _db.execute(
            "INSERT OR IGNORE INTO notices (kind, title, body, at, read) VALUES (?, ?, ?, ?, ?)",
            [
              item["kind"], item["title"], item["body"], item["at"],
              ((item["read"] ?? false) as bool) ? 1 : 0,
            ],
          );
        }
      case "drill-runs":
        for (final item in items) {
          _db.execute(
            "INSERT OR IGNORE INTO drill_runs (item_id, mistakes, at) VALUES (?, ?, ?)",
            [item["item_id"], item["mistakes"], item["at"]],
          );
        }
      case "point-notes":
        for (final item in items) {
          _db.execute(
            "INSERT OR IGNORE INTO point_notes (item_id, step, text, at) VALUES (?, ?, ?, ?)",
            [item["item_id"], item["step"], item["text"], item["at"]],
          );
        }
      case "rehearsals":
        for (final item in items) {
          _db.execute(
            "INSERT OR IGNORE INTO rehearsals (item_id, missed, total, at) VALUES (?, ?, ?, ?)",
            [item["item_id"], item["missed"], item["total"], item["at"]],
          );
        }
      case "drill-notes":
        for (final item in items) {
          _db.execute(
            "INSERT OR IGNORE INTO drill_notes (item_id, text, at) VALUES (?, ?, ?)",
            [item["item_id"], item["text"], item["at"]],
          );
        }
    }
  }

  /// 各资源的增量拉取游标（中心自增 id，只升不回退）。首拉从 0 开始即全量。
  int cursor(String resource) {
    final rows = _db.select("SELECT value FROM sync_state WHERE name = ?", ["cursor.$resource"]);
    return rows.isEmpty ? 0 : rows.first["value"] as int;
  }

  void setCursor(String resource, int value) {
    _db.execute(
      "INSERT INTO sync_state (name, value) VALUES (?, ?) "
      "ON CONFLICT (name) DO UPDATE SET value = excluded.value",
      ["cursor.$resource", value],
    );
  }

  /// 本地已有的草稿 key（同步器除了按科目枚举，也把它们拉一遍）。
  List<String> localDraftKeys() {
    final rows = _db.select("SELECT draft_key FROM exam_drafts");
    return [for (final row in rows) row["draft_key"] as String];
  }

  Future<void> close() async {
    _db.dispose();
    final dir = _tempDir;
    if (dir != null) {
      try {
        dir.deleteSync(recursive: true);
      } on FileSystemException {
        // Windows 上 WAL 句柄偶尔迟一拍释放；留给系统临时目录自己回收。
      }
    }
  }
}
