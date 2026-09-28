import "dart:math";

import "package:flutter/material.dart";

import "brief.dart";
import "drill.dart";
import "guide.dart";
import "look.dart";
import "models.dart";
import "progress.dart";

/// 科目二（C2）：动画讲解、评判条目、评判题、练车错因记录（ADR 0036）。
class Subject2Page extends StatefulWidget {
  const Subject2Page({
    super.key,
    required this.bank,
    required this.store,
    required this.mastered,
    required this.runs,
    required this.onPractice,
    required this.onChanged,
  });

  final Bank bank;
  final ProgressStore store;
  final Set<String> mastered;

  /// 练车记录，新的在前。
  final List<DrillRun> runs;
  final void Function(List<Question> questions, String title) onPractice;
  final Future<void> Function() onChanged;

  @override
  State<Subject2Page> createState() => _Subject2PageState();
}

class _Subject2PageState extends State<Subject2Page> {
  String? _item;

  Subject2Guide get _guide => widget.bank.guide;

  Future<void> _record([String? itemId]) async {
    final result = await showDrillRunDialog(context, _guide, itemId ?? _item ?? _guide.items.first.id);
    if (result == null) return;
    await widget.store.recordDrillRun(result.$1, result.$2);
    await widget.onChanged();
    if (!mounted) return;
    final score = _guide.score(result.$1, result.$2);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text("记下了：${_guide.item(result.$1)?.title} · 按考场规则 ${score.label}${score.passed ? "，能过" : "，过不了"}"),
      ),
    );
  }

  List<Question> _pending(List<Question> qs) => [
    for (final q in qs)
      if (!widget.mastered.contains(q.id)) q,
  ];

  @override
  Widget build(BuildContext context) {
    final item = _item == null ? null : _guide.item(_item!);
    if (item != null) {
      return _ItemPage(
        key: ValueKey(item.id),
        item: item,
        guide: _guide,
        questions: widget.bank.forTopic(item.topicId),
        mastered: widget.mastered,
        runs: [
          for (final r in widget.runs)
            if (r.itemId == item.id) r,
        ],
        brief: buildBrief(_guide, widget.runs).item(item.id)!,
        onBack: () => setState(() => _item = null),
        onPractice: widget.onPractice,
        onRecord: () => _record(item.id),
      );
    }
    return _overview(context);
  }

  Widget _overview(BuildContext context) {
    final theme = Theme.of(context);
    final all = widget.bank.forSubject("subject2");
    final pending = _pending(all);
    final general = widget.bank.forTopic("drive.s2.general");
    final brief = buildBrief(_guide, widget.runs);
    return ListView(
      padding: const EdgeInsets.fromLTRB(28, 24, 28, 28),
      children: [
        Wrap(
          crossAxisAlignment: WrapCrossAlignment.center,
          spacing: 12,
          runSpacing: 8,
          children: [
            CircleAvatar(
              backgroundColor: Bs.paper.withValues(alpha: 0.15),
              child: const Icon(Icons.local_parking, color: Bs.paper),
            ),
            Text("科目二", style: theme.textTheme.headlineMedium),
            Text("场地驾驶技能 · 小型自动挡（C2）", style: theme.textTheme.titleMedium?.copyWith(color: Bs.secondary)),
            BsBadge(text: "满分 ${_guide.fullScore} · ${_guide.passScore} 分合格", color: Bs.success, icon: Icons.flag),
          ],
        ),
        const SizedBox(height: 12),
        Text(
          "考倒车入库、侧方停车、曲线行驶、直角转弯四项，评判以 GA 1026—2022 为准。点开每一项看动画讲解和评判条目；"
          "练完一把车记下出的错，按考场规则给自己打分，看哪一项、哪一类错反复出现。",
          style: theme.textTheme.bodyLarge,
        ),
        const SizedBox(height: 16),
        _BriefCard(brief: brief, onOpen: (id) => setState(() => _item = id)),
        const SizedBox(height: 16),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            FilledButton.icon(
              onPressed: pending.isEmpty ? null : () => widget.onPractice(all, "评判题"),
              icon: const Icon(Icons.quiz),
              label: Text(pending.isEmpty ? "评判题（已掌握）" : "练评判题 · 待练 ${pending.length}"),
            ),
            FilledButton.tonalIcon(onPressed: _record, icon: const Icon(Icons.edit_note), label: const Text("记一把练车")),
          ],
        ),
        const SizedBox(height: 24),
        Wrap(
          spacing: 16,
          runSpacing: 16,
          children: [
            for (final item in _guide.items)
              _ItemCard(
                item: item,
                questions: widget.bank.forTopic(item.topicId),
                mastered: widget.mastered,
                runs: [
                  for (final r in widget.runs)
                    if (r.itemId == item.id) r,
                ],
                guide: _guide,
                onTap: () => setState(() => _item = item.id),
              ),
          ],
        ),
        const SizedBox(height: 28),
        _DrillStats(guide: _guide, runs: widget.runs),
        const SizedBox(height: 28),
        _Section(
          icon: Icons.rule,
          title: "通用评判（每一项都适用）",
          trailing: general.isEmpty
              ? null
              : TextButton(
                  onPressed: _pending(general).isEmpty ? null : () => widget.onPractice(general, "合格标准与通用评判"),
                  child: Text("练这部分的题 · 待练 ${_pending(general).length}"),
                ),
          child: _RuleTable(rules: _guide.generalRules),
        ),
      ],
    );
  }
}

