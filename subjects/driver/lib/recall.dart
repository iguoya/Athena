import "dart:async";
import "dart:math";

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

/// 一张速记卡现在属于哪一档（ADR 0083）。按「该不该考」从急到缓：
/// [wrong] 作答记录里答错过、或自测里答错过——最该考；
/// [due] 之前认得，复现间隔到了——该确认还记得；
/// [fresh] 没有任何证据——还没考过；
/// [partial] 相关题只做了一部分、没答错——次之；
/// [selfOnly] 自测答对（在间隔内）但作答记录还没证明——自测先不出，留给做题确认；
/// [known] 作答记录证明已掌握（或没有相关题、自测答对且在间隔内）——不考。
enum RecallBucket { wrong, due, fresh, partial, selfOnly, known }

/// 这一档里自测会抽的，按先后顺序。
const recallDrawOrder = [RecallBucket.wrong, RecallBucket.due, RecallBucket.fresh, RecallBucket.partial];

/// 判一张卡的档位。**「认得」以作答记录为准**（ADR 0083）：自测里的作答会高估自己，
/// 所以有相关题的条目，只有相关题全部答对并掌握才算认得；自测答对最多得到
/// [RecallBucket.selfOnly]，而且作答记录里答错过的，自测答得再对也还是 [RecallBucket.wrong]。
/// 没有相关题的条目（胎压灯这类）没有作答证据可用，才退回自测作答，同样按间隔复现。
RecallBucket classifyEntry({
  required List<Question> related,
  required Set<String> mastered,
  required HistorySet histories,
  required SelfTestStore store,
  required String page,
  required String id,
}) {
  if (related.isEmpty) {
    if (store.isLearning(page, id)) return RecallBucket.wrong;
    if (store.isConfirmed(page, id)) return RecallBucket.known;
    if (store.isOverdue(page, id)) return RecallBucket.due;
    return RecallBucket.fresh;
  }
  final status = statusOf(related: related, mastered: mastered, histories: histories);
  switch (status) {
    case SymbolStatus.wrong:
      return RecallBucket.wrong;
    case SymbolStatus.mastered:
      return _masteryOverdue(related, histories, store.now()) ? RecallBucket.due : RecallBucket.known;
    case SymbolStatus.partial:
    case SymbolStatus.fresh:
      if (store.isLearning(page, id)) return RecallBucket.wrong;
      if (store.isConfirmed(page, id)) return RecallBucket.selfOnly;
      if (store.isOverdue(page, id)) return RecallBucket.due;
      return status == SymbolStatus.partial ? RecallBucket.partial : RecallBucket.fresh;
  }
}

/// 作答记录证明了掌握，但离最近一次作答已经过了复现间隔：该回头确认还记得。
/// 阶梯按相关题里连对跨过的天数最少的那道算（越稳固，间隔越长）。
bool _masteryOverdue(List<Question> related, HistorySet histories, DateTime now) {
  DateTime? oldest;
  var stage = SelfTestStore.intervalDays.length;
  for (final q in related) {
    final h = histories.byQuestion[q.id];
    if (h == null || h.lastAt == null) return false;
    if (oldest == null || h.lastAt!.isBefore(oldest)) oldest = h.lastAt;
    if (h.streakDays.length < stage) stage = h.streakDays.length;
  }
  if (oldest == null) return false;
  return now.difference(oldest) >= Duration(days: SelfTestStore.daysForStage(stage));
}

