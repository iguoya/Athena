class SourceRef {
  const SourceRef({
    required this.sourceId,
    required this.relation,
    required this.locator,
    required this.url,
    required this.note,
  });

  final String sourceId;
  final String relation;
  final String locator;
  final String url;
  final String note;

  factory SourceRef.fromJson(Map<String, dynamic> json) {
    return SourceRef(
      sourceId: json["source_id"] as String? ?? "",
      relation: json["relation"] as String? ?? "",
      locator: json["locator"] as String? ?? "",
      url: json["url"] as String? ?? "",
      note: json["note"] as String? ?? "",
    );
  }
}

class QuestionBand {
  static const hot = "hot";
  static const common = "common";
  static const regular = "regular";
  static const rare = "rare";

  static const labels = {
    hot: "高频",
    common: "常考",
    regular: "常规",
    rare: "偏难",
  };
}

class Choice {
  const Choice({required this.id, required this.label, required this.ok, this.sign});

  final String id;
  final String label;
  final bool ok;
  final String? sign;

  factory Choice.fromJson(Map<String, dynamic> json) {
    return Choice(
      id: json["id"] as String,
      label: json["label"] as String,
      ok: json["ok"] as bool,
      sign: json["sign"] as String?,
    );
  }
}

class Question {
  const Question({
    required this.id,
    required this.topicId,
    required this.kind,
    required this.prompt,
    required this.choices,
    required this.explain,
    required this.sourceRefs,
    this.sign,
    this.difficulty = 1,
    this.phase = 1,
    this.band = QuestionBand.regular,
  });

  final String id;
  final String topicId;
  final String kind;
  final String prompt;
  final List<Choice> choices;
  final String explain;
  final List<SourceRef> sourceRefs;
  final String? sign;
  final int difficulty;
  final int phase;
  final String band;

  bool get isHot => band == QuestionBand.hot;
  bool get isCommon => band == QuestionBand.common;
  bool get isRegular => band == QuestionBand.regular;
  bool get isRare => band == QuestionBand.rare;

  /// 常规、偏难怪在练习里少出；偏难怪默认不出，除非刚打错。
  bool get isRoutine => isRegular || isRare;

  bool get isMulti => kind == "multi";

  int get drawWeight => switch (band) {
    QuestionBand.hot => 4,
    QuestionBand.common => 2,
    QuestionBand.rare => 0,
    _ => 1,
  };

  bool appearsInPractice({required bool mastered, required bool wrong, int attempts = 0}) {
    if (mastered) return false;
    if (wrong) return true;
    if (isRare) return false;
    if (isHot || isCommon) return true;
    return attempts < 1;
  }

  /// 出处法条去重后的条目，带条款定位。
  List<String> get articleLines {
    final seen = <String>{};
    final lines = <String>[];
    for (final ref in sourceRefs) {
      final note = ref.note.trim();
      if (note.isEmpty || !seen.add(note)) continue;
      final loc = ref.locator.trim();
      lines.add(loc.isEmpty ? note : "$loc，$note");
    }
    return lines;
  }

  /// 先读题目解释，再读法条条目；两段相同只留一次。
  String get speakText {
    final parts = <String>[];
    final extra = explain.trim();
    if (extra.isNotEmpty) parts.add(extra);
    for (final line in articleLines) {
      if (line != extra) parts.add(line);
    }
    return parts.join(" ");
  }

  Set<String> get correctIds => {
    for (final choice in choices)
      if (choice.ok) choice.id,
  };

  factory Question.fromJson(Map<String, dynamic> json) {
    return Question(
      id: json["id"] as String,
      topicId: json["topic_id"] as String,
      kind: json["kind"] as String,
      prompt: json["prompt"] as String,
      choices: [
        for (final raw in json["choices"] as List<dynamic>)
          Choice.fromJson(raw as Map<String, dynamic>),
      ],
      explain: json["explain"] as String,
      sourceRefs: [
        for (final raw in json["source_refs"] as List<dynamic>)
          SourceRef.fromJson(raw as Map<String, dynamic>),
      ],
      sign: json["sign"] as String?,
      difficulty: json["difficulty"] as int? ?? 1,
      phase: json["phase"] as int? ?? 1,
      band: json["band"] as String? ?? QuestionBand.regular,
    );
  }
}

class Topic {
  const Topic({
    required this.id,
    required this.title,
    required this.difficulty,
    required this.masteryGoal,
    required this.knowledgeType,
    required this.requires,
  });

  final String id;
  final String title;
  final int difficulty;
  final String masteryGoal;
  final String knowledgeType;
  final List<String> requires;

  factory Topic.fromJson(Map<String, dynamic> json) {
    return Topic(
      id: json["id"] as String,
      title: json["title"] as String,
      difficulty: json["difficulty"] as int,
      masteryGoal: json["mastery_goal"] as String,
      knowledgeType: json["knowledge_type"] as String,
      requires: [
        for (final raw in json["requires"] as List<dynamic>) raw as String,
      ],
    );
  }
}

class ExamRules {
  const ExamRules({
    required this.questionCount,
    required this.minutes,
    required this.passScore,
    required this.pointsPerQuestion,
  });

  final int questionCount;
  final int minutes;
  final int passScore;
  final int pointsPerQuestion;

  factory ExamRules.fromJson(Map<String, dynamic> json) {
    return ExamRules(
      questionCount: json["question_count"] as int,
      minutes: json["minutes"] as int,
      passScore: json["pass_score"] as int,
      pointsPerQuestion: json["points_per_question"] as int,
    );
  }
}

