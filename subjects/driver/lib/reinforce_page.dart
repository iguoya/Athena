import "dart:math";

import "package:flutter/services.dart";
import "package:flutter/material.dart";

import "diagnosis.dart";
import "diagnosis_panel.dart";
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
    required this.onReshuffle,
    this.onNewPractice,
    this.diagnosis,
    this.roundSize = reinforceRoundSize,
    this.onRoundSizeChanged,
    this.stubborn = const [],
  });

  final ReinforcePlan plan;
  final List<ReinforceSubjectView> subjects;
  final List<ChapterPriority> priorities;
  final Map<String, String> topicTitles;
  final VoidCallback onStart;

  /// 「换一批」：从历史错题里重新抽一轮（主仓库 ADR 0085）。
  final VoidCallback onReshuffle;

  /// 题池空时的出口：去练新题（ADR 0061 决策 4）。null 就不显示这个入口。
  final VoidCallback? onNewPractice;

  /// 学习诊断（遗忘、错因、选错的方式、与全国比、强化练习成效）；没有就不显示这一区。
  final DiagnosisData? diagnosis;

  /// 每轮抽取的题量（ADR 0069）：默认 50（主仓库 ADR 0087），界面上可调。
  final int roundSize;

  /// 轮量变化回调；null 则数字块不可点。
  final void Function(int count)? onRoundSizeChanged;

  /// 反复答错的题（累计错 2 次及以上）：还在错的在前、已修补的在后。
  final List<StubbornQuestion> stubborn;

  /// 两张配色表都含皮肤主色（consolidating / due），getter 每次取当前皮肤值。
  static Map<MasteryLevel, Color> get _levelColors => {
    MasteryLevel.fresh: const Color(0xFFADB5BD),
    MasteryLevel.learning: Bs.warning,
    MasteryLevel.consolidating: Bs.primary,
    MasteryLevel.solid: Bs.success,
  };

  static Map<String, Color> get _reasonColors => {
    "retest": Bs.danger,
    "variant": const Color(0xFF6F42C1),
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
          Row(
            children: [
              Icon(Glyph.reinforce, color: Bs.paper),
              const SizedBox(width: 8),
              const Text("强化练习", style: TextStyle(fontSize: 32, fontWeight: FontWeight.w600)),
            ],
          ),
          const SizedBox(height: 12),
          // 备选库的大小直接摆出来：总共还要练多少道，是这页最先要回答的问题。
          Wrap(
            spacing: 14,
            runSpacing: 10,
            children: [
              _CountTile(label: "还要练的错题（备选库）", value: plan.wrongPool, color: Bs.danger, emphasis: true),
              _CountTile(label: "其中还没在强化练习里测过", value: plan.untested, color: Bs.warning),
              _CountTile(label: "已测过且没出错、移出", value: plan.retired, color: Bs.success),
              PopupMenuButton<int>(
                enabled: onRoundSizeChanged != null,
                tooltip: "选择每轮抽取的题量",
                onSelected: (count) => onRoundSizeChanged?.call(count),
                itemBuilder: (context) => [
                  for (final count in const [25, 50, 75, 100])
                    PopupMenuItem(value: count, child: Text("每轮 $count 题")),
                ],
                child: _CountTile(
                  label: onRoundSizeChanged == null ? "每轮抽取" : "每轮抽取（可点调）",
                  value: roundSize,
                  color: Bs.primary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            plan.wrongPool + plan.retired > 0
                ? "错题库：历史上答错过 ${plan.wrongPool + plan.retired} 题，其中还要练 ${plan.wrongPool} 题"
                    "（${plan.untested} 题还没在强化练习里测过，每次优先抽它们）；在强化练习里测过且没有出错的 ${plan.retired} 题已移出（同考点的变式题答对也算），"
                    "再答错会自动回来。每次从还要练的题里按权重抽 ${plan.picks.length} 题——错得多、最近又错、隔得久的更容易被抽到；"
                    "不够时才用薄弱章节和到期复习补。"
                : "还没有答错过的题，先按薄弱章节的新题练起；答错的题会进错题库，之后每次从里面抽，直到在强化练习里测过且没有出错才移出。",
            style: body,
          ),
          const SizedBox(height: 6),
          Text("不计时、不占模拟考成绩；模拟考仍从整个题库按考场配比抽取。", style: body),
          const SizedBox(height: 18),
          if (plan.picks.isEmpty) ...[
            Text("题池里还没有可练的题。", style: body),
            if (onNewPractice != null) ...[
              const SizedBox(height: 12),
              FilledButton.tonal(
                onPressed: onNewPractice,
                child: const Text("去练新题"),
              ),
            ],
          ]
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
            Row(
              children: [
                FilledButton(onPressed: onStart, child: Text("开始强化练习 ${plan.picks.length} 题")),
                const SizedBox(width: 12),
                OutlinedButton(onPressed: onReshuffle, child: const Text("换一批")),
              ],
            ),
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
                          BsTweenFraction(
                            end: (chapter.expectedLoss / maxLoss).clamp(0.02, 1.0),
                            builder: (context, v) => FractionallySizedBox(
                              widthFactor: v,
                              child: Container(
                                height: 12,
                                decoration: BoxDecoration(
                                  color: Bs.danger.withValues(alpha: 0.75),
                                  borderRadius: BorderRadius.circular(3),
                                ),
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
          if (diagnosis != null) ...[
            const SizedBox(height: 32),
            const Divider(),
            DiagnosisPanel(data: diagnosis!, topicTitles: topicTitles),
          ],
          if (stubborn.isNotEmpty) ...[
            const SizedBox(height: 32),
            const Divider(),
            Text("反复错题", style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 6),
            Text(
              "累计答错 2 次及以上的题。反复错的题也可能是题目或答案本身有问题——"
              "点编号复制，报编号核对题库；「已修补」的是后来连着答对、已移出错题库的，回头扫一眼。",
              style: small,
            ),
            const SizedBox(height: 12),
            for (final s in stubborn) _StubbornRow(stubborn: s),
          ],
        ],
      ),
    );
  }
}

/// 反复错题的一行：编号（点击复制）+ 题干摘要 + 累计错次 + 状态。
class _StubbornRow extends StatelessWidget {
  const _StubbornRow({required this.stubborn});

  final StubbornQuestion stubborn;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final small = theme.textTheme.bodyMedium?.copyWith(color: const Color(0xFF6C757D), height: 1.35);
    final prompt = stubborn.question.prompt;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          InkWell(
            onTap: () {
              Clipboard.setData(ClipboardData(text: stubborn.serial));
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text("已复制编号 ${stubborn.serial}，报编号可核对题目")),
              );
            },
            borderRadius: BorderRadius.circular(6),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                border: Border.all(color: theme.dividerColor),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(stubborn.serial, style: theme.textTheme.bodySmall?.copyWith(fontFamily: "monospace")),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(prompt, maxLines: 2, overflow: TextOverflow.ellipsis, style: theme.textTheme.bodyLarge),
                const SizedBox(height: 2),
                Text(
                  "累计错 ${stubborn.wrong} 次 · 共答 ${stubborn.attempts} 次"
                  "${stubborn.repaired ? " · 已修补，移出错题库" : " · 还在错题库里"}",
                  style: small,
                ),
              ],
            ),
          ),
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
        // 分段用 flex 排比，动画从整条长出（ADR 0060）；逐段动画要重写成定宽结构，不值。
        BsTweenFraction(
          end: 1,
          builder: (context, v) => Align(
            alignment: Alignment.centerLeft,
            widthFactor: v,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: SizedBox(
                height: 18,
                width: double.infinity,
                child: Row(
                  children: [
                    for (final level in MasteryLevel.values)
                      if ((funnel[level] ?? 0) > 0)
                        Expanded(flex: funnel[level]!, child: Container(color: colors[level])),
                  ],
                ),
              ),
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


/// 一个醒目的数字块：大号数字加说明，用来摆备选库的大小。
class _CountTile extends StatelessWidget {
  const _CountTile({required this.label, required this.value, required this.color, this.emphasis = false});

  final String label;
  final int value;
  final Color color;
  final bool emphasis;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        border: Border.all(color: color, width: emphasis ? 2 : 1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.baseline,
        textBaseline: TextBaseline.alphabetic,
        children: [
          Text("$value", style: TextStyle(fontSize: emphasis ? 36 : 28, fontWeight: FontWeight.w700, color: color)),
          const SizedBox(width: 6),
          Text("题 · $label", style: Theme.of(context).textTheme.bodyMedium),
        ],
      ),
    );
  }
}
