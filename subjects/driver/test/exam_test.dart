import "dart:math";

import "package:athena_driver/exam.dart";
import "package:athena_driver/models.dart";
import "package:flutter_test/flutter_test.dart";

Question _q(
  String id, {
  String band = QuestionBand.regular,
  String kind = "judge",
  String topic = "drive.s1.license",
  String? block,
  double? rate,
}) {
  final choices = kind == "single"
      ? const [
          Choice(id: "A", label: "a", ok: true),
          Choice(id: "B", label: "b", ok: false),
          Choice(id: "C", label: "c", ok: false),
          Choice(id: "D", label: "d", ok: false),
        ]
      : const [
          Choice(id: "T", label: "正确", ok: true),
          Choice(id: "F", label: "错误", ok: false),
        ];
  return Question(
    id: id,
    topicId: topic,
    kind: kind,
    examBlock: block,
    errorRate: rate,
    prompt: "x",
    band: band,
    choices: choices,
    explain: "",
    sourceRefs: const [],
  );
}

void main() {
  const rules = ExamRules(
    questionCount: 100,
    minutes: 45,
    passScore: 90,
    pointsPerQuestion: 1,
  );

  test("题库不足时按现有题折合百分制", () {
    final paper = Paper(
      questions: List.generate(40, (i) => _q("q$i")),
      rules: rules,
      fullBank: false,
    );
    expect(paper.scaledScore(36), 90);
    expect(paper.passed(36), isTrue);
    expect(paper.passed(35), isFalse);
  });

  test("多选必须选齐才算对", () {
    final question = Question(
      id: "m",
      topicId: "drive.s4.emergency",
      kind: "multi",
      prompt: "x",
      choices: const [
        Choice(id: "A", label: "a", ok: true),
        Choice(id: "B", label: "b", ok: true),
        Choice(id: "C", label: "c", ok: false),
      ],
      explain: "",
      sourceRefs: const [],
    );
    expect(answersMatch(question, {"A", "B"}), isTrue);
    expect(answersMatch(question, {"A"}), isFalse);
    expect(answersMatch(question, {"A", "B", "C"}), isFalse);
  });

  test("模拟考不抽偏难怪，高频多于常规", () {
    final bank = [
      for (var i = 0; i < 30; i++) _q("hot$i", band: QuestionBand.hot),
      for (var i = 0; i < 30; i++) _q("reg$i"),
      for (var i = 0; i < 20; i++) _q("rare$i", band: QuestionBand.rare),
    ];
    const small = ExamRules(
      questionCount: 20,
      minutes: 10,
      passScore: 90,
      pointsPerQuestion: 1,
    );
    final paper = Paper.draw(bank, small, Random(7));
    expect(paper.questions.every((q) => !q.isRare), isTrue);
    final hot = paper.questions.where((q) => q.isHot).length;
    final regular = paper.questions.where((q) => q.isRegular).length;
    expect(hot, greaterThan(regular));
  });

  test("阶段测试从大题库只抽 100 题，判断 40 单选 60", () {
    const exam = ExamRules(
      questionCount: 100,
      minutes: 45,
      passScore: 90,
      pointsPerQuestion: 1,
      mix: {"judge": 40, "single": 60},
    );
    final bank = [
      for (var i = 0; i < 200; i++) _q("j$i"),
      for (var i = 0; i < 200; i++) _q("s$i", kind: "single"),
    ];
    final rules = phaseExamRules(exam, bank.length);
    final paper = Paper.draw(bank, rules, Random(1));
    expect(paper.questions, hasLength(100));
    expect(paper.questions.where((q) => q.kind == "judge").length, 40);
    expect(paper.questions.where((q) => q.kind == "single").length, 60);
  });

  test("偏难怪默认不进练习，打错才会再出", () {
    final rare = _q("r", band: QuestionBand.rare);
    expect(rare.appearsInPractice(mastered: false, wrong: false), isFalse);
    expect(rare.appearsInPractice(mastered: false, wrong: true), isTrue);
    final hot = _q("h", band: QuestionBand.hot);
    expect(hot.appearsInPractice(mastered: false, wrong: false), isTrue);
    expect(hot.appearsInPractice(mastered: true, wrong: false), isFalse);
  });

  test("科目一按 GA 1026 表 1 的内容块抽题，每块内判断、单选仍是 4:6", () {
    const blocked = ExamRules(
      questionCount: 100,
      minutes: 45,
      passScore: 90,
      pointsPerQuestion: 1,
      mix: {"judge": 40, "single": 60},
      blocks: {"license": 20, "traffic": 25, "penalty": 25, "accident": 10, "vehicle": 10, "local": 10},
      topicBlocks: {
        "drive.s1.license": "license",
        "drive.s1.rules": "traffic",
        "drive.s1.penalty": "penalty",
        "drive.s1.accident": "accident",
        "drive.s1.henan": "local",
      },
    );
    final cells = blockCells(blocked);
    expect(cells[("license", "judge")], 8);
    expect(cells[("license", "single")], 12);
    expect(cells[("traffic", "judge")], 10);
    expect(cells[("vehicle", "single")], 6);
    expect(cells.values.fold(0, (a, b) => a + b), 100);

    // 通行题占题库一大半，照样只抽 25 道；车辆知识题挂在通行知识点下，靠 exam_block 归块。
    final bank = [
      for (final (topic, n) in [
        ("drive.s1.license", 60),
        ("drive.s1.rules", 400),
        ("drive.s1.penalty", 60),
        ("drive.s1.accident", 30),
        ("drive.s1.henan", 30),
      ])
        for (var i = 0; i < n; i++) _q("$topic.$i", topic: topic, kind: i.isEven ? "judge" : "single"),
      for (var i = 0; i < 30; i++) _q("v$i", topic: "drive.s1.rules", block: "vehicle", kind: i.isEven ? "judge" : "single"),
    ];
    final paper = Paper.draw(bank, blocked, Random(3));
    expect(paper.questions, hasLength(100));
    int inBlock(String block) => paper.questions.where((q) => blocked.blockOf(q) == block).length;
    expect(inBlock("traffic"), 25);
    expect(inBlock("vehicle"), 10);
    expect(inBlock("local"), 10);
    expect(paper.questions.where((q) => q.kind == "judge").length, 40);
    expect(paper.fullBank, isTrue);
  });

  test("错到不可能及格的那一道就结束：科目一第 11 道，科目四第 6 道", () {
    expect(failingWrongCount(100, 90), 11);
    expect(failingWrongCount(50, 90), 6);
  });

  test("练习同档内按全国错误率从高到低，没有错误率的按中位数排（ADR 0027）", () {
    final ordered = hardestFirst([
      _q("a", rate: 5),
      _q("own"),
      _q("b", rate: 40),
      _q("c", rate: 12),
      _q("d", rate: 12),
    ]);
    // 中位数是 12：按条文写的题排在 12% 那一段，同分保持原顺序。
    expect([for (final q in ordered) q.id], ["b", "own", "c", "d", "a"]);
    expect(_q("x", rate: 20).isErrorProne, isTrue);
    expect(_q("y", rate: 19.9).isErrorProne, isFalse);
    expect(_q("z").isErrorProne, isFalse);
  });

  test("一轮练习每道题只出一次：错题、高频、常考、常规依次排（ADR 0031）", () {
    final pending = [
      _q("reg", band: QuestionBand.regular),
      _q("hot", band: QuestionBand.hot),
      _q("wrongHot", band: QuestionBand.hot),
      _q("common", band: QuestionBand.common),
      _q("wrongRare", band: QuestionBand.rare),
    ];
    final queue = practiceQueue(pending, {"wrongHot", "wrongRare"});
    final ids = [for (final q in queue) q.id];
    expect(ids.toSet().length, ids.length);
    expect(ids, ["wrongHot", "wrongRare", "hot", "common", "reg"]);
  });
}
