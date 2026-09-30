import "dart:math";

import "package:flutter/material.dart";

import "glyphs.dart";
import "brief.dart";
import "drill.dart";
import "guide.dart";
import "look.dart";
import "narration.dart";
import "models.dart";
import "points.dart";
import "readiness.dart";
import "progress.dart";
import "rehearsal.dart";
import "review.dart";

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
  Map<(String, int), PointNote> _notes = const {};
  List<PointPhoto> _photos = const [];
  List<Rehearsal> _rehearsals = const [];
  List<DrillNote> _drillNotes = const [];
  var _tab = _Tab.day;

  Subject2Guide get _guide => widget.bank.guide;

  @override
  void initState() {
    super.initState();
    _loadLocal();
  }

  /// 点位卡和默演记录只有科目二用，自己读，不经首页。
  Future<void> _loadLocal() async {
    final notes = await widget.store.pointNotes();
    final photos = await widget.store.pointPhotos();
    final rehearsals = await widget.store.rehearsals();
    final drillNotes = await widget.store.drillNotes();
    if (!mounted) return;
    setState(() {
      _notes = notes;
      _photos = photos;
      _rehearsals = rehearsals;
      _drillNotes = drillNotes;
    });
  }

  /// 每项最近一次默演卡住的步骤（ADR 0037）。
  Map<String, List<int>> get _missedSteps {
    final out = <String, List<int>>{};
    for (final r in _rehearsals) {
      out.putIfAbsent(r.itemId, () => r.missed);
    }
    return out;
  }

  Brief get _brief => buildBrief(_guide, widget.runs, missedSteps: _missedSteps);

  Readiness get _readiness => computeReadiness(_guide, widget.runs);

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
        brief: _brief.item(item.id)!,
        store: widget.store,
        notes: _notes,
        photos: _photos,
        onPointsChanged: _loadLocal,
        coachNotes: [
          for (final n in _drillNotes)
            if (n.itemId == item.id) n,
        ],
        onBack: () => setState(() => _item = null),
        onPractice: widget.onPractice,
        onRecord: () => _record(item.id),
      );
    }
    return _overview(context);
  }

  Widget _overview(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(28, 20, 28, 12),
          child: Wrap(
            crossAxisAlignment: WrapCrossAlignment.center,
            spacing: 12,
            runSpacing: 10,
            children: [
              CircleAvatar(
                backgroundColor: Bs.paper.withValues(alpha: 0.15),
                child: const Icon(Glyph.subject2, color: Bs.paper),
              ),
              Text("科目二", style: theme.textTheme.headlineMedium),
              Text("场地驾驶技能 · 小型自动挡（C2）", style: theme.textTheme.titleMedium?.copyWith(color: Bs.secondary)),
              const SizedBox(width: 12),
              SegmentedButton<_Tab>(
                showSelectedIcon: false,
                segments: const [
                  ButtonSegment(value: _Tab.day, icon: Icon(Glyph.practiceDay), label: Text("练车日")),
                  ButtonSegment(value: _Tab.handbook, icon: Icon(Glyph.handbook), label: Text("项目手册")),
                  ButtonSegment(value: _Tab.log, icon: Icon(Glyph.log), label: Text("练车日志")),
                  ButtonSegment(value: _Tab.exam, icon: Icon(Glyph.examReady), label: Text("考前")),
                ],
                selected: {_tab},
                onSelectionChanged: (v) => setState(() => _tab = v.first),
              ),
            ],
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: switch (_tab) {
            _Tab.day => _dayTab(context),
            _Tab.handbook => _handbookTab(context),
            _Tab.log => _logTab(context),
            _Tab.exam => _examTab(context),
          },
        ),
      ],
    );
  }

  Future<void> _reviewToday() async {
    final saved = await showDayReview(context, guide: _guide, store: widget.store);
    if (saved != true) return;
    await widget.onChanged();
    await _loadLocal();
  }

  Future<void> _preDrill() async {
    final ids = <String>{for (final f in _brief.focus) f.itemId};
    final items = ids.isEmpty ? _guide.items : [for (final i in _guide.items) if (ids.contains(i.id)) i];
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (context) => Dialog.fullscreen(
        child: _PreDrill(
          items: items,
          brief: _brief,
          store: widget.store,
          notes: _notes,
          photos: _photos,
          coachNotes: _drillNotes,
          onChanged: _loadLocal,
        ),
      ),
    );
  }

  /// 四项连起来默演一遍：一项做完接下一项，中途「不做了」就停。
  Future<void> _rehearseAll() async {
    for (final item in _guide.items) {
      if (!mounted) return;
      final done = await showRehearsal(
        context,
        item: item,
        store: widget.store,
        notes: _notes,
        photos: _photos,
        onChanged: _loadLocal,
      );
      if (!done) return;
    }
  }

  // ---------------------------------------------------------------- 练车日

  Widget _dayTab(BuildContext context) {
    final theme = Theme.of(context);
    final today = DateUtils.dateOnly(DateTime.now());
    final todayRuns = [for (final r in widget.runs) if (DateUtils.isSameDay(r.at, today)) r];
    final before = _Panel(
      icon: Glyph.beforeDrill,
      title: "练车前",
      children: [
        _BriefCard(brief: _brief, onOpen: (id) => setState(() => _item = id)),
        const SizedBox(height: 12),
        FilledButton.icon(
          onPressed: _preDrill,
          icon: const Icon(Glyph.brief),
          label: const Text("练车前 5 分钟：过点位卡、默演重点项"),
        ),
      ],
    );
    final after = _Panel(
      icon: Glyph.afterDrill,
      title: "练车后",
      children: [
        Text(
          "回家趁还记得，一次把今天录完：练了哪几项、每项几把、每把错在哪、教练说了什么。",
          style: theme.textTheme.bodyLarge,
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            FilledButton.icon(onPressed: _reviewToday, icon: const Icon(Glyph.review), label: const Text("复盘今天")),
            TextButton.icon(onPressed: _record, icon: const Icon(Glyph.record), label: const Text("只补一把")),
          ],
        ),
        const SizedBox(height: 12),
        if (todayRuns.isEmpty)
          Text("今天还没有记录。", style: theme.textTheme.bodyMedium?.copyWith(color: Bs.secondary))
        else
          _DaySummary(guide: _guide, runs: todayRuns, notes: const [], title: "今天已记下"),
      ],
    );
    return ListView(
      padding: const EdgeInsets.fromLTRB(28, 20, 28, 28),
      children: [
        _ReadinessCard(readiness: _readiness, lastAt: _brief.lastAt, onDetail: () => setState(() => _tab = _Tab.exam)),
        const SizedBox(height: 16),
        LayoutBuilder(
          builder: (context, c) => c.maxWidth < 1000
              ? Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [before, const SizedBox(height: 16), after])
              : Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [Expanded(child: before), const SizedBox(width: 16), Expanded(child: after)],
                ),
        ),
      ],
    );
  }

  // ---------------------------------------------------------------- 项目手册

  Widget _handbookTab(BuildContext context) {
    final theme = Theme.of(context);
    return ListView(
      padding: const EdgeInsets.fromLTRB(28, 20, 28, 28),
      children: [
        Text(
          "点进每一项：动画讲解、自己的点位卡、教练说过的话、默演、标准原文和评判条目。",
          style: theme.textTheme.bodyLarge,
        ),
        const SizedBox(height: 16),
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
      ],
    );
  }

  // ---------------------------------------------------------------- 练车日志

  Widget _logTab(BuildContext context) {
    final theme = Theme.of(context);
    final days = <DateTime, List<DrillRun>>{};
    for (final r in widget.runs) {
      days.putIfAbsent(DateUtils.dateOnly(r.at), () => []).add(r);
    }
    final noteDays = <DateTime, List<DrillNote>>{};
    for (final n in _drillNotes) {
      noteDays.putIfAbsent(DateUtils.dateOnly(n.at), () => []).add(n);
    }
    final dates = {...days.keys, ...noteDays.keys}.toList()..sort((a, b) => b.compareTo(a));
    return ListView(
      padding: const EdgeInsets.fromLTRB(28, 20, 28, 28),
      children: [
        _Section(
          icon: Glyph.trend,
          title: "按练车日看每一项能过的比例",
          child: Column(
            children: [
              for (final item in _guide.items) _TrendRow(guide: _guide, item: item, runs: widget.runs),
            ],
          ),
        ),
        const SizedBox(height: 24),
        if (dates.isEmpty)
          Text("还没有练车记录。练完在「练车日」里复盘今天。", style: theme.textTheme.bodyLarge?.copyWith(color: Bs.secondary))
        else
          for (final d in dates)
            Padding(
              padding: const EdgeInsets.only(bottom: 14),
              child: _DaySummary(
                guide: _guide,
                runs: days[d] ?? const [],
                notes: noteDays[d] ?? const [],
                title: "${d.year}-${d.month.toString().padLeft(2, "0")}-${d.day.toString().padLeft(2, "0")}（${_ago(d)}）",
              ),
            ),
        const SizedBox(height: 12),
        _DrillStats(guide: _guide, runs: widget.runs),
      ],
    );
  }

  // ---------------------------------------------------------------- 考前

  Widget _examTab(BuildContext context) {
    final theme = Theme.of(context);
    final all = widget.bank.forSubject("subject2");
    final pending = _pending(all);
    final readiness = _readiness;
    return ListView(
      padding: const EdgeInsets.fromLTRB(28, 20, 28, 28),
      children: [
        _ReadinessCard(readiness: readiness, lastAt: _brief.lastAt),
        const SizedBox(height: 16),
        _Section(
          icon: Glyph.formTable,
          title: "每一项最近的表现（最近 $readinessWindow 把）",
          child: _FormTable(readiness: readiness),
        ),
        if (readiness.culprits.isNotEmpty) ...[
          const SizedBox(height: 20),
          _Section(
            icon: Glyph.mistake,
            title: "最拖后腿的失分来源",
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (final c in readiness.culprits)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(
                      children: [
                        SizedBox(width: 96, child: BsBadge(text: c.mistake.level.label, color: levelColor(c.mistake.level))),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            "${_guide.item(c.itemId)?.title} · ${c.mistake.label}",
                            style: theme.textTheme.bodyLarge,
                          ),
                        ),
                        Text(
                          "出现在 ${(c.combos * 100 / (readiness.combos - readiness.passing)).round()}% 的过不了的组合里",
                          style: theme.textTheme.bodyMedium?.copyWith(color: Bs.secondary),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ],
        const SizedBox(height: 20),
        _Section(
          icon: Glyph.rehearse,
          title: "四项连起来默演一遍",
          child: Wrap(
            spacing: 12,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              FilledButton.icon(onPressed: _rehearseAll, icon: const Icon(Glyph.play), label: const Text("开始")),
              Text("按考试的四项依次过：倒车入库 → 侧方停车 → 曲线行驶 → 直角转弯。考场的实际顺序以考场为准。",
                  style: theme.textTheme.bodyMedium?.copyWith(color: Bs.secondary)),
            ],
          ),
        ),
        const SizedBox(height: 20),
        _Section(
          icon: Glyph.question,
          title: "规则自测",
          child: Wrap(
            spacing: 12,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              Text("评判题掌握 ${all.length - pending.length}/${all.length}", style: theme.textTheme.bodyLarge),
              FilledButton.tonalIcon(
                onPressed: pending.isEmpty ? null : () => widget.onPractice(all, "规则自测"),
                icon: const Icon(Glyph.practice),
                label: Text(pending.isEmpty ? "已全部掌握" : "自测 · 待练 ${pending.length}"),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        _Section(
          icon: Glyph.rules,
          title: "上车检查：通用评判（每一项都适用）",
          child: _RuleTable(rules: _guide.generalRules),
        ),
      ],
    );
  }
}

enum _Tab { day, handbook, log, exam }

class _Panel extends StatelessWidget {
  const _Panel({required this.icon, required this.title, required this.children});

  final IconData icon;
  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(border: Border.all(color: Bs.border), borderRadius: BorderRadius.circular(8)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Icon(icon, color: Bs.paper),
              const SizedBox(width: 8),
              Text(title, style: Theme.of(context).textTheme.titleLarge),
            ],
          ),
          const SizedBox(height: 12),
          ...children,
        ],
      ),
    );
  }
}

