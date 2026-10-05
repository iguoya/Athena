import "package:flutter/material.dart";
import "package:flutter/services.dart";

import "glyphs.dart";
import "look.dart";
import "models.dart";
import "reinforce.dart";
import "selftest_store.dart";

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

/// 速记页的「自测」模式（ADR 0077 起，ADR 0080 一轮 5 个，ADR 0082 改名并只考没认得的）：
/// 卡片流式检索练习。
///
/// 正面是条目自己提供的 [RecallEntry.front]（规范图或情景文字），先回想再点/空格揭示
/// 答案，自评「记住了（1）/ 没记住（2）」。
///
/// **只考没认得的**（ADR 0082）：自评实时记进 [SelfTestStore]——一轮里第一次问就记住的
/// 条目标为「已认得」，以后不再出；没记住的隔两张后重现，下一轮也优先再考。每轮抽
/// [RecallSession.batchSize] 个：先取没记住过的几个，再取从没考过的，不够再补。全部
/// 认得了就说清楚，并给「重新自测」。随时可退出（右上角按钮或 Esc），已经评过的不丢。
///
/// 记录**不是掌握度**：不写作答、不进统计与激励，真正的记忆闭环仍由「去练这组题」走
/// 作答通路完成。
class RecallSession extends StatefulWidget {
  const RecallSession({
    super.key,
    required this.entries,
    required this.onStartPractice,
    required this.pageKey,
    required this.store,
    this.prompt = defaultPrompt,
    this.batchSize = defaultBatchSize,
  });

  /// 一轮抽几个（使用者要求「一次 5 个」）。
  static const defaultBatchSize = 5;
  static const defaultPrompt = "想一想：这是什么？看到之后怎么开？";

  /// 参与自测的全部条目；[RecallEntry] 是页面内容的轻量视图。
  final List<RecallEntry> entries;

  /// 本页在 [SelfTestStore] 里的键，条目 id 在页内唯一即可。
  final String pageKey;
  final SelfTestStore store;

  /// 正面卡下方的提问句：符号页问「这是什么」，数字与要点页问「是多少 / 怎么办」。
  final String prompt;
  final int batchSize;

  /// 收尾的「去练这组」深链；页面自己算相关题并起练习。
  final void Function() onStartPractice;

  static Future<void> show(
    BuildContext context, {
    required List<RecallEntry> entries,
    required void Function() onStartPractice,
    required String pageKey,
    required SelfTestStore store,
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
          pageKey: pageKey,
          store: store,
          prompt: prompt,
          batchSize: batchSize,
        ),
      ),
    );
  }

  @override
  State<RecallSession> createState() => _RecallSessionState();
}

