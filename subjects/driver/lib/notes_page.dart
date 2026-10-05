import "package:flutter/material.dart";

import "glyphs.dart";
import "look.dart";
import "models.dart";
import "recall.dart";

/// 考点速记页（ADR 0064）：灯光、让行、高速、恶劣天气、应急避险、伤员急救的
/// 「情景 → 要点」对照。内容源是 `content/notes.json`，条级挂出处，每组能直接
/// 练相关的题。页面语言与易混数字、标志速记一致；没有横条比大小——那是数字
/// 组的表达。
class NotesPage extends StatelessWidget {
  const NotesPage({
    super.key,
    required this.groups,
    required this.daily,
    required this.mastered,
    required this.onStartPractice,
    this.title = "考点速记",
    this.icon = Glyph.notes,
    this.lead = "考场上没时间回想整章的内容，记得住的是「什么情景该做什么」这一句。"
        "灯光、让行、高速、恶劣天气、应急、急救——先看速记，再练相关的题。",
    this.footnote = "条目依据《道路交通安全法》《道路交通安全法实施条例》与 2022 版考试大纲，"
        "每题的完整解释在答题时给出。",
  });

  final List<NoteGroup> groups;
  final List<Question> daily;
  final Set<String> mastered;
  final void Function(List<Question> questions, String title) onStartPractice;

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
            const Spacer(),
            FilledButton.tonalIcon(
              onPressed: () => _startRecall(context),
              icon: const Icon(Glyph.question, size: 18),
              label: const Text("自我测验"),
            ),
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

  /// 自我测验（ADR 0080）：每个「情景」是一张卡，正面只给情景，揭示后看要点；
  /// 每轮抽 5 张。收尾深链练全部相关题。
  void _startRecall(BuildContext context) {
    RecallSession.show(
      context,
      prompt: "想一想：碰到这个情景该怎么做？要点有哪些？",
      entries: [
        for (final group in groups)
          for (final (i, item) in group.items.indexed)
            RecallEntry(
              id: "${group.id}/$i",
              front: _scenarioFront(context, group.title, item.scenario),
              name: "要点",
              meaning: [for (final point in item.points) "· $point"].join("\n"),
            ),
      ],
      onStartPractice: () {
        final seen = <String>{};
        final related = [
          for (final group in groups)
            for (final q in group.related(daily))
              if (seen.add(q.id)) q,
        ];
        if (related.isNotEmpty) onStartPractice(related, "$title · 自我测验");
      },
    );
  }

  Widget _scenarioFront(BuildContext context, String groupTitle, String scenario) {
    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 520, minHeight: 120),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            groupTitle,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            scenario,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700, height: 1.4),
          ),
        ],
      ),
    );
  }

  Widget _noteGroup(BuildContext context, NoteGroup group, TextStyle? muted) {
    final related = group.related(daily);
    final pending = [for (final q in related) if (!mastered.contains(q.id)) q];
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
                const Spacer(),
                FilledButton.icon(
                  onPressed: pending.isEmpty
                      ? null
                      : () => onStartPractice(related, "考点速记 · ${group.title}"),
                  icon: const Icon(Glyph.practice, size: 20),
                  label: Text(pending.isEmpty ? "这组已掌握" : "练这组 ${pending.length} 题"),
                ),
              ],
            ),
            if (group.note.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(group.note, style: muted),
            ],
            for (final (i, item) in group.items.indexed) _noteRow(context, item, muted, first: i == 0),
          ],
        ),
      ),
    );
  }

  Widget _noteRow(BuildContext context, NoteItem item, TextStyle? muted, {required bool first}) {
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
            padding: const EdgeInsets.only(top: 2),
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