/// 速记页的「自测」模式（ADR 0077 起，ADR 0080 一轮 5 个（ADR 0089 改 10 个），ADR 0082 改名并只考没认得的，
/// ADR 0083 「认得」改以作答记录为准，ADR 0085 改四选一）：卡片流式检索练习。
///
/// 正面是条目自己提供的 [RecallEntry.front]（规范图或情景文字），下方给四个选项——来自同页
/// 其他条目，同组优先、易混对排最前（[RecallEntry.group]）；点选或按 1～4 作答，对错当场判定，
/// 答后选项定格、显示答案与讲解，空格进下一张。
///
/// **只考没证明认得的，而且认得看作答记录，不看自测作答**：每轮从 [recallDrawOrder] 的档位里
/// 依次抽 [RecallSession.batchSize] 个——答错过的先来，到期复现的次之，没考过的再次，
/// 相关题只做了一部分的最后；作答记录证明已掌握的不出，自测答对、还没有作答证明的也先不出
/// （[RecallBucket.selfOnly]，留给做题确认）。答错的隔两张后重现。每判一张就记一张，随时
/// 可退出（右上角按钮或 Esc）。收尾给「去做这几个的题」：把这一轮答错、或只有自测答对的几个
/// 条目的相关题起一轮练习，让作答记录来确认——真正的记忆闭环由作答通路完成。
///
/// 自测记录**不是掌握度**：不写作答、不进统计与激励。
class RecallSession extends StatefulWidget {
  const RecallSession({
    super.key,
    required this.entries,
    required this.onStartPractice,
    required this.pageKey,
    required this.store,
    required this.histories,
    required this.mastered,
    this.prompt = defaultPrompt,
    this.batchSize = defaultBatchSize,
  });

  /// 一轮抽几个（使用者要求「一次 10 道」，ADR 0089；原为 5）。
  static const defaultBatchSize = 10;
  static const defaultPrompt = "想一想：这是什么？选一个你认得的。";

  /// 参与自测的全部条目；[RecallEntry] 是页面内容的轻量视图。
  final List<RecallEntry> entries;

  /// 本页在 [SelfTestStore] 里的键，条目 id 在页内唯一即可。
  final String pageKey;
  final SelfTestStore store;

  /// 作答历史与已掌握集合：「认得」的客观依据（ADR 0083）。
  final HistorySet histories;
  final Set<String> mastered;

  /// 正面卡下方的提问句：符号页问「这是什么」，数字与要点页问「是多少 / 怎么做」。
  final String prompt;
  final int batchSize;

  /// 收尾的「去做这几个的题」：收到这些条目相关题的去重并集；页面起一轮练习。
  final void Function(List<Question> questions) onStartPractice;

  static Future<void> show(
    BuildContext context, {
    required List<RecallEntry> entries,
    required void Function(List<Question> questions) onStartPractice,
    required String pageKey,
    required SelfTestStore store,
    required HistorySet histories,
    required Set<String> mastered,
    String prompt = defaultPrompt,
    int batchSize = defaultBatchSize,
  }) {
    return showDialog<void>(
      context: context,
      barrierColor: Colors.transparent,
      builder: (_) => Dialog(
        insetPadding: const EdgeInsets.all(24),
        backgroundColor: Colors.transparent,
        // 宽屏上两栏（选项 + 解释）别被拉得太散：最宽 1180（ADR 0089）。
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1180),
          child: RecallSession(
            entries: entries,
            onStartPractice: onStartPractice,
            pageKey: pageKey,
            store: store,
            histories: histories,
            mastered: mastered,
            prompt: prompt,
            batchSize: batchSize,
          ),
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
    this.related = const [],
    this.confuseName,
    this.confuseNote,
    this.confuseView,
    this.group,
    this.answerTexts = const [],
  });

  /// 页内稳定的键：记录按它存，内容改版后键变了就当新条目重考。
  final String id;

  /// 正面：符号页是规范图，数字与要点页是情景文字。
  final Widget front;

  /// 答后显示的答案标题与说明。
  final String name;
  final String meaning;

  /// 这个条目的相关题（客观证据的来源，ADR 0083）。符号页是按条目反向映射的题；
  /// 数字、要点页只能到「组」一级，同一组的条目共用一份。没有相关题的条目为空，
  /// 只能退回自测作答。
  final List<Question> related;

  /// 易混对撞卡（ADR 0077 决策 2）：对方名称、差异口诀与大图。
  final String? confuseName;
  final String? confuseNote;
  final Widget? confuseView;

  /// 干扰项的组键（ADR 0085）：同组条目优先做干扰——禁令混禁令、罚款混罚款；
  /// 不传则所有候选同权。
  final String? group;

  /// 选择题的正确答案候选（ADR 0085）：一个情景有多条要点时每次抽一条考，
  /// 比如要点速记页传该情景的全部要点；空则用 [name]。
  final List<String> answerTexts;
}

