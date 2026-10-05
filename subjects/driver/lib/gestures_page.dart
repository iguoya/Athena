import "package:flutter/material.dart";

import "cheat_image.dart";
import "gesture_animation.dart";
import "gesture_painter.dart";
import "glyphs.dart";
import "look.dart";
import "models.dart";
import "recall.dart";
import "reinforce.dart";

/// 手势速记页（ADR 0073）：8 个法定手势动作加「手势的效力」总则，每条配一句
/// 「看到之后怎么开」，反向映射的 29 道题能直接练。内容源是
/// `content/gestures.json`（文件级出处：实施条例），页面只负责呈现与起练习。
class GesturesPage extends StatelessWidget {
  const GesturesPage({
    super.key,
    required this.gestures,
    required this.histories,
    required this.daily,
    required this.mastered,
    required this.onStartPractice,
  });

  final List<TrafficGesture> gestures;

  /// 作答历史：格子微点由它现算（ADR 0077 决策 3）。
  final HistorySet histories;

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
            const Spacer(),
            FilledButton.tonalIcon(
              onPressed: () => _startRecall(context),
              icon: const Icon(Glyph.question, size: 18),
              label: const Text("自我测验"),
            ),
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
                    child: Text("每个动作都是规范的交警动画，点开看大图", style: muted),
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
                children: [
                for (final g in actions)
                  _GestureCell(
                    gesture: g,
                    other: g.confuseWith == null
                        ? null
                        : actions.where((x) => x.id == g.confuseWith).firstOrNull,
                    status: statusOf(
                      related: [for (final q in daily) if (g.questions.contains(q.id)) q],
                      mastered: mastered,
                      histories: histories,
                    ),
                  ),
              ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        Text(
          "手势信号依据《道路交通安全法实施条例》与公安部《交通警察道路执勤执法工作规范》；"
          "动画取自交警手势的规范图解（已去掉画面里的名称文字），认手势以现场指挥为准。",
          style: muted,
        ),
      ],
    );
  }

  RecallEntry _recallEntryOf(TrafficGesture g) {
    final other = g.confuseWith == null
        ? null
        : gestures.where((x) => x.id == g.confuseWith).firstOrNull;
    return RecallEntry(
      id: g.id,
      front: _gestureImage(g, 288),
      name: g.name,
      meaning: g.meaning,
      confuseName: other?.name,
      confuseNote: g.confuseNote,
      confuseView: other == null ? null : _gestureImage(other, 144),
    );
  }

  /// 手势动画（ADR 0080）：规范的交警手势 GIF，循环自己播；GIF 读不出来时
  /// 退回应用内绘制的示意动画（ADR 0078，那套代码保留作兜底）。
  static Widget _gestureImage(TrafficGesture g, double size) => CheatImage(
    path: g.image,
    width: size,
    fallback: (side) => GestureAnimation(id: g.id, size: side),
  );

  /// 自我测验：每轮抽 5 个手势，收尾深链练全部相关题（ADR 0077、0080）。
  void _startRecall(BuildContext context) {
    RecallSession.show(
      context,
      // 「手势的效力」是总则、没有规范动画，不进自我测验；它的相关题仍并入深链。
      entries: [for (final g in gestures) if (g.kind != "general") _recallEntryOf(g)],
      onStartPractice: () {
        final ids = {for (final g in gestures) ...g.questions};
        final related = [for (final q in daily) if (ids.contains(q.id)) q];
        if (related.isNotEmpty) onStartPractice(related, "手势速记 · 自我测验");
      },
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
  const _GestureCell({required this.gesture, required this.status, this.other});

  final TrafficGesture gesture;
  final SymbolStatus status;

  /// 易混对（ADR 0077 决策 2）：浮层里双图对照。
  final TrafficGesture? other;

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
          width: 232,
          transform: Matrix4.translationValues(0, _hover ? -2 : 0, 0),
          padding: const EdgeInsets.fromLTRB(12, 14, 12, 12),
          decoration: BoxDecoration(
            color: Bs.light,
            borderRadius: BorderRadius.circular(Bs.radius),
            boxShadow: _hover ? Bs.hoverShadow : Bs.cardShadow,
          ),
          child: Stack(
            children: [
              Positioned(
                right: 0,
                top: 0,
                child: StatusDot(status: widget.status),
              ),
              Column(
            children: [
              GesturesPage._gestureImage(widget.gesture, 192),
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
              GesturesPage._gestureImage(widget.gesture, 320),
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
                      GesturesPage._gestureImage(widget.other!, 144),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text("容易混：${widget.other!.name}", style: Theme.of(dialogContext).textTheme.titleSmall),
                            const SizedBox(height: 4),
                            Text(widget.gesture.confuseNote ?? "", style: TextStyle(
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
