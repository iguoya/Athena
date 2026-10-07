import "package:flutter/material.dart";

import "recall_status.dart";
import "../ui/glyphs.dart";
import "../ui/look.dart";
import "../core/models.dart";
import "../study/reinforce.dart";
import "recall_cards.dart";
/// 考点速记页（ADR 0064）：灯光、让行、高速、恶劣天气、应急避险、伤员急救的
/// 「情景 → 要点」对照。内容源是 `content/notes.json`，条级挂出处，每组能直接
/// 自测。页面语言与易混数字、标志速记一致；没有横条比大小——那是数字
/// 组的表达。
class NotesPage extends StatelessWidget {
  static const defaultLead = "考场上没时间回想整章的内容，记得住的是「什么情景该做什么」这一句。"
      "灯光、让行、高速、恶劣天气、应急、急救——先看速记，再按组自测。";
  static const defaultFootnote = "条目依据《道路交通安全法》《道路交通安全法实施条例》与 2022 版考试大纲，"
      "每题的完整解释在答题时给出。";

  const NotesPage({
    super.key,
    required this.groups,
    required this.histories,
    required this.onStartRecall,
    this.recallPage = "s1.keypoints",
    this.subjectLabel = "科目一",
    this.title = "考点速记",
    this.icon = Glyph.notes,
    this.lead = defaultLead,
    this.footnote = defaultFootnote,
  });

  final List<NoteGroup> groups;

  
  /// 组里的「自测」：交出这一组卡的题号，首页按条目内容现场出题、起一轮做题（ADR 0118）。
  final void Function(List<String> questionIds, String title) onStartRecall;

  /// 作答历史：自测按它判断哪些卡还要考（ADR 0094）。
  final HistorySet histories;

  /// 本页的速记页键（作答记录里的题号带它）：考点、河南、记分证照三页共用本组件，各用各的。
  final String recallPage;
  final String subjectLabel;

  /// 页面标题与图标：同一组件承载同一类「情景 → 要点对照」的内容，
  /// 河南速记（ADR 0068）传自己的标题、图标与脚注。
  final String title;
  final IconData icon;
  final String lead;
  final String footnote;

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
            Icon(icon, color: Bs.paper),
            SizedBox(width: 8),
            Text(title, style: TextStyle(fontSize: 32, fontWeight: FontWeight.w600)),
            const SizedBox(width: 12),
            BsBadge(text: subjectLabel, color: Bs.primary),
          ],
        ),
        const SizedBox(height: 8),
        Text(lead, style: Theme.of(context).textTheme.bodyLarge),
        for (final group in groups) _noteGroup(context, group, muted),
        const SizedBox(height: 24),
        Text(footnote, style: muted),
      ],
    );
  }

  Widget _noteGroup(BuildContext context, NoteGroup group, TextStyle? muted) {
    // 组状态只看这一组的自测卡（ADR 0112）：给组内「自测」按钮上色——红 = 有答错未掌握、绿 = 全部答对过、灰 = 没测完。
    final ids = [
        for (final i in group.items) recallQuestionId(recallPage, "${group.id}/${i.scenario}"),
      ];
    final status = statusOfIds(ids: ids, histories: histories);
    return Padding(
      padding: const EdgeInsets.only(top: 28),
      child: BsCard(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(group.title, style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(width: 10),
                Text("${group.items.length} 条", style: muted),
                MasteryTag(entries: singleEntries(ids), histories: histories),
                const Spacer(),
                GroupRecallButton(
                  status: status,
                  ids: ids,
                  histories: histories,
                  onStart: () => onStartRecall(ids, "$title · ${group.title} · 自测"),
                ),
              ],
            ),
            if (group.note.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(group.note, style: muted),
            ],
            for (final (i, item) in group.items.indexed)
              _noteRow(
                context,
                item,
                muted,
                first: i == 0,
                // 条目左侧的状态点：这一条自己那张自测卡的作答（ADR 0101、0112、0113）。
                status: statusOfIds(
                  ids: [recallQuestionId(recallPage, "${group.id}/${item.scenario}")],
                  histories: histories,
                ),
                remaining: recallRetireGap([recallQuestionId(recallPage, "${group.id}/${item.scenario}")], histories),
              ),
          ],
        ),
      ),
    );
  }

  Widget _noteRow(
    BuildContext context,
    NoteItem item,
    TextStyle? muted, {
    required bool first,
    required SymbolStatus status,
    int remaining = 0,
  }) {
    final source = [
      Bs.sourceShort(item.sourceId),
      if (item.locator.isNotEmpty) item.locator,
    ].join(" · ");
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (!first) ...[
          const SizedBox(height: 10),
          Divider(height: 1, color: Bs.border),
          const SizedBox(height: 10),
        ],
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            StatusDot(status: status, remaining: remaining),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                item.scenario,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600, height: 1.4),
              ),
            ),
            const SizedBox(width: 12),
            Text(source, style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            )),
          ],
        ),
        const SizedBox(height: 4),
        for (final point in item.points)
          Padding(
            // 左缩进 38 = 状态点 28 + 间距 10，要点与情景文字对齐。
            padding: const EdgeInsets.only(top: 2, left: 38),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.only(top: 9, right: 8),
                  child: Icon(Glyph.bullet, size: 5, color: Bs.primary),
                ),
                Expanded(
                  child: Text(point, style: const TextStyle(fontSize: 16, height: 1.45)),
                ),
              ],
            ),
          ),
      ],
    );
  }
}
