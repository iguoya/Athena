import "package:flutter/material.dart";

import "gesture_painter.dart";
import "glyphs.dart";
import "look.dart";
import "models.dart";

/// 手势速记页（ADR 0073）：8 个法定手势动作加「手势的效力」总则，每条配一句
/// 「看到之后怎么开」，反向映射的 29 道题能直接练。内容源是
/// `content/gestures.json`（文件级出处：实施条例），页面只负责呈现与起练习。
class GesturesPage extends StatelessWidget {
  const GesturesPage({
    super.key,
    required this.gestures,
    required this.daily,
    required this.mastered,
    required this.onStartPractice,
  });

  final List<TrafficGesture> gestures;

  /// 科目一与科目四的日常题：「练这组」按反向映射的题 id 从这里取题。
  final List<Question> daily;
  final Set<String> mastered;
  final void Function(List<Question> questions, String title) onStartPractice;

  @override
  Widget build(BuildContext context) {
    final muted = Theme.of(context).textTheme.bodyMedium?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
      height: 1.45,
    );
    final general = gestures.where((g) => g.kind == "general").toList();
    final actions = gestures.where((g) => g.kind != "general").toList();
    final relatedIds = {for (final g in gestures) ...g.questions};
    final related = [for (final q in daily) if (relatedIds.contains(q.id)) q];
    final pending = [for (final q in related) if (!mastered.contains(q.id)) q];
    return ListView(
      padding: const EdgeInsets.fromLTRB(36, 28, 36, 32),
      children: [
        Row(
          children: [
            Icon(Glyph.gestures, color: Bs.paper),
            SizedBox(width: 8),
            Text("手势速记", style: TextStyle(fontSize: 32, fontWeight: FontWeight.w600)),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          "交警的手势是效力最强的信号：现场有交警就听交警的。"
          "看图题最大的坑是方向——交警面向你，他的左右和你看到的相反。",
          style: Theme.of(context).textTheme.bodyLarge,
        ),
        if (general.isNotEmpty) ...[
          const SizedBox(height: 20),
          for (final g in general) _generalCard(context, g, muted),
        ],
        const SizedBox(height: 12),
        BsCard(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("8 个法定动作", style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(width: 10),
                  Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: Text("看伸直臂是交警哪只手、摆动臂往哪摆", style: muted),
                  ),
                  const Spacer(),
                  FilledButton.icon(
                    onPressed: pending.isEmpty
                        ? null
                        : () => onStartPractice(related, "手势速记"),
                    icon: const Icon(Glyph.practice, size: 20),
                    label: Text(pending.isEmpty ? "已全部掌握" : "练手势 ${pending.length} 题"),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              Wrap(
                spacing: 14,
                runSpacing: 14,
                children: [for (final g in actions) _GestureCell(gesture: g)],
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        Text(
          "手势信号依据《道路交通安全法实施条例》与公安部《交通警察道路执勤执法工作规范》；"
          "图是应用内示意，认手势以现场指挥为准。",
          style: muted,
        ),
      ],
    );
  }

  Widget _generalCard(BuildContext context, TrafficGesture g, TextStyle? muted) {
    return BsCard(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          GestureView(id: g.id, size: 64),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(g.name, style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 4),
                Text(g.meaning, style: muted),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// 手势速记的一个格子：手绘图 + 名称 + 「看到之后怎么开」。交互与标志、标线、
/// 仪表格一致：悬停上浮，点开玻璃浮层看大图。
class _GestureCell extends StatefulWidget {
  const _GestureCell({required this.gesture});

  final TrafficGesture gesture;

  @override
  State<_GestureCell> createState() => _GestureCellState();
}

class _GestureCellState extends State<_GestureCell> {
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
              GestureView(id: widget.gesture.id, size: 96),
              const SizedBox(height: 10),
              Text(
                widget.gesture.name,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, height: 1.2),
              ),
              if (widget.gesture.band == QuestionBandColors.hot) ...[
                const SizedBox(height: 6),
                BsBadge(
                  text: "高频",
                  color: Bs.bandColor(QuestionBandColors.hot),
                  icon: Glyph.hot,
                ),
              ],
              const SizedBox(height: 6),
              Text(widget.gesture.meaning, textAlign: TextAlign.center, style: muted),
            ],
          ),
        ),
      ),
    );
  }

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
              GestureView(id: widget.gesture.id, size: 192),
              const SizedBox(height: 14),
              Text(
                widget.gesture.name,
                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              Text(
                widget.gesture.meaning,
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
