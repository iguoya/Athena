import "package:flutter/material.dart";

import "glyphs.dart";
import "look.dart";
import "marking.dart";
import "models.dart";

/// 标线速记页（ADR 0065）：手绘标线按「指示 / 禁止 / 警告」三组摊开，每条配一句
/// 「看到之后怎么开」，每组能直接练相关的题。内容源是 `content/markings.json`
/// （文件级出处 GB 5768.3），页面只负责呈现与起练习。
class MarkingsPage extends StatelessWidget {
  const MarkingsPage({
    super.key,
    required this.markings,
    required this.daily,
    required this.all,
    required this.mastered,
    required this.onStartPractice,
  });

  final List<Marking> markings;

  /// 科目一的日常题（非偏难）：「练这组」从这里按 `Question.marking` 取题。
  final List<Question> daily;

  /// 科目一全部题：算「还有几题在偏难里没进来」。
  final List<Question> all;
  final Set<String> mastered;
  final void Function(List<Question> questions, String title) onStartPractice;

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
          "图是应用内俯视示意，认标线以路上实物为准。",
          style: muted,
        ),
      ],
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
                  onPressed: pending.isEmpty
                      ? null
                      : () => onStartPractice(related, "标线速记 · $label"),
                  icon: const Icon(Glyph.practice, size: 20),
                  label: Text(pending.isEmpty ? "这组已掌握" : "练这组 ${pending.length} 题"),
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
              children: [for (final marking in inGroup) _MarkingCell(marking: marking)],
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
  const _MarkingCell({required this.marking});

  final Marking marking;

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
          width: 176,
          transform: Matrix4.translationValues(0, _hover ? -2 : 0, 0),
          padding: const EdgeInsets.fromLTRB(12, 14, 12, 12),
          decoration: BoxDecoration(
            color: Bs.light,
            borderRadius: BorderRadius.circular(Bs.radius),
            boxShadow: _hover ? Bs.hoverShadow : Bs.cardShadow,
          ),
          child: Column(
            children: [
              MarkingView(id: widget.marking.id, size: 96),
              const SizedBox(height: 10),
              Text(
                widget.marking.name,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, height: 1.2),
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
              MarkingView(id: widget.marking.id, size: 192),
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
            ],
          ),
        ),
      ),
    );
  }
}