/// 自测的一个条目：正面由页面提供，文案在条目里。
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

  /// 页内稳定的键：记录按它存，内容改版后键变了就当新条目重考。
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

  /// 本轮已经没记住过的条目 id：它们之后再被问到、记住了，也不算「一次就记住」。
  final Set<String> _missedThisRound = {};
  final List<String> _missedNames = [];

  /// 上一轮抽到的条目 id：同一批里尽量不连着出现。
  Set<String> _lastRound = {};
  final FocusNode _focus = FocusNode();
  bool _revealed = false;
  int _asked = 0;
  int _missed = 0;
  int _rounds = 1;
  int _roundSize = 0;
  bool _done = false;

  SelfTestStore get _store => widget.store;
  String get _page => widget.pageKey;

  int get _knownCount => _store.knownCount(_page, [for (final e in widget.entries) e.id]);
  int get _unknownCount => widget.entries.length - _knownCount;

  @override
  void initState() {
    super.initState();
    _queue = _draw();
    _roundSize = _queue.length;
    _done = _queue.isEmpty;
    WidgetsBinding.instance.addPostFrameCallback((_) => _focus.requestFocus());
  }

  @override
  void dispose() {
    _focus.dispose();
    super.dispose();
  }

  /// 抽一轮，只从没认得的里抽：没记住过的先来（至多一半，其余留给没考过的），
  /// 没考过的次之，不够再用没记住过的补满；上一轮刚出现过的排在后面。
  List<RecallEntry> _draw() {
    final unknown = [for (final e in widget.entries) if (!_store.isKnown(_page, e.id)) e];
    int byLast(RecallEntry a, RecallEntry b) =>
        (_lastRound.contains(a.id) ? 1 : 0) - (_lastRound.contains(b.id) ? 1 : 0);
    final learning = [for (final e in unknown) if (_store.isLearning(_page, e.id)) e]
      ..shuffle()
      ..sort(byLast);
    final fresh = [for (final e in unknown) if (!_store.isLearning(_page, e.id)) e]..shuffle();
    final cap = (widget.batchSize / 2).ceil();
    final picked = <RecallEntry>[
      ...learning.take(cap),
      ...fresh.take(widget.batchSize),
      ...learning.skip(cap),
    ].take(widget.batchSize).toList()..shuffle();
    _lastRound = {for (final e in picked) e.id};
    return picked;
  }

  void _nextRound() {
    setState(() {
      _queue = _draw();
      _roundSize = _queue.length;
      _missedThisRound.clear();
      _missedNames.clear();
      _asked = 0;
      _missed = 0;
      _rounds++;
      _revealed = false;
      _done = _queue.isEmpty;
    });
  }

  /// 清空本页记录，从头自测一遍。
  void _restart() {
    _store.reset(_page);
    _lastRound = {};
    _rounds = 0;
    _nextRound();
  }

  void _reveal() {
    if (!_revealed) setState(() => _revealed = true);
  }

  void _grade(bool remembered) {
    final current = _queue.first;
    // 评一张就记一张：中途退出也不丢。
    _store.record(
      _page,
      current.id,
      remembered: remembered,
      firstTry: !_missedThisRound.contains(current.id),
    );
    setState(() {
      _asked++;
      _queue.removeAt(0);
      if (!remembered) {
        _missed++;
        if (_missedThisRound.add(current.id)) _missedNames.add(current.name);
        // 没记住的跳过两张新卡后重新插队（ADR 0077 决策 1）。
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

  /// 「已认得 K / N」进度条：让人看见自测在往前走，也说明为什么有些条目不再出现。
  Widget _progress(BuildContext context, TextStyle? muted) {
    final total = widget.entries.length;
    final known = _knownCount;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text("已认得 $known / $total · 只考没认得的", style: muted),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: total == 0 ? 0 : known / total,
            minHeight: 6,
            backgroundColor: Bs.border,
            color: Bs.success,
          ),
        ),
      ],
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
            Text("自测", style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(width: 10),
            Expanded(
              child: Text("第 $_rounds 轮 · 剩 ${_queue.length} 张 · 没记住 $_missed", style: muted),
            ),
            IconButton(
              tooltip: "退出自测（Esc）：评过的已经记下",
              onPressed: () => Navigator.of(context).pop(),
              icon: const Icon(Glyph.close),
            ),
          ],
        ),
        const SizedBox(height: 4),
        _progress(context, muted),
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
            ? Column(
                children: [
                  Row(
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
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "第一次就记住的，以后不再考；没记住的会再来。",
                    textAlign: TextAlign.center,
                    style: muted?.copyWith(fontSize: 13),
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
    final muted = Theme.of(context).textTheme.bodyMedium?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
      height: 1.5,
    );
    final allKnown = _unknownCount == 0;
    final remaining = _unknownCount;
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Text(allKnown ? "这一页你都认得了" : "考完了", style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 12),
        SizedBox(width: 420, child: _progress(context, muted)),
        const SizedBox(height: 12),
        if (_roundSize > 0) ...[
          Text("这一轮 $_roundSize 个，共考 $_asked 次，其中没记住 $_missed 次。", style: body),
          const SizedBox(height: 6),
        ],
        if (_missedNames.isNotEmpty)
          Text("需要再看看：${_missedNames.join("、")}", textAlign: TextAlign.center, style: body)
        else if (allKnown)
          Text("没有要再考的了。真正的检验还是做题——去把相关的题过一遍。", textAlign: TextAlign.center, style: body)
        else
          Text("这一轮全都一次记住了，还剩 $remaining 个没认得。", textAlign: TextAlign.center, style: body),
        const SizedBox(height: 18),
        Wrap(
          alignment: WrapAlignment.center,
          spacing: 12,
          runSpacing: 10,
          children: [
            if (!allKnown)
              FilledButton(
                onPressed: _nextRound,
                child: Text("再来 ${remaining < widget.batchSize ? remaining : widget.batchSize} 个"),
              )
            else
              FilledButton(
                onPressed: _restart,
                child: const Text("重新自测"),
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
