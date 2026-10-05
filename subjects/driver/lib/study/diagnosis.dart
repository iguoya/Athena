import "dart:math";

import "../core/models.dart";
import "reinforce.dart";
/// 学习诊断（主仓库 ADR 0076 决策 10「后做」那一批）：由作答记录派生，不另建表。
///
/// 全是纯函数，输入作答记录（和题库的查题函数），输出统计。数据量小（几千条作答、基本一个学习者），
/// 所以每一项都带样本量，样本不足的明说，不硬凑结论；不做跨学习者的聚合。

// ---------------------------------------------------------------- 个人遗忘率

/// 一个间隔档：上一次答对之后，隔了这么久再答，这一次答对的比例。
class RetentionBucket {
  const RetentionBucket({required this.label, required this.n, required this.correct});

  final String label;
  final int n;
  final int correct;

  double? get rate => n == 0 ? null : correct / n;

  /// 样本够不够下结论：太少的档只展示，不拿来比较。
  bool get enough => n >= retentionMinSample;
}

const retentionMinSample = 15;

const _retentionEdges = [
  ("同一天", 0, 0),
  ("隔 1 天", 1, 1),
  ("隔 2～3 天", 2, 3),
  ("隔 4～7 天", 4, 7),
  ("隔 8～14 天", 8, 14),
  ("隔 15 天以上", 15, 1000000),
];

/// 遗忘曲线：同一道题**相邻两次**作答，前一次答对，按间隔的日历天数分档，看后一次答对的比例。
/// 只取相邻两次，不重复数同一题的多个组合；答错的前一次不算（那是「没学会」，不是「忘了」）。
List<RetentionBucket> forgettingCurve(Iterable<AttemptView> attempts) {
  final byQuestion = <String, List<AttemptView>>{};
  for (final a in attempts) {
    byQuestion.putIfAbsent(a.questionId, () => []).add(a);
  }
  final n = List.filled(_retentionEdges.length, 0);
  final ok = List.filled(_retentionEdges.length, 0);
  for (final list in byQuestion.values) {
    list.sort((a, b) => a.at.compareTo(b.at));
    for (var i = 1; i < list.length; i++) {
      final previous = list[i - 1];
      if (!previous.correct) continue;
      final gap = daysBetween(previous.at, list[i].at);
      final slot = _retentionEdges.indexWhere((edge) => gap >= edge.$2 && gap <= edge.$3);
      if (slot < 0) continue;
      n[slot]++;
      if (list[i].correct) ok[slot]++;
    }
  }
  return [
    for (var i = 0; i < _retentionEdges.length; i++)
      RetentionBucket(label: _retentionEdges[i].$1, n: n[i], correct: ok[i]),
  ];
}

// ---------------------------------------------------------------- 错因分类

/// 用时加对错分出来的「错因」。不用 `chosen`，所以现有数据就能算。
enum ErrorCause {
  careless("粗心", "答得比平时快很多就错了：多半没读完题干或选项。放慢一点，圈出题干里的限定词再选。"),
  unknown("不会", "想了很久还是错：这是真的没掌握，回去看条文和解析，再用强化练习复测。"),
  ordinary("一般错", "用时正常的错题：按错题本和强化练习的复测去消化就行。"),
  shaky("不熟", "答对了但比平时慢很多：知道，但不扎实。间隔复习最适合这类题。");

  const ErrorCause(this.label, this.advice);
  final String label;
  final String advice;
}

class CauseReport {
  const CauseReport({
    required this.medianMs,
    required this.counts,
    required this.byTopic,
    required this.sample,
  });

  /// 答对题的单题用时中位数（毫秒），是「平时多快」的标尺；样本不够时为 null。
  final int? medianMs;

  /// 各类错因的次数。`shaky` 是答对但慢的次数，其余三类是答错的次数。
  final Map<ErrorCause, int> counts;
  final Map<String, Map<ErrorCause, int>> byTopic;

  /// 参与分类的作答条数（用时有效的）。
  final int sample;

  int get wrongTotal => counts[ErrorCause.careless]! + counts[ErrorCause.unknown]! + counts[ErrorCause.ordinary]!;
}