/// 整场就绪度（ADR 0039）：四项合算一个总分，按最近记录精确组合。
class _ReadinessCard extends StatelessWidget {
  const _ReadinessCard({required this.readiness, required this.lastAt, this.onDetail});

  final Readiness readiness;
  final DateTime? lastAt;
  final VoidCallback? onDetail;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final rate = readiness.rate;
    final color = rate == null
        ? Bs.secondary
        : rate >= 0.8
            ? Bs.success
            : rate >= 0.5
                ? Bs.orange
                : Bs.danger;
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.08), border: Border.all(color: color), borderRadius: BorderRadius.circular(8)),
      child: Row(
        children: [
          RateRing(rate: rate ?? 0, caption: rate == null ? "—" : "${(rate * 100).round()}%", color: color, size: 84),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("按最近的练车，整场能过的把握", style: theme.textTheme.titleLarge),
                const SizedBox(height: 6),
                Text(
                  rate == null
                      ? "数据不够：${[for (final i in readiness.missing) "${i.item.title}（${i.recent.length}/$readinessMinRuns 把）"].join("、")}。"
                          "每项至少记 $readinessMinRuns 把才算。"
                      : "四项合算一个总分：任何一项不合格整场结束，扣分四项累计，80 分合格。"
                          "用每项最近 $readinessWindow 把的真实记录全组合算出：${readiness.combos} 种组合里 ${readiness.passing} 种能过。"
                          "这是按练车表现的估计，不是考试预测；每把都记才准。",
                  style: theme.textTheme.bodyMedium,
                ),
                if (lastAt != null) ...[
                  const SizedBox(height: 4),
                  Text("上次练车：${_ago(lastAt!)}", style: theme.textTheme.bodyMedium?.copyWith(color: Bs.secondary)),
                ],
              ],
            ),
          ),
          if (onDetail != null) TextButton(onPressed: onDetail, child: const Text("看拆解")),
        ],
      ),
    );
  }
}

