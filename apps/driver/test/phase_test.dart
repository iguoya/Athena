import "package:athena_driver/exam.dart";
import "package:athena_driver/models.dart";
import "package:flutter_test/flutter_test.dart";

Question _q(String id, {int phase = 1, String topic = "drive.s1.license", String band = QuestionBand.regular}) {
  return Question(
    id: id,
    topicId: topic,
    kind: "judge",
    prompt: "x",
    phase: phase,
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
  final s1 = [
    _q("a1", phase: 1),
    _q("a2", phase: 1),
    _q("b1", phase: 2),
    _q("c1", phase: 3, topic: "drive.s1.signals"),
    _q("d1", phase: 4, topic: "drive.s1.highway"),
    _q("rare", phase: 1, band: QuestionBand.rare),
  ];

  test("科目一从第1阶段开始，前一阶段全部掌握才打开下一阶段", () {
    expect(unlockedThrough(s1, {}), 1);
    expect(unlockedThrough(s1, {"a1"}), 1);
    expect(unlockedThrough(s1, {"a1", "a2"}), 2);
    expect(unlockedThrough(s1, {"a1", "a2", "b1"}), 3);
    expect(unlockedThrough(s1, {"a1", "a2", "b1", "c1"}), 4);
    expect(unlockedThrough(s1, {"a1", "a2", "b1", "c1", "d1"}), 4);
  });

  test("偏难怪题不挡过关，也不算科目一没学完", () {
    expect(unlockedThrough(s1, {"a1", "a2"}), 2);
    expect(allMastered(s1, {"a1", "a2", "b1", "c1", "d1"}), isTrue);
  });

  test("科目一没全部掌握，就不能算过关去开科目四", () {
    expect(allMastered(s1, {"a1", "a2", "b1", "c1"}), isFalse);
    expect(allMastered(s1, {"a1", "a2", "b1", "c1", "d1"}), isTrue);
    expect(allMastered(s1, {"a1", "a2", "b1", "c1", "d1", "extra"}), isTrue);
  });

  test("阶段测试时长按题量估，最短 8 分钟", () {
    expect(phaseTestMinutes(1), 8);
    expect(phaseTestMinutes(20), 9);
    expect(phaseTestMinutes(40), 18);
  });

  test("阶段测试按考场题量和配比抽，不把整阶段摊开", () {
    const exam = ExamRules(
      questionCount: 100,
      minutes: 45,
      passScore: 90,
      pointsPerQuestion: 1,
      mix: {"judge": 30, "single": 70},
    );
    final full = phaseExamRules(exam, 476);
    expect(full.questionCount, 100);
    expect(full.minutes, 45);
    expect(full.mix["judge"], 30);
    expect(full.mix["single"], 70);

    final short = phaseExamRules(exam, 40);
    expect(short.questionCount, 100);
    expect(short.minutes, phaseTestMinutes(40));
    expect(short.mix["single"], 70);
  });
}
