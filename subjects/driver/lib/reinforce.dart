import "dart:math";

import "exam.dart";
import "models.dart";

/// 强化练习与学习建议的计算核心（主仓库 ADR 0076）。
///
/// 全部是纯函数：输入作答记录与题库，输出题单或统计，不碰界面、不碰数据库，可以单测。
/// 一切都由作答记录派生，不另存一张表（主仓库 ADR 0052）；掌握度仍只由作答写入。
///
/// 数据量小（几千条作答、基本一个学习者），所以章节与题目的估计一律用**收缩**：样本少时
/// 向总体均值靠，不用裸正确率。

/// 一次作答，只留选题需要的列。
class AttemptView {
  const AttemptView({
    required this.questionId,
    required this.topicId,
    required this.correct,
    required this.at,
    this.durationMs = 0,
    this.chosen,
    this.kind = "practice",
    this.reason,
  });

  final String questionId;
  final String topicId;
  final bool correct;
  final DateTime at;

  /// 单题用时（毫秒，已封顶 5 分钟）；老记录或没记的是 0。
  final int durationMs;

  /// 所选选项（主仓库 ADR 0076）；升级前的老记录没有。
  final String? chosen;

  /// 场合标记：practice / exam / reinforce。
  final String kind;

  /// 强化练习的选题理由；其余场合没有。
  final String? reason;
}

/// 一道题的作答历史摘要。
class QuestionHistory {
  QuestionHistory(this.questionId, this.topicId);

  final String questionId;
  final String topicId;
  int attempts = 0;
  int wrong = 0;
  bool firstCorrect = false;

  /// 最近一次答错之后连着答对的次数。
  int trailingCorrect = 0;
  DateTime? lastAt;
  bool lastCorrect = false;

  /// 当前这段连对跨过哪几天（"yyyy-mm-dd"）：隔天后仍对才算稳固。
  final Set<String> streakDays = {};

  /// 最近至多 [recentWindow] 次的对错，旧的在前。
  final List<bool> recent = [];

  static const recentWindow = 5;
}

/// 掌握度四级：新题、学习中、巩固（连对 2 次）、稳固（连对跨过至少两个日期）。
/// 「最近一次答对」和「隔了一晚还答对」是两回事。
enum MasteryLevel {
  fresh("新题"),
  learning("学习中"),
  consolidating("巩固"),
  solid("稳固");

  const MasteryLevel(this.label);
  final String label;
}

String dayKey(DateTime t) =>
    "${t.year.toString().padLeft(4, '0')}-${t.month.toString().padLeft(2, '0')}-${t.day.toString().padLeft(2, '0')}";

/// 日历天数差（不是 24 小时的倍数）：昨晚答的题今早就算隔了一天。
int daysBetween(DateTime from, DateTime to) =>
    DateTime.utc(to.year, to.month, to.day).difference(DateTime.utc(from.year, from.month, from.day)).inDays;

/// 全部作答摘要，外加几个整体统计（总体正确率、首答正确率、错题转正率）。
class HistorySet {
  HistorySet._(this.byQuestion, this._recoveryTrials, this._recoveryHits);

  final Map<String, QuestionHistory> byQuestion;
  final int _recoveryTrials;
  final int _recoveryHits;

  QuestionHistory? of(String questionId) => byQuestion[questionId];

  /// 作答按时间排序后逐条折叠；同一时刻按输入顺序（`sort` 稳定）。
  static HistorySet build(Iterable<AttemptView> attempts) {
    final sorted = [...attempts]..sort((a, b) => a.at.compareTo(b.at));
    final map = <String, QuestionHistory>{};
    var trials = 0;
    var hits = 0;
    for (final attempt in sorted) {
      final h = map.putIfAbsent(attempt.questionId, () => QuestionHistory(attempt.questionId, attempt.topicId));
      if (h.attempts == 0) h.firstCorrect = attempt.correct;
      // 上一次是错的，这一次对不对：错题「转正」的经验概率。
      if (h.attempts > 0 && !h.lastCorrect) {
        trials++;
        if (attempt.correct) hits++;
      }
      h.attempts++;
      if (attempt.correct) {
        h.trailingCorrect++;
        h.streakDays.add(dayKey(attempt.at));
      } else {
        h.wrong++;
        h.trailingCorrect = 0;
        h.streakDays.clear();
      }
      h.lastAt = attempt.at;
      h.lastCorrect = attempt.correct;
      h.recent.add(attempt.correct);
      if (h.recent.length > QuestionHistory.recentWindow) h.recent.removeAt(0);
    }
    return HistorySet._(map, trials, hits);
  }

