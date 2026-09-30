import "package:flutter/material.dart";

import "glyphs.dart";
import "guide.dart";
import "look.dart";
import "progress.dart";

/// 复盘今天（ADR 0039）：练完回家一次录入整天——今天练了哪几项、每项几把、每把错在哪、
/// 教练说了什么。每一把写成一条练车记录（ADR 0036），教练的话写进 drill_notes。
Future<bool?> showDayReview(BuildContext context, {required Subject2Guide guide, required ProgressStore store}) {
  return showDialog<bool>(
    context: context,
    barrierDismissible: false,
    builder: (context) => Dialog.fullscreen(child: DayReview(guide: guide, store: store)),
  );
}

/// 一项的录入：几把、每把的错、教练的话。
class _ItemDraft {
  _ItemDraft(this.item);

  final GuideItem item;
  var rounds = 3;
  final counts = <int, Map<String, int>>{};
  final note = TextEditingController();

  List<String> mistakesOf(int round) => [
        for (final e in (counts[round] ?? const <String, int>{}).entries)
          for (var i = 0; i < e.value; i++) e.key,
      ];

  int count(int round, String id) => counts[round]?[id] ?? 0;

  void tap(int round, Mistake m) {
    final row = counts.putIfAbsent(round, () => {});
    final n = row[m.id] ?? 0;
    if (m.repeat) {
      row[m.id] = n + 1;
    } else if (n > 0) {
      row.remove(m.id);
    } else {
      row[m.id] = 1;
    }
  }

  void untap(int round, Mistake m) {
    final row = counts[round];
    final n = row?[m.id] ?? 0;
    if (n <= 1) {
      row?.remove(m.id);
    } else {
      row![m.id] = n - 1;
    }
  }
}

class DayReview extends StatefulWidget {
  const DayReview({super.key, required this.guide, required this.store});

  final Subject2Guide guide;
  final ProgressStore store;

  @override
  State<DayReview> createState() => _DayReviewState();
}

class _DayReviewState extends State<DayReview> {
  late final _drafts = {for (final i in widget.guide.items) i.id: _ItemDraft(i)};
  final _chosen = <String>{};
  var _saving = false;