class _ItemCard extends StatelessWidget {
  const _ItemCard({
    required this.item,
    required this.questions,
    required this.mastered,
    required this.runs,
    required this.guide,
    required this.onTap,
  });

  final GuideItem item;
  final List<Question> questions;
  final Set<String> mastered;
  final List<DrillRun> runs;
  final Subject2Guide guide;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final done = questions.where((q) => mastered.contains(q.id)).length;
    final fails = item.rules.where((r) => r.level.fails).length;
    final passes = runs.where((r) => guide.score(item.id, r.mistakes).passed).length;
    return SizedBox(
      width: 380,
      child: Card(
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(child: Text(item.title, style: theme.textTheme.titleLarge)),
                    const Icon(Icons.play_circle, color: Bs.paper),
                  ],
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: [
                    BsBadge(text: "限时 ${item.limitText}", color: Bs.secondary, icon: Icons.timer),
                    BsBadge(text: "出线看${item.judgedBy}", color: Bs.secondary),
                  ],
                ),
                const SizedBox(height: 10),
                Text("不合格 $fails 条 · 扣分 ${item.rules.length - fails} 条", style: theme.textTheme.bodyMedium),
                const SizedBox(height: 10),
                Row(
                  children: [
                    SizedBox(
                      width: 110,
                      child: Text("评判题 $done/${questions.length}", style: theme.textTheme.bodyMedium),
                    ),
                    Expanded(
                      child: BsProgress(
                        value: questions.isEmpty ? 0 : done / questions.length,
                        color: done == questions.length ? Bs.success : Bs.paper,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  runs.isEmpty
                      ? "还没有练车记录"
                      : "练车 ${runs.length} 把 · 按考场规则能过 $passes 把（${(passes * 100 / runs.length).round()}%）",
                  style: theme.textTheme.bodyMedium?.copyWith(color: runs.isEmpty ? Bs.secondary : null),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _ItemPage extends StatefulWidget {
  const _ItemPage({
    super.key,
    required this.item,
    required this.guide,
    required this.questions,
    required this.mastered,
    required this.runs,
    required this.brief,
    required this.onBack,
    required this.onPractice,
    required this.onRecord,
  });

  final ItemBrief brief;
  final GuideItem item;
  final Subject2Guide guide;
  final List<Question> questions;
  final Set<String> mastered;
  final List<DrillRun> runs;
  final VoidCallback onBack;
  final void Function(List<Question> questions, String title) onPractice;
  final VoidCallback onRecord;

  @override
  State<_ItemPage> createState() => _ItemPageState();
}

class _ItemPageState extends State<_ItemPage> {
  final _player = GlobalKey<DrillPlayerState>();
  var _step = 0;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final item = widget.item;
    final scene = drillScenes[item.id]!;
    final pending = [
      for (final q in widget.questions)
        if (!widget.mastered.contains(q.id)) q,
    ];
    final player = DrillPlayer(
      key: _player,
      scene: scene,
      stepTitles: [for (final s in item.steps) s.title],
      onStep: (step) => setState(() => _step = step),
    );
    final steps = _StepList(
      steps: item.steps,
      current: _step,
      onTap: (i) {
        _player.currentState?.jumpTo(i);
        setState(() => _step = i);
      },
      onPlay: (i) => _player.currentState?.playStep(i),
    );
    return ListView(
      padding: const EdgeInsets.fromLTRB(28, 16, 28, 28),
      children: [
        Wrap(
          crossAxisAlignment: WrapCrossAlignment.center,
          spacing: 12,
          runSpacing: 8,
          children: [
            TextButton.icon(onPressed: widget.onBack, icon: const Icon(Icons.arrow_back), label: const Text("科目二")),
            Text(item.title, style: theme.textTheme.headlineMedium),
            BsBadge(text: "限时 ${item.limitText}", color: Bs.secondary, icon: Icons.timer),
            BsBadge(text: "出线看${item.judgedBy}", color: Bs.secondary),
          ],
        ),
        const SizedBox(height: 12),
        _ItemBriefCard(brief: widget.brief),
        const SizedBox(height: 16),
        LayoutBuilder(
          builder: (context, constraints) {
            if (constraints.maxWidth < 1000) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [player, const SizedBox(height: 16), steps],
              );
            }
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(flex: 3, child: player),
                const SizedBox(width: 20),
                Expanded(flex: 2, child: steps),
              ],
            );
          },
        ),
        const SizedBox(height: 20),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            FilledButton.icon(
              onPressed: pending.isEmpty ? null : () => widget.onPractice(widget.questions, item.title),
              icon: const Icon(Icons.quiz),
              label: Text(pending.isEmpty ? "评判题（已掌握）" : "练这一项的评判题 · 待练 ${pending.length}"),
            ),
            FilledButton.tonalIcon(
              onPressed: widget.onRecord,
              icon: const Icon(Icons.edit_note),
              label: const Text("记一把练车"),
            ),
          ],
        ),
        const SizedBox(height: 24),
        _Section(
          icon: Icons.menu_book,
          title: "操作要求（标准原文）",
          child: _Quote(text: item.requirementQuote, locator: item.requirementLocator),
        ),
        const SizedBox(height: 20),
        _Section(
          icon: Icons.rule,
          title: "评判",
          child: _RuleTable(rules: item.rules),
        ),
        const SizedBox(height: 20),
        _Section(
          icon: Icons.lightbulb_outline,
          title: "经验要点",
          trailing: Text(widget.guide.tipsNote, style: theme.textTheme.bodySmall?.copyWith(color: Bs.secondary)),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (final tip in item.tips)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Padding(
                        padding: EdgeInsets.only(top: 6),
                        child: Icon(Icons.circle, size: 8, color: Bs.paper),
                      ),
                      const SizedBox(width: 10),
                      Expanded(child: Text(tip, style: theme.textTheme.bodyLarge)),
                    ],
                  ),
                ),
            ],
          ),
        ),
        if (widget.runs.isNotEmpty) ...[
          const SizedBox(height: 20),
          _DrillStats(guide: widget.guide, runs: widget.runs, itemId: item.id),
        ],
      ],
    );
  }
}