class _FormTable extends StatelessWidget {
  const _FormTable({required this.readiness});

  final Readiness readiness;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    TableRow row(List<String> cells, {bool head = false}) => TableRow(
          decoration: head ? const BoxDecoration(color: Bs.light) : null,
          children: [
            for (final c in cells)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                child: Text(c, style: head ? theme.textTheme.titleSmall : theme.textTheme.bodyLarge),
              ),
          ],
        );
    return Table(
      border: TableBorder.all(color: Bs.border),
      columnWidths: const {0: FixedColumnWidth(140)},
      children: [
        row(["项目", "最近几把", "能过", "不合格", "没判不合格时平均扣分"], head: true),
        for (final f in readiness.items)
          row([
            f.item.title,
            "${f.recent.length}",
            f.recent.isEmpty ? "—" : "${f.passes} 把（${(f.passRate * 100).round()}%）",
            "${f.fails} 把",
            f.recent.isEmpty ? "—" : "${f.avgDeduct.toStringAsFixed(1)} 分",
          ]),
      ],
    );
  }
}

/// 一天的练车：每项几把、能过几把、出过什么错，教练说了什么。
class _DaySummary extends StatelessWidget {
  const _DaySummary({required this.guide, required this.runs, required this.notes, required this.title});

  final Subject2Guide guide;
  final List<DrillRun> runs;
  final List<DrillNote> notes;
  final String title;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(border: Border.all(color: Bs.border), borderRadius: BorderRadius.circular(6)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: theme.textTheme.titleMedium),
          const SizedBox(height: 6),
          for (final item in guide.items)
            if (runs.any((r) => r.itemId == item.id) || notes.any((n) => n.itemId == item.id))
              () {
                final mine = [for (final r in runs) if (r.itemId == item.id) r];
                final scores = [for (final r in mine) guide.score(item.id, r.mistakes)];
                final counts = <String, int>{};
                for (final r in mine) {
                  for (final id in r.mistakes.toSet()) {
                    counts[id] = (counts[id] ?? 0) + 1;
                  }
                }
                final top = counts.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Wrap(
                        spacing: 8,
                        runSpacing: 4,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: [
                          SizedBox(width: 90, child: Text(item.title, style: theme.textTheme.bodyLarge)),
                          if (mine.isNotEmpty) ...[
                            Text("${mine.length} 把能过 ${scores.where((s) => s.passed).length} 把"),
                            for (final s in scores.reversed)
                              Container(
                                width: 14,
                                height: 14,
                                decoration: BoxDecoration(color: s.passed ? Bs.success : Bs.danger, borderRadius: BorderRadius.circular(3)),
                              ),
                            for (final e in top.take(3))
                              if (guide.mistake(item.id, e.key) case final m?)
                                Text("· ${m.label} ${e.value} 把", style: theme.textTheme.bodyMedium?.copyWith(color: Bs.secondary)),
                          ],
                        ],
                      ),
                      for (final n in notes.where((n) => n.itemId == item.id))
                        Padding(
                          padding: const EdgeInsets.only(left: 98, top: 2),
                          child: Text("教练：${n.text}", style: theme.textTheme.bodyMedium?.copyWith(fontStyle: FontStyle.italic)),
                        ),
                    ],
                  ),
                );
              }(),
        ],
      ),
    );
  }
}

