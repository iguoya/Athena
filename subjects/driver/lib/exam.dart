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

    int count(bool Function(Question) accept) => picked.where(accept).length;

    /// 从袋子里往卷子上加题，直到满足 accept 的题有 want 道（或整卷够数）。
    void fill(bool Function(Question) accept, int want, [bool Function(Question)? from]) {
      for (final question in weightedBag(from ?? accept)) {
        if (picked.length >= take || count(accept) >= want) break;
        if (!seen.add(question.id)) continue;
        picked.add(question);
      }
    }

    // 先按内容块 × 题型的格子抽（ADR 0023）；题库不够一整卷时不分块，免得格子比题还多。
    final cells = source.length >= rules.questionCount ? blockCells(rules) : const <(String, String), int>{};
    for (final entry in cells.entries) {
      final (block, kind) = entry.key;
      fill((q) => rules.blockOf(q) == block && q.kind == kind, entry.value);
    }
    // 某格不够：先用同块的其他题型补足这一块。
    for (final entry in rules.blocks.entries) {
      if (cells.isEmpty) break;
      fill((q) => rules.blockOf(q) == entry.key, entry.value);
    }
    // 再照考场的题型配比抽（GA 1026—2022 4.1.3.1、4.3.2.3.1）：科目一判断 40 单选 60，
    // 科目四判断 20 单选 20 多选 10。
    for (final entry in rules.mix.entries) {
      fill((q) => q.kind == entry.key, entry.value);
    }
    // 配比抽不满（某个题型题不够）就用剩下的补，宁可题型偏一点也要凑够题量。
    fill((_) => true, take);
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

  /// 题型配比、内容比例有没有抽满——没抽满就不算「跟考场一样」，结果页要说明。
  static bool _mixSatisfied(List<Question> picked, ExamRules rules) {
    for (final entry in rules.mix.entries) {
      if (picked.where((q) => q.kind == entry.key).length < entry.value) return false;
    }
    for (final entry in rules.blocks.entries) {
      if (picked.where((q) => rules.blockOf(q) == entry.key).length < entry.value) return false;
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

/// 每块的题数按题型配比拆成格子：块内判断、单选的比例跟整卷一致，
/// 取整的零头按余数大小补，保证每块合计和每种题型合计都不走样。
Map<(String, String), int> blockCells(ExamRules rules) {
  if (rules.blocks.isEmpty || rules.mix.isEmpty) return const {};
  final total = rules.mix.values.fold(0, (a, b) => a + b);
  final cells = <(String, String), int>{};
  final remainders = <((String, String), double)>[];
  for (final block in rules.blocks.entries) {
    for (final kind in rules.mix.entries) {
      final exact = block.value * kind.value / total;
      cells[(block.key, kind.key)] = exact.floor();
      remainders.add(((block.key, kind.key), exact - exact.floor()));
    }
  }
  remainders.sort((a, b) => b.$2.compareTo(a.$2));
  int blockSum(String block) => cells.entries.where((e) => e.key.$1 == block).fold(0, (a, e) => a + e.value);
  int kindSum(String kind) => cells.entries.where((e) => e.key.$2 == kind).fold(0, (a, e) => a + e.value);
  for (final (cell, _) in remainders) {
    if (blockSum(cell.$1) < rules.blocks[cell.$1]! && kindSum(cell.$2) < rules.mix[cell.$2]!) {
      cells[cell] = cells[cell]! + 1;
    }
  }
  return cells;
}

/// 错到第几道就不可能及格了——考场到这一道当场结束（ADR 0023）。
/// 按折合百分制算：科目一 100 题错到第 11 道，科目四 50 题错到第 6 道。
int failingWrongCount(int total, int passScore) {
  if (total <= 0) return 1;
  for (var wrong = 0; wrong <= total; wrong++) {
    if (((total - wrong) / total * 100).round() < passScore) return wrong;
  }
  return total + 1;
}

int phaseTestMinutes(int count) {
  final minutes = (count * 27 / 60).ceil();
  return minutes < 8 ? 8 : minutes;
}

/// 阶段测试按考场口径抽：100 题、45 分钟、判断 40 / 单选 60、90 分及格；只考本阶段，不分内容块。
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