  int get totalAttempts => byQuestion.values.fold(0, (sum, h) => sum + h.attempts);
  int get totalCorrect => byQuestion.values.fold(0, (sum, h) => sum + h.attempts - h.wrong);

  static const _shrinkK = 10.0;

  /// 总体正确率（收缩到 0.7：没数据时的保守默认）。
  double get overallAccuracy => _shrunk(totalCorrect, totalAttempts, 0.7);

  /// 首答正确率：没见过的题答对的概率，用来估计「还没做过的题」。收缩到 0.6。
  double get firstAttemptAccuracy {
    var n = 0;
    var ok = 0;
    for (final h in byQuestion.values) {
      n++;
      if (h.firstCorrect) ok++;
    }
    return _shrunk(ok, n, 0.6);
  }

  /// 错题下一次答对的概率（样本少时收缩到 0.6）。
  double get recoveryRate => _shrunk(_recoveryHits, _recoveryTrials, 0.6, k: 5);

  static double _shrunk(int ok, int n, double prior, {double k = _shrinkK}) => (ok + k * prior) / (n + k);

  /// 每章的先验：没做过的题与刚见的题的预期正确率。章内首答正确率向总体首答正确率收缩。
  Map<String, double> chapterPriors() {
    final global = firstAttemptAccuracy;
    final n = <String, int>{};
    final ok = <String, int>{};
    for (final h in byQuestion.values) {
      n[h.topicId] = (n[h.topicId] ?? 0) + 1;
      if (h.firstCorrect) ok[h.topicId] = (ok[h.topicId] ?? 0) + 1;
    }
    return {for (final topic in n.keys) topic: _shrunk(ok[topic] ?? 0, n[topic]!, global)};
  }

  /// 每章的整体正确率（该章全部作答，向总体收缩）。
  Map<String, double> chapterAccuracy() {
    final global = overallAccuracy;
    final n = <String, int>{};
    final ok = <String, int>{};
    for (final h in byQuestion.values) {
      n[h.topicId] = (n[h.topicId] ?? 0) + h.attempts;
      ok[h.topicId] = (ok[h.topicId] ?? 0) + h.attempts - h.wrong;
    }
    return {for (final topic in n.keys) topic: _shrunk(ok[topic]!, n[topic]!, global)};
  }
}

MasteryLevel levelOf(QuestionHistory? h) {
  if (h == null || h.attempts == 0) return MasteryLevel.fresh;
  if (h.trailingCorrect >= 2) {
    return h.streakDays.length >= 2 ? MasteryLevel.solid : MasteryLevel.consolidating;
  }
  return MasteryLevel.learning;
}

/// 掌握度漏斗：题池里各级的题数。
Map<MasteryLevel, int> masteryFunnel(Iterable<Question> pool, HistorySet histories) {
  final out = {for (final level in MasteryLevel.values) level: 0};
  for (final q in pool) {
    final level = levelOf(histories.of(q.id));
    out[level] = out[level]! + 1;
  }
  return out;
}

/// 复习间隔（天）：连对 0、1、2、3、4、5 次以上分别隔 1、2、4、8、16、32 天。
/// 简化的间隔复习：每多对一次，间隔翻倍；答错回到 1 天。
const reviewIntervalDays = [1, 2, 4, 8, 16, 32];

int intervalFor(int streak) => reviewIntervalDays[min(streak, reviewIntervalDays.length - 1)];

/// 距上次作答的天数与间隔之比；大于等于 1 即到期。没作答过返回 null。
double? dueRatio(QuestionHistory? h, DateTime now) {
  final last = h?.lastAt;
  if (h == null || last == null) return null;
  return daysBetween(last, now) / intervalFor(h.trailingCorrect);
}

/// 一道题答对的概率：最近至多 5 次作答加章节先验（相当于 2 次的权重）。
/// 没做过的题就是章节先验。
double questionProbability(QuestionHistory? h, double chapterPrior) {
  if (h == null || h.attempts == 0) return chapterPrior;
  final ok = h.recent.where((x) => x).length;
  return (ok + 2 * chapterPrior) / (h.recent.length + 2);
}

// ---------------------------------------------------------------- 强化练习选题

