import "dart:math";

import "package:flutter/material.dart";

import "diagnosis.dart";
import "look.dart";

/// 学习诊断（主仓库 ADR 0076 决策 10「后做」）：为什么会错、忘得快不快、错在哪、和全国比。
/// 全部由作答记录派生；样本少的地方写明，不拿来下结论。
class DiagnosisPanel extends StatelessWidget {
  const DiagnosisPanel({super.key, required this.data, required this.topicTitles});

  final DiagnosisData data;
  final Map<String, String> topicTitles;

  /// 错因配色里有皮肤主色（shaky），getter 每次取当前皮肤值，换肤后跟随。
  static Map<ErrorCause, Color> get _causeColors => {
    ErrorCause.careless: Bs.warning,
    ErrorCause.unknown: Bs.danger,
    ErrorCause.ordinary: Color(0xFFADB5BD),
    ErrorCause.shaky: Bs.primary,
  };

  String _title(String topicId) => topicTitles[topicId] ?? topicId;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final small = theme.textTheme.bodyMedium?.copyWith(color: const Color(0xFF6C757D), height: 1.5);
    final body = theme.textTheme.bodyLarge;
    final heading = theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w600);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 12),
        Text("学习诊断", style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w600)),
        const SizedBox(height: 6),
        Text(
          "全部由你的 ${data.attempts} 条作答记录算出来。你的数据不多，样本少的地方会写明，别当结论。",
          style: small,
        ),
        const SizedBox(height: 24),
        Text("记忆保持：隔多久还记得", style: heading),
        const SizedBox(height: 4),
        Text("上一次答对之后，隔了多久再答，这一次还答对的比例。", style: small),
        const SizedBox(height: 10),
        ..._retention(body, small),
        const SizedBox(height: 28),
        Text("错在哪：粗心、不会、不熟", style: heading),
        const SizedBox(height: 4),
        ..._causes(theme, body, small),
        const SizedBox(height: 28),
        Text("怎么选错的", style: heading),
        const SizedBox(height: 4),
        ..._confusion(body, small),
        const SizedBox(height: 28),
        Text("和全国错误率比", style: heading),
        const SizedBox(height: 4),
        ..._comparison(body, small),
        const SizedBox(height: 28),
        Text("强化练习成效", style: heading),
        const SizedBox(height: 4),
        ..._outcomes(body, small),
      ],
    );
  }

  // ---------------------------------------------------------------- 记忆保持

  List<Widget> _retention(TextStyle? body, TextStyle? small) {
    final buckets = data.retention;
    final summary = _retentionSummary(buckets);
    return [
      for (final bucket in buckets)
        Padding(
          padding: const EdgeInsets.only(bottom: 6),
          child: Row(
            children: [
              SizedBox(width: 110, child: Text(bucket.label, style: body)),
              Expanded(
                child: bucket.n == 0
                    ? Text("还没有这一档的记录", style: small)
                    : Row(
                        children: [
                          Expanded(
                            child: FractionallySizedBox(
                              alignment: Alignment.centerLeft,
                              widthFactor: max(0.02, bucket.rate!),
                              child: Container(
                                height: 12,
                                decoration: BoxDecoration(
                                  color: (bucket.enough ? Bs.success : const Color(0xFFADB5BD)).withValues(alpha: 0.8),
                                  borderRadius: BorderRadius.circular(3),
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(width: 10),
                          SizedBox(
                            width: 190,
                            child: Text(
                              "${(bucket.rate! * 100).round()}%（${bucket.correct}/${bucket.n}）${bucket.enough ? "" : " 样本不足"}",
                              style: small,
                            ),
                          ),
                        ],
                      ),
              ),
            ],
          ),
        ),
      if (summary != null) Padding(padding: const EdgeInsets.only(top: 4), child: Text(summary, style: body)),
    ];
  }

  /// 同一天与隔天以后各取样本够的最近一档比一比，给一句话。
  String? _retentionSummary(List<RetentionBucket> buckets) {
    final same = buckets.first;
    final later = buckets.skip(1).where((b) => b.enough).toList();
    if (!same.enough || later.isEmpty) return "有结论的档位还少，攒一阵再来看。";
    final first = later.first;
    final drop = ((same.rate! - first.rate!) * 100).round();
    if (drop >= 5) return "${first.label}后答对率比同一天低 $drop 个百分点——这类题值得隔天再复习一遍。";
    if (drop <= -5) return "${first.label}后答对率反而比同一天高 ${-drop} 个百分点，记得挺牢。";
    return "${first.label}后答对率和同一天差不多（差 $drop 个百分点），暂时看不出忘得快。";
  }

  // ---------------------------------------------------------------- 错因

  List<Widget> _causes(ThemeData theme, TextStyle? body, TextStyle? small) {
    final report = data.causes;
    final median = report.medianMs;
    if (median == null) {
      return [
        Text(
          "答对的题里有用时记录的还不到 $causeMinCorrectForMedian 道，暂时没法判断「快」和「慢」，先分不了类。",
          style: body,
        ),
      ];
    }
    final total = report.counts.values.fold(0, (a, b) => a + b);
    if (total == 0) {
      return [Text("你答对一题通常用 ${seconds(median)}。没有答得特别快就错、或特别慢的题。", style: body)];
    }
    final top = report.counts.entries.where((e) => e.key != ErrorCause.shaky && e.value > 0).toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    String chapterLine(ErrorCause cause) {
      final rows = report.byTopic.entries.where((e) => (e.value[cause] ?? 0) > 0).toList()
        ..sort((a, b) => b.value[cause]!.compareTo(a.value[cause]!));
      if (rows.isEmpty) return "";
      return rows.take(3).map((e) => "${_title(e.key)} ${e.value[cause]} 次").join("、");
    }

    return [
      Text(
        "你答对一题通常用 ${seconds(median)}。比它快很多（${(median * 0.6 / 1000).toStringAsFixed(1)} 秒以内）就错的叫粗心，"
        "比它慢很多（${(median * 1.6 / 1000).toStringAsFixed(1)} 秒以上）还错的叫不会，答对但慢很多的叫不熟。",
        style: small,
      ),
      const SizedBox(height: 10),
      ClipRRect(
        borderRadius: BorderRadius.circular(4),
        child: SizedBox(
          height: 18,
          child: Row(
            children: [
              for (final cause in ErrorCause.values)
                if (report.counts[cause]! > 0)
                  Expanded(flex: report.counts[cause]!, child: Container(color: _causeColors[cause])),
            ],
          ),
        ),
      ),
      const SizedBox(height: 8),
      Wrap(
        spacing: 18,
        runSpacing: 4,
        children: [
          for (final cause in ErrorCause.values)
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(width: 10, height: 10, color: _causeColors[cause]),
                const SizedBox(width: 6),
                Text("${cause.label} ${report.counts[cause]}"),
              ],
            ),
        ],
      ),
      const SizedBox(height: 10),
      if (top.isNotEmpty) ...[
        Text("答错的题里最多的是「${top.first.key.label}」：${top.first.key.advice}", style: body),
        if (chapterLine(top.first.key).isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text("这类错集中在：${chapterLine(top.first.key)}。", style: small),
          ),
      ],
      if (report.counts[ErrorCause.shaky]! > 0)
        Padding(
          padding: const EdgeInsets.only(top: 6),
          child: Text("另外有 ${report.counts[ErrorCause.shaky]} 次答对但很慢（不熟）：${ErrorCause.shaky.advice}", style: small),
        ),
    ];
  }

  // ---------------------------------------------------------------- 选错的方式

  List<Widget> _confusion(TextStyle? body, TextStyle? small) {
    final c = data.confusion;
    if (!c.hasData) {
      return [
        Text(
          "还没有记了所选选项的答错记录（答错 ${c.wrongTotal} 次，其中记了选项的 0 次）。"
          "从升级之后的作答开始记，攒一两周再来看。",
          style: body,
        ),
      ];
    }
    final multi = c.multiMissed + c.multiExtra + c.multiBoth;
    return [
      Text("答错 ${c.wrongTotal} 次，其中 ${c.withChosen} 次记了所选选项。", style: small),
      const SizedBox(height: 6),
      if (multi > 0)
        Text("多选题答错 $multi 次：只漏选 ${c.multiMissed} · 只多选 ${c.multiExtra} · 两者都有 ${c.multiBoth}。"
            "${c.multiMissed > c.multiExtra * 2 ? "漏选更多：宁可多想一个选项，别只挑最明显的。" : (c.multiExtra > c.multiMissed * 2 ? "多选更多：每个选项都要有依据再选。" : "")}",
            style: body),
      if (c.repeated.isEmpty)
        Padding(
          padding: const EdgeInsets.only(top: 6),
          child: Text("还没有哪道题反复选同一个错误选项（至少 2 次才算）。", style: body),
        )
      else ...[
        Padding(padding: const EdgeInsets.only(top: 6), child: Text("反复选同一个错误选项的题：", style: body)),
        for (final r in c.repeated.take(6))
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              "· ${r.question.serial}　${_snippet(r.question.prompt)}　"
              "你选了「${_label(r, r.chosen)}」${r.times} 次，答案是「${_rightLabel(r)}」",
              style: small,
            ),
          ),
      ],
    ];
  }

  String _snippet(String prompt) {
    final line = prompt.replaceAll("\n", " ").trim();
    return line.length <= 24 ? line : "${line.substring(0, 24)}…";
  }

  String _label(RepeatedWrong r, String id) {
    for (final choice in r.question.choices) {
      if (choice.id == id) return "$id ${choice.label}".trim();
    }
    return id;
  }

  String _rightLabel(RepeatedWrong r) =>
      r.question.choices.where((c) => c.ok).map((c) => "${c.id} ${c.label}".trim()).join("、");

  // ---------------------------------------------------------------- 与全国错误率比

  List<Widget> _comparison(TextStyle? body, TextStyle? small) {
    final c = data.comparison;
    if (c.coveredAttempts == 0) {
      return [Text("还没有带全国错误率的题的作答记录（自编题没有这项数据）。", style: body)];
    }
    final worse = c.chapters.where((g) => g.diff > 0.02).take(3).toList();
    final better = c.chapters.reversed.where((g) => g.diff < -0.02).take(2).toList();
    return [
      Text(
        "带全国错误率的题占你全部作答的 ${(c.coverage * 100).round()}%（自编题没有这项数据）。"
        "下面只比这部分。",
        style: small,
      ),
      const SizedBox(height: 8),
      if (worse.isEmpty && better.isEmpty)
        Text("各章和全国水平差不多，没有明显偏离。", style: body)
      else ...[
        for (final g in worse)
          Text("· ${_title(g.topicId)}：你错 ${(g.mine * 100).round()}%，全国平均 ${(g.national * 100).round()}%，"
              "多错 ${(g.diff * 100).round()} 个百分点（${g.n} 次作答）", style: body),
        for (final g in better)
          Text("· ${_title(g.topicId)}：你错 ${(g.mine * 100).round()}%，全国平均 ${(g.national * 100).round()}%，"
              "比全国少错 ${(-g.diff * 100).round()} 个百分点（${g.n} 次作答）", style: small),
      ],
      const SizedBox(height: 10),
      Text(
        c.blindSpots.isEmpty
            ? "没有「全国大多数人都对、你却反复错」的题。"
            : "个人盲区（全国错误率 ≤ ${blindSpotMaxNational.round()}%，你错了至少 2 次）：",
        style: body,
      ),
      for (final g in c.blindSpots.take(5))
        Padding(
          padding: const EdgeInsets.only(top: 4),
          child: Text(
            "· ${g.question.serial}　${_snippet(g.question.prompt)}　全国错误率 ${g.question.errorRate!.round()}%，"
            "你错了 ${g.wrong}/${g.attempts} 次",
            style: small,
          ),
        ),
      const SizedBox(height: 10),
      Text(
        c.strengths.isEmpty
            ? "还没有「全国易错、你一直答对」的题（至少答 3 次且全对）。"
            : "你的强项（全国错误率 ≥ ${strengthMinNational.round()}%，你答对了每一次）：",
        style: body,
      ),
      for (final g in c.strengths.take(5))
        Padding(
          padding: const EdgeInsets.only(top: 4),
          child: Text(
            "· ${g.question.serial}　${_snippet(g.question.prompt)}　全国错误率 ${g.question.errorRate!.round()}%，"
            "你 ${g.attempts} 次全对",
            style: small,
          ),
        ),
    ];
  }

  // ---------------------------------------------------------------- 强化练习成效

  List<Widget> _outcomes(TextStyle? body, TextStyle? small) {
    if (data.outcomes.isEmpty) {
      return [
        Text("还没有记了选题理由的强化练习作答。练几次之后，这里会显示复测错题的转正率、到期复习的保持率。", style: body),
        const SizedBox(height: 4),
        Text("变式题的差距（同考点换问法答得怎么样）要等考点簇索引，还没做。", style: small),
      ];
    }
    const roles = {
      "retest": "复测错题 · 转正率",
      "variant": "同考点变式 · 答对率",
      "weak": "薄弱章节 · 答对率",
      "due": "到期复习 · 保持率",
      "fill": "补足 · 答对率",
    };
    return [
      for (final o in data.outcomes)
        Padding(
          padding: const EdgeInsets.only(bottom: 6),
          child: Row(
            children: [
              SizedBox(width: 190, child: Text(roles[o.reason] ?? o.reason, style: body)),
              Expanded(
                child: FractionallySizedBox(
                  alignment: Alignment.centerLeft,
                  widthFactor: max(0.02, o.rate ?? 0),
                  child: Container(
                    height: 12,
                    decoration: BoxDecoration(color: Bs.primary.withValues(alpha: 0.75), borderRadius: BorderRadius.circular(3)),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              SizedBox(width: 140, child: Text("${((o.rate ?? 0) * 100).round()}%（${o.correct}/${o.n}）", style: small)),
            ],
          ),
        ),
      ..._variantNote(body, small),
    ];
  }

  /// 变式差距：复测原题和同考点变式答对率的差。
  List<Widget> _variantNote(TextStyle? body, TextStyle? small) {
    final gap = variantGap(data.outcomes);
    if (gap == null) {
      return [Text("还没有同考点变式题的记录；练过几次强化练习后，这里会比较「原题」和「换了问法」哪个答得更好。", style: small)];
    }
    final points = (gap.gap * 100).round();
    final verdict = points >= 15
        ? "换了问法就差了 $points 个百分点：多半记住的是那几道题，不是考点本身，值得回去看条文。"
        : points <= -15
            ? "变式反而答得更好（高 ${-points} 个百分点），说明是真懂了。"
            : "差距不大（$points 个百分点），原题和换了问法答得差不多。";
    return [
      const SizedBox(height: 6),
      Text(
        "复测原题答对 ${((gap.retest.rate ?? 0) * 100).round()}%（${gap.retest.n} 次），"
        "同考点变式答对 ${((gap.variant.rate ?? 0) * 100).round()}%（${gap.variant.n} 次）。$verdict",
        style: body,
      ),
      if (!gap.enough) Text("任何一边不到 10 次都只当线索，别当结论。", style: small),
    ];
  }
}
