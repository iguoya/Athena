import "package:flutter/material.dart";

import "cheat_image.dart";
import "gauge.dart";
import "glyphs.dart";
import "look.dart";
import "models.dart";
import "recall.dart";
import "reinforce.dart";
import "selftest_store.dart";

/// 仪表速记页（ADR 0067）：手绘车内符号按「报警灯 / 指示灯 / 仪表表盘 /
/// 开关与操纵件」四组摊开，每条配一句「亮了怎么办 / 这是什么」，每组能直接
/// 练相关的题。内容源是 `content/gauges.json`（文件级出处 GB 4094），相关题
/// 由每条的反向映射声明（决策 3），页面只负责呈现与起练习。
class GaugesPage extends StatelessWidget {
  const GaugesPage({
    super.key,
    required this.gauges,
    required this.histories,
    required this.daily,
    required this.mastered,
    required this.selfTest,
    required this.onStartPractice,
  });

  final List<Gauge> gauges;

  /// 作答历史：格子微点由它现算（ADR 0077 决策 3）。
  final HistorySet histories;

  /// 科目一的日常题（非偏难）：「练这组」按反向映射的题 id 从这里取题。
  final List<Question> daily;
  final Set<String> mastered;

  /// 自测的「认得了没有」记录（ADR 0082）。
  final SelfTestStore selfTest;
  final void Function(List<Question> questions, String title) onStartPractice;

  /// 组的顺序与每组的读法口诀；分组本身由 json 的 `kind` 决定。
  static const _groups = [
    (kind: "alarm", hint: "红色亮了先处理，黄色亮了尽快查——这些灯都在说「车有问题」。"),
    (kind: "indicate", hint: "蓝绿只是告诉你什么开着：蓝远光、绿近光，会车记得换。"),
    (kind: "dial", hint: "四个表盘读数：车速、转速、水温、油量，行车时扫一眼心里有数。"),
    (kind: "control", hint: "开关与操纵件：认得符号才知道拧的是哪一路，别等下雨再找刮水器。"),
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
            Icon(Glyph.gauges, color: Bs.paper),
            SizedBox(width: 8),
            Text("仪表速记", style: TextStyle(fontSize: 32, fontWeight: FontWeight.w600)),
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
          "车也在跟你说话：红黄是报警，蓝绿是指示，表盘给读数，开关看符号。"
          "每张卡都写着「亮了怎么办」，每组都能直接练相关的题。",
          style: Theme.of(context).textTheme.bodyLarge,
        ),
        for (final group in _groups)
          _gaugeGroup(context, group.kind, group.hint, muted),
        const SizedBox(height: 24),
        Text(
          "符号与含义依据 GB 4094—2016《汽车操纵件、指示器及信号装置的标志》；"
          "图用题库里的官方题图（座舱图里的问号是题目指的位置），认符号以车内实物为准。",
          style: muted,
        ),
      ],
    );
  }

  RecallEntry _recallEntryOf(Gauge gauge) {
    final other = gauge.confuseWith == null
        ? null
        : gauges.where((g) => g.id == gauge.confuseWith).firstOrNull;
    return RecallEntry(
      id: gauge.id,
      front: _gaugeImage(gauge, 360),
      related: [for (final q in daily) if (gauge.questions.contains(q.id)) q],
      name: gauge.name,
      meaning: gauge.meaning,
      confuseName: other?.name,
      confuseNote: gauge.confuseNote,
      confuseView: other == null ? null : _gaugeImage(other, 168),
    );
  }

  /// 仪表图（ADR 0080）：题库官方题图（报警灯/指示灯裁成方图，表盘与座舱图原样），
  /// 按 4:3 取框；胎压、ESC 灯题库没有图，退回手绘符号。
  static Widget _gaugeImage(Gauge gauge, double width) => CheatImage(
    path: gauge.image,
    width: width,
    height: width * 3 / 4,
    fallback: (side) => GaugeView(id: gauge.id, size: side),
  );

  /// 自测：每轮抽 5 个符号，收尾深链练全部相关题（ADR 0077、0080）。
  void _startRecall(BuildContext context) {
    RecallSession.show(
      context,
      pageKey: "gauges",
      store: selfTest,
      histories: histories,
      mastered: mastered,
      entries: [for (final g in gauges) _recallEntryOf(g)],
      onStartPractice: (questions) => onStartPractice(questions, "仪表速记 · 自测"),
    );
  }

  Widget _gaugeGroup(BuildContext context, String kind, String hint, TextStyle? muted) {
    final inGroup = [for (final gauge in gauges) if (gauge.kind == kind) gauge];
    if (inGroup.isEmpty) return const SizedBox.shrink();
    final label = inGroup.first.kindLabel;
    final relatedIds = {for (final gauge in inGroup) ...gauge.questions};
    final related = [for (final q in daily) if (relatedIds.contains(q.id)) q];
    final pending = [for (final q in related) if (!mastered.contains(q.id)) q];
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
                      : () => onStartPractice(related, "仪表速记 · $label"),
                  icon: const Icon(Glyph.practice, size: 20),
                  label: Text(pending.isEmpty ? "这组已掌握" : "练这组 ${pending.length} 题"),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(hint, style: muted),
            const SizedBox(height: 14),
            Wrap(
              spacing: 14,
              runSpacing: 14,
              children: [
                for (final gauge in inGroup)
                  _GaugeCell(
                    gauge: gauge,
                    other: gauge.confuseWith == null
                        ? null
                        : inGroup.where((g) => g.id == gauge.confuseWith).firstOrNull,
                    status: statusOf(
                      related: [for (final q in daily) if (gauge.questions.contains(q.id)) q],
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

/// 仪表速记的一个格子：手绘符号 + 名称 + 「亮了怎么办」。交互与标志、标线格
/// 一致：悬停上浮，点开玻璃浮层看大图。
class _GaugeCell extends StatefulWidget {
  const _GaugeCell({required this.gauge, required this.status, this.other});

  final Gauge gauge;
  final SymbolStatus status;

  /// 易混对（ADR 0077 决策 2）：浮层里双图对照。
  final Gauge? other;

  @override
  State<_GaugeCell> createState() => _GaugeCellState();
}

class _GaugeCellState extends State<_GaugeCell> {
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
          width: 256,
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
              GaugesPage._gaugeImage(widget.gauge, 232),
              const SizedBox(height: 10),
              Text(
                widget.gauge.name,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, height: 1.2),
              ),
              if (widget.gauge.band == QuestionBandColors.hot) ...[
                const SizedBox(height: 6),
                BsBadge(
                  text: "高频",
                  color: Bs.bandColor(QuestionBandColors.hot),
                  icon: Glyph.hot,
                ),
              ],
              const SizedBox(height: 6),
              Text(widget.gauge.meaning, textAlign: TextAlign.center, style: muted),
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
              GaugesPage._gaugeImage(widget.gauge, 400),
              const SizedBox(height: 14),
              Text(
                widget.gauge.name,
                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              Text(
                widget.gauge.meaning,
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
                      GaugesPage._gaugeImage(widget.other!, 168),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text("容易混：${widget.other!.name}", style: Theme.of(dialogContext).textTheme.titleSmall),
                            const SizedBox(height: 4),
                            Text(widget.gauge.confuseNote ?? "", style: TextStyle(
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
