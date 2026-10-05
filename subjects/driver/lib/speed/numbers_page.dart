import "package:flutter/material.dart";

import "cloze.dart";
import "../ui/glyphs.dart";
import "../ui/look.dart";
import "../core/models.dart";
import "recall_status.dart";
import "recall.dart";
import "recall_cards.dart";
import "../study/reinforce.dart";
import "speed_topics.dart";
/// 易混数字一行的状态微点：与速记格子的微点（[StatusDot]）同一套样式，只换悬停措辞
/// ——口径是这一行自己的自测卡（填数、选择、反向），不是组级关联真题（ADR 0095、0101）。
class RecallRowDot extends StatelessWidget {
  const RecallRowDot({super.key, required this.status});

  final SymbolStatus status;

  @override
  Widget build(BuildContext context) {
    return StatusDot(
      status: status,
      tooltip: switch (status) {
        SymbolStatus.wrong => "这一行的自测题最近答错过，还没掌握",
        SymbolStatus.mastered => "这一行的自测题答对过",
        SymbolStatus.partial || SymbolStatus.fresh => "这一行还没自测过",
      },
    );
  }
}

/// 易混数字页（ADR 0028）：同类数字并排，配横条比大小，每行指到条文，每组能直接练专属题。
/// 与标志、标线、仪表、手势、考点各页同构：页面只管呈现与起练习，作答记录、练习队列由首页接上。
class NumbersPage extends StatelessWidget {
  const NumbersPage({
    super.key,
    required this.bank,
    required this.topic,
    required this.histories,
    required this.mastered,
    required this.onRecallAnswer,
    required this.pendingOf,
    required this.onStartPractice,
  });

  final Bank bank;

  /// 本页所属的专题（页键、科目、标题、导语都取自它）。
  final SpeedTopic topic;
  final HistorySet histories;
  final Set<String> mastered;

  /// 每次自测作答记一条作答记录（ADR 0094）。
  final RecallAnswerRecorder onRecallAnswer;

  /// 这些题里还要练的：首页按练习的出题规则筛（答对到答错 2 倍才算移出，ADR 0079）。
  final List<Question> Function(List<Question> questions) pendingOf;
  final void Function(List<Question> questions, String title, bool again) onStartPractice;

  List<CheatGroup> get _groups => cheatGroupsOf(bank, topic);

  /// 一个数字组的专属题（ADR 0102）：组内自测卡对应的题，行与题一对一。
  List<Question> _groupQuestions(CheatGroup group) => recallQuestionsOfNumberGroup(topic.id, _groups, group.id);

  /// 一行易混数字对应的自测卡题号：每条情形一张填数/选择卡（f/），这个值一张反向卡（r/）。
  /// 与 [recallCardsOfNumbers] 的卡 id 同构（ADR 0094）；反向卡按值合并，同值的行共用一张。
  /// 页键是专题 id——自测作答记的题号用它（ADR 0097 分科目后页键不再是 "numbers"）。
  List<String> _rowQuestionIds(CheatGroup group, CheatRow row) => [
    for (final single in splitCase(row.caseText)) recallQuestionId(topic.id, "f/${group.id}/$single|${row.value}"),
    recallQuestionId(topic.id, "r/${group.id}/${row.value}"),
  ];

  /// 行的状态微点档位（ADR 0101，三态）：这一行有答错过且未掌握的自测卡 → 红；
  /// 答对过（哪怕只答对了一部分卡）→ 绿；一张都没答过 → 灰。只看这一行自己的卡。
  SymbolStatus _rowStatus(CheatGroup group, CheatRow row) {
    final ids = _rowQuestionIds(group, row);
    final touched = [for (final id in ids) if (histories.byQuestion.containsKey(id)) id];
    if (touched.isEmpty) return SymbolStatus.fresh;
    if (touched.any((id) => (histories.byQuestion[id]?.wrong ?? 0) > 0 && !mastered.contains(id))) {
      return SymbolStatus.wrong;
    }
    return SymbolStatus.mastered;
  }

  /// 易混数字的自测（ADR 0095）：每行情形拆成单条，数值题手输（题干把数字挖成括号），非数值的值选择，
  /// 每个数值再出一张反向题（「12 分」对应哪一项）。作答记成普通作答记录，错题本、强化练习随之更新。
  void _recall(BuildContext context) {
    final cards = recallCardsOfNumbers(topic.id, _groups);
    RecallSession.show(
      context,
      onAnswer: onRecallAnswer,
      histories: histories,
      mastered: mastered,
      entries: [
        // 关联题就是这张卡自己（ADR 0102）：收尾的「去做这几个的题」练的是答错的卡，
        // 行与题一对一，不再指向组级正则捞出来的真题。
        for (final c in cards)
          RecallEntry.fromCard(
            c,
            front: _front(context, c),
            related: c.stem == null ? const [] : [recallQuestionOf(c, cards)],
          ),
      ],
      onStartPractice: (questions) => onStartPractice(questions, "易混数字 · 自测", false),
    );
  }

  /// 易混数字卡的正面：组名（小）加题干（大）。
  Widget _front(BuildContext context, RecallCard card) {
    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 560, minHeight: 100),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            card.inputLabel ?? "",
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            card.stem ?? "",
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700, height: 1.4),
          ),
        ],
      ),
    );
  }

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
            const Spacer(),
            FilledButton.tonalIcon(
              onPressed: () => _recall(context),
              icon: const Icon(Glyph.question, size: 18),
              label: const Text("自测"),
            ),
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
    final pending = pendingOf(related);
    final maxAmount = group.maxAmount;
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
              const Spacer(),
              FilledButton.icon(
                style: practiceButtonStyle(statusOf(related: related, mastered: mastered, histories: histories)),
                onPressed: () => onStartPractice(related, "易混数字 · ${group.title}", pending.isEmpty),
                icon: const Icon(Glyph.practice, size: 20),
                label: Text(pending.isEmpty ? "这组已掌握 · 再练一遍" : "练这组 ${pending.length} 题"),
              ),
            ],
          ),
          if (group.note.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(group.note, style: muted),
          ],
          const SizedBox(height: 12),
          for (final row in group.rows) _row(context, group, row, maxAmount, muted),
        ],
      ),
    );
  }

  Widget _row(BuildContext context, CheatGroup group, CheatRow row, double maxAmount, TextStyle? muted) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 2),
            child: RecallRowDot(status: _rowStatus(group, row)),
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
