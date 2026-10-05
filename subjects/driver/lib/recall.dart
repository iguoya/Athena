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

/// 速记页的「自我测验」模式（ADR 0077，ADR 0080 改名并改成一轮 5 个）：卡片流式
/// 检索练习。
///
/// 每一轮从条目里随机抽 [RecallSession.batchSize] 个（不够就全上）。正面是条目自己
/// 提供的 [RecallEntry.front]（规范图或情景文字），先回想再点/空格揭示答案，自评
/// 「记住了（1）/ 没记住（2）」。没记住的条目在隔两张后重新插队，直到这一轮的
/// 全部记住了或 Esc 退出。一轮收尾统计考了多少次、没记住几次，可以「再来 5 个」
/// 或深链「去练这组」——真正的记忆闭环由作答通路完成，这里的自评不落库、不写
/// 掌握度，退出即消失。
class RecallSession extends StatefulWidget {
  const RecallSession({
    super.key,
    required this.entries,
    required this.onStartPractice,
    this.prompt = defaultPrompt,
    this.batchSize = defaultBatchSize,
  });

  /// 一轮抽几个（使用者要求「一次 5 个」）。
  static const defaultBatchSize = 5;
  static const defaultPrompt = "想一想：这是什么？看到之后怎么开？";

  /// 参与自我测验的条目；[RecallEntry] 是页面内容的轻量视图。
  final List<RecallEntry> entries;

  /// 正面卡下方的提问句：符号页问「这是什么」，数字与要点页问「是多少 / 怎么办」。
  final String prompt;
  final int batchSize;

  /// 收尾的「去练这组」深链；页面自己算相关题并起练习。
  final void Function() onStartPractice;

  static Future<void> show(
    BuildContext context, {
    required List<RecallEntry> entries,
    required void Function() onStartPractice,
    String prompt = defaultPrompt,
    int batchSize = defaultBatchSize,
  }) {
    return showDialog<void>(
      context: context,
      barrierColor: Colors.transparent,
      builder: (_) => Dialog(
        insetPadding: const EdgeInsets.all(24),
        backgroundColor: Colors.transparent,
        child: RecallSession(
          entries: entries,
          onStartPractice: onStartPractice,
          prompt: prompt,
          batchSize: batchSize,
        ),
      ),
    );
  }

  @override
  State<RecallSession> createState() => _RecallSessionState();
}

/// 自我测验的一个条目：正面由页面提供，文案在条目里。
class RecallEntry {
  const RecallEntry({
    required this.id,
    required this.front,
    required this.name,
    required this.meaning,
    this.confuseName,
    this.confuseNote,
    this.confuseView,
  });

  final String id;

  /// 正面：符号页是规范图，数字与要点页是情景文字。
  final Widget front;

  /// 揭示后的答案标题与说明。
  final String name;
  final String meaning;

  /// 易混对撞卡（ADR 0077 决策 2）：对方名称、差异口诀与大图。
  final String? confuseName;
  final String? confuseNote;
  final Widget? confuseView;
}

class _RecallSessionState extends State<RecallSession> {
  /// 本轮待考队列；没记住的条目在消耗两张新卡后重新插入。
  late List<RecallEntry> _queue;

  /// 上一轮抽到的条目 id：「再来 5 个」尽量抽没考过的。
  Set<String> _lastRound = {};
  final FocusNode _focus = FocusNode();
  bool _revealed = false;
  int _asked = 0;
  int _missed = 0;
  int _rounds = 1;
  bool _done = false;

  @override
  void initState() {
    super.initState();
    _queue = _draw();
    WidgetsBinding.instance.addPostFrameCallback((_) => _focus.requestFocus());
  }

  @override
  void dispose() {
    _focus.dispose();
    super.dispose();
  }

  /// 抽一轮：先从上一轮没出现过的里抽，不够再用上一轮的补满。
  List<RecallEntry> _draw() {
    final fresh = [for (final e in widget.entries) if (!_lastRound.contains(e.id)) e]..shuffle();
    final seen = [for (final e in widget.entries) if (_lastRound.contains(e.id)) e]..shuffle();
    final round = [...fresh, ...seen].take(widget.batchSize).toList()..shuffle();
    _lastRound = {for (final e in round) e.id};
    return round;
  }

  void _nextRound() {
    setState(() {
      _queue = _draw();
      _asked = 0;
      _missed = 0;
      _rounds++;
      _revealed = false;
      _done = false;
    });
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
        // 图放大一倍后卡片可能高过小窗口，整张卡可滚，按钮不会掉出屏幕。
        child: SingleChildScrollView(child: _done ? _summary(context) : _card(context)),
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
            Text("自我测验", style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(width: 10),
            Text("第 $_rounds 轮 · 剩 ${_queue.length} 张 · 没记住 $_missed · Esc 退出", style: muted),
          ],
        ),
        const SizedBox(height: 16),
        Center(child: entry.front),
        const SizedBox(height: 14),
        if (!_revealed)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 18),
            child: Text(
              widget.prompt,
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
                    entry.confuseView!,
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
        Text("这一轮 ${_lastRound.length} 个，共考 $_asked 次，其中没记住 $_missed 次。", style: body),
        const SizedBox(height: 6),
        Text(
          _missed == 0 ? "全部记住了。真正的检验还是做题——有空把这几组题过一遍。" : "没记住的再看看；真正的检验还是做题。",
          textAlign: TextAlign.center,
          style: body,
        ),
        const SizedBox(height: 18),
        Wrap(
          alignment: WrapAlignment.center,
          spacing: 12,
          runSpacing: 10,
          children: [
            FilledButton(
              onPressed: _nextRound,
              child: Text("再来 ${widget.batchSize} 个"),
            ),
            OutlinedButton(
              onPressed: () {
                Navigator.of(context).pop();
                widget.onStartPractice();
              },
              child: const Text("去练这组题"),
            ),
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