  @override
  void dispose() {
    for (final d in _drafts.values) {
      d.note.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    // 同一天的每一把错开 1 毫秒，保住先后顺序，也让同步去重（项目 + 时间）不误伤。
    var at = DateTime.now();
    for (final item in widget.guide.items) {
      if (!_chosen.contains(item.id)) continue;
      final draft = _drafts[item.id]!;
      for (var r = 0; r < draft.rounds; r++) {
        await widget.store.recordDrillRun(item.id, draft.mistakesOf(r), at: at);
        at = at.add(const Duration(milliseconds: 1));
      }
      final note = draft.note.text.trim();
      if (note.isNotEmpty) await widget.store.recordDrillNote(item.id, note, at: at);
    }
    if (mounted) Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final total = [for (final id in _chosen) _drafts[id]!.rounds].fold(0, (a, b) => a + b);
    return Scaffold(
      appBar: AppBar(
        title: const Text("复盘今天"),
        automaticallyImplyLeading: false,
        actions: [
          TextButton(onPressed: _saving ? null : () => Navigator.of(context).pop(false), child: const Text("取消")),
          const SizedBox(width: 8),
          FilledButton.icon(
            onPressed: _chosen.isEmpty || _saving ? null : _save,
            icon: const Icon(Glyph.save),
            label: Text(_chosen.isEmpty ? "先选今天练了哪几项" : "保存今天 $total 把"),
          ),
          const SizedBox(width: 16),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(28, 20, 28, 40),
        children: [
          Text("今天练了哪几项？", style: theme.textTheme.titleMedium),
          const SizedBox(height: 8),
          Wrap(
            spacing: 10,
            children: [
              for (final item in widget.guide.items)
                FilterChip(
                  label: Text(item.title),
                  selected: _chosen.contains(item.id),
                  onSelected: (v) => setState(() => v ? _chosen.add(item.id) : _chosen.remove(item.id)),
                ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            "每一把都记，能过的也记——就绪度按最近几把算，只记坏的会偏低。点格子记错，按次计的错可以点多次，右键或长按减一次。",
            style: theme.textTheme.bodyMedium?.copyWith(color: Bs.secondary),
          ),
          for (final item in widget.guide.items)
            if (_chosen.contains(item.id)) _itemGrid(context, _drafts[item.id]!),
        ],
      ),
    );
  }

  Widget _itemGrid(BuildContext context, _ItemDraft draft) {
    final theme = Theme.of(context);
    final guide = widget.guide;
    final rows = [...draft.item.mistakes, ...guide.generalMistakes];
    const cellWidth = 86.0;
    Widget cell(Widget child, {double width = cellWidth, Color? color}) => Container(
          width: width,
          height: 40,
          alignment: Alignment.center,
          decoration: BoxDecoration(color: color, border: Border.all(color: Bs.border, width: 0.5)),
          child: child,
        );
    return Padding(
      padding: const EdgeInsets.only(top: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(draft.item.title, style: theme.textTheme.titleLarge),
              const SizedBox(width: 16),
              Text("练了 ${draft.rounds} 把", style: theme.textTheme.bodyLarge),
              IconButton(
                tooltip: "少一把",
                onPressed: draft.rounds > 1
                    ? () => setState(() {
                          draft.counts.remove(draft.rounds - 1);
                          draft.rounds--;
                        })
                    : null,
                icon: const Icon(Glyph.less),
              ),
              IconButton(
                tooltip: "多一把",
                onPressed: draft.rounds < 12 ? () => setState(() => draft.rounds++) : null,
                icon: const Icon(Glyph.more),
              ),
            ],
          ),
          const SizedBox(height: 6),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    cell(Text("错因", style: theme.textTheme.titleSmall), width: 300, color: Bs.light),
                    for (var r = 0; r < draft.rounds; r++)
                      cell(Text("第 ${r + 1} 把", style: theme.textTheme.titleSmall), color: Bs.light),
                  ],
                ),
                for (final m in rows)
                  Row(
                    children: [
                      cell(
                        Row(
                          children: [
                            const SizedBox(width: 8),
                            CircleAvatar(radius: 5, backgroundColor: levelColor(m.level)),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                "${m.label}${draft.item.mistakes.contains(m) ? "" : "（通用）"}",
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            Text("${m.level.label}${m.repeat ? "/次" : ""}  ", style: theme.textTheme.bodySmall),
                          ],
                        ),
                        width: 300,
                      ),
                      for (var r = 0; r < draft.rounds; r++)
                        GestureDetector(
                          key: ValueKey("review-${draft.item.id}-$r-${m.id}"),
                          onSecondaryTap: () => setState(() => draft.untap(r, m)),
                          onLongPress: () => setState(() => draft.untap(r, m)),
                          child: InkWell(
                            onTap: () => setState(() => draft.tap(r, m)),
                            child: cell(
                              Text(
                                switch (draft.count(r, m.id)) {
                                  0 => "",
                                  1 => m.repeat ? "×1" : "✗",
                                  final n => "×$n",
                                },
                                style: TextStyle(color: levelColor(m.level), fontWeight: FontWeight.w700, fontSize: 18),
                              ),
                              color: draft.count(r, m.id) > 0 ? levelColor(m.level).withValues(alpha: 0.12) : null,
                            ),
                          ),
                        ),
                    ],
                  ),
                Row(
                  children: [
                    cell(Text("这一把按考场规则", style: theme.textTheme.titleSmall), width: 300, color: Bs.light),
                    for (var r = 0; r < draft.rounds; r++)
                      () {
                        final score = guide.score(draft.item.id, draft.mistakesOf(r));
                        return cell(
                          Text(score.label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                          color: score.passed ? Bs.success : Bs.danger,
                        );
                      }(),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),
          SizedBox(
            width: 720,
            child: TextField(
              controller: draft.note,
              minLines: 2,
              maxLines: 5,
              decoration: InputDecoration(
                border: const OutlineInputBorder(),
                labelText: "教练说了什么（${draft.item.title}）",
                hintText: "原话最好，比如「车尾到库角再打，别急」",
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// 评判档位的颜色：不合格红、扣 10 分橙、扣 5 分黄。
Color levelColor(Level level) => level.fails
    ? Bs.danger
    : level.deduct >= 10
        ? Bs.orange
        : Bs.warning;
