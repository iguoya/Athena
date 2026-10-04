import "package:flutter/material.dart";

import "glyphs.dart";
import "look.dart";
import "models.dart";
import "sign.dart";

/// 标志速记页（ADR 0059）：手绘标志按「禁令 / 警告 / 指示 / 指路」四组摊开，
/// 每条配一句「看到之后怎么开」，每组能直接练相关的题。内容源是
/// `content/signs.json`（文件级出处 GB 5768.2），页面只负责呈现与起练习。
class SignsPage extends StatelessWidget {
  const SignsPage({
    super.key,
    required this.signs,
    required this.daily,
    required this.all,
    required this.mastered,
    required this.onStartPractice,
  });

  final List<RoadSign> signs;

  /// 科目一的日常题（非偏难）：「练这组」从这里按 `Question.sign` 取题。
  final List<Question> daily;

  /// 科目一全部题：算「还有几题在偏难里没进来」。
  final List<Question> all;
  final Set<String> mastered;
  final void Function(List<Question> questions, String title) onStartPractice;

  /// 组的顺序与每组的形状口诀；分组本身由 json 的 `kind` 决定。
  static const _groups = [
    (kind: "prohibit", hint: "红圈在说「不许」——红圈、红杠都是禁令。"),
    (kind: "warning", hint: "黄三角在提醒「当心」——见到先减速。"),
    (kind: "indicate", hint: "蓝盘告诉你「该怎么走」——照它走不违规。"),
    (kind: "guide", hint: "绿底白字报方向和距离，提前看、提前变道。"),
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
            Icon(Glyph.signs, color: Bs.paper),
            SizedBox(width: 8),
            Text("标志速记", style: TextStyle(fontSize: 32, fontWeight: FontWeight.w600)),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          "标志是路上的语言：先认形状，再记含义。红圈禁、黄三角警、蓝盘指、绿牌路；"
          "每张卡都写着「看到之后怎么开」，每组都能直接练相关的题。",
          style: Theme.of(context).textTheme.bodyLarge,
        ),
        for (final group in _groups)
          _signGroup(context, group.kind, group.hint, muted),
        const SizedBox(height: 24),
        Text(
          "分类与含义依据 GB 5768.2—2022《道路交通标志和标线 第 2 部分：道路交通标志》；"
          "图是应用内示意，认标志以路上实物为准。",
          style: muted,
        ),
      ],
    );
  }

  Widget _signGroup(BuildContext context, String kind, String hint, TextStyle? muted) {
    final inGroup = [for (final sign in signs) if (sign.kind == kind) sign];
    if (inGroup.isEmpty) return const SizedBox.shrink();
    final label = inGroup.first.kindLabel;
    final related = [
      for (final sign in inGroup)
        for (final q in daily)
          if (q.sign == sign.id) q,
    ];
    final pending = [for (final q in related) if (!mastered.contains(q.id)) q];
    final allRelated = [
      for (final sign in inGroup)
        for (final q in all)
          if (q.sign == sign.id) q,
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
                      : () => onStartPractice(related, "标志速记 · $label"),
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
              children: [for (final sign in inGroup) _SignCell(sign: sign)],
            ),
          ],
        ),
      ),
    );
  }
}

/// 标志速记的一个格子：手绘图 + 名称 + 「怎么开」。悬停上浮是唯一的动效，
/// 复用 BsCard 的语言与令牌（ADR 0059 决策 5）。
class _SignCell extends StatefulWidget {
  const _SignCell({required this.sign});

  final RoadSign sign;

  @override
  State<_SignCell> createState() => _SignCellState();
}

class _SignCellState extends State<_SignCell> {
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
              SignView(id: widget.sign.id, size: 96),
              const SizedBox(height: 10),
              Text(
                widget.sign.name,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, height: 1.2),
              ),
              if (widget.sign.band == QuestionBandColors.hot) ...[
                const SizedBox(height: 6),
                BsBadge(
                  text: "高频",
                  color: Bs.bandColor(QuestionBandColors.hot),
                  icon: Glyph.hot,
                ),
              ],
              const SizedBox(height: 6),
              Text(widget.sign.meaning, textAlign: TextAlign.center, style: muted),
            ],
          ),
        ),
      ),
    );
  }

  /// 点开看大图（ADR 0059）：速记格子里 96px 的图看细节不够，放大用玻璃浮层——
  /// 它本来就是「小面积浮层」的既定用途（ADR 0058），遮罩不遮暗，速记页还在身后。
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
              SignView(id: widget.sign.id, size: 192),
              const SizedBox(height: 14),
              Text(
                widget.sign.name,
                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              Text(
                widget.sign.meaning,
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
