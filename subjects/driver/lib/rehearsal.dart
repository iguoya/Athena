import "package:flutter/material.dart";

import "drill.dart";
import "guide.dart";
import "look.dart";
import "points.dart";
import "progress.dart";

/// 默演（ADR 0037）：逐步先口述、再对照。想象演练和看示范能帮新手先在脑子里搭起动作框架，
/// 但要和真车练习接上才生效——所以放在练车前后做，不替代练车。自评，不写掌握度。
Future<void> showRehearsal(
  BuildContext context, {
  required GuideItem item,
  required ProgressStore store,
  required Map<(String, int), PointNote> notes,
  required List<PointPhoto> photos,
  required Future<void> Function() onChanged,
}) {
  return showDialog<void>(
    context: context,
    barrierDismissible: false,
    builder: (context) => Dialog.fullscreen(
      child: RehearsalView(item: item, store: store, notes: notes, photos: photos, onChanged: onChanged),
    ),
  );
}

enum _Phase { recall, compare, done }

class RehearsalView extends StatefulWidget {
  const RehearsalView({
    super.key,
    required this.item,
    required this.store,
    required this.notes,
    required this.photos,
    required this.onChanged,
  });

  final GuideItem item;
  final ProgressStore store;
  final Map<(String, int), PointNote> notes;
  final List<PointPhoto> photos;
  final Future<void> Function() onChanged;

  @override
  State<RehearsalView> createState() => _RehearsalViewState();
}

class _RehearsalViewState extends State<RehearsalView> {
  final _player = GlobalKey<DrillPlayerState>();
  var _step = 0;
  var _phase = _Phase.recall;
  final _missed = <int>[];

  int get _total => widget.item.steps.length;

  void _compare() {
    setState(() => _phase = _Phase.compare);
    _player.currentState?.playStep(_step);
  }

  Future<void> _judge(bool ok) async {
    if (!ok) _missed.add(_step);
    if (_step + 1 < _total) {
      setState(() {
        _step++;
        _phase = _Phase.recall;
      });
      _player.currentState?.jumpTo(_step);
      return;
    }
    setState(() => _phase = _Phase.done);
    await widget.store.recordRehearsal(widget.item.id, _missed, _total);
    await widget.onChanged();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final item = widget.item;
    return Scaffold(
      appBar: AppBar(
        title: Text("默演 · ${item.title}"),
        automaticallyImplyLeading: false,
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text(_phase == _Phase.done ? "完成" : "不做了"),
          ),
          const SizedBox(width: 12),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              flex: 3,
              child: DrillPlayer(
                key: _player,
                scene: drillScenes[item.id]!,
                stepTitles: [for (final s in item.steps) s.title],
                hideCue: _phase == _Phase.recall,
              ),
            ),
            const SizedBox(width: 24),
            Expanded(flex: 2, child: SingleChildScrollView(child: _panel(theme))),
          ],
        ),
      ),
    );
  }

  Widget _panel(ThemeData theme) {
    final item = widget.item;
    if (_phase == _Phase.done) {
      final hit = _total - _missed.length;
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("$_total 步里对上 $hit 步", style: theme.textTheme.headlineSmall),
          const SizedBox(height: 12),
          if (_missed.isEmpty)
            Text("全对上了。练车时照这个顺序做。", style: theme.textTheme.bodyLarge)
          else ...[
            Text("卡在：", style: theme.textTheme.titleMedium),
            const SizedBox(height: 6),
            for (final i in _missed)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Text("第 ${i + 1} 步 · ${item.steps[i].title}", style: theme.textTheme.bodyLarge),
              ),
            const SizedBox(height: 12),
            Text("这几步会进练车前简报。练车时先盯住它们，回来把点位卡补上。", style: theme.textTheme.bodyMedium),
          ],
          const SizedBox(height: 20),
          FilledButton(onPressed: () => Navigator.of(context).pop(), child: const Text("完成")),
        ],
      );
    }
    final step = item.steps[_step];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("第 ${_step + 1} / $_total 步", style: theme.textTheme.bodyMedium?.copyWith(color: Bs.secondary)),
        const SizedBox(height: 4),
        Text(step.title, style: theme.textTheme.headlineSmall),
        const SizedBox(height: 8),
        LinearProgressIndicator(value: (_step + (_phase == _Phase.compare ? 1 : 0)) / _total),
        const SizedBox(height: 20),
        if (_phase == _Phase.recall) ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(color: Bs.info.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8)),
            child: Text(
              "先别看答案。说出来（或在心里过一遍）：\n这一步看哪里？看到什么时？手脚做什么？",
              style: theme.textTheme.bodyLarge,
            ),
          ),
          const SizedBox(height: 20),
          FilledButton.icon(onPressed: _compare, icon: const Icon(Icons.visibility), label: const Text("说完了，对照")),
        ] else ...[
          Text("讲解", style: theme.textTheme.titleMedium),
          const SizedBox(height: 6),
          Text(step.body, style: theme.textTheme.bodyLarge),
          const SizedBox(height: 16),
          PointCard(
            item: item,
            step: _step,
            store: widget.store,
            note: widget.notes[(item.id, _step)],
            photos: [for (final ph in widget.photos) if (ph.itemId == item.id && ph.step == _step) ph],
            onChanged: widget.onChanged,
            compact: true,
          ),
          const SizedBox(height: 16),
          Text("刚才说的对上了吗？", style: theme.textTheme.titleMedium),
          const SizedBox(height: 8),
          Wrap(
            spacing: 10,
            children: [
              FilledButton.icon(
                onPressed: () => _judge(true),
                icon: const Icon(Icons.check),
                label: const Text("对上了"),
                style: FilledButton.styleFrom(backgroundColor: Bs.success),
              ),
              FilledButton.icon(
                onPressed: () => _judge(false),
                icon: const Icon(Icons.close),
                label: const Text("漏了或说错了"),
                style: FilledButton.styleFrom(backgroundColor: Bs.danger),
              ),
            ],
          ),
        ],
      ],
    );
  }
}
