import "dart:math";

import "clusters.dart";
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

  /// 在强化练习里作答过几次（`kind = reinforce`）。0 表示还没在强化练习里测过。
  int reinforced = 0;

  /// 最近一次答错之后，在强化练习里答对了几次；答错清零（主仓库 ADR 0086）。
  int reinforcedSinceWrong = 0;

  /// 最近一次答错之后，同考点簇里的变式题在强化练习里答对了几次；这道题自己答错清零（主仓库 ADR 0088）。
  /// 要给 [HistorySet.build] 传考点簇才会累计。
  int variantPassesSinceWrong = 0;

  /// 错题能不能从强化练习的备选库移出，两种验收来源任一成立即可：
  /// 自最近一次答错以来，它自己在强化练习里测过且之后没有出错（主仓库 ADR 0086）；
  /// 或同簇的变式题在强化练习里答对过（主仓库 ADR 0088）。
  /// 它自己任何一次答错（不管在哪）都让它回到备选库。
  bool get retiredFromWrongPool =>
      wrong > 0 && ((lastCorrect && reinforcedSinceWrong >= 1) || variantPassesSinceWrong >= 1);

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
  ///
  /// 给了 [clusters]（考点簇，主仓库 ADR 0079）时，强化练习里答对的变式题（`reason = variant`）
  /// 会记给同簇的其他题，作为它们的验收来源（主仓库 ADR 0088）。
  static HistorySet build(Iterable<AttemptView> attempts, {ClusterIndex? clusters}) {
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
      if (attempt.kind == "reinforce") h.reinforced++;
      if (attempt.correct) {
        h.trailingCorrect++;
        h.streakDays.add(dayKey(attempt.at));
        if (attempt.kind == "reinforce") h.reinforcedSinceWrong++;
      } else {
        h.wrong++;
        h.trailingCorrect = 0;
        h.streakDays.clear();
        h.reinforcedSinceWrong = 0;
        h.variantPassesSinceWrong = 0;
      }
      if (clusters != null && attempt.correct && attempt.kind == "reinforce" && attempt.reason == "variant") {
        // 还没有历史的同簇题不用记：它还没答错过，之后第一次答错会清零，本来也不会用到这条记录。
        for (final mate in clusters.mates(attempt.questionId)) {
          map[mate]?.variantPassesSinceWrong++;
        }
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

/// 选题理由。`retest` 从历史上全部错题里抽到的题（不管后来是否答对，主仓库 ADR 0085），`variant`
/// 错题的同考点变式（换了一种问法），`weak` 薄弱章节，`due` 间隔到期，`fill` 数据不够时按公开错误率补足
/// （主仓库 ADR 0076 决策 7、8，ADR 0079）。
const reinforceReasonLabels = {
  "retest": "复测错题",
  "variant": "同考点变式",
  "weak": "薄弱章节",
  "due": "到期复习",
  "fill": "补足",
};

class ReinforcePick {
  const ReinforcePick(this.question, this.reason);

  final Question question;
  final String reason;
}

/// 同考点变式占整轮的比例（考点簇就绪时）。经验值，没有数据支撑（主仓库 ADR 0085）。
const reinforceVariantShare = 0.25;

/// 一轮强化练习默认出多少题（主仓库 ADR 0087，修订 ADR 0076 决策 7 的「默认 20 题」）。
/// 一页十题，50 题是五页；20 题一轮太少，错题库几百道要练很多轮。
const reinforceRoundSize = 50;

/// 错题名额里留给「还没在强化练习里测过」的题的比例（主仓库 ADR 0086）。经验值。
const reinforceCoverageShare = 0.5;

/// 备选库里一道错题被抽到的权重（主仓库 ADR 0085、0086）：错得越多、最近一次还是错、隔得越久越重；
/// 越熟越轻。权重不会降到 0——真正从备选库消失只有一个条件：在强化练习里测过且没有出错
/// （[QuestionHistory.retiredFromWrongPool]）。
double wrongWeight(QuestionHistory h, DateTime now) {
  final state = !h.lastCorrect
      ? 3.0
      : switch (levelOf(h)) {
          MasteryLevel.solid => 0.3,
          MasteryLevel.consolidating => 0.6,
          _ => 1.2,
        };
  final last = h.lastAt;
  final days = last == null ? 0 : max(0, daysBetween(last, now));
  final age = 1 + min(days, 30) / 15;
  return (1 + h.wrong) * state * age;
}

/// 按权重随机、不放回地排出一个抽取顺序（Efraimidis–Spirakis：键 = u^(1/权重)，从大到小）。
List<Question> weightedOrder(List<Question> items, double Function(Question) weight, Random random) {
  final keyed = [
    for (final q in items) (q, pow(max(random.nextDouble(), 1e-12), 1 / weight(q)).toDouble()),
  ];
  keyed.sort((a, b) => b.$2.compareTo(a.$2));
  return [for (final k in keyed) k.$1];
}

class ReinforcePlan {
  const ReinforcePlan(this.picks, {this.wrongPool = 0, this.retired = 0, this.untested = 0});

  final List<ReinforcePick> picks;

  /// 备选库里还要练的错题多少道（抽取的总体，不是这一轮抽到的数量）。
  final int wrongPool;

  /// 其中还没在强化练习里测过的多少道。
  final int untested;

  /// 已经在强化练习里测过且没有出错、从备选库移出的错题多少道；再答错会自动回来。
  final int retired;

  List<Question> get questions => [for (final p in picks) p.question];

  Map<String, int> get byReason {
    final out = <String, int>{};
    for (final p in picks) {
      out[p.reason] = (out[p.reason] ?? 0) + 1;
    }
    return out;
  }
}

/// 强化练习选题（主仓库 ADR 0085、0086，修订 ADR 0076 决策 7）：整轮默认从**历史上答错过、还没验收的题**里按权重
/// 随机抽取（见 [wrongWeight]）。一道错题要在强化练习里测过且没有出错才移出备选库；每一轮重算都是新的一次抽取。
///
/// [pool] 由调用方给出——已排除锁着的科目、偏难怪题（不挡过关，ADR 0032）。每题最多出一次
/// （driver ADR 0031）。错题池不够一轮时，按错题、薄弱章节、到期复习、同考点变式的顺序补足；
/// 候选全不够（新学习者）时按公开错误率补足。
///
/// 给了 [clusters]（考点簇，ADR 0079）时，整轮的 [reinforceVariantShare] 让给**同考点变式**：错了一道题，
/// 就出它同簇里换了问法的另一道（优先没做过的），检验是真懂还是只背了那道题；没给就没有变式。
ReinforcePlan planReinforcement({
  required Iterable<Question> pool,
  required HistorySet histories,
  required DateTime now,
  Random? random,
  int count = reinforceRoundSize,
  ClusterIndex? clusters,
}) {
  random ??= Random();
  final all = <String, Question>{for (final q in pool) q.id: q};
  final chapterAcc = histories.chapterAccuracy();
  final overall = histories.overallAccuracy;
  double weakness(String topic) => 1 - (chapterAcc[topic] ?? overall);

  // 备选库：历史上答错过、还没在强化练习里验收通过（测过且没有出错）的题。
  // 验收通过的从这里移出，仍归「到期复习」按间隔管；再答错会自动回来。
  final wrongPool = <Question>[];
  var retired = 0;
  final due = <Question>[];
  final weak = <Question>[];
  for (final q in all.values) {
    final h = histories.of(q.id);
    final isRetired = h != null && h.retiredFromWrongPool;
    if (isRetired) retired++;
    if (h != null && h.wrong > 0 && !isRetired) {
      wrongPool.add(q);
    } else if (h != null && h.attempts > 0 && (dueRatio(h, now) ?? 0) >= 1) {
      due.add(q);
    } else if (levelOf(h) == MasteryLevel.fresh || levelOf(h) == MasteryLevel.learning) {
      weak.add(q);
    }
  }
  // 按权重随机排出抽取顺序：错得多、最近又错、隔得久的更容易靠前，但每一轮都不一样。
  final drawOrder = weightedOrder(wrongPool, (q) => wrongWeight(histories.of(q.id)!, now), random);
  // 覆盖保证：还没在强化练习里测过的题，错题名额的一半优先给它们（组内仍按权重），其余名额按权重从整个备选库抽。
  final variantSlots = (clusters != null && !clusters.isEmpty) ? (count * reinforceVariantShare).round() : 0;
  final coverageSlots = ((count - variantSlots) * reinforceCoverageShare).ceil();
  final untestedOrder = [for (final q in drawOrder) if (histories.of(q.id)!.reinforced == 0) q];
  final covered = untestedOrder.take(coverageSlots).toList();
  final coveredIds = {for (final q in covered) q.id};
  final retest = [...covered, for (final q in drawOrder) if (!coveredIds.contains(q.id)) q];
  // 超期越久越先。
  due.sort((a, b) => dueRatio(histories.of(b.id), now)!.compareTo(dueRatio(histories.of(a.id), now)!));
  // 章节越弱越先；没做过的略加分；加一点随机，免得每次都是同一批。
  final weakScore = {
    for (final q in weak)
      q.id: weakness(q.topicId) + (histories.of(q.id) == null ? 0.15 : 0) + random.nextDouble() * 0.05,
  };
  weak.sort((a, b) => weakScore[b.id]!.compareTo(weakScore[a.id]!));

  // 整轮默认全部来自错题池；薄弱章节和到期复习只在错题池不够时补足（主仓库 ADR 0085）。
  var retestQuota = count;
  const weakQuota = 0;
  const dueQuota = 0;

  // 同考点变式：每道错题轮流各出一个同簇的题（先出没做过的，再出答对过的），不出错题本身。
  final variants = <Question>[];
  var variantQuota = 0;
  if (clusters != null && !clusters.isEmpty) {
    variantQuota = (count * reinforceVariantShare).round();
    retestQuota -= variantQuota;
    final isRetest = {for (final q in retest) q.id};
    final perWrong = <List<Question>>[];
    // 变式从排在前面的那些错题出（这一轮最可能抽到的），不是整个错题池。
    for (final wrong in retest.take(count)) {
      final mates = [
        for (final id in clusters.mates(wrong.id))
          if (all.containsKey(id) && !isRetest.contains(id)) all[id]!,
      ]..sort((a, b) {
          // 没做过的在前；都做过的，隔得久的在前。
          final ha = histories.of(a.id);
          final hb = histories.of(b.id);
          if (ha == null || ha.attempts == 0) return (hb == null || hb.attempts == 0) ? a.id.compareTo(b.id) : -1;
          if (hb == null || hb.attempts == 0) return 1;
          return ha.lastAt!.compareTo(hb.lastAt!);
        });
      perWrong.add(mates);
    }
    final seen = <String>{};
    for (var round = 0; perWrong.any((m) => m.length > round); round++) {
      for (final mates in perWrong) {
        if (mates.length > round && seen.add(mates[round].id)) variants.add(mates[round]);
      }
    }
  }
  final lists = {"retest": retest, "variant": variants, "weak": weak, "due": due};
  final quotas = {"retest": retestQuota, "variant": variantQuota, "weak": weakQuota, "due": dueQuota};
  const order = ["retest", "variant", "weak", "due"];
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

  for (final reason in order) {
    take(reason, quotas[reason]!);
  }
  // 不够时的补足顺序：变式放最后，不超过它的名额，除非别的都没有了。
  for (final reason in const ["retest", "weak", "due", "variant"]) {
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
  return ReinforcePlan(
    picks,
    wrongPool: wrongPool.length,
    untested: untestedOrder.length,
    retired: retired,
  );
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

/// 反复答错的题（ADR 0069）：累计答错 2 次及以上，分「还在错」与「已修补」。
/// 「已修补」是最近一次答错之后连着答对、已按主仓库 ADR 0086 验收移出备选库
/// 的题——它们不再参与抽取，但值得回头扫一眼。
class StubbornQuestion {
  const StubbornQuestion(this.question, this.wrong, this.attempts, this.repaired);

  final Question question;
  final int wrong;
  final int attempts;

  /// true = 已修补（验收移出备选库）；false = 还在错（在备选库里）。
  final bool repaired;

  /// 稳定编号：题库 id 去掉 `drive.` 前缀，反馈题目问题时报这个号。
  String get serial => question.serial;
}

/// 累计答错 [minWrong] 次及以上的题：还在错的在前、已修补的在后，各自按错次
/// 降序。题库改版删掉的题不展示。
List<StubbornQuestion> stubbornQuestions(HistorySet histories, Map<String, Question> byId, {int minWrong = 2}) {
  final out = <StubbornQuestion>[];
  for (final entry in histories.byQuestion.entries) {
    final h = entry.value;
    if (h.wrong < minWrong) continue;
    final q = byId[entry.key];
    if (q == null) continue;
    out.add(StubbornQuestion(q, h.wrong, h.attempts, h.lastCorrect));
  }
  out.sort((a, b) {
    if (a.repaired != b.repaired) return a.repaired ? 1 : -1;
    return b.wrong.compareTo(a.wrong);
  });
  return out;
}
