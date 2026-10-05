import "dart:async";
import "dart:math";

import "package:flutter/material.dart";
import "package:flutter/services.dart";

import "glyphs.dart";
import "look.dart";
import "models.dart";
import "quiz_options.dart";
import "recall_cards.dart";
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

/// 一张速记卡现在属于哪一档（ADR 0094）。**只看作答记录**——速记卡对应一道有稳定编号的速记题，
/// 自测的每次作答和练习、模拟考一样记进作答记录，错题本、考前复习、强化练习用的是同一份记录：
/// - [wrong]：这张卡的题答错过、且还在错题库里（累计答对没达到答错的 2 倍，ADR 0079）；或者它关联的
///   真题答错过——最该考；
/// - [fresh]：没有任何记录——还没考过；
/// - [partial]：关联的真题只做了一部分、没答错——次之；
/// - [done]：这张卡答对过且没答错过，或错题已经移出错题库，或关联的真题全部答对掌握——不再出现。
enum RecallBucket { wrong, fresh, partial, done }

/// 自测会抽的档位，按先后顺序。
const recallDrawOrder = [RecallBucket.wrong, RecallBucket.fresh, RecallBucket.partial];

/// 判一张卡的档位：先看这张卡自己的作答记录，没有再看关联真题的记录。
RecallBucket classifyEntry({
  required String questionId,
  required List<Question> related,
  required Set<String> mastered,
  required HistorySet histories,
}) {
  final own = classifyOwn(questionId, histories);
  if (own != null) return own;
  if (related.isEmpty) return RecallBucket.fresh;
  return switch (statusOf(related: related, mastered: mastered, histories: histories)) {
    SymbolStatus.wrong => RecallBucket.wrong,
    SymbolStatus.mastered => RecallBucket.done,
    SymbolStatus.partial => RecallBucket.partial,
    SymbolStatus.fresh => RecallBucket.fresh,
  };
}

/// 只按这张卡**自己**的作答记录判档：答错过且还在错题库里（[RecallBucket.wrong]）、
/// 答对过或已移出错题库（[RecallBucket.done]）、没答过返回 null——不看关联真题。
/// 进度反馈用它计数：关联真题的掌握是「这组内容你会」，不是「这张卡你测过」，
/// 混进来会把「已答对」灌成满格（ADR 0097 分科目后易混数字页实际发生过）。
RecallBucket? classifyOwn(String questionId, HistorySet histories) {
  final own = histories.byQuestion[questionId];
  if (own == null || own.attempts == 0) return null;
  // 答错过的卡和错题一个规矩：累计答对达到答错的 2 倍才移出错题库（ADR 0079）。
  if (own.wrong > 0) return own.retiredFromWrongPool ? RecallBucket.done : RecallBucket.wrong;
  return RecallBucket.done;
}

/// 记一次自测作答：由首页接上，写成一条普通作答记录（题号是速记题的编号），错题本、强化练习随之更新。
typedef RecallAnswerRecorder = Future<void> Function(RecallEntry entry, {required bool correct});

/// 速记页的「自测」（ADR 0077 起；ADR 0094 并入作答记录）：卡片流式检索练习。
///
/// 正面是条目自己提供的 [RecallEntry.front]（规范图或情景 / 情形文字）。大多数卡出四选一——选项来自
/// 同页其他条目，同组优先、易混对排最前；点选或按 1～4 作答。易混数字里的数值题改成**手输**：下面一个输入框，
/// 前后带值的前缀和单位，自己把数字敲进去，不给选项。对错当场判定，答后给解释，答对自动切下一张。
///
/// **自测的每次作答就是一条作答记录**（[RecallAnswerRecorder]）：答错的卡进错题库，被考前复习、强化练习
/// 接着练；累计答对达到答错 2 倍才移出，规矩和错题一样。自测只考「没考过」和「还在错题库里」的卡，按轻重缓急排成
/// 一队逐张过完，没有张数上限；答对过的不再出现。答错的隔两张后重现。随时可退出（右上角按钮或 Esc），
/// 判过的已经记下。收尾给「去做这几个的题」：把答错的几张的关联真题起一轮练习。
class RecallSession extends StatefulWidget {
  const RecallSession({
    super.key,
    required this.entries,
    required this.onStartPractice,
    required this.onAnswer,
    required this.histories,
    required this.mastered,
    this.prompt = defaultPrompt,
  });