const causeMinCorrectForMedian = 20;
const _fastRatio = 0.6;
const _slowRatio = 1.6;

/// 错因分类。标尺是**这位学习者自己**答对题的用时中位数：比它快很多就错的叫粗心，
/// 比它慢很多还错的叫不会，答对但慢很多的叫不熟。用时无效的（0 或超过封顶）不参与。
CauseReport errorCauses(Iterable<AttemptView> attempts) {
  final valid = [for (final a in attempts) if (a.durationMs > 0 && a.durationMs <= 300000) a];
  final correctTimes = [for (final a in valid) if (a.correct) a.durationMs]..sort();
  final empty = {for (final cause in ErrorCause.values) cause: 0};
  if (correctTimes.length < causeMinCorrectForMedian) {
    return CauseReport(medianMs: null, counts: empty, byTopic: const {}, sample: valid.length);
  }
  final median = correctTimes[correctTimes.length ~/ 2];
  final counts = {...empty};
  final byTopic = <String, Map<ErrorCause, int>>{};
  void add(String topic, ErrorCause cause) {
    counts[cause] = counts[cause]! + 1;
    final row = byTopic.putIfAbsent(topic, () => {for (final c in ErrorCause.values) c: 0});
    row[cause] = row[cause]! + 1;
  }

  for (final a in valid) {
    final fast = a.durationMs <= median * _fastRatio;
    final slow = a.durationMs >= median * _slowRatio;
    if (!a.correct) {
      add(a.topicId, fast ? ErrorCause.careless : (slow ? ErrorCause.unknown : ErrorCause.ordinary));
    } else if (slow) {
      add(a.topicId, ErrorCause.shaky);
    }
  }
  return CauseReport(medianMs: median, counts: counts, byTopic: byTopic, sample: valid.length);
}

// ---------------------------------------------------------------- 选错的方式（需要 chosen）

/// 同一道题反复选同一个错误选项。
class RepeatedWrong {
  const RepeatedWrong({required this.question, required this.chosen, required this.times});

  final Question question;
  final String chosen;
  final int times;
}

class ConfusionReport {
  const ConfusionReport({
    required this.wrongTotal,
    required this.withChosen,
    required this.repeated,
    required this.multiMissed,
    required this.multiExtra,
    required this.multiBoth,
  });

  /// 答错的作答总数，以及其中记了所选选项的（升级前的老记录没有）。
  final int wrongTotal;
  final int withChosen;

  /// 反复选同一个错选项的题，次数多的在前。
  final List<RepeatedWrong> repeated;

  /// 多选题答错的方式：只漏选（少选了对的）、只多选（选了错的）、两者都有。
  final int multiMissed;
  final int multiExtra;
  final int multiBoth;

  bool get hasData => withChosen > 0;
}

/// 混淆分析。只看记了 `chosen` 的答错作答；单选和判断题看是不是总选同一个错选项，
/// 多选题看是漏选还是多选。[lookup] 按题号取题，取不到的（题库已删）跳过。
ConfusionReport analyzeConfusion(Iterable<AttemptView> attempts, Question? Function(String id) lookup) {
  var wrongTotal = 0;
  var withChosen = 0;
  var missed = 0;
  var extra = 0;
  var both = 0;
  final picks = <(String, String), int>{};
  for (final a in attempts) {
    if (a.correct) continue;
    wrongTotal++;
    final chosen = a.chosen;
    final question = lookup(a.questionId);
    if (chosen == null || chosen.isEmpty || question == null) continue;
    withChosen++;
    final picked = chosen.split(",").toSet();
    final right = {for (final c in question.choices) if (c.ok) c.id};
    if (question.isMulti) {
      final lack = right.difference(picked).isNotEmpty;
      final more = picked.difference(right).isNotEmpty;
      if (lack && more) {
        both++;
      } else if (lack) {
        missed++;
      } else if (more) {
        extra++;
      }
    } else {
      final key = (a.questionId, picked.first);
      picks[key] = (picks[key] ?? 0) + 1;
    }
  }
  final repeated = <RepeatedWrong>[
    for (final entry in picks.entries)
      if (entry.value >= 2) RepeatedWrong(question: lookup(entry.key.$1)!, chosen: entry.key.$2, times: entry.value),
  ]..sort((a, b) => b.times.compareTo(a.times));
  return ConfusionReport(
    wrongTotal: wrongTotal,
    withChosen: withChosen,
    repeated: repeated,
    multiMissed: missed,
    multiExtra: extra,
    multiBoth: both,
  );
}

