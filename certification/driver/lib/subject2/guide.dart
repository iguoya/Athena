/// 科目二（C2）讲解与练车记录的数据（ADR 0036），内容在 `content/subject2.json`。
///
/// 评判条目和错因都带条款号，逐条对应 GA 1026—2022；错因能按考场规则给一把练车打分。
library;

import "dart:math" as math;
import "dart:ui";

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
  const GuideRule({
    required this.level,
    required this.text,
    required this.locator,
    required this.quote,
  });

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
  const Mistake({
    required this.id,
    required this.label,
    required this.level,
    required this.repeat,
    required this.locator,
  });

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

/// 车内这一眼：盯哪一对关系、新手会盯错的那一对、手脚做什么。
class StepInside {
  const StepInside({
    required this.look,
    required this.wrong,
    required this.action,
  });

  /// 这一步该盯的参照。和 [StepOutside.focus] 用同一种颜色画，是两格之间的关联。
  final String look;

  /// 新手本能会盯的错参照。空串表示这一步没有要画出来的错参照。
  final String wrong;

  /// 脚、挡、方向这一下做什么。
  final String action;

  factory StepInside.fromJson(Map<String, dynamic> json) => StepInside(
    look: json["look"] as String,
    wrong: json["wrong"] as String? ?? "",
    action: json["do"] as String,
  );
}

/// 车外这一眼：车身相对线在哪、这一下要防的结果。
class StepOutside {
  const StepOutside({required this.focus, required this.risk});

  final String focus;
  final String risk;

  factory StepOutside.fromJson(Map<String, dynamic> json) => StepOutside(
    focus: json["focus"] as String,
    risk: json["risk"] as String? ?? "",
  );
}

/// 这一步偏了之后的修正：看到什么迹象、手脚怎么动。不写死点位。
class StepFix {
  const StepFix({required this.sign, required this.action});

  final String sign;
  final String action;

  factory StepFix.fromJson(Map<String, dynamic> json) =>
      StepFix(sign: json["sign"] as String, action: json["action"] as String);
}

/// 一步上的一张真实图或动图，标记用 0～1 的归一化坐标，不烧进图片。
class StepShot {
  const StepShot({
    required this.file,
    required this.kind,
    required this.view,
    required this.caption,
    required this.note,
    required this.marks,
  });

  final String file;
  final String kind;
  final String view;
  final String caption;
  final String note;
  final List<StepMark> marks;

  factory StepShot.fromJson(Map<String, dynamic> json) {
    return StepShot(
      file: json["file"] as String? ?? "",
      kind: json["kind"] as String? ?? "image",
      view: json["view"] as String? ?? "",
      caption: json["caption"] as String? ?? "",
      note: json["note"] as String? ?? "",
      marks: [
        for (final raw in json["marks"] as List<dynamic>? ?? const [])
          StepMark.fromJson(raw as Map<String, dynamic>),
      ],
    );
  }
}

class StepMark {
  const StepMark({
    required this.type,
    required this.label,
    this.x = 0,
    this.y = 0,
    this.x1 = 0,
    this.y1 = 0,
    this.x2 = 0,
    this.y2 = 0,
  });

  final String type;
  final String label;
  final double x;
  final double y;
  final double x1;
  final double y1;
  final double x2;
  final double y2;

  factory StepMark.fromJson(Map<String, dynamic> json) {
    double n(String key) => (json[key] as num?)?.toDouble() ?? 0;
    return StepMark(
      type: json["type"] as String? ?? "point",
      label: json["label"] as String? ?? "",
      x: n("x"),
      y: n("y"),
      x1: n("x1"),
      y1: n("y1"),
      x2: n("x2"),
      y2: n("y2"),
    );
  }

  Offset at(Rect image) =>
      Offset(image.left + image.width * x, image.top + image.height * y);

  Offset from(Rect image) =>
      Offset(image.left + image.width * x1, image.top + image.height * y1);

  Offset to(Rect image) =>
      Offset(image.left + image.width * x2, image.top + image.height * y2);
}

/// 图在框里按 contain 放下之后的矩形。标记打在这张矩形上，才跟画面重合。
Rect fittedImageRect(Size box, Size image) {
  if (box.isEmpty || image.isEmpty) return Offset.zero & box;
  final scale = math.min(box.width / image.width, box.height / image.height);
  final width = image.width * scale;
  final height = image.height * scale;
  return Rect.fromLTWH(
    (box.width - width) / 2,
    (box.height - height) / 2,
    width,
    height,
  );
}

