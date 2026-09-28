import "guide.dart";

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
  const Choice({required this.id, required this.label, required this.ok, this.sign, this.image});

  final String id;
  final String label;
  final bool ok;

  /// 自绘标志的 id；选项本身就是一个标志时用它。
  final String? sign;

  /// 选项配图在 content/ 下的相对路径——考场上四个选项各一张图的题靠它。
  final String? image;

  factory Choice.fromJson(Map<String, dynamic> json) {
    return Choice(
      id: json["id"] as String,
      label: json["label"] as String,
      ok: json["ok"] as bool,
      sign: json["sign"] as String?,
      image: json["image"] as String?,
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
    this.image,
    this.difficulty = 1,
    this.phase = 1,
    this.band = QuestionBand.regular,
    this.examBlock,
    this.errorRate,
  });

  final String id;
  final String topicId;
  final String kind;
  final String prompt;
  final List<Choice> choices;
  final String explain;
  final List<SourceRef> sourceRefs;
  final String? sign;

  /// 题图在 content/ 下的相对路径，例如 images/subject1/xxx.jpg。
  final String? image;
  final int difficulty;
  final int phase;
  final String band;

  /// 模拟考组卷时归哪一块（GA 1026 表 1）；空就按知识点的默认块（ADR 0023）。
  final String? examBlock;

  /// 公开题库给的全国错误率（百分数）；自己按条文写的题没有（ADR 0027）。
  final double? errorRate;

  /// 练习时标「易错」的门槛：约是最难的四分之一。
  static const errorProneRate = 20.0;

  bool get isErrorProne => (errorRate ?? 0) >= errorProneRate;

  bool get isHot => band == QuestionBand.hot;
  bool get isCommon => band == QuestionBand.common;
  bool get isRegular => band == QuestionBand.regular;
  bool get isRare => band == QuestionBand.rare;

  /// 稳定编号：题库 id 去掉 `drive.` 前缀（如 `s1.signals.207`）。任何页面、任何一轮都一样，
  /// 反馈题目问题时报这个号就能定位；「第几题」只是这一轮里的位置。
  String get serial => id.startsWith("drive.") ? id.substring("drive.".length) : id;

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
      // selection_basis 说的是「这题为什么收进来」，不是法条，不该念也不该显示在条文里。
      if (ref.relation == "selection_basis" ||
          ref.relation == "exam_alignment" ||
          ref.relation == "see_also") {
        continue;
      }
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
      image: json["image"] as String?,
      difficulty: json["difficulty"] as int? ?? 1,
      phase: json["phase"] as int? ?? 1,
      band: json["band"] as String? ?? QuestionBand.regular,
      examBlock: json["exam_block"] as String?,
      errorRate: (json["error_rate"] as num?)?.toDouble(),
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
    this.mix = const {},
    this.blocks = const {},
    this.topicBlocks = const {},
  });

  final int questionCount;
  final int minutes;
  final int passScore;
  final int pointsPerQuestion;

  /// 考场的题型配比（GA 1026）：科目一 40 判断 + 60 单选，科目四 20 判断 + 20 单选 + 10 多选。
  /// 空表示不限题型，按权重随机抽。
  final Map<String, int> mix;

  /// 考场的内容比例：块 -> 题数（GA 1026 表 1）。空表示不分块（ADR 0023）。
  final Map<String, int> blocks;

  /// 知识点 -> 默认块；题目自己标了 exam_block 的以题目为准。
  final Map<String, String> topicBlocks;

  String? blockOf(Question question) => question.examBlock ?? topicBlocks[question.topicId];

  factory ExamRules.fromJson(Map<String, dynamic> json) {
    final rawMix = json["mix"] as Map<String, dynamic>?;
    final rawBlocks = json["blocks"] as Map<String, dynamic>?;
    final rawTopicBlocks = json["topic_blocks"] as Map<String, dynamic>?;
    return ExamRules(
      questionCount: json["question_count"] as int,
      minutes: json["minutes"] as int,
      passScore: json["pass_score"] as int,
      pointsPerQuestion: json["points_per_question"] as int,
      mix: {
        for (final entry in (rawMix ?? const <String, dynamic>{}).entries)
          entry.key: entry.value as int,
      },
      blocks: {
        for (final entry in (rawBlocks ?? const <String, dynamic>{}).entries)
          entry.key: entry.value as int,
      },
      topicBlocks: {
        for (final entry in (rawTopicBlocks ?? const <String, dynamic>{}).entries)
          entry.key: entry.value as String,
      },
    );
  }
}

/// 一次模拟考的战绩。
class ExamRecord {
  const ExamRecord({
    required this.subjectId,
    required this.score,
    required this.passed,
    required this.at,
  });

  final String subjectId;
  final int score;
  final bool passed;
  final DateTime at;
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

  /// 笔试规则；科目二没有笔试，为空（ADR 0036）。
  final ExamRules? exam;
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
      exam: json["exam"] == null ? null : ExamRules.fromJson(json["exam"] as Map<String, dynamic>),
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

/// 易混数字对照页的一行：数字、适用情形、出处（ADR 0028）。
class CheatRow {
  const CheatRow({
    required this.value,
    required this.caseText,
    required this.sourceId,
    required this.locator,
    this.amount,
  });

