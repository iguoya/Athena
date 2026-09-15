import "dart:io";

import "package:path/path.dart" as p;
import "package:path_provider/path_provider.dart";
import "package:sqflite_common_ffi/sqflite_ffi.dart";

class TopicStats {
  const TopicStats({required this.attempts, required this.correct});

  final int attempts;
  final int correct;

  double get rate => attempts == 0 ? 0 : correct / attempts;
}

class ProgressStore {
  ProgressStore(this._db);

  final Database _db;

  static Future<ProgressStore> open({String? path}) async {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
    final dbPath = path ?? await _defaultPath();
    final db = await databaseFactory.openDatabase(
      dbPath,
      options: OpenDatabaseOptions(version: 1, onCreate: _onCreate),
    );
    return ProgressStore(db);
  }

  static Future<String> _defaultPath() async {
    final support = await getApplicationSupportDirectory();
    final folder = Directory(p.join(support.path, "AthenaDriving"));
    await folder.create(recursive: true);
    return p.join(folder.path, "learning.db");
  }

  static Future<void> _onCreate(Database db, int version) async {
    await db.execute("""
      CREATE TABLE attempts (
        id INTEGER PRIMARY KEY,
        question_id TEXT NOT NULL,
        topic_id TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        correct INTEGER NOT NULL,
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

  Future<void> recordAttempt({
    required String questionId,
    required String topicId,
    required String subjectId,
    required bool correct,
  }) {
    return _db.insert("attempts", {
      "question_id": questionId,
      "topic_id": topicId,
      "subject_id": subjectId,
      "correct": correct ? 1 : 0,
      "at": DateTime.now().toIso8601String(),
    });
  }

  Future<void> recordExam({
    required String subjectId,
    required int score,
    required bool passed,
  }) {
    return _db.insert("exams", {
      "subject_id": subjectId,
      "score": score,
      "passed": passed ? 1 : 0,
      "at": DateTime.now().toIso8601String(),
    });
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
      SELECT question_id FROM attempts AS a
      WHERE correct = 0
        AND at = (SELECT MAX(at) FROM attempts WHERE question_id = a.question_id)
      ORDER BY at DESC
    """);
    return [for (final row in rows) row["question_id"] as String];
  }

  Future<void> close() => _db.close();
}