// ---------------------------------------------------------------- 与全国错误率对照

class QuestionGap {
  const QuestionGap({required this.question, required this.attempts, required this.wrong});

  final Question question;
  final int attempts;
  final int wrong;
}

class ChapterGap {
  const ChapterGap({required this.topicId, required this.n, required this.mine, required this.national});

  final String topicId;
  final int n;

  /// 我在这一章带全国错误率的题上的错误率，和这些题的全国平均错误率（都是 0～1）。
  final double mine;
  final double national;

  /// 正数 = 我比全国错得多。
  double get diff => mine - national;
}

class PublicComparison {
  const PublicComparison({
    required this.coveredAttempts,
    required this.totalAttempts,
    required this.blindSpots,
    required this.strengths,
    required this.chapters,
  });

  /// 带全国错误率的题的作答条数，占全部作答的多少——自编题没有这项数据，覆盖不全。
  final int coveredAttempts;
  final int totalAttempts;

  /// 个人盲区：全国多数人做对（错误率低），我却反复错。
  final List<QuestionGap> blindSpots;

  /// 强项：全国错得多（易错题），我一直对。
  final List<QuestionGap> strengths;

  /// 各章相对全国的差距，差距最大（我错得更多）的在前。
  final List<ChapterGap> chapters;

  double get coverage => totalAttempts == 0 ? 0 : coveredAttempts / totalAttempts;
}

const blindSpotMaxNational = 10.0; // 全国错误率（%）不超过它才算「大家都对」
const strengthMinNational = Question.errorProneRate; // 易错题的门槛，同 driver ADR 0027
const chapterGapMinSample = 20;

PublicComparison publicComparison(Iterable<AttemptView> attempts, Question? Function(String id) lookup) {
  var total = 0;
  var covered = 0;
  final byQuestion = <String, List<AttemptView>>{};
  final chapterN = <String, int>{};
  final chapterWrong = <String, int>{};
  final chapterNational = <String, double>{};
  for (final a in attempts) {
    total++;
    final question = lookup(a.questionId);
    final rate = question?.errorRate;
    if (question == null || rate == null) continue;
    covered++;
    byQuestion.putIfAbsent(a.questionId, () => []).add(a);
    chapterN[a.topicId] = (chapterN[a.topicId] ?? 0) + 1;
    if (!a.correct) chapterWrong[a.topicId] = (chapterWrong[a.topicId] ?? 0) + 1;
    chapterNational[a.topicId] = (chapterNational[a.topicId] ?? 0) + rate / 100;
  }
  final blind = <QuestionGap>[];
  final strong = <QuestionGap>[];
  for (final entry in byQuestion.entries) {
    final question = lookup(entry.key)!;
    final list = entry.value..sort((a, b) => a.at.compareTo(b.at));
    final wrong = list.where((a) => !a.correct).length;
    final gap = QuestionGap(question: question, attempts: list.length, wrong: wrong);
    final rate = question.errorRate!;
    if (rate <= blindSpotMaxNational && list.length >= 2 && wrong >= 2) blind.add(gap);
    if (rate >= strengthMinNational && list.length >= 3 && wrong == 0) strong.add(gap);
  }
  // 盲区：全国越没人错、我错得越多越靠前；强项：全国越容易错、我对的次数越多越靠前。
  blind.sort((a, b) {
    final byWrong = b.wrong.compareTo(a.wrong);
    return byWrong != 0 ? byWrong : a.question.errorRate!.compareTo(b.question.errorRate!);
  });
  strong.sort((a, b) {
    final byRate = b.question.errorRate!.compareTo(a.question.errorRate!);
    return byRate != 0 ? byRate : b.attempts.compareTo(a.attempts);
  });
  final chapters = <ChapterGap>[
    for (final topic in chapterN.keys)
      if (chapterN[topic]! >= chapterGapMinSample)
        ChapterGap(
          topicId: topic,
          n: chapterN[topic]!,
          mine: (chapterWrong[topic] ?? 0) / chapterN[topic]!,
          national: chapterNational[topic]! / chapterN[topic]!,
        ),
  ]..sort((a, b) => b.diff.compareTo(a.diff));
  return PublicComparison(
    coveredAttempts: covered,
    totalAttempts: total,
    blindSpots: blind,
    strengths: strong,
    chapters: chapters,
  );
}