class StudyPhase {
  const StudyPhase({required this.id, required this.title, this.plain = ""});

  final int id;
  final String title;
  final String plain;

  factory StudyPhase.fromJson(Map<String, dynamic> json) {
    return StudyPhase(
      id: json["id"] as int,
      title: json["title"] as String,
      plain: json["plain"] as String? ?? "",
    );
  }
}

class Subject {
  const Subject({
    required this.id,
    required this.code,
    required this.title,
    required this.exam,
    required this.topics,
    this.officialName,
    this.phases = const [],
  });

  final String id;
  final String code;
  final String title;
  final String? officialName;
  final ExamRules exam;
  final List<Topic> topics;
  final List<StudyPhase> phases;

  bool get gated => phases.length > 1;

  StudyPhase? phaseById(int id) {
    for (final phase in phases) {
      if (phase.id == id) return phase;
    }
    return null;
  }

  factory Subject.fromJson(Map<String, dynamic> json) {
    return Subject(
      id: json["id"] as String,
      code: json["code"] as String,
      title: json["title"] as String,
      officialName: json["official_name"] as String?,
      exam: ExamRules.fromJson(json["exam"] as Map<String, dynamic>),
      topics: [
        for (final raw in json["topics"] as List<dynamic>)
          Topic.fromJson(raw as Map<String, dynamic>),
      ],
      phases: [
        for (final raw in json["phases"] as List<dynamic>? ?? const [])
          StudyPhase.fromJson(raw as Map<String, dynamic>),
      ],
    );
  }
}

class Curriculum {
  const Curriculum({
    required this.title,
    required this.plainTitle,
    required this.scopeNote,
    required this.subjects,
  });

  final String title;
  final String plainTitle;
  final String scopeNote;
  final List<Subject> subjects;

  factory Curriculum.fromJson(Map<String, dynamic> json) {
    return Curriculum(
      title: json["title"] as String,
      plainTitle: json["plain_title"] as String,
      scopeNote: json["scope_note"] as String,
      subjects: [
        for (final raw in json["subjects"] as List<dynamic>)
          Subject.fromJson(raw as Map<String, dynamic>),
      ],
    );
  }

  Subject subject(String id) => subjects.firstWhere((item) => item.id == id);

  Topic? topic(String id) {
    for (final subject in subjects) {
      for (final item in subject.topics) {
        if (item.id == id) return item;
      }
    }
    return null;
  }
}

class RoadSign {
  const RoadSign({required this.id, required this.name, required this.kind, this.band = QuestionBand.common});

  final String id;
  final String name;
  final String kind;
  final String band;

  String get kindLabel => switch (kind) {
    "prohibit" => "禁令标志",
    "warning" => "警告标志",
    "indicate" => "指示标志",
    "guide" => "指路标志",
    _ => "交通标志",
  };

  factory RoadSign.fromJson(Map<String, dynamic> json) {
    return RoadSign(
      id: json["id"] as String,
      name: json["name"] as String,
      kind: json["kind"] as String,
      band: json["band"] as String? ?? QuestionBand.common,
    );
  }
}

class Bank {
  const Bank({required this.curriculum, required this.questions, this.signs = const []});

  final Curriculum curriculum;
  final List<Question> questions;
  final List<RoadSign> signs;

  List<Question> forSubject(String subjectId) {
    final ids = {
      for (final topic in curriculum.subject(subjectId).topics) topic.id,
    };
    final list = [for (final q in questions) if (ids.contains(q.topicId)) q];
    list.sort((a, b) {
      final byPhase = a.phase.compareTo(b.phase);
      return byPhase != 0 ? byPhase : a.difficulty.compareTo(b.difficulty);
    });
    return list;
  }

  List<Question> forTopic(String topicId) {
    final list = [for (final q in questions) if (q.topicId == topicId) q];
    list.sort((a, b) {
      final byPhase = a.phase.compareTo(b.phase);
      return byPhase != 0 ? byPhase : a.difficulty.compareTo(b.difficulty);
    });
    return list;
  }

  List<Question> forPhase(String subjectId, int phase) {
    return [for (final q in forSubject(subjectId)) if (q.phase == phase) q];
  }

  List<Question> unlocked(String subjectId, int through) {
    return [for (final q in forSubject(subjectId)) if (q.phase <= through) q];
  }

  Question byId(String id) => questions.firstWhere((q) => q.id == id);
}

/// 当前最高已开放阶段：前一阶段全部掌握才进入下一阶段。
int unlockedThrough(Iterable<Question> questions, Set<String> mastered) {
  var maxPhase = 1;
  for (final question in questions) {
    if (question.isRare) continue;
    if (question.phase > maxPhase) maxPhase = question.phase;
  }
  for (var phase = 1; phase <= maxPhase; phase++) {
    var any = false;
    var done = true;
    for (final question in questions) {
      if (question.isRare || question.phase != phase) continue;
      any = true;
      if (!mastered.contains(question.id)) done = false;
    }
    if (!any) continue;
    if (!done) return phase;
  }
  return maxPhase;
}

bool allMastered(Iterable<Question> questions, Set<String> mastered) {
  var any = false;
  for (final question in questions) {
    if (question.isRare) continue;
    any = true;
    if (!mastered.contains(question.id)) return false;
  }
  return any;
}

List<Question> dailyQuestions(Iterable<Question> questions) {
  return [for (final question in questions) if (!question.isRare) question];
}
