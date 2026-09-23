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
    final seen = <String>{};
    final picked = <Question>[];
    final take = min(rules.questionCount, source.length);

    /// 高频、常考的题在袋子里多放几份，抽中的机会更大。
    List<Question> weightedBag(bool Function(Question) accept) {
      return <Question>[
        for (final question in source)
          if (accept(question))
            for (var i = 0; i < question.drawWeight; i++) question,
      ]..shuffle(random);
    }

    void fill(Iterable<Question> bag, int want) {
      for (final question in bag) {
        if (picked.length >= want) break;
        if (!seen.add(question.id)) continue;
        picked.add(question);
      }
    }

    // 先照考场的题型配比抽：科目一判断 30 单选 70，科目四判断 10 单选 30 多选 10。
    var quota = 0;
    for (final entry in rules.mix.entries) {
      quota += entry.value;
      fill(weightedBag((q) => q.kind == entry.key), min(quota, take));
    }
    // 配比抽不满（某个题型题不够）就用剩下的补，宁可题型偏一点也要凑够题量。
    fill(weightedBag((_) => true), take);
    if (picked.length < take) {
      final rest = [for (final question in source) if (!seen.contains(question.id)) question]..shuffle(random);
      picked.addAll(rest.take(take - picked.length));
    }
    picked.shuffle(random);
    return Paper(
      questions: picked,
      rules: rules,
      fullBank: source.length >= rules.questionCount && _mixSatisfied(picked, rules),
    );
  }

  /// 题型配比有没有抽满——没抽满就不算「跟考场一样」，结果页要说明。
  static bool _mixSatisfied(List<Question> picked, ExamRules rules) {
    if (rules.mix.isEmpty) return true;
    for (final entry in rules.mix.entries) {
      if (picked.where((q) => q.kind == entry.key).length < entry.value) return false;
    }
    return true;
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

/// 阶段测试按考场口径抽：100 题、45 分钟、判断 30 / 单选 70、90 分及格。
/// 本阶段日常题不够 100 道时，时长按题量估，分数仍折合百分制。
ExamRules phaseExamRules(ExamRules exam, int poolSize) {
  final take = min(exam.questionCount, poolSize);
  return ExamRules(
    questionCount: exam.questionCount,
    minutes: take >= exam.questionCount ? exam.minutes : phaseTestMinutes(take),
    passScore: exam.passScore,
    pointsPerQuestion: exam.pointsPerQuestion,
    mix: exam.mix,
  );
}

bool answersMatch(Question question, Set<String> selected) {
  return setEquals(selected, question.correctIds);
}

bool setEquals(Set<String> a, Set<String> b) {
  return a.length == b.length && a.containsAll(b);
}
