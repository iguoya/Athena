import "package:flutter/material.dart";

import "../ui/glyphs.dart";
import "../ui/look.dart";
import "../core/models.dart";
import "recall_status.dart";
import "recall_cards.dart";
import "../study/reinforce.dart";
import "speed_topics.dart";
/// 易混数字一行的状态微点：与速记格子的微点（[StatusDot]）同一套样式，只换悬停措辞
/// ——口径是这一行自己的自测卡（正向、反向），不是关联真题（ADR 0095、0101、0112）。
class RecallRowDot extends StatelessWidget {
  const RecallRowDot({super.key, required this.status, this.remaining = 0});

  final SymbolStatus status;

  /// 这一行还要再答对几次才算掌握（最近一次答错的卡数），写在红点里（ADR 0120、0121）。
  final int remaining;

  @override
  Widget build(BuildContext context) {
    return StatusDot(
      status: status,
      remaining: remaining,
      tooltip: switch (status) {
        SymbolStatus.wrong => "这一行有 ${remaining > 0 ? remaining : 1} 张自测卡最近一次答错，各再答对一次就算掌握",
        SymbolStatus.mastered => "这一行的自测题全部答对过",
        SymbolStatus.fresh => "这一行还没测完",
      },
    );
  }
}

/// 易混数字页（ADR 0028）：同类数字并排，配横条比大小，每行指到条文，每组能直接自测。
/// 与标志、标线、仪表、手势、考点各页同构：页面只管呈现与起练习，作答记录、练习队列由首页接上。
class NumbersPage extends StatelessWidget {
  const NumbersPage({
    super.key,
    required this.bank,
    required this.topic,
    required this.histories,
    required this.onStartRecall,
  });

  final Bank bank;

  /// 本页所属的专题（页键、科目、标题、导语都取自它）。
  final SpeedTopic topic;
  final HistorySet histories;

  
  /// 组里的「自测」：交出这一组卡的题号，首页按条目内容现场出题、起一轮做题（ADR 0118）。
  final void Function(List<String> questionIds, String title) onStartRecall;

  List<CheatGroup> get _groups => cheatGroupsOf(bank, topic);

  /// 一个数字组的专属题（ADR 0102）：组内自测卡对应的题，行与题一对一。
  List<Question> _groupQuestions(CheatGroup group) => recallQuestionsOfNumberGroup(topic.id, _groups, group.id);

  /// 一行易混数字名下的卡（[numberRowIds]）。
  List<String> _rowQuestionIds(CheatGroup group, CheatRow row, Set<String> groupIds) =>
      numberRowIds(topic.id, group, row, groupIds);

  /// 行的状态微点档位（ADR 0101，三态）：这一行有答错过且未掌握的自测卡 → 红；
  /// 这一行的卡全部答对过 → 绿；没测完（含只测了一部分）→ 灰。只看这一行自己的卡（ADR 0112）。
  SymbolStatus _rowStatus(CheatGroup group, CheatRow row, Set<String> groupIds) => statusOfIds(
    ids: _rowQuestionIds(group, row, groupIds),
    histories: histories,
  );

  @override
  Widget build(BuildContext context) {
    final subject = bank.curriculum.subject(topic.subjectId);
    final muted = Theme.of(context).textTheme.bodyMedium?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
      height: 1.45,
    );
    return ListView(
      padding: const EdgeInsets.fromLTRB(36, 28, 36, 32),
      children: [
        Row(
          children: [
            Icon(Glyph.numbers, color: Bs.paper),
            const SizedBox(width: 8),
            Text(topic.title, style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w600)),
            const SizedBox(width: 12),
            BsBadge(text: subject.code, color: Bs.primary),
          ],
        ),
        const SizedBox(height: 8),
        Text(topic.lead ?? "", style: Theme.of(context).textTheme.bodyLarge),
        for (final group in _groups) ...[
          const SizedBox(height: 28),
          _groupCard(context, group, muted),
        ],
      ],
    );
  }

  Widget _groupCard(BuildContext context, CheatGroup group, TextStyle? muted) {
    // 组按钮练的是本组的专属题——组内自测卡对应的题，行与题一对一（ADR 0102）。
    final related = _groupQuestions(group);
    final maxAmount = group.maxAmount;
    // 组状态只看这一组的自测卡（ADR 0112）：给组内「自测」按钮上色——红 = 有答错未掌握、绿 = 全部答对过、灰 = 没测完。
    final ids = [for (final q in related) q.id];
    final groupIds = ids.toSet();
    final status = statusOfIds(ids: ids, histories: histories);
    return BsCard(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(group.title, style: Theme.of(context).textTheme.titleLarge),
              if (group.unit.isNotEmpty) ...[
                const SizedBox(width: 10),
                Text(group.unit, style: muted),
              ],
              MasteryTag(entries: [for (final row in group.rows) _rowQuestionIds(group, row, groupIds)], histories: histories),
              const Spacer(),
              GroupRecallButton(
                status: status,
                ids: ids,
                histories: histories,
                onStart: () => onStartRecall(ids, "${topic.title} · ${group.title} · 自测"),
              ),
            ],
          ),
          if (group.note.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(group.note, style: muted),
          ],
          const SizedBox(height: 12),
          for (final row in group.rows) _row(context, group, row, maxAmount, muted, groupIds),
        ],
      ),
    );
  }

  Widget _row(
    BuildContext context,
    CheatGroup group,
    CheatRow row,
    double maxAmount,
    TextStyle? muted,
    Set<String> groupIds,
  ) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 2),
            child: RecallRowDot(
              status: _rowStatus(group, row, groupIds),
              remaining: recallRetireGap(_rowQuestionIds(group, row, groupIds), histories),
            ),
          ),
          const SizedBox(width: 12),
          SizedBox(
            width: 190,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(row.value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: Bs.paper)),
                if (row.amount != null && maxAmount > 0) ...[
                  const SizedBox(height: 4),
                  // 横条长度按本组最大值换算：高低一眼看出来（仓库 ADR 0056）。
                  FractionallySizedBox(
                    alignment: Alignment.centerLeft,
                    widthFactor: (row.amount! / maxAmount).clamp(0.04, 1.0),
                    child: Container(
                      height: 8,
                      decoration: BoxDecoration(
                        color: Bs.paper.withValues(alpha: 0.75),
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(row.caseText, style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.45)),
                const SizedBox(height: 2),
                Text("${Bs.sourceShort(row.sourceId)} ${row.locator}", style: muted),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
