import "dart:async";
import "dart:convert";
import "dart:io";

import "package:path/path.dart" as p;
import "package:postgres/postgres.dart";

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
    this.savedAt,
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

  /// 上次停下之前已经答了多久。老草稿不知道，按 0 算——宁可少算，不把挂起的几天算进去。
  Duration get spent {
    final end = savedAt;
    if (end == null || end.isBefore(startedAt)) return Duration.zero;
    return end.difference(startedAt);
  }
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

/// postgres 驱动对 BIGINT（COUNT、IDENTITY）在不同小版本里可能给 int 或 String，
/// 计数与 ID 列统一从这里过，免得每处都写一遍类型分叉。
int _asInt(Object? value) {
  if (value is int) return value;
  if (value is String) return int.tryParse(value) ?? 0;
  if (value is double) return value.round();
  return 0;
}

/// ResultRow 自带 int 下标（继承 List），按列名取值要走 toColumnMap。
extension _RowByName on ResultRow {
  Object? at(String name) => toColumnMap()[name];
}

/// 把每条查询投回建立连接的 zone 执行。
///
/// flutter_test 的 fake-async zone 会接管 timer 与事件循环：页面代码在 fake
/// zone 里直接 await socket 查询，future 永远等不到 socket 事件。连接在哪个
/// zone 建立（生产同一 zone、widget 测试是 runAsync 的真实 zone），查询就在
/// 哪个 zone 跑——对生产行为无影响，测试里查询走真实事件循环，能真正完成。
class PinnedConnection {
  PinnedConnection(this._conn, this._zone);

  final Connection _conn;
  final Zone _zone;

  Future<Result> execute(Object query, {Map<String, Object?>? parameters}) {
    final sql = query is String ? Sql.named(query) : query as Sql;
    return _zone.run(() => _conn.execute(sql, parameters: parameters));
  }

  Future<void> close() => _zone.run(() => _conn.close());
}

/// 中心 PG 不可达（内网不通）。上层据此给出「纯在线」的诚实提示，
/// 不悄悄降级（ADR 0067 第 5 条）。外网场景不在这一层：数据库端口不出
/// 内网（ADR 0068），离开内网时就是本异常。
class ProgressUnavailable implements Exception {
  ProgressUnavailable(this.detail);

  final String detail;

  @override
  String toString() => "学习记录服务不可达：检查是否在内网、软路由是否在线。详情：$detail";
}

/// 连接配置还没填。上层（main 的启动门）据此弹配置对话框，不写默认密码
/// （ADR 0068：凭据不进仓库，每台机器各自配置）。
class ProgressNotConfigured implements Exception {
  @override
  String toString() => "数据库连接尚未配置";
}

/// 数据库连接参数。密码只存在这两个地方，绝不写进代码或仓库：
/// 环境变量 `ATHENA_DRIVER_DB`（完整 URI，脚本/CI 用）或用户数据目录的
/// `db.json`（对话框保存，POSIX 上 chmod 600）。
class DbConfig {
  const DbConfig({
    required this.host,
    required this.port,
    required this.database,
    required this.username,
    required this.password,
  });

  final String host;
  final int port;
  final String database;
  final String username;
  final String password;

  static String get _file => p.join(ProgressStore.userDataDir(), "db.json");

  static DbConfig? load() {
    final uri = Platform.environment["ATHENA_DRIVER_DB"];
    if (uri != null && uri.isNotEmpty) {
      final parsed = Uri.tryParse(uri);
      if (parsed != null && parsed.hasScheme) {
        return DbConfig(
          host: parsed.host,
          port: parsed.hasPort ? parsed.port : 5432,
          database: parsed.path.replaceFirst("/", ""),
          username: Uri.decodeComponent(parsed.userInfo.split(":").first),
          password: parsed.userInfo.contains(":")
              ? Uri.decodeComponent(parsed.userInfo.split(":").last)
              : "",
        );
      }
    }
    final file = File(_file);
    if (!file.existsSync()) return null;
    try {
      final map = jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
      return DbConfig(
        host: map["host"] as String,
        port: (map["port"] as num).toInt(),
        database: map["database"] as String,
        username: map["username"] as String,
        password: map["password"] as String,
      );
    } on FormatException {
      return null;
    }
  }

