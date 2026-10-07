import "package:flutter/material.dart";

import "recall_status.dart";
import "cheat_image.dart";
import "../ui/glyphs.dart";
import "../ui/look.dart";
import "marking.dart";
import "../core/models.dart";
import "../study/reinforce.dart";
import "recall_cards.dart";
/// 标线速记页（ADR 0065）：手绘标线按「指示 / 禁止 / 警告」三组摊开，每条配一句
/// 「看到之后怎么开」，每组能直接自测。内容源是 `content/markings.json`
/// （文件级出处 GB 5768.3），页面只负责呈现与起练习。
class MarkingsPage extends StatelessWidget {
  const MarkingsPage({
    super.key,
    required this.markings,
    required this.histories,
    this.recallPage = "s1.markings",
    this.subjectLabel = "科目一",
    required this.onStartRecall,
  });

  final List<Marking> markings;

  /// 作答历史：格子微点由它现算——只看这一条自己的自测卡（ADR 0077 决策 3、0112）。
  final HistorySet histories;

  /// 本专题的页键（`s1.signs` 这样，作答记录里的题号带它）与所属科目的名称（ADR 0096）。
  final String recallPage;
  final String subjectLabel;
  
  /// 组里的「自测」：交出这一组卡的题号，首页按条目内容现场出题、起一轮做题（ADR 0118）。
  final void Function(List<String> questionIds, String title) onStartRecall;

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
          ],
        ),
        const SizedBox(height: 8),
        Text(
          "路面也在说话：黄线分对向、白线分同向，虚线可跨越、实线不许越。"
          "每张卡都写着「看到之后怎么开」，每组都能直接自测。",
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

  /// 标线图（ADR 0080）：题库官方题图，横向场景，按 4:3 取框；读不出来时退回
  /// 手绘俯视图。
  static Widget _markingImage(Marking marking, double width) => CheatImage(
    path: marking.image,
    width: width,
    height: width * 3 / 4,
    fallback: (side) => MarkingView(id: marking.id, size: side),
  );

  Widget _markingGroup(BuildContext context, String kind, String hint, TextStyle? muted) {
    final inGroup = [for (final marking in markings) if (marking.kind == kind) marking];
    if (inGroup.isEmpty) return const SizedBox.shrink();
    final label = inGroup.first.kindLabel;
    // 组状态只看这一组的自测卡（ADR 0112）：给组内「自测」按钮上色——红 = 有答错未掌握、绿 = 全部答对过、灰 = 没测完。
    final ids = [for (final marking in inGroup) recallQuestionId(recallPage, marking.id)];
    final status = statusOfIds(ids: ids, histories: histories);
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
                MasteryTag(entries: singleEntries(ids), histories: histories),
                const Spacer(),
                GroupRecallButton(
                  status: status,
                  ids: ids,
                  histories: histories,
                  onStart: () => onStartRecall(ids, "标线速记 · $label · 自测"),
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
                for (final marking in inGroup)
                  _MarkingCell(
                    marking: marking,
                    other: marking.confuseWith == null
                        ? null
                        : inGroup.where((m) => m.id == marking.confuseWith).firstOrNull,
                    status: statusOfIds(
                      ids: [recallQuestionId(recallPage, marking.id)],
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