/// 一项按练车日的能过比例折线：看是不是在进步。
class _TrendRow extends StatelessWidget {
  const _TrendRow({required this.guide, required this.item, required this.runs});

  final Subject2Guide guide;
  final GuideItem item;
  final List<DrillRun> runs;

  @override
  Widget build(BuildContext context) {
    final byDay = <DateTime, List<bool>>{};
    for (final r in runs.where((r) => r.itemId == item.id)) {
      byDay.putIfAbsent(DateUtils.dateOnly(r.at), () => []).add(guide.score(item.id, r.mistakes).passed);
    }
    final days = byDay.keys.toList()..sort();
    final recent = days.length > 12 ? days.sublist(days.length - 12) : days;
    final rates = [for (final d in recent) byDay[d]!.where((p) => p).length / byDay[d]!.length];
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          SizedBox(width: 100, child: Text(item.title, style: theme.textTheme.bodyLarge)),
          Expanded(
            child: rates.isEmpty
                ? Text("还没有记录", style: theme.textTheme.bodyMedium?.copyWith(color: Bs.secondary))
                : SizedBox(height: 44, child: CustomPaint(painter: _TrendPainter(rates))),
          ),
          SizedBox(
            width: 150,
            child: Text(
              rates.isEmpty ? "" : "最近一天 ${(rates.last * 100).round()}% · ${rates.length} 个练车日",
              textAlign: TextAlign.right,
              style: theme.textTheme.bodyMedium,
            ),
          ),
        ],
      ),
    );
  }
}

