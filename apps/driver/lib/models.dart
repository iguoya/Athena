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

class Choice {
  const Choice({required this.id, required this.label, required this.ok});

  final String id;
  final String label;
  final bool ok;

  factory Choice.fromJson(Map<String, dynamic> json) {
    return Choice(
      id: json["id"] as String,
      label: json["label"] as String,
      ok: json["ok"] as bool,
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
  });

  final String id;
  final String topicId;
  final String kind;
  final String prompt;
  final List<Choice> choices;
  final String explain;
  final List<SourceRef> sourceRefs;
  final String? sign;

  bool get isMulti => kind == "multi";

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

class Subject {
  const Subject({
    required this.id,
    required this.code,
    required this.title,
    required this.exam,
    required this.topics,
    this.officialName,
  });

  final String id;
  final String code;
  final String title;
  final String? officialName;
  final ExamRules exam;
  final List<Topic> topics;

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

class Bank {
  const Bank({required this.curriculum, required this.questions});

  final Curriculum curriculum;
  final List<Question> questions;

  List<Question> forSubject(String subjectId) {
    final ids = {
      for (final topic in curriculum.subject(subjectId).topics) topic.id,
    };
    return [for (final q in questions) if (ids.contains(q.topicId)) q];
  }

  List<Question> forTopic(String topicId) => [
    for (final q in questions)
      if (q.topicId == topicId) q,
  ];

  Question byId(String id) => questions.firstWhere((q) => q.id == id);
}