  static const defaultPrompt = "想一想：这是什么？选一个。";

  /// 参与自测的全部条目；[RecallEntry] 是页面内容的轻量视图。
  final List<RecallEntry> entries;

  /// 作答历史与已掌握集合：判断哪些卡还要考（ADR 0094）。
  final HistorySet histories;
  final Set<String> mastered;

  /// 每次作答记一条作答记录。
  final RecallAnswerRecorder onAnswer;

  /// 卡片下方的默认提问句；条目自己有的优先。
  final String prompt;

  /// 收尾的「去做这几个的题」：收到这些条目关联真题的去重并集；页面起一轮练习。
  final void Function(List<Question> questions) onStartPractice;

  static Future<void> show(
    BuildContext context, {
    required List<RecallEntry> entries,
    required void Function(List<Question> questions) onStartPractice,
    required RecallAnswerRecorder onAnswer,
    required HistorySet histories,
    required Set<String> mastered,
    String prompt = defaultPrompt,
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
            onAnswer: onAnswer,
            histories: histories,
            mastered: mastered,
            prompt: prompt,
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
    required this.questionId,
    required this.front,
    required this.name,
    required this.meaning,
    this.related = const [],
    this.confuseName,
    this.confuseNote,
    this.confuseView,
    this.group,
    this.answerTexts = const [],
    this.stemText,
    this.typed,
    this.inputLabel,
    this.prompt,
    this.kind,
    this.nearOnly = false,
  });

  /// 从一张速记卡建条目：数据取自 [RecallCard]，界面部分（正面、易混对方的图）与关联真题由页面补。
  factory RecallEntry.fromCard(
    RecallCard card, {
    required Widget front,
    List<Question> related = const [],
    Widget? confuseView,
  }) {
    return RecallEntry(
      id: card.id,
      questionId: card.questionId,
      front: front,
      name: card.name,
      meaning: card.meaning,
      related: related,
      confuseName: card.confuseName,
      confuseNote: card.confuseNote,
      confuseView: confuseView,
      group: card.group,
      answerTexts: card.answerTexts,
      stemText: card.stemText,
      typed: card.typed,
      inputLabel: card.inputLabel,
      prompt: card.prompt,
      kind: card.kind,
      nearOnly: card.nearOnly,
    );
  }

  /// 页内稳定的键，与对应的速记题编号（作答记录里的题号）。
  final String id;
  final String questionId;

  /// 正面：符号页是规范图，数字与要点页是情景文字。
  final Widget front;

  /// 答后显示的答案标题与说明。
  final String name;
  final String meaning;

  /// 这个条目关联的真题（符号页按条目反向映射，数字、要点页到「组」一级）：自测先考关联真题答错过的，
  /// 收尾「去做这几个的题」也用它。没有关联真题的条目为空。
  final List<Question> related;

  /// 易混对撞卡（ADR 0077 决策 2）：对方名称、差异口诀与大图。
  final String? confuseName;
  final String? confuseNote;
  final Widget? confuseView;

  /// 干扰项的组键、选择题的正确答案候选、题干文字、选项来源种类，见 [QuizSource]。
  final String? group;
  final List<String> answerTexts;
  final String? stemText;
  final String? kind;
  final bool nearOnly;

  /// 数值题的手输答案：非空就出输入框、不出选项；[inputLabel] 是输入框前的小标签（组名）。
  final TypedAnswer? typed;
  final String? inputLabel;

  /// 本条目自己的提问句；空则用会话的。
  final String? prompt;
}

class _RecallSessionState extends State<RecallSession> {
  /// 本次待考队列；答错的条目在消耗两张新卡后重新插入。
  late List<RecallEntry> _queue;

  /// 这次答错过的条目 id 与名字：收尾列出来，也据此挑「去做这几个的题」。
  final Set<String> _missedIds = {};
  final List<String> _missedNames = [];

  /// 这次排进队的条目。
  List<RecallEntry> _round = [];