  final String value;
  final String caseText;
  final String sourceId;
  final String locator;

  /// 画横条用的数值；区间、期限这类不好比大小的没有。
  final double? amount;

  factory CheatRow.fromJson(Map<String, dynamic> json) {
    return CheatRow(
      value: json["value"] as String,
      caseText: json["case"] as String,
      sourceId: json["source_id"] as String,
      locator: json["locator"] as String? ?? "",
      amount: (json["amount"] as num?)?.toDouble(),
    );
  }
}

/// 一组易混数字，外加按题面找相关题的匹配式。
class CheatGroup {
  const CheatGroup({
    required this.id,
    required this.title,
    required this.unit,
    required this.note,
    required this.match,
    required this.rows,
  });

  final String id;
  final String title;
  final String unit;
  final String note;
  final RegExp match;
  final List<CheatRow> rows;

  double get maxAmount => rows.fold(0, (m, r) => (r.amount ?? 0) > m ? r.amount! : m);

  /// 题干或选项里提到这组数字的题。
  List<Question> related(Iterable<Question> questions) => [
    for (final q in questions)
      if (match.hasMatch(q.prompt) || q.choices.any((c) => match.hasMatch(c.label))) q,
  ];

  factory CheatGroup.fromJson(Map<String, dynamic> json) {
    return CheatGroup(
      id: json["id"] as String,
      title: json["title"] as String,
      unit: json["unit"] as String? ?? "",
      note: json["note"] as String? ?? "",
      match: RegExp(json["match"] as String),
      rows: [
        for (final raw in json["rows"] as List<dynamic>) CheatRow.fromJson(raw as Map<String, dynamic>),
      ],
    );
  }
}

class Bank {
  const Bank({
    required this.curriculum,
    required this.questions,
    this.signs = const [],
    this.cheatsheet = const [],
    this.guide = Subject2Guide.empty,
  });

  final Curriculum curriculum;
  final Subject2Guide guide;
  final List<Question> questions;
  final List<RoadSign> signs;
  final List<CheatGroup> cheatsheet;

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

/// 同一档里按全国错误率从高到低排，先练大家最容易错的；没有错误率的按中位数算，
/// 不把按条文写的核心题压到最后（ADR 0027）。排序稳定，错误率相同的保持原顺序。
List<Question> hardestFirst(List<Question> questions) {
  final rates = [for (final q in questions) if (q.errorRate != null) q.errorRate!]..sort();
  final median = rates.isEmpty ? 0.0 : rates[rates.length ~/ 2];
  final indexed = [for (var i = 0; i < questions.length; i++) (i, questions[i])];
  indexed.sort((a, b) {
    final byRate = (b.$2.errorRate ?? median).compareTo(a.$2.errorRate ?? median);
    return byRate != 0 ? byRate : a.$1.compareTo(b.$1);
  });
  return [for (final (_, q) in indexed) q];
}

/// 一轮练习的出题顺序：错题、高频、常考、常规，同一档里先练全国错误率高的（ADR 0027）。
/// 每道题只出一次——答对就算掌握，同一轮里再出一遍是白做；「高频多练」靠排在前面
/// 和模拟考多抽体现，不靠重复（ADR 0031）。
List<Question> practiceQueue(List<Question> pending, Set<String> wrongIds) {
  final wrong = [for (final q in pending) if (wrongIds.contains(q.id)) q];
  final rest = [for (final q in pending) if (!wrongIds.contains(q.id)) q];
  return [
    ...hardestFirst(wrong),
    ...hardestFirst([for (final q in rest) if (q.isHot) q]),
    ...hardestFirst([for (final q in rest) if (q.isCommon) q]),
    ...hardestFirst([for (final q in rest) if (q.isRegular) q]),
  ];
}

/// 累计答错到几次进考前复习（ADR 0033）。
const reviewMinWrong = 2;

/// 移出考前复习要累计答对几次：比答错多 1～2 次（ADR 0035）。
/// 错 2 次多 1 次（对 3 次），错 3 次及以上多 2 次（错 3 对 5、错 8 对 10）。
/// 答对按累计算，错之前答对过的也算，所以错得再多也有出路，只是要多做几轮。
int reviewExitCorrect(int wrongCount) => wrongCount + (wrongCount >= 3 ? 2 : 1);

/// 这道题现在该不该留在考前复习：错够了次数，且还没做到「最近一次答对、
/// 累计答对够数」。[streak] 是最后一次错之后的连对次数，只用来判断最近一次对不对——
/// 刚答错的题哪怕累计答对够了也不放出去。
bool inReview({required int wrongCount, required int correctCount, required int streak}) =>
    wrongCount >= reviewMinWrong &&
    !(streak > 0 && correctCount >= reviewExitCorrect(wrongCount));

List<Question> dailyQuestions(Iterable<Question> questions) {
  return [for (final question in questions) if (!question.isRare) question];
}
