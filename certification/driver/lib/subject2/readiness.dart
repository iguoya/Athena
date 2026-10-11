import "guide.dart";
import "../core/progress.dart";
/// 整场就绪度（ADR 0039）。
///
/// GA 1026—2022 6.2.1：科目二四项合在一起算一个总分，满分 100、80 分合格；任何一项不合格
/// 即不合格。所以单项能过不等于整场能过——把每项最近几把的真实记录做全组合，数能过的组合。
/// 精确枚举（最多 5⁴ = 625 种），不抽样：同样的记录永远算出同一个数。

/// 每项取最近几把。
const readinessWindow = 5;

/// 一项少于这么多把，不给整场结论。
const readinessMinRuns = 3;

class ItemForm {
  const ItemForm({required this.item, required this.recent});

  final GuideItem item;

  /// 最近几把（≤ [readinessWindow]），新的在前。
  final List<(DrillRun, RunScore)> recent;

  bool get enough => recent.length >= readinessMinRuns;
  int get passes => recent.where((r) => r.$2.passed).length;
  double get passRate => recent.isEmpty ? 0 : passes / recent.length;
  int get fails => recent.where((r) => r.$2.failed).length;

  /// 没判不合格的那几把里平均扣几分。
  double get avgDeduct {
    final scored = [for (final r in recent) if (!r.$2.failed) r.$2];
    if (scored.isEmpty) return 0;
    return scored.map((s) => 100 - s.score).reduce((a, b) => a + b) / scored.length;
  }
}

class Culprit {
  const Culprit({required this.itemId, required this.mistake, required this.combos});

  final String itemId;
  final Mistake mistake;

  /// 在多少种过不了的组合里出现。
  final int combos;
}

class Readiness {
  const Readiness({required this.items, required this.combos, required this.passing, required this.culprits});

  final List<ItemForm> items;
  final int combos;
  final int passing;

  /// 过不了的组合里最常出现的错因，最多 3 个。
  final List<Culprit> culprits;

  bool get enough => items.every((i) => i.enough);

  /// 整场能过的比例；数据不够时为空。
  double? get rate => enough && combos > 0 ? passing / combos : null;

  List<ItemForm> get missing => [for (final i in items) if (!i.enough) i];
}

/// [runs] 新的在前（`ProgressStore.drillRuns` 的顺序）。
Readiness computeReadiness(Subject2Guide guide, List<DrillRun> runs) {
  final items = [
    for (final item in guide.items)
      ItemForm(
        item: item,
        recent: [
          for (final r in runs.where((r) => r.itemId == item.id).take(readinessWindow)) (r, guide.score(item.id, r.mistakes)),
        ],
      ),
  ];
  if (items.any((i) => !i.enough)) {
    return Readiness(items: items, combos: 0, passing: 0, culprits: const []);
  }
  final allowance = guide.fullScore - guide.passScore;
  var combos = 0;
  var passing = 0;
  final blame = <(String, String), int>{};

  void walk(int index, int deducted, bool failed, List<(String, DrillRun)> picked) {
    if (index == items.length) {
      combos++;
      if (!failed && deducted <= allowance) {
        passing++;
        return;
      }
      final seen = <(String, String)>{};
      for (final (itemId, run) in picked) {
        for (final id in run.mistakes) {
          if (seen.add((itemId, id))) blame[(itemId, id)] = (blame[(itemId, id)] ?? 0) + 1;
        }
      }
      return;
    }
    final form = items[index];
    for (final (run, score) in form.recent) {
      picked.add((form.item.id, run));
      walk(index + 1, deducted + (score.failed ? 0 : guide.fullScore - score.score), failed || score.failed, picked);
      picked.removeLast();
    }
  }

  walk(0, 0, false, []);
  final culprits = [
    for (final e in blame.entries)
      if (guide.mistake(e.key.$1, e.key.$2) case final m?) Culprit(itemId: e.key.$1, mistake: m, combos: e.value),
  ]..sort((a, b) => b.combos.compareTo(a.combos));
  return Readiness(items: items, combos: combos, passing: passing, culprits: culprits.take(3).toList());
}