String _ago(DateTime at) {
  final days = DateUtils.dateOnly(DateTime.now()).difference(DateUtils.dateOnly(at)).inDays;
  return switch (days) {
    0 => "今天",
    1 => "昨天",
    _ => "$days 天前",
  };
}

/// 总览顶部：今天练车的重点（ADR 0037）。
class _BriefCard extends StatelessWidget {
  const _BriefCard({required this.brief, required this.onOpen});

  final Brief brief;
  final ValueChanged<String> onOpen;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final lastAt = brief.lastAt;
    return Container(
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 14),
      decoration: BoxDecoration(
        color: Bs.warning.withValues(alpha: 0.12),
        border: Border.all(color: Bs.warning),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 10,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              const Icon(Icons.assignment_turned_in, color: Bs.orange),
              Text("今天练车的重点", style: theme.textTheme.titleMedium),
              Text(
                lastAt == null ? "还没有练车记录，先记几把，这里才有东西可说" : "上次练车：${_ago(lastAt)}",
                style: theme.textTheme.bodyMedium?.copyWith(color: Bs.secondary),
              ),
            ],
          ),
          const SizedBox(height: 8),
          for (final f in brief.focus)
            InkWell(
              onTap: () => onOpen(f.itemId),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    Icon(
                      switch (f.kind) {
                        FocusKind.mistake => Icons.error_outline,
                        FocusKind.weak => Icons.trending_down,
                        FocusKind.rehearsal => Icons.record_voice_over,
                        FocusKind.untried => Icons.fiber_new,
                      },
                      size: 20,
                      color: f.kind == FocusKind.mistake ? Bs.danger : Bs.secondary,
                    ),
                    const SizedBox(width: 8),
                    Expanded(child: Text(f.text, style: theme.textTheme.bodyLarge)),
                    const Icon(Icons.chevron_right, color: Bs.secondary),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}