class GuideStep {
  const GuideStep({
    required this.title,
    required this.body,
    this.steer = "",
    this.reference = "",
    this.skill = "",
    this.fix = const [],
    this.caution = "",
    this.cautionLocators = const [],
    this.inside,
    this.outside,
    this.done = "",
    this.media = const [],
  });

  final String title;
  final String body;

  /// 方向盘：以什么迹象为时机、打多少、打多快、何时回。
  final String steer;

  /// 眼睛盯哪、什么关系算对。
  final String reference;

  /// 操作技巧。没有就不写。
  final String skill;

  /// 偏了怎么修，每步 0–2 条。
  final List<StepFix> fix;

  /// 实战注意：要不要停、要不要回、常见翻车点。扣分条款留在 [GuideItem.rules]。
  final String caution;
  final List<String> cautionLocators;

  /// 双视角。缺字段时界面仍只播原来的动画。
  final StepInside? inside;
  final StepOutside? outside;

  /// 怎样算这一步做完。念出来的完成口令。
  final String done;

  /// 真实图或动图。没有就是空，页面不占位。
  final List<StepShot> media;

  GuideStep withMedia(List<StepShot> media) => GuideStep(
    title: title,
    body: body,
    steer: steer,
    reference: reference,
    skill: skill,
    fix: fix,
    caution: caution,
    cautionLocators: cautionLocators,
    inside: inside,
    outside: outside,
    done: done,
    media: media,
  );

  /// 语音讲解的稿子。有双视角时先念车外全局，再念车内参照（T-003）。
  /// 方向盘、参照、修正留在数据里，页面由 T-007 承接，这里不改念稿。
  String narration(int index) {
    final head = "第${index + 1}步，$title。";
    final inside = this.inside;
    final outside = this.outside;
    if (inside == null || outside == null) {
      return [head, body, if (caution.isNotEmpty) "注意：$caution"].join("");
    }
    return [
      head,
      "车外：${outside.focus}",
      if (outside.risk.isNotEmpty) "扣分点：${outside.risk}",
      "车内看：${inside.look}",
      if (inside.wrong.isNotEmpty) "别按这个来：${inside.wrong}",
      "手脚：${inside.action}",
      if (done.isNotEmpty) "做完：$done",
      if (caution.isNotEmpty) "注意：$caution",
    ].join("");
  }

  factory GuideStep.fromJson(Map<String, dynamic> json) {
    final caution = json["caution"] as Map<String, dynamic>?;
    final inside = json["inside"] as Map<String, dynamic>?;
    final outside = json["outside"] as Map<String, dynamic>?;
    return GuideStep(
      title: json["title"] as String,
      body: json["body"] as String,
      steer: json["steer"] as String? ?? "",
      reference: json["reference"] as String? ?? "",
      skill: json["skill"] as String? ?? "",
      fix: [
        for (final f in json["fix"] as List<dynamic>? ?? const [])
          StepFix.fromJson(f as Map<String, dynamic>),
      ],
      caution: caution?["text"] as String? ?? "",
      cautionLocators: [
        for (final l in caution?["locators"] as List<dynamic>? ?? const [])
          l as String,
      ],
      inside: inside == null ? null : StepInside.fromJson(inside),
      outside: outside == null ? null : StepOutside.fromJson(outside),
      done: json["done"] as String? ?? "",
    );
  }
}