  /// 对话框「保存并连接」用。写完在 POSIX 上收紧权限；Windows 没有 chmod，
  /// 用户数据目录本身的 ACL 已按用户隔离。
  void save() {
    final file = File(_file);
    file.parent.createSync(recursive: true);
    file.writeAsStringSync(jsonEncode({
      "host": host,
      "port": port,
      "database": database,
      "username": username,
      "password": password,
    }));
    if (!Platform.isWindows) {
      Process.runSync("chmod", ["600", _file]);
    }
  }
}

class ProgressStore {
  ProgressStore(this._conn);

  final PinnedConnection _conn;

  static const _connectTimeout = Duration(seconds: 4);

  /// [suite] 供测试：连本机（或 CI 注入）PG 上属于该测试文件的独立库
  /// `athena_driver_test_<suite>`，打开时清空全部表——顶替原来「每个测试一个
  /// 临时 SQLite 文件」的隔离语义。一个测试文件一个库（ADR 0068），flutter
  /// test 并发跑不同文件时互不踩。测试不依赖软路由，账号是本地约定值。
  static Future<ProgressStore> open({String? suite}) async {
    final Endpoint endpoint;
    final ConnectionSettings settings;
    if (suite != null) {
      final uri = Platform.environment["ATHENA_DRIVER_TEST_DB"] ??
          "postgresql://athena_driver:athena_driver@localhost:5432/athena_driver_test";
      final parsed = Uri.parse(uri);
      final base = Endpoint(
        host: parsed.host,
        port: parsed.hasPort ? parsed.port : 5432,
        database: parsed.path.replaceFirst("/", ""),
        username: Uri.decodeComponent(parsed.userInfo.split(":").first),
        password: Uri.decodeComponent(parsed.userInfo.split(":").last),
      );
      final safe = suite.replaceAll(RegExp(r"[^a-zA-Z0-9_]"), "_");
      final database = "athena_driver_test_$safe";
      await _ensureDatabase(base, database);
      endpoint = Endpoint(
        host: base.host,
        port: base.port,
        database: database,
        username: base.username,
        password: base.password,
      );
      settings = const ConnectionSettings(sslMode: SslMode.disable);
    } else {
      final config = DbConfig.load();
      if (config == null) throw ProgressNotConfigured();
      endpoint = Endpoint(
        host: config.host,
        port: config.port,
        database: config.database,
        username: config.username,
        password: config.password,
      );
      // 驱动默认要求 SSL，软路由的 PG 没配证书；内网本身可信。
      settings = const ConnectionSettings(sslMode: SslMode.disable, connectTimeout: _connectTimeout);
    }

    final Connection conn;
    try {
      conn = await Connection.open(endpoint, settings: settings);
      await conn.execute("SELECT 1");
    } catch (error) {
      throw ProgressUnavailable("$error");
    }
    await _ensureSchema(conn);
    if (suite != null) await _clearAll(conn);
    // 查询固定在建立连接的 zone 里执行（见 PinnedConnection）：widget 测试里
    // 连接在 tester.runAsync 的真实 zone 建立，页面代码在 fake-async zone 发起
    // 的查询如果不投回真实 zone，socket 事件永远不会被 fake 时钟推进。
    return ProgressStore(PinnedConnection(conn, Zone.current));
  }

  /// 第一次用到某测试文件专属库时把它建出来。CREATE DATABASE 没有
  /// IF NOT EXISTS，两个文件同时首跑可能撞重复建库——撞上就算成功。
  static Future<void> _ensureDatabase(Endpoint base, String database) async {
    final admin = await Connection.open(
      base,
      settings: const ConnectionSettings(sslMode: SslMode.disable),
    );
    try {
      final exists = await admin.execute(
        Sql.named("SELECT 1 FROM pg_database WHERE datname = @name"),
        parameters: {"name": database},
      );
      if (exists.isEmpty) {
        try {
          await admin.execute('CREATE DATABASE "$database"');
        } on PgException catch (error) {
          if (!error.message.contains("already exists")) rethrow;
        }
      }
    } finally {
      await admin.close();
    }
  }