/// 单项页顶部：这一项的简报。
class _ItemBriefCard extends StatelessWidget {
  const _ItemBriefCard({required this.brief});

  final ItemBrief brief;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final lastAt = brief.lastAt;
    final lines = <Widget>[
      Text(
        brief.neverPracticed
            ? "这一项还没记过练车。练完记一把，下次这里会告诉你该盯什么。"
            : "最近 ${brief.recent} 把能过 ${brief.passes} 把 · 上次练：${_ago(lastAt!)}",
        style: theme.textTheme.bodyLarge,
      ),
      if (brief.recurring.isNotEmpty) ...[
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 6,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            Text("反复出现：", style: theme.textTheme.bodyMedium),
            for (final r in brief.recurring)
              BsBadge(text: "${r.mistake.label} · ${r.runs} 把", color: levelColor(r.mistake.level)),
          ],
        ),
      ],
      if (brief.missedSteps.isNotEmpty) ...[
        const SizedBox(height: 8),
        Text(
          "上次默演卡在：${[for (final i in brief.missedSteps) "第 ${i + 1} 步「${brief.item.steps[i].title}」"].join("、")}",
          style: theme.textTheme.bodyMedium,
        ),
      ],
    ];
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      decoration: BoxDecoration(
        color: (brief.recurring.isNotEmpty || brief.weak ? Bs.warning : Bs.info).withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.assignment_turned_in, color: Bs.orange),
          const SizedBox(width: 10),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: lines)),
        ],
      ),
    );
  }
}

class _StepList extends StatelessWidget {
  const _StepList({required this.steps, required this.current, required this.onTap, required this.onPlay});

  final List<GuideStep> steps;
  final int current;
  final ValueChanged<int> onTap;
  final ValueChanged<int> onPlay;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (var i = 0; i < steps.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Material(
              color: i == current ? Bs.paper.withValues(alpha: 0.08) : Colors.transparent,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(6),
                side: BorderSide(color: i == current ? Bs.paper : Bs.border),
              ),
              child: InkWell(
                borderRadius: BorderRadius.circular(6),
                onTap: () => onTap(i),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(12, 10, 4, 10),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      CircleAvatar(
                        radius: 13,
                        backgroundColor: i == current ? Bs.paper : Bs.border,
                        child: Text(
                          "${i + 1}",
                          style: TextStyle(fontSize: 14, color: i == current ? Colors.white : Bs.dark),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(steps[i].title, style: theme.textTheme.titleMedium),
                            if (i == current) ...[
                              const SizedBox(height: 4),
                              Text(steps[i].body, style: theme.textTheme.bodyMedium),
                            ],
                          ],
                        ),
                      ),
                      IconButton(
                        tooltip: "播这一步",
                        onPressed: () => onPlay(i),
                        icon: const Icon(Icons.play_arrow, size: 20),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.icon, required this.title, required this.child, this.trailing});

  final IconData icon;
  final String title;
  final Widget child;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          crossAxisAlignment: WrapCrossAlignment.center,
          spacing: 8,
          runSpacing: 4,
          children: [
            Icon(icon, color: Bs.paper, size: 22),
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            ?trailing,
          ],
        ),
        const SizedBox(height: 10),
        child,
      ],
    );
  }
}

class _Quote extends StatelessWidget {
  const _Quote({required this.text, required this.locator});

  final String text;
  final String locator;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      decoration: const BoxDecoration(
        color: Bs.light,
        border: Border(left: BorderSide(color: Bs.paper, width: 4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(text, style: Theme.of(context).textTheme.bodyLarge),
          const SizedBox(height: 6),
          Text(locator, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Bs.secondary)),
        ],
      ),
    );
  }
}

Color levelColor(Level level) => level.fails
    ? Bs.danger
    : level.deduct >= 10
    ? Bs.orange
    : Bs.warning;

class _RuleTable extends StatelessWidget {
  const _RuleTable({required this.rules});