class _RecallSessionState extends State<RecallSession> {
  /// 本轮待考队列；没记住的条目在消耗两张新卡后重新插入。
  late List<RecallEntry> _queue;

  /// 本轮已经没记住过的条目 id：它们之后再被问到、答对了，也不算「一次就记住」。
  final Set<String> _missedThisRound = {};
  final List<String> _missedNames = [];

  /// 本轮抽到的条目：收尾据此挑出「要去做题确认」的几个。
  List<RecallEntry> _round = [];

  /// 这次打开自测期间答对（第一次就选对）的条目 id：同一次里不再重复抽它们，即使作答记录
  /// 里它们仍是答错 / 没做过——自测答对只能让它们这一次不再出现，认得与否仍等作答来证明。
  final Set<String> _doneThisSession = {};

  /// 上一轮抽到的条目 id：同一档里尽量不连着出现。
  Set<String> _lastRound = {};
  final FocusNode _focus = FocusNode();

  /// 答对后自动切下一张的计时（ADR 0089）；答错不自动切，留着看解释。
  Timer? _autoTimer;

  /// 答对后停多久再自动切：够看清选项变绿和一眼解释，又不拖节奏。
  static const autoAdvanceDelay = Duration(milliseconds: 900);

  /// 宽度够才分两栏（选项左、解释右）；窄窗口把解释叠到选项下面。
  static const _twoColumnMinWidth = 760.0;

  /// 本轮的考卷（ADR 0085）：条目键 → 正确答案与选项。重现的卡沿用同一张卷，
  /// 避免同一张卡两回考不同侧面；进下一轮重新出。
  final Map<String, String> _answerById = {};
  final Map<String, List<String>> _optionsById = {};
  final Random _random = Random();

  bool _revealed = false;

  /// 本次作答选中的选项文本：答后高亮判定用。
  String? _selected;
  bool _lastCorrect = false;
  int _asked = 0;
  int _missed = 0;
  int _rounds = 1;
  bool _done = false;

  SelfTestStore get _store => widget.store;
  String get _page => widget.pageKey;

  RecallBucket _bucketOf(RecallEntry e) => classifyEntry(
    related: e.related,
    mastered: widget.mastered,
    histories: widget.histories,
    store: _store,
    page: _page,
    id: e.id,
  );

  int _count(RecallBucket bucket) => widget.entries.where((e) => _bucketOf(e) == bucket).length;

  /// 还能抽的（排除这次已经答对过的）。
  int get _drawable => widget.entries
      .where((e) => recallDrawOrder.contains(_bucketOf(e)) && !_doneThisSession.contains(e.id))
      .length;

  @override
  void initState() {
    super.initState();
    _queue = _draw();
    _round = [..._queue];
    _done = _queue.isEmpty;
    WidgetsBinding.instance.addPostFrameCallback((_) => _focus.requestFocus());
  }

  @override
  void dispose() {
    _autoTimer?.cancel();
    _focus.dispose();
    super.dispose();
  }

  /// 抽一轮：按 [recallDrawOrder] 逐档取，每档内先打乱、上一轮刚出现过的排后面；
  /// 这次答对过的不再抽。抽到的条目都出一张卷（重现时沿用）。
  List<RecallEntry> _draw() {
    final byBucket = {for (final b in recallDrawOrder) b: <RecallEntry>[]};
    for (final e in widget.entries) {
      if (_doneThisSession.contains(e.id)) continue;
      byBucket[_bucketOf(e)]?.add(e);
    }
    final picked = <RecallEntry>[];
    for (final b in recallDrawOrder) {
      final list = byBucket[b]!
        ..shuffle()
        ..sort((a, c) => (_lastRound.contains(a.id) ? 1 : 0) - (_lastRound.contains(c.id) ? 1 : 0));
      picked.addAll(list);
      if (picked.length >= widget.batchSize) break;
    }
    final round = picked.take(widget.batchSize).toList()..shuffle();
    _lastRound = {for (final e in round) e.id};
    for (final e in round) {
      _makeQuiz(e);
    }
    return round;
  }

