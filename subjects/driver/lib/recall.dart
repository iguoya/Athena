import "package:flutter/material.dart";
import "package:flutter/services.dart";

import "glyphs.dart";
import "look.dart";
import "models.dart";
import "reinforce.dart";

/// 格子角的掌握度微点（ADR 0077 决策 3）：红 = 相关题最近答错、
/// 黄 = 部分掌握、绿 = 全部掌握、灰 = 从未作答。纯展示。
class StatusDot extends StatelessWidget {
  const StatusDot({super.key, required this.status});

  final SymbolStatus status;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      SymbolStatus.wrong => Bs.danger,
      SymbolStatus.partial => Bs.warning,
      SymbolStatus.mastered => Bs.success,
      SymbolStatus.fresh => const Color(0xFFADB5BD),
    };
    return Tooltip(
      message: switch (status) {
        SymbolStatus.wrong => "相关题最近答错过",
        SymbolStatus.partial => "相关题部分掌握",
        SymbolStatus.mastered => "相关题已掌握",
        SymbolStatus.fresh => "相关题还没做过",
      },
      child: Container(
        width: 10,
        height: 10,
        decoration: BoxDecoration(color: color, shape: BoxShape.circle),
      ),
    );
  }
}

/// 条目相关题的作答状态。
enum SymbolStatus { wrong, partial, mastered, fresh }

/// 由相关题集合算微点状态：答错优先红，全掌握绿，其余黄，没做过灰。
SymbolStatus statusOf({
  required List<Question> related,
  required Set<String> mastered,
  required HistorySet histories,
}) {
  if (related.isEmpty) return SymbolStatus.fresh;
  final touched = [for (final q in related) if (histories.byQuestion.containsKey(q.id)) q];
  if (touched.isEmpty) return SymbolStatus.fresh;
  if (touched.any((q) => (histories.byQuestion[q.id]?.wrong ?? 0) > 0 && !mastered.contains(q.id))) {
    return SymbolStatus.wrong;
  }
  return related.every((q) => mastered.contains(q.id)) ? SymbolStatus.mastered : SymbolStatus.partial;
}

/// 速记页的「考我」模式（ADR 0077）：卡片流式检索练习。
///
/// 正面是大图（条目自己提供 [RecallCard.buildFront]），先回想再点/空格揭示
/// 名称与「看到之后怎么开」，自评「记住了（1）/ 没记住（2）」。没记住的条目
/// 在隔两张后重新插队，直到全部记住了或 Esc 退出。收尾统计考了多少张、
/// 没记住几张，深链「去练这组」——真正的记忆闭环由作答通路完成，这里的
/// 自评不落库、不写掌握度，退出即消失。
class RecallSession extends StatefulWidget {
  const RecallSession({
    super.key,
    required this.entries,
    required this.viewOf,
    required this.onStartPractice,
  });

  /// 参与考我的条目；[RecallEntry] 是符号条目的轻量视图。
  final List<RecallEntry> entries;

  /// 条目 id → 大图 widget（四个符号页各自的 painter 视图）。
  final Widget Function(String id) viewOf;

  /// 收尾的「去练这组」深链；传相关题与标题。
  final void Function() onStartPractice;

  static Future<void> show(
    BuildContext context, {
    required List<RecallEntry> entries,
    required Widget Function(String id) viewOf,
    required void Function() onStartPractice,
  }) {
    return showDialog<void>(
      context: context,
      barrierColor: Colors.transparent,
      builder: (_) => Dialog(
        insetPadding: const EdgeInsets.all(24),
        backgroundColor: Colors.transparent,
        child: RecallSession(entries: entries, viewOf: viewOf, onStartPractice: onStartPractice),
      ),
    );
  }

  @override
  State<RecallSession> createState() => _RecallSessionState();
}

/// 考我模式的一个条目视图：大图由页面提供，文案在条目里。
class RecallEntry {
  const RecallEntry({
    required this.id,
    required this.name,
    required this.meaning,
    this.confuseName,
    this.confuseNote,
    this.confuseView,
  });

  final String id;
  final String name;
  final String meaning;

  /// 易混对撞卡（ADR 0077 决策 2）：对方名称、差异口诀与大图。
  final String? confuseName;
  final String? confuseNote;
  final Widget? confuseView;
}

class _RecallSessionState extends State<RecallSession> {
  /// 待考队列；没记住的条目在消耗两张新卡后重新插入。
  late List<RecallEntry> _queue;
  final FocusNode _focus = FocusNode();
  bool _revealed = false;
  int _asked = 0;
  int _missed = 0;
  bool _done = false;