class _TrendPainter extends CustomPainter {
  _TrendPainter(this.rates);

  final List<double> rates;

  @override
  void paint(Canvas canvas, Size size) {
    final grid = Paint()
      ..color = Bs.border
      ..strokeWidth = 1;
    canvas.drawLine(Offset(0, size.height * 0.2), Offset(size.width, size.height * 0.2), grid);
    canvas.drawLine(Offset(0, size.height - 2), Offset(size.width, size.height - 2), grid);
    Offset at(int i) => Offset(
          rates.length == 1 ? size.width / 2 : i * size.width / (rates.length - 1),
          (size.height - 4) * (1 - rates[i]) + 2,
        );
    final line = Paint()
      ..color = Bs.paper
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;
    final path = Path()..moveTo(at(0).dx, at(0).dy);
    for (var i = 1; i < rates.length; i++) {
      path.lineTo(at(i).dx, at(i).dy);
    }
    canvas.drawPath(path, line);
    for (var i = 0; i < rates.length; i++) {
      canvas.drawCircle(at(i), 4, Paint()..color = rates[i] >= 0.8 ? Bs.success : (rates[i] >= 0.5 ? Bs.orange : Bs.danger));
    }
  }

  @override
  bool shouldRepaint(_TrendPainter old) => old.rates != rates;
}