  /// 表结构按本地 SQLite 时代的 V9 现状一次建齐；迁移历史（V1→V9）不搬，
  /// 历史数据由 scripts/migrate_progress_to_pg.py 一次性导入（ADR 0067）。
  /// `at` 等时间列沿用 ISO 字符串存 TEXT——应用层只做字符串比较与解析，
  /// 不依赖数据库时区，跨机器也不受服务器时区影响。
  static Future<void> _ensureSchema(Connection conn) async {
    await conn.execute("""
      CREATE TABLE IF NOT EXISTS attempts (
        id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        question_id TEXT NOT NULL,
        topic_id TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        correct INTEGER NOT NULL,
        duration_ms INTEGER NOT NULL DEFAULT 0,
        hesitant INTEGER NOT NULL DEFAULT 0,
        at TEXT NOT NULL
      )
    """);
    await conn.execute("""
      CREATE TABLE IF NOT EXISTS exams (
        id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        subject_id TEXT NOT NULL,
        score INTEGER NOT NULL,
        passed INTEGER NOT NULL,
        at TEXT NOT NULL
      )
    """);
    await conn.execute("""
      CREATE TABLE IF NOT EXISTS notices (
        id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        kind TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        at TEXT NOT NULL,
        read INTEGER NOT NULL
      )
    """);
    await conn.execute("""
      CREATE TABLE IF NOT EXISTS achievements (
        key TEXT PRIMARY KEY,
        at TEXT NOT NULL
      )
    """);
    await conn.execute("""
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
    await conn.execute("""
      CREATE TABLE IF NOT EXISTS drill_runs (
        id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        item_id TEXT NOT NULL,
        mistakes TEXT NOT NULL,
        at TEXT NOT NULL
      )
    """);
    await conn.execute("""
      CREATE TABLE IF NOT EXISTS point_notes (
        id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        item_id TEXT NOT NULL,
        step INTEGER NOT NULL,
        text TEXT NOT NULL,
        at TEXT NOT NULL
      )
    """);
    await conn.execute("""
      CREATE TABLE IF NOT EXISTS point_photos (
        id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        item_id TEXT NOT NULL,
        step INTEGER NOT NULL,
        file TEXT NOT NULL,
        caption TEXT NOT NULL,
        at TEXT NOT NULL,
        removed INTEGER NOT NULL DEFAULT 0
      )
    """);
    await conn.execute("""
      CREATE TABLE IF NOT EXISTS rehearsals (
        id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        item_id TEXT NOT NULL,
        missed TEXT NOT NULL,
        total INTEGER NOT NULL,
        at TEXT NOT NULL
      )
    """);
    await conn.execute("""
      CREATE TABLE IF NOT EXISTS drill_notes (
        id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        item_id TEXT NOT NULL,
        text TEXT NOT NULL,
        at TEXT NOT NULL
      )
    """);
  }

  static Future<void> _clearAll(Connection conn) async {
    await conn.execute("""
      TRUNCATE attempts, exams, notices, achievements, exam_drafts,
        drill_runs, point_notes, point_photos, rehearsals, drill_notes
      RESTART IDENTITY
    """);
  }

  /// 点位卡照片与进度同住一处：工作树里在 `progress/points`（随仓库走），
  /// 发行副本在用户数据目录。照片文件本体不进数据库，跨机器靠仓库（ADR 0037）。
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

  /// 放用户数据的目录（发行包用；工作树里跑的时候进度在中心 PG）。
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

  Future<List<Notice>> recordAttempt({
    required String questionId,
    required String topicId,
    required String subjectId,
    required bool correct,
    int durationMs = 0,
    String? topicTitle,
    DateTime? at,
  }) async {
    final beforeWrong = (await wrongQuestionIds()).length;
    await _conn.execute(
      Sql.named(
        "INSERT INTO attempts (question_id, topic_id, subject_id, correct, duration_ms, hesitant, at) "
        "VALUES (@questionId, @topicId, @subjectId, @correct, @durationMs, 0, @at)",
      ),
      parameters: {
        "questionId": questionId,
        "topicId": topicId,
        "subjectId": subjectId,
        "correct": correct ? 1 : 0,
        "durationMs": durationMs,
        "at": (at ?? DateTime.now()).toIso8601String(),
      },
    );
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
    DateTime? at,
  }) async {
    await _conn.execute(
      Sql.named(
        "INSERT INTO exams (subject_id, score, passed, at) "
        "VALUES (@subjectId, @score, @passed, @at)",
      ),
      parameters: {
        "subjectId": subjectId,
        "score": score,
        "passed": passed ? 1 : 0,
        "at": (at ?? DateTime.now()).toIso8601String(),
      },
    );
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
    await _conn.execute(
      Sql.named(
        "INSERT INTO exam_drafts (draft_key, subject_id, title, question_ids, question_count, "
        "minutes, pass_score, points_per_question, mix, full_bank, picked, started_at, saved_at) "
        "VALUES (@draftKey, @subjectId, @title, @questionIds, @questionCount, @minutes, @passScore, "
        "@pointsPerQuestion, @mix, @fullBank, @picked, @startedAt, @savedAt) "
        "ON CONFLICT (draft_key) DO UPDATE SET subject_id = EXCLUDED.subject_id, "
        "title = EXCLUDED.title, question_ids = EXCLUDED.question_ids, "
        "question_count = EXCLUDED.question_count, minutes = EXCLUDED.minutes, "
        "pass_score = EXCLUDED.pass_score, points_per_question = EXCLUDED.points_per_question, "
        "mix = EXCLUDED.mix, full_bank = EXCLUDED.full_bank, picked = EXCLUDED.picked, "
        "started_at = EXCLUDED.started_at, saved_at = EXCLUDED.saved_at",
      ),
      parameters: {
        "draftKey": draftKey,
        "subjectId": draft.subjectId,
        "title": draft.title,
        "questionIds": jsonEncode(draft.questionIds),
        "questionCount": draft.questionCount,
        "minutes": draft.minutes,
        "passScore": draft.passScore,
        "pointsPerQuestion": draft.pointsPerQuestion,
        "mix": jsonEncode(draft.mix),
        "fullBank": draft.fullBank ? 1 : 0,
        "picked": jsonEncode({
          for (final entry in draft.picked.entries) "${entry.key}": entry.value.toList(),
        }),
        "startedAt": draft.startedAt.toIso8601String(),
        "savedAt": (draft.savedAt ?? DateTime.now()).toIso8601String(),
      },
    );
  }

  Future<ExamDraft?> loadExamDraft(String draftKey) async {
    final rows = await _conn.execute(
      Sql.named("SELECT * FROM exam_drafts WHERE draft_key = @key"),
      parameters: {"key": draftKey},
    );
    if (rows.isEmpty) return null;
    final row = rows.first;
    final pickedRaw = jsonDecode(row.at("picked") as String) as Map<String, dynamic>;
    return ExamDraft(
      subjectId: row.at("subject_id") as String,
      title: row.at("title") as String,
      questionIds: [for (final id in jsonDecode(row.at("question_ids") as String) as List<dynamic>) id as String],
      questionCount: row.at("question_count") as int,
      minutes: row.at("minutes") as int,
      passScore: row.at("pass_score") as int,
      pointsPerQuestion: row.at("points_per_question") as int,
      mix: {
        for (final entry in (jsonDecode(row.at("mix") as String) as Map<String, dynamic>).entries) entry.key: entry.value as int,
      },
      fullBank: (row.at("full_bank") as int) == 1,
      picked: {
        for (final entry in pickedRaw.entries)
          int.parse(entry.key): {for (final id in entry.value as List<dynamic>) id as String},
      },
      startedAt: DateTime.tryParse(row.at("started_at") as String? ?? "") ?? DateTime.now(),
      savedAt: DateTime.tryParse(row.at("saved_at") as String? ?? ""),
    );
  }

  Future<void> clearExamDraft(String draftKey) async {
    await _conn.execute(
      Sql.named("DELETE FROM exam_drafts WHERE draft_key = @key"),
      parameters: {"key": draftKey},
    );
  }

  Future<int> currentStreak() async {
    final rows = await _conn.execute("SELECT correct FROM attempts ORDER BY at DESC, id DESC LIMIT 40");
    var n = 0;
    for (final row in rows) {
      if ((row.at("correct") as int?) == 1) {
        n += 1;
      } else {
        break;
      }
    }
    return n;
  }

  Future<int> unreadCount() async {
    final rows = await _conn.execute("SELECT COUNT(*) AS n FROM notices WHERE read = 0");
    return _asInt(rows.first.at("n"));
  }

  Future<List<Notice>> notices({int limit = 30}) async {
    final rows = await _conn.execute(
      Sql.named("SELECT * FROM notices ORDER BY id DESC LIMIT @limit"),
      parameters: {"limit": limit},
    );
    return [for (final row in rows) _noticeFrom(row)];
  }

  Future<void> markAllRead() async {
    await _conn.execute("UPDATE notices SET read = 1 WHERE read = 0");
  }

  Future<Map<String, TopicStats>> topicStats() async {
    final rows = await _conn.execute("""
      SELECT topic_id, COUNT(*) AS attempts, SUM(correct)::int AS correct
      FROM attempts GROUP BY topic_id
    """);
    return {
      for (final row in rows)
        row.at("topic_id") as String: TopicStats(
          attempts: _asInt(row.at("attempts")),
          correct: _asInt(row.at("correct")),
        ),
    };
  }

  /// 最近 N 天每天的练习量，没练的天数补 0——柱子连不上就是断更了。
  Future<List<DailyCount>> dailyAttempts({int days = 14}) async {
    final today = DateTime.now();
    final since = DateTime(today.year, today.month, today.day).subtract(Duration(days: days - 1));
    final rows = await _conn.execute(
      Sql.named("SELECT at, correct FROM attempts WHERE at >= @since"),
      parameters: {"since": since.toIso8601String()},
    );
    String key(DateTime d) =>
        "${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}";
    final counts = <String, List<int>>{};
    for (final row in rows) {
      final at = DateTime.tryParse(row.at("at") as String? ?? "");
      if (at == null) continue;
      final entry = counts.putIfAbsent(key(at), () => [0, 0]);
      entry[0] += 1;
      if ((row.at("correct") as int?) == 1) entry[1] += 1;
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
  static const _latestAttempts = """
    SELECT question_id, correct, at, id FROM (
      SELECT question_id, correct, at, id,
        ROW_NUMBER() OVER (PARTITION BY question_id ORDER BY at DESC, id DESC) AS rn
      FROM attempts
    ) t WHERE rn = 1
  """;

  Future<List<String>> wrongQuestionIds() async {
    final rows = await _conn.execute("""
      SELECT a.question_id
      FROM ($_latestAttempts) a
      WHERE a.correct = 0
      ORDER BY a.at DESC, a.id DESC
    """);
    return [for (final row in rows) row.at("question_id") as String];
  }

  /// 每道答错过的题，最后一次答错之后又连着答对了几次（考前复习的移出判据，ADR 0034）。
  /// 「最后一次」跟 `_latestAttempts` 同一个排序：先按时间，时间相同按行号。
  Future<Map<String, int>> correctStreaksSinceWrong() async {
    final rows = await _conn.execute("""
      WITH last_wrong AS (
        SELECT question_id, at, id FROM (
          SELECT question_id, at, id,
            ROW_NUMBER() OVER (PARTITION BY question_id ORDER BY at DESC, id DESC) AS rn
          FROM attempts WHERE correct = 0
        ) t WHERE rn = 1
      )
      SELECT w.question_id, COUNT(a.id)::int AS n
      FROM last_wrong w
      LEFT JOIN attempts a
        ON a.question_id = w.question_id AND a.correct = 1
        AND (a.at > w.at OR (a.at = w.at AND a.id > w.id))
      GROUP BY w.question_id
    """);
    return {
      for (final row in rows) row.at("question_id") as String: _asInt(row.at("n")),
    };
  }

  /// 每道题累计答错过几次。考前最该刷的是反复栽跟头的题，不是最近错的那一道。
  Future<Map<String, int>> wrongCounts() async {
    final rows = await _conn.execute(
      "SELECT question_id, COUNT(*)::int AS n FROM attempts WHERE correct = 0 GROUP BY question_id",
    );
    return {
      for (final row in rows) row.at("question_id") as String: _asInt(row.at("n")),
    };
  }

  /// 最近几次模拟考的成绩，新的在前——记了不给人看，等于没记（主仓库 ADR 0052）。
  Future<List<ExamRecord>> recentExams({String? subjectId, int limit = 12}) async {
    final rows = subjectId == null
        ? await _conn.execute(
            Sql.named("SELECT subject_id, score, passed, at FROM exams ORDER BY id DESC LIMIT @limit"),
            parameters: {"limit": limit},
          )
        : await _conn.execute(
            Sql.named(
              "SELECT subject_id, score, passed, at FROM exams WHERE subject_id = @subjectId "
              "ORDER BY id DESC LIMIT @limit",
            ),
            parameters: {"subjectId": subjectId, "limit": limit},
          );
    return [
      for (final row in rows)
        ExamRecord(
          subjectId: row.at("subject_id") as String,
          score: row.at("score") as int,
          passed: (row.at("passed") as int) == 1,
          at: DateTime.tryParse(row.at("at") as String? ?? "") ?? DateTime.now(),
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
    final rows = await _conn.execute("""
      SELECT a.question_id
      FROM ($_latestAttempts) a
      WHERE a.correct = 1
    """);
    return {for (final row in rows) row.at("question_id") as String};
  }

  Future<int> averageDurationMs() async {
    // PG 的 AVG 是 NUMERIC，驱动给的不是 num——在 SQL 里转成 float8 再取整。
    final rows = await _conn.execute(
      "SELECT AVG(duration_ms)::float8 AS ms FROM attempts WHERE duration_ms > 0",
    );
    final value = rows.first.at("ms");
    if (value is num) return value.round();
    return 0;
  }

  Future<Map<String, int>> attemptCounts() async {
    final rows = await _conn.execute(
      "SELECT question_id, COUNT(*)::int AS n FROM attempts GROUP BY question_id",
    );
    return {
      for (final row in rows) row.at("question_id") as String: _asInt(row.at("n")),
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
    final existing = await _conn.execute(
      Sql.named("SELECT 1 FROM achievements WHERE key = @key"),
      parameters: {"key": key},
    );
    if (existing.isNotEmpty) return null;
    final at = DateTime.now().toIso8601String();
    await _conn.execute(
      Sql.named("INSERT INTO achievements (key, at) VALUES (@key, @at) ON CONFLICT (key) DO NOTHING"),
      parameters: {"key": key, "at": at},
    );
    return _notice(kind: kind, title: title, body: body, at: at);
  }

  Future<Notice> _notice({
    required String kind,
    required String title,
    required String body,
    String? at,
  }) async {
    final stamp = at ?? DateTime.now().toIso8601String();
    final result = await _conn.execute(
      Sql.named(
        "INSERT INTO notices (kind, title, body, at, read) "
        "VALUES (@kind, @title, @body, @at, 0) RETURNING id",
      ),
      parameters: {"kind": kind, "title": title, "body": body, "at": stamp},
    );
    return Notice(id: _asInt(result.first.at("id")), kind: kind, title: title, body: body, at: stamp, read: false);
  }

  Notice _noticeFrom(ResultRow row) {
    return Notice(
      id: _asInt(row.at("id")),
      kind: row.at("kind") as String,
      title: row.at("title") as String,
      body: row.at("body") as String,
      at: row.at("at") as String,
      read: (row.at("read") as int) == 1,
    );
  }

  /// 记一把练车。不写掌握度——掌握度只由答题写入（ADR 0036）。
  Future<void> recordDrillRun(String itemId, List<String> mistakes, {DateTime? at}) async {
    await _conn.execute(
      Sql.named(
        "INSERT INTO drill_runs (item_id, mistakes, at) VALUES (@itemId, @mistakes, @at)",
      ),
      parameters: {
        "itemId": itemId,
        "mistakes": mistakes.join(","),
        "at": (at ?? DateTime.now()).toIso8601String(),
      },
    );
  }

  /// 练车记录，新的在前。
  Future<List<DrillRun>> drillRuns() async {
    final rows = await _conn.execute("SELECT * FROM drill_runs ORDER BY at DESC, id DESC");
    return [
      for (final row in rows)
        DrillRun(
          itemId: row.at("item_id") as String,
          mistakes: [
            for (final id in (row.at("mistakes") as String).split(","))
              if (id.isNotEmpty) id,
          ],
          at: DateTime.parse(row.at("at") as String),
        ),
    ];
  }

  Future<void> savePointNote(String itemId, int step, String text, {DateTime? at}) async {
    await _conn.execute(
      Sql.named("INSERT INTO point_notes (item_id, step, text, at) VALUES (@itemId, @step, @text, @at)"),
      parameters: {
        "itemId": itemId,
        "step": step,
        "text": text,
        "at": (at ?? DateTime.now()).toIso8601String(),
      },
    );
  }

  /// 每一步最新的一版文字，键是（项目, 步骤）。
  Future<Map<(String, int), PointNote>> pointNotes() async {
    final rows = await _conn.execute("""
      SELECT item_id, step, text, at FROM (
        SELECT item_id, step, text, at,
          ROW_NUMBER() OVER (PARTITION BY item_id, step ORDER BY at DESC, id DESC) AS rn
        FROM point_notes
      ) t WHERE rn = 1
    """);
    return {
      for (final row in rows)
        (row.at("item_id") as String, row.at("step") as int): PointNote(
          itemId: row.at("item_id") as String,
          step: row.at("step") as int,
          text: row.at("text") as String,
          at: DateTime.parse(row.at("at") as String),
        ),
    };
  }

  Future<void> addPointPhoto(String itemId, int step, String file, String caption) async {
    await _conn.execute(
      Sql.named(
        "INSERT INTO point_photos (item_id, step, file, caption, at) "
        "VALUES (@itemId, @step, @file, @caption, @at)",
      ),
      parameters: {
        "itemId": itemId,
        "step": step,
        "file": file,
        "caption": caption,
        "at": DateTime.now().toIso8601String(),
      },
    );
  }

  Future<List<PointPhoto>> pointPhotos() async {
    final rows = await _conn.execute("SELECT * FROM point_photos WHERE removed = 0 ORDER BY at, id");
    return [
      for (final row in rows)
        PointPhoto(
          id: _asInt(row.at("id")),
          itemId: row.at("item_id") as String,
          step: row.at("step") as int,
          file: row.at("file") as String,
          caption: row.at("caption") as String,
          at: DateTime.parse(row.at("at") as String),
        ),
    ];
  }

  /// 删照片：删文件，记录标记删除。
  Future<void> removePointPhoto(PointPhoto photo) async {
    await _conn.execute(
      Sql.named("UPDATE point_photos SET removed = 1 WHERE id = @id"),
      parameters: {"id": photo.id},
    );
    final file = File(p.join(pointsDir, photo.file));
    if (await file.exists()) await file.delete();
  }

  Future<void> recordRehearsal(String itemId, List<int> missed, int total, {DateTime? at}) async {
    await _conn.execute(
      Sql.named(
        "INSERT INTO rehearsals (item_id, missed, total, at) VALUES (@itemId, @missed, @total, @at)",
      ),
      parameters: {
        "itemId": itemId,
        "missed": missed.join(","),
        "total": total,
        "at": (at ?? DateTime.now()).toIso8601String(),
      },
    );
  }

  /// 默演记录，新的在前。
  Future<List<Rehearsal>> rehearsals() async {
    final rows = await _conn.execute("SELECT * FROM rehearsals ORDER BY at DESC, id DESC");
    return [
      for (final row in rows)
        Rehearsal(
          itemId: row.at("item_id") as String,
          missed: [
            for (final s in (row.at("missed") as String).split(","))
              if (s.isNotEmpty) int.parse(s),
          ],
          total: row.at("total") as int,
          at: DateTime.parse(row.at("at") as String),
        ),
    ];
  }

  Future<void> recordDrillNote(String itemId, String text, {DateTime? at}) async {
    await _conn.execute(
      Sql.named("INSERT INTO drill_notes (item_id, text, at) VALUES (@itemId, @text, @at)"),
      parameters: {
        "itemId": itemId,
        "text": text,
        "at": (at ?? DateTime.now()).toIso8601String(),
      },
    );
  }

  /// 教练的话，新的在前。
  Future<List<DrillNote>> drillNotes() async {
    final rows = await _conn.execute("SELECT * FROM drill_notes ORDER BY at DESC, id DESC");
    return [
      for (final row in rows)
        DrillNote(itemId: row.at("item_id") as String, text: row.at("text") as String, at: DateTime.parse(row.at("at") as String)),
    ];
  }

  Future<int> attemptTotal() async {
    final rows = await _conn.execute("SELECT COUNT(*) AS n FROM attempts");
    return _asInt(rows.first.at("n"));
  }

  Future<void> close() => _conn.close();
}