  final List<GuideRule> rules;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      children: [
        for (final r in rules)
          Tooltip(
            message: "${r.locator}：${r.quote}",
            waitDuration: const Duration(milliseconds: 300),
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 5),
              child: Row(
                children: [
                  SizedBox(
                    width: 110,
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: BsBadge(text: r.level.label, color: levelColor(r.level)),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(child: Text(r.text, style: theme.textTheme.bodyLarge)),
                  Text(
                    r.locator.replaceFirst("GA 1026—2022 ", ""),
                    style: theme.textTheme.bodySmall?.copyWith(color: Bs.secondary),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

/// 练车统计：记了就要给人看（主仓库 ADR 0052）。[itemId] 为空时统计全部项目。
class _DrillStats extends StatelessWidget {
  const _DrillStats({required this.guide, required this.runs, this.itemId});

  final Subject2Guide guide;
  final List<DrillRun> runs;
  final String? itemId;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (runs.isEmpty) {
      return _Section(
        icon: Icons.insights,
        title: "练车记录",
        child: Text(
          "还没有练车记录。练完一把车点「记一把练车」，勾上出的错，按考场规则打分。",
          style: theme.textTheme.bodyLarge?.copyWith(color: Bs.secondary),
        ),
      );
    }
    final scores = [for (final r in runs) guide.score(r.itemId, r.mistakes)];
    final passes = scores.where((s) => s.passed).length;
    // 错因按「在几把里出现过」计：同一把里中途停车三次也只算这一把出过这个错。
    final counts = <(String, String), int>{};
    for (final r in runs) {
      for (final id in r.mistakes.toSet()) {
        counts[(r.itemId, id)] = (counts[(r.itemId, id)] ?? 0) + 1;
      }
    }
    final top = counts.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
    final today = DateUtils.dateOnly(DateTime.now());
    final days = [
      for (var i = 13; i >= 0; i--)
        () {
          final day = today.subtract(Duration(days: i));
          final those = [
            for (var k = 0; k < runs.length; k++)
              if (DateUtils.isSameDay(runs[k].at, day)) k,
          ];
          return DailyCount(day: day, attempts: those.length, correct: those.where((k) => scores[k].passed).length);
        }(),
    ];
    final maxCount = top.isEmpty ? 1 : top.first.value;
    return _Section(
      icon: Icons.insights,
      title: itemId == null ? "练车记录" : "这一项的练车记录",
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              StatTile(icon: Icons.directions_car, label: "练了", value: "${runs.length} 把"),
              StatTile(
                icon: Icons.verified,
                label: "按考场规则能过",
                value: "$passes 把 · ${(passes * 100 / runs.length).round()}%",
                color: Bs.success,
              ),
              StatTile(
                icon: Icons.today,
                label: "最近 7 天",
                value: "${runs.where((r) => r.at.isAfter(today.subtract(const Duration(days: 7)))).length} 把",
                color: Bs.purple,
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text("最近两周（深色是按考场规则能过的）", style: theme.textTheme.bodyMedium?.copyWith(color: Bs.secondary)),
          const SizedBox(height: 6),
          DailyActivityChart(days: days),
          if (top.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text("最常出的错（在几把里出现过）", style: theme.textTheme.titleSmall),
            const SizedBox(height: 8),
            for (final e in top.take(8))
              () {
                final m = guide.mistake(e.key.$1, e.key.$2);
                if (m == null) return const SizedBox.shrink();
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    children: [
                      SizedBox(
                        width: 96,
                        child: BsBadge(text: m.level.label, color: levelColor(m.level)),
                      ),
                      const SizedBox(width: 8),
                      SizedBox(
                        width: 300,
                        child: Text(
                          itemId == null ? "${guide.item(e.key.$1)?.title ?? ""} · ${m.label}" : m.label,
                          style: theme.textTheme.bodyLarge,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: LayoutBuilder(
                          builder: (context, c) => Align(
                            alignment: Alignment.centerLeft,
                            child: Container(
                              width: max(6, c.maxWidth * e.value / maxCount),
                              height: 14,
                              decoration: BoxDecoration(
                                color: levelColor(m.level),
                                borderRadius: BorderRadius.circular(3),
                              ),
                            ),
                          ),
                        ),
                      ),
                      SizedBox(width: 60, child: Text("${e.value} 把", textAlign: TextAlign.right)),
                    ],
                  ),
                );
              }(),
          ],
          const SizedBox(height: 16),
          Text("最近几把", style: theme.textTheme.titleSmall),
          const SizedBox(height: 6),
          for (var k = 0; k < min(8, runs.length); k++)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 130,
                    child: Text(
                      "${runs[k].at.month}-${runs[k].at.day} ${runs[k].at.hour.toString().padLeft(2, "0")}:${runs[k].at.minute.toString().padLeft(2, "0")}",
                      style: theme.textTheme.bodyMedium?.copyWith(color: Bs.secondary),
                    ),
                  ),
                  if (itemId == null)
                    SizedBox(width: 110, child: Text(guide.item(runs[k].itemId)?.title ?? runs[k].itemId)),
                  SizedBox(
                    width: 96,
                    child: BsBadge(text: scores[k].label, color: scores[k].passed ? Bs.success : Bs.danger),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      runs[k].mistakes.isEmpty ? "没毛病" : _mistakeSummary(guide, runs[k]),
                      style: theme.textTheme.bodyMedium,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

String _mistakeSummary(Subject2Guide guide, DrillRun run) {
  final counts = <String, int>{};
  for (final id in run.mistakes) {
    counts[id] = (counts[id] ?? 0) + 1;
  }
  return [
    for (final e in counts.entries)
      "${guide.mistake(run.itemId, e.key)?.label ?? e.key}${e.value > 1 ? " ×${e.value}" : ""}",
  ].join("、");
}

/// 记一把练车：选项目、勾错因，实时按考场规则算分。返回（项目 id, 错因 id 列表）。
Future<(String, List<String>)?> showDrillRunDialog(BuildContext context, Subject2Guide guide, String initialItem) {
  return showDialog<(String, List<String>)>(
    context: context,
    builder: (context) => _DrillRunDialog(guide: guide, initialItem: initialItem),
  );
}

class _DrillRunDialog extends StatefulWidget {
  const _DrillRunDialog({required this.guide, required this.initialItem});

  final Subject2Guide guide;
  final String initialItem;

  @override
  State<_DrillRunDialog> createState() => _DrillRunDialogState();
}

class _DrillRunDialogState extends State<_DrillRunDialog> {
  late String _item = widget.initialItem;
  final _counts = <String, int>{};

  List<String> get _mistakes => [
    for (final e in _counts.entries)
      for (var i = 0; i < e.value; i++) e.key,
  ];

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final guide = widget.guide;
    final item = guide.item(_item)!;
    final score = guide.score(_item, _mistakes);
    Widget chip(Mistake m) {
      final n = _counts[m.id] ?? 0;
      return InputChip(
        selected: n > 0,
        showCheckmark: !m.repeat,
        avatar: CircleAvatar(backgroundColor: levelColor(m.level), radius: 6),
        label: Text("${m.label}${m.repeat && n > 0 ? " ×$n" : ""}  ${m.level.label}${m.repeat ? "/次" : ""}"),
        tooltip: m.locator,
        onPressed: () => setState(() {
          if (m.repeat) {
            _counts[m.id] = n + 1;
          } else if (n > 0) {
            _counts.remove(m.id);
          } else {
            _counts[m.id] = 1;
          }
        }),
        onDeleted: m.repeat && n > 0
            ? () => setState(() => n == 1 ? _counts.remove(m.id) : _counts[m.id] = n - 1)
            : null,
        deleteIcon: const Icon(Icons.remove, size: 18),
      );
    }

    return AlertDialog(
      title: const Text("记一把练车"),
      content: SizedBox(
        width: 720,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              SegmentedButton<String>(
                showSelectedIcon: false,
                segments: [for (final i in guide.items) ButtonSegment(value: i.id, label: Text(i.title))],
                selected: {_item},
                onSelectionChanged: (v) => setState(() {
                  _item = v.first;
                  _counts.clear();
                }),
              ),
              const SizedBox(height: 16),
              Text("${item.title}专项（按次计的错可以点多次）", style: theme.textTheme.titleSmall),
              const SizedBox(height: 8),
              Wrap(spacing: 8, runSpacing: 8, children: [for (final m in item.mistakes) chip(m)]),
              const SizedBox(height: 16),
              Text("通用", style: theme.textTheme.titleSmall),
              const SizedBox(height: 8),
              Wrap(spacing: 8, runSpacing: 8, children: [for (final m in guide.generalMistakes) chip(m)]),
              const SizedBox(height: 20),
              Row(
                children: [
                  Text("按考场规则：", style: theme.textTheme.titleMedium),
                  BsBadge(text: score.label, color: score.passed ? Bs.success : Bs.danger),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      score.failed
                          ? "不合格：${score.failReasons.join("、")}"
                          : score.passed
                          ? "${score.passScore} 分合格，这把能过"
                          : "不到 ${score.passScore} 分，这把过不了",
                      style: theme.textTheme.bodyMedium,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text("取消")),
        FilledButton(
          onPressed: () => Navigator.of(context).pop((_item, _mistakes)),
          child: Text(_counts.isEmpty ? "这把没毛病，记下" : "记下这一把"),
        ),
      ],
    );
  }
}