  /// 出一张卷（ADR 0085）：正确选项从 [RecallEntry.answerTexts] 里随机抽一条（多条要点的
  /// 情景每次考一条），干扰项取其他条目的答案文本——易混对与同组优先、跨组补位，排除与
  /// 正确答案相同的文本；凑不满四个就按实际个数出。整组打乱后按条目键存，重现沿用。
  void _makeQuiz(RecallEntry e) {
    if (_answerById.containsKey(e.id)) return;
    final answers = e.answerTexts.isEmpty ? [e.name] : e.answerTexts;
    final answer = answers[_random.nextInt(answers.length)];
    final near = <String>[];
    final far = <String>[];
    final seen = {answer};
    if (e.confuseName != null && seen.add(e.confuseName!)) near.add(e.confuseName!);
    for (final other in widget.entries) {
      if (other.id == e.id) continue;
      final texts = other.answerTexts.isEmpty ? [other.name] : other.answerTexts;
      for (final t in texts) {
        if (!seen.add(t)) continue;
        (other.group != null && other.group == e.group ? near : far).add(t);
      }
    }
    near.shuffle(_random);
    far.shuffle(_random);
    _answerById[e.id] = answer;
    _optionsById[e.id] = [answer, ...near, ...far].take(4).toList()..shuffle(_random);
  }

  void _nextRound() {
    setState(() {
      _answerById.clear();
      _optionsById.clear();
      _queue = _draw();
      _round = [..._queue];
      _missedThisRound.clear();
      _missedNames.clear();
      _asked = 0;
      _missed = 0;
      _rounds++;
      _revealed = false;
      _selected = null;
      _done = _queue.isEmpty;
    });
  }

  /// 清空本页自测记录，从头自测一遍（作答记录不动）。
  void _restart() {
    _store.reset(_page);
    _doneThisSession.clear();
    _lastRound = {};
    _rounds = 0;
    _nextRound();
  }

  /// 作答一张（ADR 0085）：对错当场判定，判一次就记一次，中途退出也不丢。
  void _choose(String selected) {
    final current = _queue.first;
    final correct = selected == _answerById[current.id];
    final firstTry = !_missedThisRound.contains(current.id);
    _store.record(_page, current.id, remembered: correct, firstTry: firstTry);
    if (correct && firstTry) _doneThisSession.add(current.id);
    setState(() {
      _asked++;
      _revealed = true;
      _selected = selected;
      _lastCorrect = correct;
      if (!correct) {
        _missed++;
        if (_missedThisRound.add(current.id)) _missedNames.add(current.name);
      }
    });
    // 答对自动切下一张；答错留在解释上，自己点「下一张」。
    _autoTimer?.cancel();
    if (correct) {
      _autoTimer = Timer(autoAdvanceDelay, () {
        if (mounted && _revealed && _queue.isNotEmpty && _queue.first.id == current.id) _advance();
      });
    }
  }

  /// 看完讲解，推进：答错的隔两张新卡后重现插队（ADR 0077 决策 1）。
  void _advance() {
    _autoTimer?.cancel();
    final current = _queue.first;
    setState(() {
      _queue.removeAt(0);
      if (!_lastCorrect) {
        if (_queue.length > 2) {
          _queue.insert(2, current);
        } else {
          _queue.add(current);
        }
      }
      _revealed = false;
      _selected = null;
      if (_queue.isEmpty) _done = true;
    });
  }

  /// 收尾要去做题确认的条目：这一轮答错的，加上只有自测答对、没有作答证明的
  /// （本轮抽到的，或抽不出新卡时全部「自测答对」的）。
  List<RecallEntry> _focusEntries() {
    final pool = _drawable == 0 ? widget.entries : _round;
    return [
      for (final e in pool)
        if (_bucketOf(e) != RecallBucket.known && e.related.isNotEmpty) e,
    ];
  }

  List<Question> _focusQuestions() {
    final seen = <String>{};
    return [
      for (final e in _focusEntries())
        for (final q in e.related)
          if (!widget.mastered.contains(q.id) && seen.add(q.id)) q,
    ];
  }