/// 选题理由。`retest` 复测错题，`weak` 薄弱章节，`due` 间隔到期，`fill` 数据不够时按
/// 公开错误率补足（主仓库 ADR 0076 决策 7、8）。
const reinforceReasonLabels = {
  "retest": "复测错题",
  "weak": "薄弱章节",
  "due": "到期复习",
  "fill": "补足",
};

class ReinforcePick {
  const ReinforcePick(this.question, this.reason);

  final Question question;
  final String reason;
}

class ReinforcePlan {
  const ReinforcePlan(this.picks);

  final List<ReinforcePick> picks;

  List<Question> get questions => [for (final p in picks) p.question];

  Map<String, int> get byReason {
    final out = <String, int>{};
    for (final p in picks) {
      out[p.reason] = (out[p.reason] ?? 0) + 1;
    }
    return out;
  }
}

/// 强化练习选题：错题、薄弱章节、到期复习三类信号合成一张题单。
///
/// [pool] 由调用方给出——已排除锁着的科目、偏难怪题（不挡过关，ADR 0032）。每题最多出一次
/// （driver ADR 0031）。初始配额 复测 40%、薄弱 30%、到期 30%；某类不够，按复测、薄弱、
/// 到期的顺序拿别的类补；候选全不够（新学习者）时按公开错误率补足。
ReinforcePlan planReinforcement({
  required Iterable<Question> pool,
  required HistorySet histories,
  required DateTime now,
  Random? random,
  int count = 20,
}) {
  random ??= Random();
  final all = <String, Question>{for (final q in pool) q.id: q};
  final chapterAcc = histories.chapterAccuracy();
  final overall = histories.overallAccuracy;
  double weakness(String topic) => 1 - (chapterAcc[topic] ?? overall);

  final retest = <Question>[];
  final due = <Question>[];
  final weak = <Question>[];
  for (final q in all.values) {
    final h = histories.of(q.id);
    if (h != null && h.attempts > 0 && !h.lastCorrect) {
      retest.add(q);
    } else if (h != null && h.attempts > 0 && (dueRatio(h, now) ?? 0) >= 1) {
      due.add(q);
    } else if (levelOf(h) == MasteryLevel.fresh || levelOf(h) == MasteryLevel.learning) {
      weak.add(q);
    }
  }
  // 错得多的先复测；同样多的，隔得久的先。
  retest.sort((a, b) {
    final ha = histories.of(a.id)!;
    final hb = histories.of(b.id)!;
    final byWrong = hb.wrong.compareTo(ha.wrong);
    return byWrong != 0 ? byWrong : ha.lastAt!.compareTo(hb.lastAt!);
  });
  // 超期越久越先。
  due.sort((a, b) => dueRatio(histories.of(b.id), now)!.compareTo(dueRatio(histories.of(a.id), now)!));
  // 章节越弱越先；没做过的略加分；加一点随机，免得每次都是同一批。
  final weakScore = {
    for (final q in weak)
      q.id: weakness(q.topicId) + (histories.of(q.id) == null ? 0.15 : 0) + random.nextDouble() * 0.05,
  };
  weak.sort((a, b) => weakScore[b.id]!.compareTo(weakScore[a.id]!));

  final retestQuota = (count * 0.4).round();
  final weakQuota = (count * 0.3).round();
  final dueQuota = count - retestQuota - weakQuota;
  final lists = {"retest": retest, "weak": weak, "due": due};
  final quotas = {"retest": retestQuota, "weak": weakQuota, "due": dueQuota};
  final picks = <ReinforcePick>[];
  final used = <String>{};

  void take(String reason, int n) {
    for (final q in lists[reason]!) {
      if (n <= 0 || picks.length >= count) return;
      if (used.add(q.id)) {
        picks.add(ReinforcePick(q, reason));
        n--;
      }
    }
  }

  for (final reason in ["retest", "weak", "due"]) {
    take(reason, quotas[reason]!);
  }
  for (final reason in ["retest", "weak", "due"]) {
    take(reason, count - picks.length);
  }
  if (picks.length < count) {
    final rest = [for (final q in all.values) if (!used.contains(q.id)) q]
      ..sort((a, b) => (b.errorRate ?? 0).compareTo(a.errorRate ?? 0));
    for (final q in rest) {
      if (picks.length >= count) break;
      picks.add(ReinforcePick(q, "fill"));
    }
  }
  picks.shuffle(random);
  return ReinforcePlan(picks);
}

// ---------------------------------------------------------------- 优先章节

