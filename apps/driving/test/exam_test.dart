import "package:athena_driving/exam.dart";
import "package:athena_driving/models.dart";
import "package:flutter_test/flutter_test.dart";

Question _q(String id) {
  return Question(
    id: id,
    topicId: "drive.s1.license",
    kind: "judge",
    prompt: "x",
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
}