/// 练车前 5 分钟（ADR 0039）：今日重点的每一项，过一遍简报、点位卡、教练的话，想默演就默演。
class _PreDrill extends StatefulWidget {
  const _PreDrill({
    required this.items,
    required this.brief,
    required this.store,
    required this.notes,
    required this.photos,
    required this.coachNotes,
    required this.onChanged,
  });

  final List<GuideItem> items;
  final Brief brief;
  final ProgressStore store;
  final Map<(String, int), PointNote> notes;
  final List<PointPhoto> photos;
  final List<DrillNote> coachNotes;
  final Future<void> Function() onChanged;

  @override
  State<_PreDrill> createState() => _PreDrillState();
}

class _PreDrillState extends State<_PreDrill> {
  var _index = 0;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final item = widget.items[_index];
    final last = _index + 1 == widget.items.length;
    final itemBrief = widget.brief.item(item.id)!;
    final coach = [for (final n in widget.coachNotes) if (n.itemId == item.id) n].take(3).toList();
    return Scaffold(
      appBar: AppBar(
        title: Text("练车前 · ${item.title}（${_index + 1}/${widget.items.length}）"),
        automaticallyImplyLeading: false,
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text("结束")),
          const SizedBox(width: 12),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(28, 20, 28, 28),
        children: [
          _ItemBriefCard(brief: itemBrief, pointsWritten: -1),
          if (coach.isNotEmpty) ...[
            const SizedBox(height: 16),
            _Section(
              icon: Glyph.coach,
              title: "教练说过",
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  for (final n in coach)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 3),
                      child: Text("${_ago(n.at)}：${n.text}", style: theme.textTheme.bodyLarge),
                    ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 16),
          _Section(
            icon: Glyph.pointCard,
            title: "我的点位卡",
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                for (var i = 0; i < item.steps.length; i++)
                  PointCard(
                    item: item,
                    step: i,
                    store: widget.store,
                    note: widget.notes[(item.id, i)],
                    photos: [for (final ph in widget.photos) if (ph.itemId == item.id && ph.step == i) ph],
                    onChanged: widget.onChanged,
                    compact: true,
                  ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          Wrap(
            spacing: 12,
            children: [
              FilledButton.tonalIcon(
                onPressed: () => showRehearsal(
                  context,
                  item: item,
                  store: widget.store,
                  notes: widget.notes,
                  photos: widget.photos,
                  onChanged: widget.onChanged,
                ),
                icon: const Icon(Glyph.rehearse),
                label: const Text("默演这一项"),
              ),
              FilledButton.icon(
                onPressed: last ? () => Navigator.of(context).pop() : () => setState(() => _index++),
                icon: Icon(last ? Glyph.finish : Glyph.next),
                label: Text(last ? "准备好了，去练车" : "下一项"),
              ),
            ],
          ),
        ],
      ),
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
                    const Icon(Glyph.animation, color: Bs.paper),
                  ],
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: [
                    BsBadge(text: "限时 ${item.limitText}", color: Bs.secondary, icon: Glyph.duration),
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
    required this.store,
    required this.notes,
    required this.photos,
    required this.onPointsChanged,
    required this.coachNotes,
    required this.onBack,
    required this.onPractice,
    required this.onRecord,
  });