  @override
  void initState() {
    super.initState();
    _queue = [...widget.entries]..shuffle();
    WidgetsBinding.instance.addPostFrameCallback((_) => _focus.requestFocus());
  }

  @override
  void dispose() {
    _focus.dispose();
    super.dispose();
  }

  void _reveal() {
    if (!_revealed) setState(() => _revealed = true);
  }

  void _grade(bool remembered) {
    final current = _queue.first;
    setState(() {
      _asked++;
      if (remembered) {
        _queue.removeAt(0);
      } else {
        _missed++;
        // 没记住的先摘下来，跳过两张新卡后重新插队（ADR 0077 决策 1）。
        _queue.removeAt(0);
        if (_queue.length > 2) {
          _queue.insert(2, current);
        } else {
          _queue.add(current);
        }
      }
      _revealed = false;
      if (_queue.isEmpty) _done = true;
    });
  }

  KeyEventResult _onKey(FocusNode node, KeyEvent event) {
    if (event is! KeyDownEvent) return KeyEventResult.ignored;
    if (event.logicalKey == LogicalKeyboardKey.escape) {
      Navigator.of(context).pop();
      return KeyEventResult.handled;
    }
    if (_done) return KeyEventResult.ignored;
    if (event.logicalKey == LogicalKeyboardKey.space) {
      _reveal();
      return KeyEventResult.handled;
    }
    if (_revealed && event.logicalKey == LogicalKeyboardKey.digit1) {
      _grade(true);
      return KeyEventResult.handled;
    }
    if (_revealed && event.logicalKey == LogicalKeyboardKey.digit2) {
      _grade(false);
      return KeyEventResult.handled;
    }
    return KeyEventResult.ignored;
  }

  @override
  Widget build(BuildContext context) {
    return Focus(
      focusNode: _focus,
      onKeyEvent: _onKey,
      child: GlassPanel(
        padding: const EdgeInsets.all(28),
        child: _done ? _summary(context) : _card(context),
      ),
    );
  }

  Widget _card(BuildContext context) {
    final entry = _queue.first;
    final muted = Theme.of(context).textTheme.bodyMedium?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
      height: 1.5,
    );
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Text("考我", style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(width: 10),
            Text("剩 ${_queue.length} 张 · 没记住 $_missed · Esc 退出", style: muted),
          ],
        ),
        const SizedBox(height: 16),
        Center(child: widget.viewOf(entry.id)),
        const SizedBox(height: 14),
        if (!_revealed)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 18),
            child: Text(
              "想一想：这是什么？看到之后怎么开？",
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium,
            ),
          )
        else ...[
          Center(
            child: Text(entry.name, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700)),
          ),
          const SizedBox(height: 8),
          Text(entry.meaning, textAlign: TextAlign.center, style: muted),
          if (entry.confuseName != null) ...[
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
                  if (entry.confuseView != null) ...[
                    SizedBox(width: 72, height: 72, child: entry.confuseView!),
                    const SizedBox(width: 12),
                  ],
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text("容易混：${entry.confuseName}", style: Theme.of(context).textTheme.titleSmall),
                        const SizedBox(height: 4),
                        Text(entry.confuseNote ?? "", style: muted),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
        const SizedBox(height: 16),
        _revealed
            ? Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  FilledButton.icon(
                    onPressed: () => _grade(true),
                    icon: const Icon(Glyph.correct, size: 18),
                    label: const Text("记住了（1）"),
                  ),
                  const SizedBox(width: 12),
                  OutlinedButton.icon(
                    onPressed: () => _grade(false),
                    icon: const Icon(Glyph.wrong, size: 18),
                    label: const Text("没记住（2）"),
                  ),
                ],
              )
            : Center(
                child: OutlinedButton(
                  onPressed: _reveal,
                  child: const Text("揭示（空格）"),
                ),
              ),
      ],
    );
  }

  Widget _summary(BuildContext context) {
    final body = Theme.of(context).textTheme.bodyLarge;
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Text("考完了", style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 10),
        Text("共考 $_asked 次，其中没记住 $_missed 次。", style: body),
        const SizedBox(height: 6),
        Text(
          _missed == 0 ? "全部记住了。真正的检验还是做题——有空把这几组题过一遍。" : "没记住的再看看；真正的检验还是做题。",
          textAlign: TextAlign.center,
          style: body,
        ),
        const SizedBox(height: 18),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            FilledButton(
              onPressed: () {
                Navigator.of(context).pop();
                widget.onStartPractice();
              },
              child: const Text("去练这组题"),
            ),
            const SizedBox(width: 12),
            OutlinedButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text("关闭"),
            ),
          ],
        ),
      ],
    );
  }
}