  KeyEventResult _onKey(FocusNode node, KeyEvent event) {
    if (event is! KeyDownEvent) return KeyEventResult.ignored;
    if (event.logicalKey == LogicalKeyboardKey.escape) {
      Navigator.of(context).pop();
      return KeyEventResult.handled;
    }
    if (_done) return KeyEventResult.ignored;
    if (_revealed) {
      if (event.logicalKey == LogicalKeyboardKey.space ||
          event.logicalKey == LogicalKeyboardKey.enter ||
          event.logicalKey == LogicalKeyboardKey.numpadEnter) {
        _advance();
        return KeyEventResult.handled;
      }
      return KeyEventResult.ignored;
    }
    // 未作答：1～4 选选项。
    final option = switch (event.logicalKey) {
      LogicalKeyboardKey.digit1 || LogicalKeyboardKey.numpad1 => 0,
      LogicalKeyboardKey.digit2 || LogicalKeyboardKey.numpad2 => 1,
      LogicalKeyboardKey.digit3 || LogicalKeyboardKey.numpad3 => 2,
      LogicalKeyboardKey.digit4 || LogicalKeyboardKey.numpad4 => 3,
      _ => null,
    };
    final options = _optionsById[_queue.first.id];
    if (option != null && options != null && option < options.length) {
      _choose(options[option]);
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

  /// 进度反馈：作答记录证明认得的（实心绿）与只有自测答对的（浅色）分开画、分开写，
  /// 让人看见哪些是客观的、哪些还待做题确认。
  Widget _progress(BuildContext context, TextStyle? muted) {
    final total = widget.entries.length;
    final known = _count(RecallBucket.known);
    final selfOnly = _count(RecallBucket.selfOnly);
    double frac(int n) => total == 0 ? 0 : n / total;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          "已认得 $known / $total（以作答记录为准）${selfOnly > 0 ? " · 自测答对 $selfOnly，待做题确认" : ""}",
          style: muted,
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: SizedBox(
            height: 6,
            child: Stack(
              children: [
                Positioned.fill(child: ColoredBox(color: Bs.border)),
                FractionallySizedBox(
                  widthFactor: frac(known + selfOnly).clamp(0.0, 1.0),
                  child: ColoredBox(color: Bs.success.withValues(alpha: 0.35)),
                ),
                FractionallySizedBox(
                  widthFactor: frac(known).clamp(0.0, 1.0),
                  child: ColoredBox(color: Bs.success),
                ),
              ],
            ),
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
    // 左：提问与四个选项；右：答案解释（ADR 0089）。窄窗口放不下两栏就把解释叠到下面。
    final left = Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 4),
          child: Text(widget.prompt, style: Theme.of(context).textTheme.titleMedium),
        ),
        _options(context, entry),
      ],
    );
    final right = _explanation(context, entry, muted);
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
              tooltip: "退出自测（Esc）：判过的已经记下",
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
        LayoutBuilder(
          builder: (context, constraints) {
            if (constraints.maxWidth < _twoColumnMinWidth) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [left, const SizedBox(height: 12), right],
              );
            }
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(flex: 5, child: left),
                const SizedBox(width: 20),
                Expanded(flex: 4, child: right),
              ],
            );
          },
        ),
        // 「下一张」固定在底部中间；答对会自动切（_autoAdvance），按钮 / 空格可以抢先。
        if (_revealed) ...[
          const SizedBox(height: 16),
          Center(
            child: FilledButton(
              onPressed: _advance,
              child: Text(_lastCorrect ? "下一张（空格）· 自动切换中" : "下一张（空格）"),
            ),
          ),
        ],
      ],
    );
  }

  /// 右栏的答案解释（ADR 0089）：没作答时只给一句提示，免得右栏空着；答后给判定、答案标题、
  /// 说明与易混卡。固定在选项右侧，选项不再拉满整行。
  Widget _explanation(BuildContext context, RecallEntry entry, TextStyle? muted) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Bs.light,
        borderRadius: BorderRadius.circular(Bs.radius),
      ),
      child: !_revealed
          ? Padding(
              padding: const EdgeInsets.symmetric(vertical: 24),
              child: Text("选一个答案，这里给出解释。", textAlign: TextAlign.center, style: muted),
            )
          : Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _lastCorrect ? "答对了" : "答错了，正确答案：",
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: _lastCorrect ? Bs.success : Bs.danger,
                  ),
                ),
                const SizedBox(height: 8),
                Text(entry.name, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                Text(entry.meaning, style: muted),
                if (entry.confuseName != null) ...[
                  const SizedBox(height: 14),
                  Divider(height: 1, color: Bs.border),
                  const SizedBox(height: 12),
                  Row(
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
                ],
              ],
            ),
    );
  }

  /// 四个选项（ADR 0085）：未作答时可点，答后定格——正确项标绿、选错的标红、
  /// 其余暗淡。序号对应快捷键 1～4。
  Widget _options(BuildContext context, RecallEntry entry) {
    final options = _optionsById[entry.id] ?? const <String>[];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final (i, text) in options.indexed)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: _optionTile(context, entry, i, text),
          ),
      ],
    );
  }

  Widget _optionTile(BuildContext context, RecallEntry entry, int index, String text) {
    final correct = text == _answerById[entry.id];
    final chosen = text == _selected;
    Color? fill;
    Color border = Bs.border;
    Color? foreground;
    if (_revealed) {
      if (correct) {
        fill = Bs.success.withValues(alpha: 0.12);
        border = Bs.success;
      } else if (chosen) {
        fill = Bs.danger.withValues(alpha: 0.10);
        border = Bs.danger;
      } else {
        foreground = Theme.of(context).colorScheme.onSurfaceVariant;
      }
    }
    return OutlinedButton(
      key: ValueKey(correct ? "recall-correct" : "recall-option-$index"),
      onPressed: _revealed ? null : () => _choose(text),
      style: OutlinedButton.styleFrom(
        backgroundColor: fill,
        side: BorderSide(color: border),
        foregroundColor: foreground,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        alignment: Alignment.centerLeft,
      ),
      child: Row(
        children: [
          Text(
            "${index + 1}.",
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: foreground,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: TextStyle(fontSize: 16, height: 1.4, color: foreground),
            ),
          ),
          if (_revealed && correct) Icon(Glyph.correct, size: 16, color: Bs.success),
          if (_revealed && chosen && !correct) Icon(Glyph.wrong, size: 16, color: Bs.danger),
        ],
      ),
    );
  }

  Widget _summary(BuildContext context) {
    final body = Theme.of(context).textTheme.bodyLarge;
    final muted = Theme.of(context).textTheme.bodyMedium?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
      height: 1.5,
    );
    final remaining = _drawable;
    final selfOnly = _count(RecallBucket.selfOnly);
    final allKnown = remaining == 0 && selfOnly == 0 && _count(RecallBucket.known) == widget.entries.length;
    final focus = _focusQuestions();
    final title = allKnown
        ? "这一页作答记录都证明你认得了"
        : remaining == 0
        ? "这一页没有要再考的了"
        : "考完了";
    final String message;
    if (_missedNames.isNotEmpty) {
      message = "需要再看看：${_missedNames.join("、")}";
    } else if (allKnown) {
      message = "没有要再考的了。隔一段时间会按间隔回头确认。";
    } else if (remaining == 0) {
      message = "剩下的是你自测答对、但作答记录还没证明的。去做几道相关题，让作答记录来确认。";
    } else {
      message = "这一轮全都一次答对了，还有 $remaining 个没认得。";
    }
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Text(title, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 12),
        SizedBox(width: 460, child: _progress(context, muted)),
        const SizedBox(height: 12),
        if (_round.isNotEmpty) ...[
          Text("这一轮 ${_round.length} 个，共考 $_asked 次，其中没记住 $_missed 次。", style: body),
          const SizedBox(height: 6),
        ],
        Text(message, textAlign: TextAlign.center, style: body),
        const SizedBox(height: 18),
        Wrap(
          alignment: WrapAlignment.center,
          spacing: 12,
          runSpacing: 10,
          children: [
            if (remaining > 0)
              FilledButton(
                onPressed: _nextRound,
                child: Text("再来 ${remaining < widget.batchSize ? remaining : widget.batchSize} 个"),
              )
            else if (!allKnown)
              FilledButton(
                onPressed: _restart,
                child: const Text("重新自测"),
              ),
            if (focus.isNotEmpty)
              (remaining > 0 ? OutlinedButton.new : FilledButton.new)(
                onPressed: () {
                  Navigator.of(context).pop();
                  widget.onStartPractice(focus);
                },
                child: Text("去做这几个的题（${focus.length} 题）"),
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