  final ItemBrief brief;
  final ProgressStore store;
  final Map<(String, int), PointNote> notes;
  final List<PointPhoto> photos;
  final Future<void> Function() onPointsChanged;
  final List<DrillNote> coachNotes;
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
  final _narrator = defaultNarrator();
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
      narration: [for (var i = 0; i < item.steps.length; i++) item.steps[i].narration(i)],
      cautions: [for (final s in item.steps) s.caution],
      narrator: _narrator,
    );
    final steps = _StepList(
      steps: item.steps,
      notes: [for (var i = 0; i < item.steps.length; i++) widget.notes[(item.id, i)]?.text.trim() ?? ""],
      current: _step,
      onTap: (i) {
        _player.currentState?.jumpTo(i);
        setState(() => _step = i);
      },
      onPlay: (i) => _player.currentState?.playStep(i),
    );
    return ListView(
      key: const ValueKey("subject2-item"),
      padding: const EdgeInsets.fromLTRB(28, 16, 28, 28),
      children: [
        Wrap(
          crossAxisAlignment: WrapCrossAlignment.center,
          spacing: 12,
          runSpacing: 8,
          children: [
            TextButton.icon(onPressed: widget.onBack, icon: const Icon(Glyph.back), label: const Text("科目二")),
            Text(item.title, style: theme.textTheme.headlineMedium),
            BsBadge(text: "限时 ${item.limitText}", color: Bs.secondary, icon: Glyph.duration),
            BsBadge(text: "出线看${item.judgedBy}", color: Bs.secondary),
          ],
        ),
        const SizedBox(height: 12),
        _ItemBriefCard(
          brief: widget.brief,
          pointsWritten: [
            for (var i = 0; i < item.steps.length; i++)
              if ((widget.notes[(item.id, i)]?.text.trim().isNotEmpty ?? false) ||
                  widget.photos.any((ph) => ph.itemId == item.id && ph.step == i))
                i,
          ].length,
        ),
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
              icon: const Icon(Glyph.practice),
              label: Text(pending.isEmpty ? "评判题（已掌握）" : "练这一项的评判题 · 待练 ${pending.length}"),
            ),
            FilledButton.tonalIcon(
              onPressed: widget.onRecord,
              icon: const Icon(Glyph.record),
              label: const Text("记一把练车"),
            ),
            FilledButton.tonalIcon(
              onPressed: () => showRehearsal(
                context,
                item: item,
                store: widget.store,
                notes: widget.notes,
                photos: widget.photos,
                onChanged: widget.onPointsChanged,
              ),
              icon: const Icon(Glyph.rehearse),
              label: const Text("默演一遍"),
            ),
          ],
        ),
        const SizedBox(height: 24),
        _Section(
          icon: Glyph.pointCard,
          title: "我的点位卡",
          trailing: Text(
            "只写你自己验证过的：教练怎么说、你在车里实测怎样",
            style: theme.textTheme.bodySmall?.copyWith(color: Bs.secondary),
          ),
          child: PointCards(
            item: item,
            store: widget.store,
            notes: widget.notes,
            photos: widget.photos,
            onChanged: widget.onPointsChanged,
          ),
        ),
        if (widget.coachNotes.isNotEmpty) ...[
          const SizedBox(height: 20),
          _Section(
            icon: Glyph.coach,
            title: "教练说过",
            trailing: Text("原话，按时间倒序；整理过的放进点位卡", style: theme.textTheme.bodySmall?.copyWith(color: Bs.secondary)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (final n in widget.coachNotes.take(8))
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 3),
                    child: Text("${_ago(n.at)}：${n.text}", style: theme.textTheme.bodyLarge),
                  ),
              ],
            ),
          ),
        ],
        const SizedBox(height: 20),
        _Section(
          icon: Glyph.source,
          title: "操作要求（标准原文）",
          child: _Quote(text: item.requirementQuote, locator: item.requirementLocator),
        ),
        const SizedBox(height: 20),
        _Section(
          icon: Glyph.rules,
          title: "评判",
          child: _RuleTable(rules: item.rules),
        ),
        const SizedBox(height: 20),
        _Section(
          icon: Glyph.tips,
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
                        child: Icon(Glyph.bullet, size: 8, color: Bs.paper),
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
              const Icon(Glyph.brief, color: Bs.orange),
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
                        FocusKind.mistake => Glyph.mistake,
                        FocusKind.weak => Glyph.weak,
                        FocusKind.rehearsal => Glyph.rehearse,
                        FocusKind.untried => Glyph.untried,
                      },
                      size: 20,
                      color: f.kind == FocusKind.mistake ? Bs.danger : Bs.secondary,
                    ),
                    const SizedBox(width: 8),
                    Expanded(child: Text(f.text, style: theme.textTheme.bodyLarge)),
                    const Icon(Glyph.goTo, color: Bs.secondary),
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
  const _ItemBriefCard({required this.brief, required this.pointsWritten});

  final ItemBrief brief;
  final int pointsWritten;

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
      if (pointsWritten >= 0) const SizedBox(height: 8),
      if (pointsWritten >= 0)
      Text(
        pointsWritten == 0
            ? "点位卡还空着：练车时把教练说的点位记下来，下次练车前在这里过一遍。"
            : "点位卡写了 $pointsWritten/${brief.item.steps.length} 步，练车前过一遍。",
        style: theme.textTheme.bodyMedium,
      ),
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
          const Icon(Glyph.brief, color: Bs.orange),
          const SizedBox(width: 10),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: lines)),
        ],
      ),
    );
  }
}