// ---------------------------------------------------------------- 强化练习成效

class ReasonOutcome {
  const ReasonOutcome({required this.reason, required this.n, required this.correct});

  final String reason;
  final int n;
  final int correct;

  double? get rate => n == 0 ? null : correct / n;
}

/// 强化练习各类选题这次的答对比例：复测错题的是「转正率」，到期复习的是「保持率」。
/// 需要作答记了 `reason`（升级后的强化练习才有）。变式题的差距要等考点簇索引（ADR 0076 阶段 4）。
List<ReasonOutcome> reasonOutcomes(Iterable<AttemptView> attempts) {
  final n = <String, int>{};
  final ok = <String, int>{};
  for (final a in attempts) {
    final reason = a.reason;
    if (a.kind != "reinforce" || reason == null) continue;
    n[reason] = (n[reason] ?? 0) + 1;
    if (a.correct) ok[reason] = (ok[reason] ?? 0) + 1;
  }
  return [
    for (final reason in reinforceReasonLabels.keys)
      if (n.containsKey(reason)) ReasonOutcome(reason: reason, n: n[reason]!, correct: ok[reason] ?? 0),
  ];
}

// ---------------------------------------------------------------- 汇总

/// 学习诊断页要的全部统计，一次算好。
class DiagnosisData {
  const DiagnosisData({
    required this.retention,
    required this.causes,
    required this.confusion,
    required this.comparison,
    required this.outcomes,
    required this.attempts,
  });

  final List<RetentionBucket> retention;
  final CauseReport causes;
  final ConfusionReport confusion;
  final PublicComparison comparison;
  final List<ReasonOutcome> outcomes;
  final int attempts;

  static DiagnosisData build(List<AttemptView> attempts, Question? Function(String id) lookup) => DiagnosisData(
        retention: forgettingCurve(attempts),
        causes: errorCauses(attempts),
        confusion: analyzeConfusion(attempts, lookup),
        comparison: publicComparison(attempts, lookup),
        outcomes: reasonOutcomes(attempts),
        attempts: attempts.length,
      );
}

/// 变式差距（主仓库 ADR 0076、0079）：复测原题答对的比例减去同考点变式答对的比例。
/// 正数 = 换了问法就答不好，多半记住的是那几道题而不是考点本身。两类都得有记录才算得出。
class VariantGap {
  const VariantGap({required this.retest, required this.variant});

  final ReasonOutcome retest;
  final ReasonOutcome variant;

  double get gap => retest.rate! - variant.rate!;

  /// 任何一边样本太少都只当线索。
  bool get enough => retest.n >= 10 && variant.n >= 10;
}

VariantGap? variantGap(List<ReasonOutcome> outcomes) {
  final retest = outcomes.where((o) => o.reason == "retest" && o.n > 0).firstOrNull;
  final variant = outcomes.where((o) => o.reason == "variant" && o.n > 0).firstOrNull;
  if (retest == null || variant == null) return null;
  return VariantGap(retest: retest, variant: variant);
}

/// 方便界面写「约 X 秒」。
String seconds(int ms) => "${(ms / 1000).toStringAsFixed(ms >= 10000 ? 0 : 1)} 秒";

/// 防止界面把很小的差距当成结论。
double clampRate(double value) => max(0, min(1, value));
