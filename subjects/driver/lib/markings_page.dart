import "package:flutter/material.dart";

import "practice_button.dart";
import "cheat_image.dart";
import "glyphs.dart";
import "look.dart";
import "marking.dart";
import "models.dart";
import "recall.dart";
import "reinforce.dart";
import "recall_cards.dart";

/// 标线速记页（ADR 0065）：手绘标线按「指示 / 禁止 / 警告」三组摊开，每条配一句
/// 「看到之后怎么开」，每组能直接练相关的题。内容源是 `content/markings.json`
/// （文件级出处 GB 5768.3），页面只负责呈现与起练习。
class MarkingsPage extends StatelessWidget {
  const MarkingsPage({
    super.key,
    required this.markings,
    required this.histories,
    required this.daily,
    required this.all,
    required this.mastered,
    required this.onRecallAnswer,
    this.recallPage = "s1.markings",
    this.subjectLabel = "科目一",
    required this.onStartPractice,
  });

  final List<Marking> markings;

  /// 作答历史：格子微点由它现算（ADR 0077 决策 3）。
  final HistorySet histories;

  /// 科目一的日常题（非偏难）：「练这组」从这里按 `Question.marking` 取题。
  final List<Question> daily;

  /// 科目一全部题：算「还有几题在偏难里没进来」。
  final List<Question> all;
  final Set<String> mastered;

  /// 每次自测作答记一条作答记录（ADR 0094）：首页接上，写进进度库。
  final RecallAnswerRecorder onRecallAnswer;

  /// 本专题的页键（`s1.signs` 这样，作答记录里的题号带它）与所属科目的名称（ADR 0096）。
  final String recallPage;
  final String subjectLabel;
  final void Function(List<Question> questions, String title, bool again) onStartPractice;

  /// 组的顺序与每组的读法口诀；分组本身由 json 的 `kind` 决定，三分法与题库一致
  /// （s1.signals.055/476、s1.signals.266 的口径）。
  static const _groups = [
    (kind: "indicative", hint: "白色在告诉你往哪走：照指示走，虚线可跨越、实线守住车道。"),
    (kind: "prohibit", hint: "黄线分对向、实线不许越：黄实线禁跨越，网格和导流线里别停别压。"),
    (kind: "warning", hint: "这些线在提醒你提前减速：车道变窄、前方有障碍、该拉开距离了。"),
  ];

