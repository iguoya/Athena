import "guide.dart";
import "progress.dart";

/// 练车前简报（ADR 0037）：全部由练车记录推导，没有记录就不给建议。

/// 每项只看最近几把。
const briefWindow = 5;

/// 在窗口里出现几把算「反复出现」。
const briefRecurringRuns = 2;

/// 最近几把能过的比例低于这个，这一项要重点练。
const briefWeakRate = 0.6;

/// 总览最多列几条重点。
const briefFocusLimit = 3;

class RecurringMistake {
  const RecurringMistake({required this.mistake, required this.runs});

  final Mistake mistake;

  /// 在最近几把里出现在几把中（同一把里出现多次只算一把）。
  final int runs;
}

class ItemBrief {
  const ItemBrief({
    required this.item,
    required this.recent,
    required this.passes,
    required this.lastAt,
    required this.recurring,
    this.missedSteps = const [],
  });

  final GuideItem item;

  /// 窗口里有几把（≤ [briefWindow]）。
  final int recent;
  final int passes;
  final DateTime? lastAt;
  final List<RecurringMistake> recurring;

  /// 最近一次默演卡住的步骤（下标）。
  final List<int> missedSteps;

  bool get neverPracticed => recent == 0;
  bool get weak => recent > 0 && passes / recent < briefWeakRate;
}

enum FocusKind { mistake, weak, untried, rehearsal }

class FocusLine {
  const FocusLine({required this.itemId, required this.kind, required this.text});

  final String itemId;
  final FocusKind kind;
  final String text;
}

class Brief {
  const Brief({required this.items, required this.focus, required this.lastAt});

  final List<ItemBrief> items;
  final List<FocusLine> focus;
  final DateTime? lastAt;

  ItemBrief? item(String id) {
    for (final b in items) {
      if (b.item.id == id) return b;
    }
    return null;
  }

  bool get empty => lastAt == null;
}

/// 档位排序：不合格最重，其次扣 10 分，再次扣 5 分。
int severity(Mistake m) => m.level.fails ? 0 : (m.level.deduct >= 10 ? 1 : 2);

/// [runs] 新的在前（`ProgressStore.drillRuns` 的顺序）。[missedSteps] 是每项最近一次默演卡住的步骤。
Brief buildBrief(Subject2Guide guide, List<DrillRun> runs, {Map<String, List<int>> missedSteps = const {}}) {
  final items = <ItemBrief>[];
  for (final item in guide.items) {
    final mine = [for (final r in runs) if (r.itemId == item.id) r].take(briefWindow).toList();
    final counts = <String, int>{};
    for (final r in mine) {
      for (final id in r.mistakes.toSet()) {
        counts[id] = (counts[id] ?? 0) + 1;
      }
    }
    final recurring = [
      for (final e in counts.entries)
        if (e.value >= briefRecurringRuns)
          if (guide.mistake(item.id, e.key) case final m?) RecurringMistake(mistake: m, runs: e.value),
    ]..sort((a, b) {
        final bySeverity = severity(a.mistake).compareTo(severity(b.mistake));
        return bySeverity != 0 ? bySeverity : b.runs.compareTo(a.runs);
      });
    items.add(ItemBrief(
      item: item,
      recent: mine.length,
      passes: mine.where((r) => guide.score(item.id, r.mistakes).passed).length,
      lastAt: mine.isEmpty ? null : mine.first.at,
      recurring: recurring,
      missedSteps: missedSteps[item.id] ?? const [],
    ));
  }

  // 重点：反复出现的错（按档位、把数）→ 能过比例低的项 → 默演卡住的项 → 没练过的项。
  final mistakes = [
    for (final b in items)
      for (final r in b.recurring) (b, r),
  ]..sort((x, y) {
      final bySeverity = severity(x.$2.mistake).compareTo(severity(y.$2.mistake));
      return bySeverity != 0 ? bySeverity : y.$2.runs.compareTo(x.$2.runs);
    });
  final focus = <FocusLine>[
    for (final (b, r) in mistakes)
      FocusLine(
        itemId: b.item.id,
        kind: FocusKind.mistake,
        text: "${b.item.title} · ${r.mistake.label}（${r.mistake.level.label}）：最近 ${b.recent} 把里出了 ${r.runs} 把",
      ),
    for (final b in items)
      if (b.weak)
        FocusLine(itemId: b.item.id, kind: FocusKind.weak, text: "${b.item.title}：最近 ${b.recent} 把只能过 ${b.passes} 把"),
    for (final b in items)
      if (b.missedSteps.isNotEmpty)
        FocusLine(
          itemId: b.item.id,
          kind: FocusKind.rehearsal,
          text: "${b.item.title}：上次默演卡在${[for (final i in b.missedSteps) "第 ${i + 1} 步"].join("、")}",
        ),
    for (final b in items)
      if (b.neverPracticed) FocusLine(itemId: b.item.id, kind: FocusKind.untried, text: "${b.item.title}：还没记过练车"),
  ];
  // 同一项只留最重的一条，免得三条重点全是同一项。
  final seen = <String>{};
  final picked = [
    for (final f in focus)
      if (seen.add(f.itemId)) f,
  ].take(briefFocusLimit).toList();
  return Brief(items: items, focus: picked, lastAt: runs.isEmpty ? null : runs.first.at);
}
