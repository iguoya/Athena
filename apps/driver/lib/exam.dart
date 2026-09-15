import "dart:math";

import "models.dart";

class Paper {
  const Paper({required this.questions, required this.rules, required this.fullBank});

  final List<Question> questions;
  final ExamRules rules;
  final bool fullBank;

  static Paper draw(List<Question> bank, ExamRules rules, Random random) {
    final pool = dailyQuestions(bank);
    final source = pool.isNotEmpty ? pool : [...bank];
    final bag = <Question>[
      for (final question in source)
        for (var i = 0; i < question.drawWeight; i++) question,
    ]..shuffle(random);
    final seen = <String>{};
    final picked = <Question>[];
    final take = min(rules.questionCount, source.length);
    for (final question in bag) {
      if (!seen.add(question.id)) continue;
      picked.add(question);
      if (picked.length >= take) break;
    }
    if (picked.length < take) {
      final rest = [for (final question in source) if (!seen.contains(question.id)) question]..shuffle(random);
      picked.addAll(rest.take(take - picked.length));
    }
    return Paper(
      questions: picked,
      rules: rules,
      fullBank: source.length >= rules.questionCount,
    );
  }

  /// 折合百分制，便于对照考场 90 分及格。
  int scaledScore(int correct) {
    if (questions.isEmpty) return 0;
    return ((correct / questions.length) * 100).round();
  }

  bool passed(int correct) => scaledScore(correct) >= rules.passScore;
}

int phaseTestMinutes(int count) {
  final minutes = (count * 27 / 60).ceil();
  return minutes < 8 ? 8 : minutes;
}

bool answersMatch(Question question, Set<String> selected) {
  return setEquals(selected, question.correctIds);
}

bool setEquals(Set<String> a, Set<String> b) {
  return a.length == b.length && a.containsAll(b);
}