  @override
  Widget build(BuildContext context) {
    final muted = Theme.of(context).textTheme.bodyMedium?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
      height: 1.45,
    );
    return ListView(
      padding: const EdgeInsets.fromLTRB(36, 28, 36, 32),
      children: [
        Row(
          children: [
            Icon(Glyph.markings, color: Bs.paper),
            SizedBox(width: 8),
            Text("标线速记", style: TextStyle(fontSize: 32, fontWeight: FontWeight.w600)),
            const SizedBox(width: 12),
            BsBadge(text: subjectLabel, color: Bs.primary),
            const Spacer(),
            FilledButton.tonalIcon(
              onPressed: () => _startRecall(context),
              icon: const Icon(Glyph.question, size: 18),
              label: const Text("自测"),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          "路面也在说话：黄线分对向、白线分同向，虚线可跨越、实线不许越。"
          "每张卡都写着「看到之后怎么开」，每组都能直接练相关的题。",
          style: Theme.of(context).textTheme.bodyLarge,
        ),
        for (final group in _groups)
          _markingGroup(context, group.kind, group.hint, muted),
        const SizedBox(height: 24),
        Text(
          "分组与含义依据 GB 5768.3—2009《道路交通标志和标线 第 3 部分：道路交通标线》；"
          "图用题库里的官方题图（带红圈的是题目指的位置），认标线以路上实物为准。",
          style: muted,
        ),
      ],
    );
  }

  RecallEntry _recallEntryOf(Marking marking, RecallCard card) {
    final other = marking.confuseWith == null
        ? null
        : markings.where((x) => x.id == marking.confuseWith).firstOrNull;
    return RecallEntry.fromCard(
      card,
      front: _markingImage(marking, 400),
      related: [for (final q in daily) if (q.marking == marking.id) q],
      confuseView: other == null ? null : _markingImage(other, 168),
    );
  }

  /// 标线图（ADR 0080）：题库官方题图，横向场景，按 4:3 取框；读不出来时退回
  /// 手绘俯视图。
  static Widget _markingImage(Marking marking, double width) => CheatImage(
    path: marking.image,
    width: width,
    height: width * 3 / 4,
    fallback: (side) => MarkingView(id: marking.id, size: side),
  );

  /// 自测：把没认得的标线逐张过完，收尾深链练相关题（ADR 0077、0090）。
  void _startRecall(BuildContext context) {
    final cards = {for (final c in recallCardsOfMarkings(recallPage, markings)) c.id: c};
    RecallSession.show(
      context,
      onAnswer: onRecallAnswer,
      histories: histories,
      mastered: mastered,
      entries: [for (final m in markings) _recallEntryOf(m, cards[m.id]!)],
      onStartPractice: (questions) => onStartPractice(questions, "标线速记 · 自测", false),
    );
  }

  Widget _markingGroup(BuildContext context, String kind, String hint, TextStyle? muted) {
    final inGroup = [for (final marking in markings) if (marking.kind == kind) marking];
    if (inGroup.isEmpty) return const SizedBox.shrink();
    final label = inGroup.first.kindLabel;
    final related = [
      for (final marking in inGroup)
        for (final q in daily)
          if (q.marking == marking.id) q,
    ];
    final pending = [for (final q in related) if (!mastered.contains(q.id)) q];
    final allRelated = [
      for (final marking in inGroup)
        for (final q in all)
          if (q.marking == marking.id) q,
    ];
    final locked = allRelated.length - related.length;
    return Padding(
      padding: const EdgeInsets.only(top: 28),
      child: BsCard(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(width: 10),
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text("${inGroup.length} 种", style: muted),
                ),
                const Spacer(),
                FilledButton.icon(
                  style: practiceButtonStyle(statusOf(related: related, mastered: mastered, histories: histories)),
                  onPressed: () => onStartPractice(related, "标线速记 · $label", pending.isEmpty),
                  icon: const Icon(Glyph.practice, size: 20),
                  label: Text(pending.isEmpty ? "这组已掌握 · 再练一遍" : "练这组 ${pending.length} 题"),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(hint, style: muted),
            if (locked > 0) ...[
              const SizedBox(height: 4),
              Text("还有 $locked 道相关题在偏难里，不挡过关。", style: muted),
            ],
            const SizedBox(height: 14),
            Wrap(
              spacing: 14,
              runSpacing: 14,
              children: [
                for (final marking in inGroup)
                  _MarkingCell(
                    marking: marking,
                    other: marking.confuseWith == null
                        ? null
                        : inGroup.where((m) => m.id == marking.confuseWith).firstOrNull,
                    status: statusOf(
                      related: [for (final q in daily) if (q.marking == marking.id) q],
                      mastered: mastered,
                      histories: histories,
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// 标线速记的一个格子：手绘俯视图 + 名称 + 「怎么开」。交互与标志格一致：
/// 悬停上浮，点开玻璃浮层看大图（ADR 0061）。
class _MarkingCell extends StatefulWidget {
  const _MarkingCell({required this.marking, required this.status, this.other});

  final Marking marking;
  final SymbolStatus status;

  /// 易混对（ADR 0077 决策 2）：浮层里双图对照。
  final Marking? other;

  @override
  State<_MarkingCell> createState() => _MarkingCellState();
}

class _MarkingCellState extends State<_MarkingCell> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final muted = Theme.of(context).textTheme.bodySmall?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
      height: 1.35,
    );
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: GestureDetector(
        onTap: () => _zoom(context),
        child: AnimatedContainer(
          duration: Bs.durFast,
          curve: Curves.easeOut,
          width: 304,
          transform: Matrix4.translationValues(0, _hover ? -2 : 0, 0),
          padding: const EdgeInsets.fromLTRB(12, 14, 12, 12),
          decoration: BoxDecoration(
            color: Bs.light,
            borderRadius: BorderRadius.circular(Bs.radius),
            boxShadow: _hover ? Bs.hoverShadow : Bs.cardShadow,
          ),
          child: Column(
            children: [
              MarkingsPage._markingImage(widget.marking, 280),
              const SizedBox(height: 10),
              // 状态点在图标下方、条目文字左侧（ADR 0101：与行点同一套样式）。
              Row(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  StatusDot(status: widget.status),
                  const SizedBox(width: 8),
                  Flexible(
                    child: Text(
                      widget.marking.name,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, height: 1.2),
                    ),
                  ),
                ],
              ),
              if (widget.marking.band == QuestionBandColors.hot) ...[
                const SizedBox(height: 6),
                BsBadge(
                  text: "高频",
                  color: Bs.bandColor(QuestionBandColors.hot),
                  icon: Glyph.hot,
                ),
              ],
              const SizedBox(height: 6),
              Text(widget.marking.meaning, textAlign: TextAlign.center, style: muted),
            ],
          ),
        ),
      ),
    );
  }

  /// 点开看大图：与标志速记同一只玻璃浮层——遮罩不遮暗，速记页还在身后。
  void _zoom(BuildContext context) {
    showDialog<void>(
      context: context,
      barrierColor: Colors.transparent,
      builder: (dialogContext) => Dialog(
        insetPadding: const EdgeInsets.all(32),
        backgroundColor: Colors.transparent,
        child: GlassPanel(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              MarkingsPage._markingImage(widget.marking, 440),
              const SizedBox(height: 14),
              Text(
                widget.marking.name,
                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              Text(
                widget.marking.meaning,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 16,
                  height: 1.45,
                  color: Theme.of(dialogContext).colorScheme.onSurfaceVariant,
                ),
              ),
              if (widget.other != null) ...[
                const SizedBox(height: 14),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Bs.light,
                    borderRadius: BorderRadius.circular(Bs.radius),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      MarkingsPage._markingImage(widget.other!, 168),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text("容易混：${widget.other!.name}", style: Theme.of(dialogContext).textTheme.titleSmall),
                            const SizedBox(height: 4),
                            Text(widget.marking.confuseNote ?? "", style: TextStyle(
                              fontSize: 14,
                              height: 1.45,
                              color: Theme.of(dialogContext).colorScheme.onSurfaceVariant,
                            )),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
