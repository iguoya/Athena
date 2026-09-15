import "dart:math";

import "models.dart";

class Paper {
  const Paper({required this.questions, required this.rules, required this.fullBank});

  final List<Question> questions;
  final ExamRules rules;
  final bool fullBank;

  static Paper draw(List<Question> bank, ExamRules rules, Random random) {
    final copy = [...bank]..shuffle(random);
    final take = min(rules.questionCount, copy.length);
    return Paper(
      questions: copy.take(take).toList(growable: false),
      rules: rules,
      fullBank: bank.length >= rules.questionCount,
    );
  }

  /// 折合百分制，便于对照考场 90 分及格。
  int scaledScore(int correct) {
    if (questions.isEmpty) return 0;
    return ((correct / questions.length) * 100).round();
  }

  bool passed(int correct) => scaledScore(correct) >= rules.passScore;
}

bool answersMatch(Question question, Set<String> selected) {
  return setEquals(selected, question.correctIds);
}

bool setEquals(Set<String> a, Set<String> b) {
  return a.length == b.length && a.containsAll(b);
}
