/// 科目二（C2）讲解与练车记录的数据（ADR 0036），内容在 `content/subject2.json`。
///
/// 评判条目和错因都带条款号，逐条对应 GA 1026—2022；错因能按考场规则给一把练车打分。
library;

/// 评判档位：不合格、扣 10 分、扣 5 分。
class Level {
  const Level._(this.raw);

  factory Level.parse(String raw) {
    if (raw != "fail" && raw != "-10" && raw != "-5") {
      throw FormatException("未知的评判档位：$raw");
    }
    return Level._(raw);
  }

  final String raw;

  bool get fails => raw == "fail";

  /// 扣几分；不合格为 0（不合格不看分数）。
  int get deduct => fails ? 0 : -int.parse(raw);

  String get label => fails ? "不合格" : "扣 $deduct 分";
}

class GuideRule {
  const GuideRule({required this.level, required this.text, required this.locator, required this.quote});

  final Level level;
  final String text;
  final String locator;

  /// 条款原句。
  final String quote;

  factory GuideRule.fromJson(Map<String, dynamic> json) => GuideRule(
        level: Level.parse(json["level"] as String),
        text: json["text"] as String,
        locator: json["locator"] as String,
        quote: json["quote"] as String,
      );
}

/// 练车时可能犯的一个错，对应一条评判条款。[repeat] 为真的按次计（中途停车每次扣 5 分）。
class Mistake {
  const Mistake({required this.id, required this.label, required this.level, required this.repeat, required this.locator});

  final String id;
  final String label;
  final Level level;
  final bool repeat;
  final String locator;

  factory Mistake.fromJson(Map<String, dynamic> json) => Mistake(
        id: json["id"] as String,
        label: json["label"] as String,
        level: Level.parse(json["level"] as String),
        repeat: json["repeat"] as bool? ?? false,
        locator: json["locator"] as String,
      );
}

class GuideStep {
  const GuideStep({required this.title, required this.body, this.caution = "", this.cautionLocators = const []});

  final String title;
  final String body;

  /// 注意事项：这一步最容易被判扣分或不合格的地方，逐条对应评判条款（ADR 0040）。
  final String caution;
  final List<String> cautionLocators;

  /// 语音讲解的稿子：第几步、做什么、注意什么（ADR 0040）。
  String narration(int index) => [
        "第${index + 1}步，$title。",
        body,
        if (caution.isNotEmpty) "注意：$caution",
      ].join("");

  factory GuideStep.fromJson(Map<String, dynamic> json) {
    final caution = json["caution"] as Map<String, dynamic>?;
    return GuideStep(
      title: json["title"] as String,
      body: json["body"] as String,
      caution: caution?["text"] as String? ?? "",
      cautionLocators: [for (final l in caution?["locators"] as List<dynamic>? ?? const []) l as String],
    );
  }
}

class GuideItem {
  const GuideItem({
    required this.id,
    required this.topicId,
    required this.title,
    required this.limitText,
    required this.judgedBy,
    required this.requirementLocator,
    required this.requirementQuote,
    required this.rules,
    required this.steps,
    required this.tips,
    required this.mistakes,
  });

  final String id;
  final String topicId;
  final String title;
  final String limitText;

  /// 出线看什么：车身、车轮。
  final String judgedBy;
  final String requirementLocator;
  final String requirementQuote;
  final List<GuideRule> rules;
  final List<GuideStep> steps;
  final List<String> tips;
  final List<Mistake> mistakes;

  factory GuideItem.fromJson(Map<String, dynamic> json) {
    final requirement = json["requirement"] as Map<String, dynamic>;
    return GuideItem(
      id: json["id"] as String,
      topicId: json["topic_id"] as String,
      title: json["title"] as String,
      limitText: json["limit_text"] as String,
      judgedBy: json["judged_by"] as String,
      requirementLocator: requirement["locator"] as String,
      requirementQuote: requirement["quote"] as String,
      rules: [for (final r in json["rules"] as List<dynamic>) GuideRule.fromJson(r as Map<String, dynamic>)],
      steps: [for (final s in json["steps"] as List<dynamic>) GuideStep.fromJson(s as Map<String, dynamic>)],
      tips: [for (final t in json["tips"] as List<dynamic>) t as String],
      mistakes: [for (final m in json["mistakes"] as List<dynamic>) Mistake.fromJson(m as Map<String, dynamic>)],
    );
  }
}

/// 按考场规则给一把练车打的分。
class RunScore {
  const RunScore({required this.failed, required this.score, required this.passScore, required this.failReasons});

  final bool failed;
  final int score;
  final int passScore;
  final List<String> failReasons;

  bool get passed => !failed && score >= passScore;

  String get label => failed ? "不合格" : "$score 分";
}

class Subject2Guide {
  const Subject2Guide({
    required this.fullScore,
    required this.passScore,
    required this.passLocator,
    required this.tipsNote,
    required this.generalRules,
    required this.generalMistakes,
    required this.items,
  });

  final int fullScore;
  final int passScore;
  final String passLocator;
  final String tipsNote;
  final List<GuideRule> generalRules;
  final List<Mistake> generalMistakes;
  final List<GuideItem> items;

  static const empty = Subject2Guide(
    fullScore: 100,
    passScore: 80,
    passLocator: "",
    tipsNote: "",
    generalRules: [],
    generalMistakes: [],
    items: [],
  );

  factory Subject2Guide.fromJson(Map<String, dynamic> json) {
    final general = json["general"] as Map<String, dynamic>;
    return Subject2Guide(
      fullScore: json["full_score"] as int,
      passScore: json["pass_score"] as int,
      passLocator: json["pass_locator"] as String,
      tipsNote: json["tips_note"] as String,
      generalRules: [for (final r in general["rules"] as List<dynamic>) GuideRule.fromJson(r as Map<String, dynamic>)],
      generalMistakes: [for (final m in general["mistakes"] as List<dynamic>) Mistake.fromJson(m as Map<String, dynamic>)],
      items: [for (final i in json["items"] as List<dynamic>) GuideItem.fromJson(i as Map<String, dynamic>)],
    );
  }

  GuideItem? item(String id) {
    for (final item in items) {
      if (item.id == id) return item;
    }
    return null;
  }

  /// 某一项能勾的错因：先本项专属，再通用。
  List<Mistake> mistakesFor(String itemId) => [...?item(itemId)?.mistakes, ...generalMistakes];

  Mistake? mistake(String itemId, String mistakeId) {
    for (final m in mistakesFor(itemId)) {
      if (m.id == mistakeId) return m;
    }
    return null;
  }

  /// 按考场规则打分：有一条不合格就不合格；否则满分减去扣分，[passScore] 及格（6.2.1）。
  /// [mistakeIds] 里同一个 id 可以出现多次（按次计的错）。认不出的 id 忽略——
  /// 错因清单改名后，旧记录不该让统计崩掉。
  RunScore score(String itemId, List<String> mistakeIds) {
    var score = fullScore;
    final fails = <String>[];
    for (final id in mistakeIds) {
      final m = mistake(itemId, id);
      if (m == null) continue;
      if (m.level.fails) {
        fails.add(m.label);
      } else {
        score -= m.level.deduct;
      }
    }
    return RunScore(failed: fails.isNotEmpty, score: max0(score), passScore: passScore, failReasons: fails);
  }

  static int max0(int v) => v < 0 ? 0 : v;
}