class _StepList extends StatelessWidget {
  const _StepList({
    required this.steps,
    required this.notes,
    required this.current,
    required this.onTap,
    required this.onPlay,
  });

  final List<GuideStep> steps;

  /// 每一步自己写的点位，空串表示没写。
  final List<String> notes;
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
                              if (steps[i].caution.isNotEmpty) ...[
                                const SizedBox(height: 6),
                                Tooltip(
                                  message: steps[i].cautionLocators.join("；"),
                                  child: Row(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Icon(Glyph.caution, size: 18, color: Bs.danger),
                                      const SizedBox(width: 6),
                                      Expanded(
                                        child: Text(
                                          steps[i].caution,
                                          style: theme.textTheme.bodyMedium?.copyWith(color: Bs.danger),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                              if (notes[i].isNotEmpty) ...[
                                const SizedBox(height: 6),
                                Container(
                                  width: double.infinity,
                                  padding: const EdgeInsets.all(8),
                                  decoration: BoxDecoration(
                                    color: Bs.warning.withValues(alpha: 0.12),
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Text("我的点位：${notes[i]}", style: theme.textTheme.bodyMedium),
                                ),
                              ],
                            ],
                          ],
                        ),
                      ),
                      IconButton(
                        tooltip: "播这一步",
                        onPressed: () => onPlay(i),
                        icon: const Icon(Glyph.playStep, size: 20),
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
        icon: Glyph.runs,
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
      icon: Glyph.runs,
      title: itemId == null ? "练车记录" : "这一项的练车记录",
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              StatTile(icon: Glyph.runCount, label: "练了", value: "${runs.length} 把"),
              StatTile(
                icon: Glyph.passable,
                label: "按考场规则能过",
                value: "$passes 把 · ${(passes * 100 / runs.length).round()}%",
                color: Bs.success,
              ),
              StatTile(
                icon: Glyph.recentDays,
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
        deleteIcon: const Icon(Glyph.less, size: 18),
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