  /// 这次打开期间第一次就答对的条目 id：作答记录是打开时的快照，同一次里不再重复抽它们。
  final Set<String> _doneThisSession = {};

  final FocusNode _focus = FocusNode();
  final FocusNode _inputFocus = FocusNode();
  final TextEditingController _input = TextEditingController();

  /// 答对后自动切下一张的计时（ADR 0089）；答错不自动切，留着看解释。
  Timer? _autoTimer;

  /// 答对后停多久再自动切：够看清选项变绿和一眼解释，又不拖节奏。
  static const autoAdvanceDelay = Duration(milliseconds: 900);

  /// 宽度够才分两栏（选项左、解释右）；窄窗口把解释叠到选项下面。
  static const _twoColumnMinWidth = 760.0;

  /// 这次的考卷（ADR 0085）：条目键 → 正确答案与选项。重现的卡沿用同一张卷，
  /// 避免同一张卡两回考不同侧面。
  final Map<String, String> _answerById = {};
  final Map<String, List<String>> _optionsById = {};
  final Random _random = Random();

  bool _revealed = false;

  /// 本次作答选中的选项文本（选择题）或手输的文字（数值题）：答后高亮判定用。
  String? _selected;
  bool _lastCorrect = false;
  int _asked = 0;
  int _missed = 0;
  bool _done = false;

  RecallBucket _bucketOf(RecallEntry e) => classifyEntry(
    questionId: e.questionId,
    related: e.related,
    mastered: widget.mastered,
    histories: widget.histories,
  );