class GuideItem {
  const GuideItem({
    required this.id,
    required this.topicId,
    required this.title,
    required this.limitText,
    required this.limitSeconds,
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

  /// [limitText] 换算成的秒数（「3.5 分钟」→ 210），写「无时限」等就没有。给用时记录判超时用。
  final int? limitSeconds;

  /// 出线看什么：车身、车轮。
  final String judgedBy;
  final String requirementLocator;
  final String requirementQuote;
  final List<GuideRule> rules;
  final List<GuideStep> steps;
  final List<String> tips;
  final List<Mistake> mistakes;

  GuideItem withSteps(List<GuideStep> steps) => GuideItem(
    id: id,
    topicId: topicId,
    title: title,
    limitText: limitText,
    limitSeconds: limitSeconds,
    judgedBy: judgedBy,
    requirementLocator: requirementLocator,
    requirementQuote: requirementQuote,
    rules: rules,
    steps: steps,
    tips: tips,
    mistakes: mistakes,
  );

  factory GuideItem.fromJson(Map<String, dynamic> json) {
    final requirement = json["requirement"] as Map<String, dynamic>;
    return GuideItem(
      id: json["id"] as String,
      topicId: json["topic_id"] as String,
      title: json["title"] as String,
      limitText: json["limit_text"] as String,
      limitSeconds: limitSecondsOf(json["limit_text"] as String),
      judgedBy: json["judged_by"] as String,
      requirementLocator: requirement["locator"] as String,
      requirementQuote: requirement["quote"] as String,
      rules: [
        for (final r in json["rules"] as List<dynamic>)
          GuideRule.fromJson(r as Map<String, dynamic>),
      ],
      steps: [
        for (final s in json["steps"] as List<dynamic>)
          GuideStep.fromJson(s as Map<String, dynamic>),
      ],
      tips: [for (final t in json["tips"] as List<dynamic>) t as String],
      mistakes: [
        for (final m in json["mistakes"] as List<dynamic>)
          Mistake.fromJson(m as Map<String, dynamic>),
      ],
    );
  }
}

/// 时限文案换算成秒（「3.5 分钟」→ 210、「无时限」→ null）。判超时是仅有的用途。
int? limitSecondsOf(String text) {
  final m = RegExp(r"([\d.]+)\s*分钟").firstMatch(text);
  if (m == null) return null;
  final value = num.tryParse(m.group(1)!);
  return value == null || value <= 0 ? null : (value * 60).round();
}

/// 按考场规则给一把练车打的分。
class RunScore {
  const RunScore({
    required this.failed,
    required this.score,
    required this.passScore,
    required this.failReasons,
  });

  final bool failed;
  final int score;
  final int passScore;
  final List<String> failReasons;

  bool get passed => !failed && score >= passScore;

  String get label => failed ? "不合格" : "$score 分";
}

/// 项目手册顶部的「C2 怎么开科目二」：操作原理集中讲一次，经验要点，不写点位。
class C2Block {
  const C2Block({
    required this.title,
    required this.body,
    required this.locators,
  });

  final String title;
  final String body;
  final List<String> locators;

  factory C2Block.fromJson(Map<String, dynamic> json) => C2Block(
    title: json["title"] as String,
    body: json["body"] as String,
    locators: [for (final l in json["locators"] as List<dynamic>) l as String],
  );
}

class C2Guide {
  const C2Guide({
    required this.title,
    required this.note,
    required this.order,
    required this.blocks,
  });

  final String title;
  final String note;

  /// 学习顺序的项目 id：先易后难。考试顺序仍是 [Subject2Guide.items]。
  final List<String> order;
  final List<C2Block> blocks;

  static const empty = C2Guide(title: "", note: "", order: [], blocks: []);

  factory C2Guide.fromJson(Map<String, dynamic> json) => C2Guide(
    title: json["title"] as String,
    note: json["note"] as String,
    order: [for (final id in json["order"] as List<dynamic>) id as String],
    blocks: [
      for (final b in json["blocks"] as List<dynamic>)
        C2Block.fromJson(b as Map<String, dynamic>),
    ],
  );
}

/// 考前区的「考试日怎么走」：流程性知识，流程与顺序以考场现场为准（ADR 0036：
/// 判分边界之外的通用流程，挂条款的只有国标里有的那几句）。
class ExamDayStep {
  const ExamDayStep({
    required this.title,
    required this.body,
    required this.locators,
  });

  final String title;
  final String body;
  final List<String> locators;

  factory ExamDayStep.fromJson(Map<String, dynamic> json) => ExamDayStep(
    title: json["title"] as String,
    body: json["body"] as String,
    locators: [
      for (final l in (json["locators"] ?? []) as List<dynamic>) l as String,
    ],
  );
}

class ExamDayGuide {
  const ExamDayGuide({
    required this.title,
    required this.note,
    required this.steps,
  });

  final String title;
  final String note;
  final List<ExamDayStep> steps;

  static const empty = ExamDayGuide(title: "", note: "", steps: []);

  factory ExamDayGuide.fromJson(Map<String, dynamic> json) => ExamDayGuide(
    title: json["title"] as String,
    note: json["note"] as String,
    steps: [
      for (final s in json["steps"] as List<dynamic>)
        ExamDayStep.fromJson(s as Map<String, dynamic>),
    ],
  );
}

List<StepShot> _shotsOf(Object? itemRaw, int stepNumber) {
  if (itemRaw is! Map) return const [];
  final shots = itemRaw["$stepNumber"];
  if (shots is! List) return const [];
  return [
    for (final raw in shots)
      if (raw is Map) StepShot.fromJson(Map<String, dynamic>.from(raw)),
  ];
}

class Subject2Guide {
  const Subject2Guide({
    required this.fullScore,
    required this.passScore,
    required this.passLocator,
    required this.tipsNote,
    required this.generalRules,
    required this.generalMistakes,
    required this.c2,
    required this.examDay,
    required this.items,
  });

  final int fullScore;
  final int passScore;
  final String passLocator;
  final String tipsNote;
  final List<GuideRule> generalRules;
  final List<Mistake> generalMistakes;
  final C2Guide c2;

  /// 考试日的流程与兜底规则（当场补考、终止、签字）。
  final ExamDayGuide examDay;

  /// 考试顺序：倒车入库、侧方停车、曲线行驶、直角转弯。
  final List<GuideItem> items;

  static const empty = Subject2Guide(
    fullScore: 100,
    passScore: 80,
    passLocator: "",
    tipsNote: "",
    generalRules: [],
    generalMistakes: [],
    c2: C2Guide.empty,
    examDay: ExamDayGuide.empty,
    items: [],
  );

  factory Subject2Guide.fromJson(Map<String, dynamic> json) {
    final general = json["general"] as Map<String, dynamic>;
    return Subject2Guide(
      fullScore: json["full_score"] as int,
      passScore: json["pass_score"] as int,
      passLocator: json["pass_locator"] as String,
      tipsNote: json["tips_note"] as String,
      generalRules: [
        for (final r in general["rules"] as List<dynamic>)
          GuideRule.fromJson(r as Map<String, dynamic>),
      ],
      generalMistakes: [
        for (final m in general["mistakes"] as List<dynamic>)
          Mistake.fromJson(m as Map<String, dynamic>),
      ],
      c2: C2Guide.fromJson(json["c2"] as Map<String, dynamic>),
      examDay: json["exam_day"] == null
          ? ExamDayGuide.empty
          : ExamDayGuide.fromJson(json["exam_day"] as Map<String, dynamic>),
      items: [
        for (final i in json["items"] as List<dynamic>)
          GuideItem.fromJson(i as Map<String, dynamic>),
      ],
    );
  }

  /// [raw] 是 subject2_media.json。缺项、缺步都当没有，不抛错。步骤号从 1 起。
  Subject2Guide withMedia(Map<String, dynamic> raw) {
    return Subject2Guide(
      fullScore: fullScore,
      passScore: passScore,
      passLocator: passLocator,
      tipsNote: tipsNote,
      generalRules: generalRules,
      generalMistakes: generalMistakes,
      c2: c2,
      examDay: examDay,
      items: [
        for (final item in items)
          item.withSteps([
            for (var i = 0; i < item.steps.length; i++)
              item.steps[i].withMedia(_shotsOf(raw[item.id], i + 1)),
          ]),
      ],
    );
  }

  /// 手册上的四项：按 [c2] 的学习顺序，先易后难。
  List<GuideItem> get learnItems {
    final byId = {for (final item in items) item.id: item};
    return [for (final id in c2.order) byId[id]!];
  }

  GuideItem? item(String id) {
    for (final item in items) {
      if (item.id == id) return item;
    }
    return null;
  }

  /// 某一项能勾的错因：先本项专属，再通用。
  List<Mistake> mistakesFor(String itemId) => [
    ...?item(itemId)?.mistakes,
    ...generalMistakes,
  ];

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
    return RunScore(
      failed: fails.isNotEmpty,
      score: max0(score),
      passScore: passScore,
      failReasons: fails,
    );
  }

  static int max0(int v) => v < 0 ? 0 : v;
}