class ChapterPriority {
  const ChapterPriority({
    required this.topicId,
    required this.total,
    required this.unsettled,
    required this.expectedLoss,
    required this.recoverable,
  });

  final String topicId;
  final int total;

  /// 还没巩固的题数（新题加学习中）。
  final int unsettled;

  /// 按现在的状态，这一章在满分 100 的卷子上预计丢多少分（题量占比乘以各题答错的概率）。
  final double expectedLoss;

  /// 再练 [minutes] 分钟预计能挽回多少分：丢分乘以「这段时间能覆盖的未稳题比例」再乘以
  /// 错题转正率。是粗略的启发式，用来排先后，不是承诺。
  final double recoverable;
}

/// 优先章节：按「再练 30 分钟预计挽回的分数」从高到低。
/// [questionsPerSession] 是 30 分钟大约能做多少题（由平均用时推出）。
List<ChapterPriority> chapterPriorities({
  required Iterable<Question> pool,
  required HistorySet histories,
  required int questionsPerSession,
}) {
  final priors = histories.chapterPriors();
  final fallbackPrior = histories.firstAttemptAccuracy;
  final recovery = histories.recoveryRate;
  final byTopic = <String, List<Question>>{};
  var total = 0;
  for (final q in pool) {
    byTopic.putIfAbsent(q.topicId, () => []).add(q);
    total++;
  }
  if (total == 0) return const [];
  final out = <ChapterPriority>[];
  for (final entry in byTopic.entries) {
    final prior = priors[entry.key] ?? fallbackPrior;
    var lossMass = 0.0;
    var unsettled = 0;
    for (final q in entry.value) {
      final h = histories.of(q.id);
      lossMass += 1 - questionProbability(h, prior);
      final level = levelOf(h);
      if (level == MasteryLevel.fresh || level == MasteryLevel.learning) unsettled++;
    }
    final loss = 100 * lossMass / total;
    final coverage = unsettled == 0 ? 0.0 : min(1.0, questionsPerSession / unsettled);
    out.add(ChapterPriority(
      topicId: entry.key,
      total: entry.value.length,
      unsettled: unsettled,
      expectedLoss: loss,
      recoverable: loss * coverage * recovery,
    ));
  }
  out.sort((a, b) => b.recoverable.compareTo(a.recoverable));
  return out;
}

// ---------------------------------------------------------------- 通过概率

class PassEstimate {
  const PassEstimate({
    required this.probability,
    required this.mean,
    required this.low,
    required this.high,
    required this.coverage,
    required this.trials,
  });

  /// 模拟抽卷中及格的比例。
  final double probability;

  /// 模拟得分的平均、第 10 与第 90 百分位（折合百分制）。
  final double mean;
  final double low;
  final double high;

  /// 题库里做过的题的比例：低说明模拟主要靠先验，可信度差。
  final double coverage;
  final int trials;
}

/// 通过概率：按模拟考的抽题规则（[Paper.draw]）反复抽卷，每道题按它的答对概率掷骰子。
/// 注意：这是模型估计，必须与真实模拟考的成绩并列看；覆盖率低时尤其不可靠。
PassEstimate estimatePass({
  required List<Question> bank,
  required ExamRules rules,
  required HistorySet histories,
  int trials = 300,
  Random? random,
}) {
  random ??= Random();
  final priors = histories.chapterPriors();
  final fallbackPrior = histories.firstAttemptAccuracy;
  final p = <String, double>{
    for (final q in bank)
      q.id: questionProbability(histories.of(q.id), priors[q.topicId] ?? fallbackPrior),
  };
  final scores = <double>[];
  var passed = 0;
  for (var i = 0; i < trials; i++) {
    final paper = Paper.draw(bank, rules, random);
    var correct = 0;
    for (final q in paper.questions) {
      if (random.nextDouble() < p[q.id]!) correct++;
    }
    scores.add(paper.scaledScore(correct).toDouble());
    if (paper.passed(correct)) passed++;
  }
  scores.sort();
  double at(double q) => scores[min(scores.length - 1, (q * scores.length).floor())];
  final seen = bank.where((q) => (histories.of(q.id)?.attempts ?? 0) > 0).length;
  return PassEstimate(
    probability: passed / trials,
    mean: scores.reduce((a, b) => a + b) / scores.length,
    low: at(0.1),
    high: at(0.9),
    coverage: bank.isEmpty ? 0 : seen / bank.length,
    trials: trials,
  );
}
