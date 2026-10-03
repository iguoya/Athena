import "dart:math";

import "package:flutter/material.dart";

import "glyphs.dart";
import "look.dart";
import "models.dart";
import "reinforce.dart";

/// 一个科目在「强化练习」页里的数据：掌握度漏斗、通过概率与真实模拟考。
class ReinforceSubjectView {
  const ReinforceSubjectView({
    required this.id,
    required this.title,
    required this.funnel,
    required this.exams,
    required this.passScore,
    this.pass,
    this.passComputing = false,
  });

  final String id;
  final String title;
  final Map<MasteryLevel, int> funnel;

  /// 该科目最近几场模拟考，新的在前。
  final List<ExamRecord> exams;
  final int passScore;

  /// 模型估计的通过概率；还没算完时为空。
  final PassEstimate? pass;
  final bool passComputing;
}

/// 强化练习页（主仓库 ADR 0076）：把错题、薄弱章节、间隔到期合成一张题单，
/// 并说明为什么这样选——掌握度漏斗、优先章节、通过概率（与真实模拟考并列看）。
///
/// 它是练习，不是考试：不计时收卷、不占模拟考成绩；模拟考仍从整个题库按考场配比抽取。
class ReinforcePage extends StatelessWidget {
  const ReinforcePage({
    super.key,
    required this.plan,
    required this.subjects,
    required this.priorities,
    required this.topicTitles,
    required this.onStart,
  });

  final ReinforcePlan plan;
  final List<ReinforceSubjectView> subjects;
  final List<ChapterPriority> priorities;
  final Map<String, String> topicTitles;
  final VoidCallback onStart;

  static const _levelColors = {
    MasteryLevel.fresh: Color(0xFFADB5BD),
    MasteryLevel.learning: Bs.warning,
    MasteryLevel.consolidating: Bs.primary,
    MasteryLevel.solid: Bs.success,
  };

  static const _reasonColors = {
    "retest": Bs.danger,
    "weak": Bs.warning,
    "due": Bs.primary,
    "fill": Bs.secondary,
  };

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final body = theme.textTheme.bodyLarge;
    final small = theme.textTheme.bodyMedium?.copyWith(color: const Color(0xFF6C757D), height: 1.5);
    final top = priorities.where((c) => c.expectedLoss >= 0.5).take(5).toList();
    final maxLoss = top.isEmpty ? 1.0 : top.map((c) => c.expectedLoss).reduce(max);

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(36, 28, 36, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Glyph.reinforce, color: Bs.paper),
              SizedBox(width: 8),
              Text("强化练习", style: TextStyle(fontSize: 32, fontWeight: FontWeight.w600)),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            "把错题、薄弱章节和到期该复习的题合在一起选，每次 ${plan.picks.length} 题。"
            "不计时、不占模拟考成绩；模拟考仍从整个题库按考场配比抽取。",
            style: body,
          ),
          const SizedBox(height: 18),
          if (plan.picks.isEmpty)
            Text("题池里还没有可练的题。", style: body)
          else ...[
            Wrap(
              spacing: 10,
              runSpacing: 8,
              children: [
                for (final reason in reinforceReasonLabels.keys)
                  if ((plan.byReason[reason] ?? 0) > 0)
                    BsBadge(
                      text: "${reinforceReasonLabels[reason]} ${plan.byReason[reason]}",
                      color: _reasonColors[reason]!,
                    ),
              ],
            ),
            const SizedBox(height: 16),
            FilledButton(onPressed: onStart, child: Text("开始强化练习 ${plan.picks.length} 题")),
          ],
          const SizedBox(height: 32),
          for (final subject in subjects) ...[
            Text(subject.title, style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 10),
            _Funnel(funnel: subject.funnel, colors: _levelColors),
            const SizedBox(height: 14),
            _PassBlock(subject: subject, small: small, body: body),
            const SizedBox(height: 28),
          ],
          if (top.isNotEmpty) ...[
            Text("优先练哪几章", style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            Text(
              "按「再练 30 分钟预计能挽回的分数」排序。预计丢分 = 章节题量占比 × 各题答错的概率（满分 100）；"
              "是粗略估计，用来排先后，不是承诺。",
              style: small,
            ),
            const SizedBox(height: 12),
            for (final chapter in top)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                      width: 190,
                      child: Text(topicTitles[chapter.topicId] ?? chapter.topicId, style: body),
                    ),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          FractionallySizedBox(
                            widthFactor: (chapter.expectedLoss / maxLoss).clamp(0.02, 1.0),
                            child: Container(
                              height: 12,
                              decoration: BoxDecoration(
                                color: Bs.danger.withValues(alpha: 0.75),
                                borderRadius: BorderRadius.circular(3),
                              ),
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            "预计丢 ${chapter.expectedLoss.toStringAsFixed(1)} 分 · "
                            "未稳 ${chapter.unsettled}/${chapter.total} 题 · "
                            "再练 30 分钟约挽回 ${chapter.recoverable.toStringAsFixed(1)} 分",
                            style: small,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ],
      ),
    );
  }
}

/// 掌握度漏斗：一条分段横条加图例。
class _Funnel extends StatelessWidget {
  const _Funnel({required this.funnel, required this.colors});

  final Map<MasteryLevel, int> funnel;
  final Map<MasteryLevel, Color> colors;

  @override
  Widget build(BuildContext context) {
    final total = funnel.values.fold(0, (a, b) => a + b);
    if (total == 0) return const Text("这个科目还没有可练的题。");
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: SizedBox(
            height: 18,
            child: Row(
              children: [
                for (final level in MasteryLevel.values)
                  if ((funnel[level] ?? 0) > 0)
                    Expanded(flex: funnel[level]!, child: Container(color: colors[level])),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 18,
          runSpacing: 4,
          children: [
            for (final level in MasteryLevel.values)
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(width: 10, height: 10, color: colors[level]),
                  const SizedBox(width: 6),
                  Text("${level.label} ${funnel[level] ?? 0}"),
                ],
              ),
          ],
        ),
      ],
    );
  }
}

/// 通过概率：模型估计与真实模拟考并列，模型旁边写明可信度。
class _PassBlock extends StatelessWidget {
  const _PassBlock({required this.subject, required this.small, required this.body});

  final ReinforceSubjectView subject;
  final TextStyle? small;
  final TextStyle? body;

  @override
  Widget build(BuildContext context) {
    final exams = subject.exams;
    final passed = exams.where((e) => e.passed).length;
    final pass = subject.pass;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          exams.isEmpty
              ? "还没有模拟考成绩。"
              : "最近 ${exams.length} 场模拟考：${exams.map((e) => e.score).join("、")} 分，"
                  "及格线 ${subject.passScore}，及格 $passed 场。",
          style: body,
        ),
        const SizedBox(height: 6),
        if (subject.passComputing && pass == null)
          Text("模型估计计算中…", style: small)
        else if (pass != null) ...[
          Text(
            "模型估计：按现在的状态模拟抽卷 ${pass.trials} 次，及格概率约 ${(pass.probability * 100).round()}%，"
            "得分多在 ${pass.low.round()}～${pass.high.round()} 分（做过的题占题库的 ${(pass.coverage * 100).round()}%）。",
            style: body,
          ),
          const SizedBox(height: 4),
          Text(
            pass.coverage < 0.5
                ? "做过的题还不到一半，这个数更多来自对没做过的题的猜测，别当真；以真实模拟考为准。"
                : "这是模型估计，以真实模拟考为准；两者差得远时，多半是做过的题里有侥幸答对的。",
            style: small,
          ),
        ],
      ],
    );
  }
}
