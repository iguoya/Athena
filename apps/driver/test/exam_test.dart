import "dart:math";

import "package:athena_driver/exam.dart";
import "package:athena_driver/models.dart";
import "package:flutter_test/flutter_test.dart";

Question _q(String id, {String band = QuestionBand.regular}) {
  return Question(
    id: id,
    topicId: "drive.s1.license",
    kind: "judge",
    prompt: "x",
    band: band,
    choices: const [
      Choice(id: "T", label: "正确", ok: true),
      Choice(id: "F", label: "错误", ok: false),
    ],
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

  test("偏难怪默认不进练习，打错才会再出", () {
    final rare = _q("r", band: QuestionBand.rare);
    expect(rare.appearsInPractice(mastered: false, wrong: false), isFalse);
    expect(rare.appearsInPractice(mastered: false, wrong: true), isTrue);
    final hot = _q("h", band: QuestionBand.hot);
    expect(hot.appearsInPractice(mastered: false, wrong: false), isTrue);
    expect(hot.appearsInPractice(mastered: true, wrong: false), isFalse);
  });
}