  /// 已经答对的卡数：作答记录里答对过的，加上这次第一次就答对的。
  /// 已答对的卡数：只数**自己答对过**的（最近一次作答答对、已移出错题库，或这次第一次就答对），
  /// 不把关联真题的掌握算进来（classifyOwn 的注释说明了为什么）。
  int get _correctCount => widget.entries
      .where((e) => classifyOwn(e.questionId, widget.histories) == RecallBucket.done || _doneThisSession.contains(e.id))
      .length;

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
    WidgetsBinding.instance.addPostFrameCallback((_) => _focusCurrent());
  }

  @override
  void dispose() {
    _autoTimer?.cancel();
    _focus.dispose();
    _inputFocus.dispose();
    _input.dispose();
    super.dispose();
  }

  /// 当前卡是数值题就把光标放进输入框，否则放回整张卡（空格 / 回车 / 数字键作答）。
  void _focusCurrent() {
    if (!mounted) return;
    if (!_done && !_revealed && _queue.isNotEmpty && _queue.first.typed != null) {
      _inputFocus.requestFocus();
    } else {
      _focus.requestFocus();
    }
  }

  /// 排一队：按 [recallDrawOrder] 逐档取，每档内先打乱、档位顺序保留——答错过的先考，没考过的次之；
  /// 这次答对过的不再抽。抽到的条目都出一张卷（重现时沿用）。
  List<RecallEntry> _draw() {
    final byBucket = {for (final b in recallDrawOrder) b: <RecallEntry>[]};
    for (final e in widget.entries) {
      if (_doneThisSession.contains(e.id)) continue;
      byBucket[_bucketOf(e)]?.add(e);
    }
    final picked = <RecallEntry>[];
    for (final b in recallDrawOrder) {
      picked.addAll(byBucket[b]!..shuffle());
    }
    for (final e in picked) {
      _makeQuiz(e);
    }
    return picked;
  }

  /// 出一张卷（ADR 0085、0094、0095）：数值题没有选项，标准答案是值原文；其余交给 [buildQuiz]——
  /// 正确项从条目的要点里抽一条，干扰项取其他条目的答案文本，选项文字去掉解释性括号。
  void _makeQuiz(RecallEntry e) {
    if (_answerById.containsKey(e.id)) return;
    final typed = e.typed;
    if (typed != null) {
      _answerById[e.id] = typed.display;
      _optionsById[e.id] = const [];
      return;
    }
    final quiz = buildQuiz(_sourceOf(e), [for (final o in widget.entries) _sourceOf(o)], random: _random);
    _answerById[e.id] = quiz.answer;
    _optionsById[e.id] = quiz.options;
  }

  QuizSource _sourceOf(RecallEntry e) => QuizSource(
    id: e.id,
    name: e.name,
    answerTexts: e.answerTexts,
    group: e.group,
    stemText: e.stemText,
    confuseName: e.confuseName,
    kind: e.kind,
    nearOnly: e.nearOnly,
  );

  /// 选择题作答。
  void _choose(String selected) {
    final current = _queue.first;
    _judge(current, selected: selected, correct: selected == _answerById[current.id]);
  }

  /// 数值题提交：输入里的数字按顺序与答案逐个比对（带不带单位、用哪种连接符都行）。
  void _submitTyped() {
    if (_revealed || _queue.isEmpty) return;
    final current = _queue.first;
    final typed = current.typed;
    final text = _input.text.trim();
    if (typed == null || text.isEmpty) return;
    _judge(current, selected: text, correct: typed.matches(text));
  }

  /// 数值题「不知道」：算答错，直接看答案。
  void _giveUp() {
    if (_revealed || _queue.isEmpty) return;
    _judge(_queue.first, selected: "", correct: false);
  }

  /// 判定一张：对错当场出，**记一条作答记录**（错题本、强化练习随之更新），中途退出也不丢。
  void _judge(RecallEntry current, {required String selected, required bool correct}) {
    final firstTry = !_missedIds.contains(current.id);
    unawaited(widget.onAnswer(current, correct: correct));
    if (correct && firstTry) _doneThisSession.add(current.id);
    setState(() {
      _asked++;
      _revealed = true;
      _selected = selected;
      _lastCorrect = correct;
      if (!correct) {
        _missed++;
        if (_missedIds.add(current.id)) _missedNames.add(current.name);
      }
    });
    // 判完把焦点交还整张卡，空格 / 回车才能进下一张。
    WidgetsBinding.instance.addPostFrameCallback((_) => _focusCurrent());
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
      _input.clear();
      if (_queue.isEmpty) _done = true;
    });
    WidgetsBinding.instance.addPostFrameCallback((_) => _focusCurrent());
  }

  /// 收尾「去做这几个的题」：这次答错的条目的关联真题（去重、排除已掌握的）。
  List<Question> _focusQuestions() {
    final seen = <String>{};
    return [
      for (final e in widget.entries)
        if (_missedIds.contains(e.id))
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
    // 未作答：1～4 选选项（数值题没有选项，数字归输入框）。
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

  /// 进度反馈：直接写答题过程——已经答对几张（共几张）。
  Widget _progress(BuildContext context, TextStyle? muted) {
    final total = widget.entries.length;
    final correct = _correctCount;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text("已答对 $correct / $total", style: muted),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: SizedBox(
            height: 6,
            child: Stack(
              children: [
                Positioned.fill(child: ColoredBox(color: Bs.border)),
                FractionallySizedBox(
                  widthFactor: total == 0 ? 0 : (correct / total).clamp(0.0, 1.0),
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
    // 左：提问与四个选项（数值题是输入框）；右：答案解释（ADR 0089）。窄窗口放不下两栏就把解释叠到下面。
    final left = Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 4),
          child: Text(entry.prompt ?? widget.prompt, style: Theme.of(context).textTheme.titleMedium),
        ),
        if (entry.typed != null) _typedInput(context, entry, muted) else _options(context, entry),
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
              child: Text("剩 ${_queue.length} 张 · 答错 $_missed", style: muted),
            ),
            IconButton(
              tooltip: "退出自测（Esc）：判过的已经记进作答记录",
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
        // 「下一张」固定在底部中间；答对会自动切，按钮 / 空格可以抢先。
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

  /// 数值题的输入框（ADR 0095）：前缀 + 输入框 + 单位，自己敲数字，不给选项。
  Widget _typedInput(BuildContext context, RecallEntry entry, TextStyle? muted) {
    final typed = entry.typed!;
    final color = !_revealed ? null : (_lastCorrect ? Bs.success : Bs.danger);
    const big = TextStyle(fontSize: 22, fontWeight: FontWeight.w600);
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (entry.inputLabel != null) Text(entry.inputLabel!, style: muted),
          const SizedBox(height: 6),
          Row(
            children: [
              if (typed.prefix.isNotEmpty) Text("${typed.prefix} ", style: big),
              SizedBox(
                width: 200,
                child: TextField(
                  key: const ValueKey("recall-typed"),
                  controller: _input,
                  focusNode: _inputFocus,
                  enabled: !_revealed,
                  autofocus: true,
                  style: big.copyWith(color: color),
                  inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r"[0-9.\-–—~～ 至到]"))],
                  onSubmitted: (_) => _submitTyped(),
                  decoration: InputDecoration(
                    isDense: true,
                    border: const OutlineInputBorder(),
                    disabledBorder: OutlineInputBorder(
                      borderSide: BorderSide(color: color ?? Bs.border, width: _revealed ? 2 : 1),
                    ),
                  ),
                ),
              ),
              if (typed.suffix.isNotEmpty) Text(" ${typed.suffix}", style: big),
            ],
          ),
          if (!_revealed) ...[
            const SizedBox(height: 8),
            Text("区间用「-」连接，例如 50-100", style: muted?.copyWith(fontSize: 13)),
            const SizedBox(height: 12),
            Row(
              children: [
                FilledButton(onPressed: _submitTyped, child: const Text("确定（Enter）")),
                const SizedBox(width: 12),
                TextButton(onPressed: _giveUp, child: const Text("不知道")),
              ],
            ),
          ] else if (!_lastCorrect && (_selected ?? "").isNotEmpty) ...[
            const SizedBox(height: 8),
            Text("你填的：$_selected", style: muted),
          ],
        ],
      ),
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
              child: Text("作答之后，这里给出解释。", textAlign: TextAlign.center, style: muted),
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
    final allCorrect = _drawable == 0;
    // 「全部答对」只数自己答过的卡（_correctCount 的口径）。关联真题都掌握也会让抽不出卡，
    // 那不叫「全部答对」，标题和文案要分开说，免得以为都测过了（ADR 0099 之后的实际反馈）。
    final ownAllCorrect = _correctCount == widget.entries.length && widget.entries.isNotEmpty;
    final focus = _focusQuestions();
    final title = ownAllCorrect
        ? "这一页全部答对了"
        : allCorrect
        ? "没有要自动出的卡了"
        : "考完了";
    final String message;
    if (_missedNames.isNotEmpty) {
      message = "答错的：${_missedNames.join("、")}。它们已经进了错题库，下次自测、强化练习会再考；答对的不会再出现。";
    } else if (_round.isEmpty && !ownAllCorrect && allCorrect) {
      message = "没考过的卡，因为关联的真题都已掌握，不再自动出。想自己过一遍，点「再测一遍」。";
    } else if (_round.isEmpty) {
      message = "没有要考的了：没考过的都考过，答错的也都答对到了移出错题库的次数。想再过一遍，点「再测一遍」。";
    } else {
      message = "全都一次答对了，答对的不会再出现。";
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
          Text("这次共 ${_round.length} 张，作答 $_asked 次，答错 $_missed 次。", style: body),
          const SizedBox(height: 6),
        ],
        Text(message, textAlign: TextAlign.center, style: body),
        const SizedBox(height: 18),
        Wrap(
          alignment: WrapAlignment.center,
          spacing: 12,
          runSpacing: 10,
          children: [
            if (allCorrect)
              FilledButton(
                onPressed: _retestAll,
                child: const Text("再测一遍"),
              ),
            if (focus.isNotEmpty)
              FilledButton.tonal(
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

  /// 全部答对后的「再测一遍」（ADR 0099）：绕开档位把整页卡重新考一遍，作答照写——
  /// 这是全对之后唯一的重考入口；平时抽卡仍然只出没答对过的。
  void _retestAll() {
    setState(() {
      _doneThisSession.clear();
      _queue = [...widget.entries]..shuffle();
      _round = [..._queue];
      for (final e in _queue) {
        _makeQuiz(e);
      }
      _missedIds.clear();
      _missedNames.clear();
      _asked = 0;
      _missed = 0;
      _revealed = false;
      _selected = null;
      _done = _queue.isEmpty;
    });
    _focusCurrent();
  }
}
