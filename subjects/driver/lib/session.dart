import "dart:async";
import "dart:math";

import "package:flutter/material.dart";
import "package:flutter/services.dart";

import "exam.dart";
import "look.dart";
import "models.dart";
import "progress.dart";
import "sign.dart";
import "speak.dart";

class SessionLaunch {
  const SessionLaunch({
    required this.title,
    required this.subjectId,
    required this.questions,
    required this.timed,
    required this.revealImmediately,
    this.minutes,
    this.paper,
    this.draftKey,
    this.resumePicked,
    this.resumeStartedAt,
  });

  final String title;
  final String subjectId;
  final List<Question> questions;
  final bool timed;
  final bool revealImmediately;
  final int? minutes;
  final Paper? paper;

  /// 模拟考草稿在库里的 key；非空才会边答边存、交卷后清掉（ADR 0016）。
  final String? draftKey;

  /// 从草稿续上时，已经选过的答案；不续就是全新一场，留空。
  final Map<int, Set<String>>? resumePicked;

  /// 草稿最初开考的时刻，用来算倒计时还剩多少——不是「续上的时刻」。
  final DateTime? resumeStartedAt;
}

/// 嵌在工作台主区里的做题台：左题右据，不用整页路由。
class SessionStage extends StatefulWidget {
  const SessionStage({
    super.key,
    required this.launch,
    required this.store,
    required this.onClose,
  });

  final SessionLaunch launch;
  final ProgressStore store;
  final VoidCallback onClose;

  @override
  State<SessionStage> createState() => _SessionStageState();
}

class _SessionStageState extends State<SessionStage> {
  /// 一页十题：少了翻页太勤；页面放不下就靠答完自动滚到下一题补上（ADR 0022）。
  static const _groupSize = 10;

  /// 一页全对之后停这么久再翻：让最后一题的绿色先落进眼里，再换页。
  static const _autoAdvanceDelay = Duration(milliseconds: 900);

  var _start = 0;
  final _picked = <int, Set<String>>{};
  final _judged = <int>{};
  final _correct = <int>{};

  /// 右栏依据显示哪一题：作答后自动跟到刚答的题，也可以用题干右侧的「解析」调回来。
  int? _focus;
  var _busy = false;
  var _submitting = false;
  DateTime _shownAt = DateTime.now();
  Timer? _timer;
  late Duration _left;
  late DateTime _examStartedAt;
  _Result? _result;
  final _speaker = Speaker();
  final _scroll = ScrollController();

  /// 每道题块的 key：答完一题要把下一道没答的滚进视野，得先找得到它。
  final _blockKeys = <int, GlobalKey>{};

  SessionLaunch get _launch => widget.launch;

  /// 模拟考按考场走：整卷答完再交卷，中途可以改答案，交卷前不判对错。
  bool get _isExam => !_launch.revealImmediately;

  int get _total => _launch.questions.length;

  int _groupStartContaining(int index) => index ~/ _groupSize * _groupSize;

  int get _end => min(_start + _groupSize, _total);

  Iterable<int> get _group => [for (var i = _start; i < _end; i++) i];

  bool get _lastGroup => _end >= _total;

  bool _answered(int index) => (_picked[index] ?? const <String>{}).isNotEmpty;

  /// 练习里这一组全判过了才翻页；模拟考随时可以翻。
  bool get _groupDone => _isExam ? _group.every(_answered) : _group.every(_judged.contains);

  /// 练习里这一页全判过且全对：没有要回头看的，直接翻（ADR 0022）。
  bool get _groupClean => !_isExam && _groupDone && _group.every(_correct.contains);

  int get _answeredCount => _isExam
      ? [for (var i = 0; i < _total; i++) i].where(_answered).length
      : _judged.length;

  /// 练习里作答即揭晓；模拟考只记选择，对错留到交卷（ADR 0005）。
  bool _revealed(int index) => _launch.revealImmediately && _judged.contains(index);

  /// 多选题要自己点「确认作答」——按选够个数自动判分，等于告诉你这题该选几个。
  bool _awaitingConfirm(int index) {
    if (_isExam || _judged.contains(index)) return false;
    return _launch.questions[index].isMulti && _answered(index);
  }

  @override
  void initState() {
    super.initState();
    _shownAt = DateTime.now();
    _speaker.prepare().then((_) {
      if (mounted) setState(() {});
    });
    final resumePicked = _launch.resumePicked;
    if (resumePicked != null) {
      for (final entry in resumePicked.entries) {
        _picked[entry.key] = {...entry.value};
      }
      // 续上后先跳到第一道还没选的题，不用从头翻。
      final firstUnanswered = [for (var i = 0; i < _total; i++) i].firstWhere((i) => !_answered(i), orElse: () => -1);
      _start = firstUnanswered < 0 ? 0 : _groupStartContaining(firstUnanswered);
    }
    _examStartedAt = _launch.resumeStartedAt ?? DateTime.now();
    if (_launch.timed && _launch.minutes != null) {
      final elapsed = DateTime.now().difference(_examStartedAt);
      _left = Duration(minutes: _launch.minutes!) - elapsed;
      if (_left <= Duration.zero) {
        // 挂起的这段时间已经超时了，回来就直接按超时交卷处理。
        _left = Duration.zero;
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted) _submitExam(auto: true);
        });
      } else {
        _timer = Timer.periodic(const Duration(seconds: 1), (_) {
          if (!mounted) return;
          if (_left.inSeconds <= 1) {
            _timer?.cancel();
            _submitExam(auto: true);
            return;
          }
          setState(() => _left -= const Duration(seconds: 1));
        });
      }
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _speaker.stop();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_launch.questions.isEmpty) {
      return _EmptyPane(message: "这里还没有题目。", onClose: widget.onClose);
    }
    if (_result != null) {
      return _ResultPane(result: _result!, onClose: widget.onClose);
    }
    return CallbackShortcuts(
      bindings: _shortcuts(),
      child: Focus(
        autofocus: true,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _stageHead(context),
            const Divider(height: 1),
            Expanded(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Expanded(flex: 5, child: _leftColumn(context)),
                  const VerticalDivider(width: 1),
                  Expanded(flex: 3, child: _sideColumn(context)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 键盘落在本组第一道还没答的题上；一组答完，回车和空格翻页。
  int? get _pending {
    for (final i in _group) {
      if (_isExam ? !_answered(i) : !_judged.contains(i)) return i;
    }
    return null;
  }

  Map<ShortcutActivator, VoidCallback> _shortcuts() {
    void advance() {
      final index = _pending;
      if (index != null && _awaitingConfirm(index)) {
        _commit(index, _launch.questions[index]);
        return;
      }
      if (_groupDone && !_lastGroup) _nextGroup();
    }

    final bindings = <ShortcutActivator, VoidCallback>{
      const SingleActivator(LogicalKeyboardKey.enter): advance,
      const SingleActivator(LogicalKeyboardKey.space): advance,
      const SingleActivator(LogicalKeyboardKey.arrowRight): () {
        if (!_lastGroup) _nextGroup();
      },
      const SingleActivator(LogicalKeyboardKey.arrowLeft): _prevGroup,
    };
    const letters = [
      LogicalKeyboardKey.keyA,
      LogicalKeyboardKey.keyB,
      LogicalKeyboardKey.keyC,
      LogicalKeyboardKey.keyD,
    ];
    const digits = [
      LogicalKeyboardKey.digit1,
      LogicalKeyboardKey.digit2,
      LogicalKeyboardKey.digit3,
      LogicalKeyboardKey.digit4,
    ];
    void onIndexed(int slot) {
      final index = _pending;
      if (index == null) return;
      final q = _launch.questions[index];
      if (slot >= q.choices.length) return;
      _pick(index, q, q.choices[slot].id);
    }

    for (var i = 0; i < letters.length; i++) {
      bindings[SingleActivator(letters[i])] = () => onIndexed(i);
      bindings[SingleActivator(digits[i])] = () => onIndexed(i);
    }
    void onJudge(String id) {
      final index = _pending;
      if (index == null) return;
      final q = _launch.questions[index];
      if (q.choices.any((choice) => choice.id == id)) _pick(index, q, id);
    }

    bindings[const SingleActivator(LogicalKeyboardKey.keyT)] = () => onJudge("T");
    bindings[const SingleActivator(LogicalKeyboardKey.keyF)] = () => onJudge("F");
    return bindings;
  }

  Widget _stageHead(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.fromLTRB(28, 16, 28, 12),
      child: Row(
        children: [
          IconButton(
            tooltip: "退出，不交卷",
            onPressed: () => _confirmExit(context),
            icon: const Icon(Icons.close),
          ),
          const SizedBox(width: 4),
          Text(_launch.title, style: textTheme.titleMedium),
          const SizedBox(width: 16),
          Text(
            _end - _start == 1 ? "$_end / $_total" : "${_start + 1}–$_end / $_total",
            style: textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
          if (_isExam) ...[
            const SizedBox(width: 16),
            Text("已答 $_answeredCount / $_total", style: textTheme.bodyMedium),
          ],
          const Spacer(),
          SizedBox(
            width: 160,
            child: LinearProgressIndicator(
              value: _total == 0 ? 0 : _answeredCount / _total,
              minHeight: 6,
              borderRadius: BorderRadius.circular(4),
              color: Bs.paper,
              backgroundColor: Bs.border,
            ),
          ),
          const SizedBox(width: 16),
          if (_launch.timed)
            Text(
              _clock(_left),
              style: textTheme.titleMedium?.copyWith(fontFeatures: const [FontFeature.tabularFigures()]),
            ),
        ],
      ),
    );
  }

  /// 左栏：题目占满剩余高度，翻页按钮钉在左栏最下方，不用跟着内容滚下去才够得着。
  Widget _leftColumn(BuildContext context) {
    final pager = _pager(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Expanded(child: _groupColumn(context)),
        if (pager != null) ...[
          const Divider(height: 1),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 10),
            child: pager,
          ),
        ],
      ],
    );
  }

  Widget _groupColumn(BuildContext context) {
    // 底部留出半屏空白：不然本页最后几道题被滚动范围卡住，只能停在屏幕下半截。
    return LayoutBuilder(
      builder: (context, constraints) => ListView(
        controller: _scroll,
        padding: EdgeInsets.fromLTRB(28, 20, 24, max(16, constraints.maxHeight / 2)),
        children: [
          for (final i in _group) ...[
            KeyedSubtree(
              key: _blockKeys.putIfAbsent(i, GlobalKey.new),
              child: _questionBlock(context, i),
            ),
            if (i + 1 < _end)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 12),
                child: Divider(height: 1),
              ),
          ],
        ],
      ),
    );
  }

  Widget _sideColumn(BuildContext context) {
    return _isExam ? _answerCard(context) : _evidenceColumn(context);
  }

  /// 翻页/交卷条：练习组没答完时没有下一步，返回 null 就不占左栏底部的位置。
  /// 全对的一页会自动翻；这个按钮留给有错题、看完解析再走的时候。
  Widget? _pager(BuildContext context) {
    if (_isExam) return _examNav(context);
    if (!_groupDone) return null;
    return FilledButton.icon(
      onPressed: _nextGroup,
      style: FilledButton.styleFrom(
        backgroundColor: Bs.primary,
        foregroundColor: Colors.white,
        minimumSize: const Size(190, 56),
        textStyle: const TextStyle(fontSize: Bs.bodySize, fontWeight: FontWeight.w700),
      ),
      icon: Icon(_lastGroup ? Icons.flag : Icons.arrow_forward, size: 22),
      label: Text(_lastGroup ? "结束本轮" : "下一组"),
    );
  }

  /// 模拟考的翻页条：能回头改答案，所以上一组、下一组都留着。
  Widget _examNav(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Wrap(
          alignment: WrapAlignment.center,
          spacing: 12,
          runSpacing: 12,
          children: [
            OutlinedButton(
              onPressed: _start == 0 ? null : _prevGroup,
              style: OutlinedButton.styleFrom(minimumSize: const Size(120, 48)),
              child: const Text("上一组"),
            ),
            FilledButton.icon(
              onPressed: _lastGroup ? null : _nextGroup,
              style: FilledButton.styleFrom(
                backgroundColor: Bs.primary,
                foregroundColor: Colors.white,
                minimumSize: const Size(130, 48),
              ),
              icon: const Icon(Icons.arrow_forward, size: 20),
              label: const Text("下一组"),
            ),
            FilledButton.icon(
              onPressed: _submitting ? null : () => _confirmSubmit(context),
              style: FilledButton.styleFrom(
                backgroundColor: Bs.success,
                foregroundColor: Colors.white,
                minimumSize: const Size(140, 48),
              ),
              icon: const Icon(Icons.assignment_turned_in, size: 20),
              label: const Text("交卷"),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          "考场规则：交卷前可以回头改答案，交卷后一次性判分。",
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }

  Widget _questionBlock(BuildContext context, int index) {
    final q = _launch.questions[index];
    final canExplain = _revealed(index);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            BsBadge(text: "第${index + 1}题", icon: Icons.tag, color: Bs.paper),
            BsBadge(
              text: Bs.kindLabel(q.kind),
              icon: Bs.kindIcon(q.kind),
              color: Bs.kindColor(q.kind),
            ),
            BsBadge(
              text: QuestionBand.labels[q.band] ?? "常规",
              icon: q.isHot ? Icons.local_fire_department : Icons.route,
              color: Bs.bandColor(q.band),
            ),
            for (final ref in q.sourceRefs)
              if (Bs.isContentSource(ref.relation))
                BsBadge(
                  text: "${Bs.sourceShort(ref.sourceId)} ${ref.locator}".trim(),
                  icon: Icons.menu_book,
                  color: Bs.teal,
                ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: PromptText(
                q.prompt,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(height: 1.35),
              ),
            ),
            const SizedBox(width: 16),
            // 解析按钮只在答完后才能点：答之前点得开，等于把答案摆在题面上。
            // 用 Visibility 占位而不是条件插入——不然按钮一出现，题干可用宽度
            // 跟着变窄，文字重新换行，题块高度跟着抖一下。
            Visibility(
              visible: canExplain,
              maintainSize: true,
              maintainAnimation: true,
              maintainState: true,
              child: OutlinedButton.icon(
                onPressed: canExplain ? () => setState(() => _focus = index) : null,
                icon: const Icon(Icons.menu_book, size: 20),
                label: const Text("解析"),
                style: OutlinedButton.styleFrom(
                  foregroundColor: _focus == index ? Bs.paper : Bs.secondary,
                  side: BorderSide(color: _focus == index ? Bs.paper : Bs.border),
                  minimumSize: const Size(96, 44),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        if (q.image != null) ...[
          QuestionImage(path: q.image!),
          const SizedBox(height: 10),
        ],
        if (q.sign != null) ...[
          SignView(id: q.sign!, size: 160),
          const SizedBox(height: 10),
        ],
        if (q.isMulti && !_judged.contains(index)) ...[
          Text(
            "多选题：选完点「确认作答」。",
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 8),
        ],
        for (final choice in q.choices) _choiceRow(context, index, q, choice),
        if (_awaitingConfirm(index)) ...[
          const SizedBox(height: 4),
          Align(
            alignment: Alignment.centerLeft,
            child: FilledButton(
              onPressed: _busy ? null : () => _commit(index, q),
              style: FilledButton.styleFrom(
                backgroundColor: Bs.paper,
                foregroundColor: Colors.white,
                minimumSize: const Size(160, 48),
              ),
              child: const Text("确认作答"),
            ),
          ),
        ],
      ],
    );
  }

  /// 选项块：选中的那一项整块上色、白字，"我选的是哪个"先于对错跳出来。
  /// 答错时正确项只用淡底描边补位，比我的选择弱一档，免得两块同样抢眼。
  Widget _choiceRow(BuildContext context, int index, Question question, Choice choice) {
    final selected = _picked[index]?.contains(choice.id) ?? false;
    final revealed = _revealed(index);
    Color? solid;
    Color? tint;
    IconData? mark;
    if (revealed) {
      if (selected) {
        solid = choice.ok ? Bs.success : Bs.danger;
        mark = choice.ok ? Icons.check_circle : Icons.cancel;
      } else if (choice.ok) {
        tint = Bs.success;
        mark = Icons.check_circle;
      }
    } else if (selected) {
      // 已选中、还没判定：用主色蓝，跟「答对」的绿、「答错」的红分三档
      solid = Bs.primary;
    }
    final fg = solid != null ? Colors.white : (tint ?? Theme.of(context).colorScheme.onSurface);
    final textTheme = Theme.of(context).textTheme;
    final signId = choice.sign;
    final locked = _judged.contains(index);
    return Padding(
      // 选项间距压缩到 4：一页十题，每题都省一点高度，少滚几下。
      padding: const EdgeInsets.only(bottom: 4),
      child: Align(
        alignment: Alignment.centerLeft,
        // 块宽占栏宽八成：跟题干这一段的长度呼应，又不至于拉成整条。
        child: FractionallySizedBox(
          alignment: Alignment.centerLeft,
          widthFactor: 0.8,
          child: Material(
            color: solid ?? tint?.withValues(alpha: 0.12) ?? Bs.body,
            borderRadius: BorderRadius.circular(Bs.radius),
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: locked ? null : () => _pick(index, question, choice.id),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    SizedBox(
                      width: 32,
                      child: Text(
                        choice.id,
                        style: textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w700,
                          color: fg,
                        ),
                      ),
                    ),
                    if (signId != null) ...[
                      // 标志本来就画在白底上，实色块里给它一块白托才不糊。
                      Container(
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          color: Bs.body,
                          borderRadius: BorderRadius.circular(Bs.radius),
                        ),
                        child: SignView(id: signId, size: revealed && choice.ok ? 72 : 64),
                      ),
                      const SizedBox(width: 10),
                    ],
                    if (choice.image != null) ...[
                      Container(
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          color: Bs.body,
                          borderRadius: BorderRadius.circular(Bs.radius),
                        ),
                        child: QuestionImage(path: choice.image!, maxWidth: 180),
                      ),
                      const SizedBox(width: 10),
                    ],
                    Flexible(
                      child: Text(
                        choice.label,
                        style: textTheme.bodyLarge?.copyWith(
                          color: fg,
                          fontWeight: solid != null ? FontWeight.w600 : null,
                        ),
                      ),
                    ),
                    if (mark != null) ...[
                      const SizedBox(width: 10),
                      Icon(mark, size: Bs.bodySize, color: fg),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  /// 模拟考的答题卡：哪些答了、哪些空着一眼看全，点一下跳到那一组。
  Widget _answerCard(BuildContext context) {
    final muted = Theme.of(context).textTheme.bodyMedium?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
      height: 1.45,
    );
    final unanswered = [for (var i = 0; i < _total; i++) i].where((i) => !_answered(i)).toList();
    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 20, 28, 28),
      children: [
        Text("答题卡", style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 4),
        Text(
          unanswered.isEmpty ? "全部答完了，可以交卷。" : "还剩 ${unanswered.length} 题没答。",
          style: muted,
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: [
            for (var i = 0; i < _total; i++)
              _statCell(context, i, showResult: false),
          ],
        ),
        const SizedBox(height: 16),
        Text(
          "模拟考不显示对错，交卷后一次性判分。时间到了会自动交卷。",
          style: muted,
        ),
      ],
    );
  }

  /// 小方块统计格：练习里分未答/答对/答错三色，模拟考只分答了没答。
  Widget _statCell(BuildContext context, int index, {required bool showResult}) {
    final inGroup = index >= _start && index < _end;
    Color fill;
    Color fg;
    if (showResult) {
      if (!_judged.contains(index)) {
        fill = Bs.body;
        fg = Bs.dark;
      } else if (_correct.contains(index)) {
        fill = Bs.success;
        fg = Colors.white;
      } else {
        fill = Bs.danger;
        fg = Colors.white;
      }
    } else {
      final answered = _answered(index);
      fill = answered ? Bs.paper : Bs.body;
      fg = answered ? Colors.white : Bs.dark;
    }
    return SizedBox(
      width: 30,
      height: 28,
      child: Material(
        color: fill,
        borderRadius: BorderRadius.circular(6),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: () => _jumpTo(index),
          child: Container(
            decoration: BoxDecoration(
              border: Border.all(color: inGroup ? Bs.dark : Bs.border, width: inGroup ? 2 : 1),
              borderRadius: BorderRadius.circular(6),
            ),
            alignment: Alignment.center,
            child: Text(
              "${index + 1}",
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: fg),
            ),
          ),
        ),
      ),
    );
  }

  /// 右栏顶部的统计区：一眼看全组内外哪些题打过、答对答错，点一下跳过去。
  Widget _progressGrid(BuildContext context) {
    final muted = Theme.of(context).textTheme.bodyMedium?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("答题情况", style: Theme.of(context).textTheme.labelLarge),
        const SizedBox(height: 4),
        Text("已答 ${_judged.length} / $_total", style: muted),
        const SizedBox(height: 10),
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: [
            for (var i = 0; i < _total; i++) _statCell(context, i, showResult: true),
          ],
        ),
      ],
    );
  }

  Widget _evidenceColumn(BuildContext context) {
    final muted = Theme.of(context).textTheme.bodyMedium?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
      height: 1.45,
    );
    final focus = _focus;
    if (focus == null || !_revealed(focus)) {
      return ListView(
        padding: const EdgeInsets.fromLTRB(24, 20, 28, 28),
        children: [
          _progressGrid(context),
          const SizedBox(height: 16),
          const Divider(height: 1),
          const SizedBox(height: 16),
          Text(
            "点选项就出对错。答错的题会自动把解释念出来，答完也能点题干右边的「解析」回看。",
            style: muted,
          ),
        ],
      );
    }
    final q = _launch.questions[focus];
    final ok = _correct.contains(focus);
    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 20, 28, 28),
      children: [
        _progressGrid(context),
        const SizedBox(height: 16),
        const Divider(height: 1),
        const SizedBox(height: 16),
        Text("第${focus + 1}题 · 依据", style: Theme.of(context).textTheme.labelLarge),
        const SizedBox(height: 12),
        if (q.sign != null) ...[
          SignView(id: q.sign!, size: 180),
          const SizedBox(height: 24),
        ],
        BsAlert(
          color: ok ? Bs.success : Bs.danger,
          icon: ok ? Icons.check_circle : Icons.cancel,
          child: Text(
            _gradeLine(focus),
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
        ),
        const SizedBox(height: 12),
        // 只留「简短解释」（explain）和「详细解释」（条文原文）两段，不重复：
        // articleLines 和下面的可点条文列表说的是同一件事，只留能点开链接的那份。
        BsAlert(
          color: Bs.paper,
          icon: Icons.volume_up,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (q.explain.trim().isNotEmpty) ...[
                Text("简短解释", style: Theme.of(context).textTheme.labelLarge),
                const SizedBox(height: 6),
                Text(q.explain, style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.5)),
              ],
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  FilledButton(
                    onPressed: _speaker.available ? () => _speak(q) : null,
                    style: _voiceButtonStyle(Bs.success),
                    child: const Text("系统朗读"),
                  ),
                  FilledButton(
                    onPressed: _speaker.available ? _stopSpeaking : null,
                    style: _voiceButtonStyle(Bs.secondary),
                    child: const Text("停止朗读"),
                  ),
                ],
              ),
            ],
          ),
        ),
        if (q.sourceRefs.any((ref) => Bs.isContentSource(ref.relation))) ...[
          const SizedBox(height: 16),
          Text("详细解释", style: Theme.of(context).textTheme.labelLarge),
          const SizedBox(height: 8),
          for (final ref in q.sourceRefs)
            if (Bs.isContentSource(ref.relation))
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                // 纯文字展示，不做成可点的外链——练习中间跳出浏览器太打断节奏。
                child: Text(
                  "${ref.locator.isEmpty ? Bs.sourceShort(ref.sourceId) : ref.locator} · ${ref.note}",
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface,
                    height: 1.4,
                  ),
                ),
              ),
        ],
      ],
    );
  }

  String _gradeLine(int index) => _correct.contains(index) ? "答对" : "答错";

  void _pick(int index, Question question, String id) {
    if (_busy || _judged.contains(index)) return;
    setState(() {
      final chosen = _picked.putIfAbsent(index, () => <String>{});
      if (question.isMulti) {
        if (chosen.contains(id)) {
          chosen.remove(id);
        } else {
          chosen.add(id);
        }
      } else {
        chosen
          ..clear()
          ..add(id);
      }
    });
    // 模拟考边选边存草稿，中途崩了或被重启也能续上（ADR 0016）。
    if (_isExam) unawaited(_saveDraft());
    // 模拟考只记选择；练习里单选和判断点一下就判，多选要自己点「确认作答」。
    if (_isExam || question.isMulti) return;
    _commit(index, question);
  }

  Future<void> _saveDraft() async {
    final draftKey = _launch.draftKey;
    final paper = _launch.paper;
    if (draftKey == null || paper == null) return;
    await widget.store.saveExamDraft(
      ExamDraft(
        subjectId: _launch.subjectId,
        title: _launch.title,
        questionIds: [for (final q in _launch.questions) q.id],
        questionCount: paper.rules.questionCount,
        minutes: paper.rules.minutes,
        passScore: paper.rules.passScore,
        pointsPerQuestion: paper.rules.pointsPerQuestion,
        mix: paper.rules.mix,
        fullBank: paper.fullBank,
        picked: _picked,
        startedAt: _examStartedAt,
      ),
      draftKey: draftKey,
    );
  }

  Future<void> _commit(int index, Question question) async {
    if (_busy || _judged.contains(index)) return;
    final chosen = _picked[index];
    if (chosen == null || chosen.isEmpty) return;
    _busy = true;
    final ok = answersMatch(question, chosen);
    final durationMs = DateTime.now().difference(_shownAt).inMilliseconds;
    final notices = await widget.store.recordAttempt(
      questionId: question.id,
      topicId: question.topicId,
      subjectId: _launch.subjectId,
      correct: ok,
      durationMs: durationMs,
    );
    if (!mounted) return;
    setState(() {
      _judged.add(index);
      if (ok) _correct.add(index);
      // 下一题的用时从这一题判定的那一刻算起。
      _shownAt = DateTime.now();
      _focus = index;
      _busy = false;
    });
    _announce(notices);
    if (_groupClean) {
      _autoAdvance();
      return;
    }
    final next = _pending;
    if (next != null) _centerOn(next);
    // 答错才念：答对还要听完一段解释，反而拖住手上的节奏。
    if (!ok) await _speak(question);
  }

  /// 一页十题一屏放不下：把要答的那道题滚到屏幕正中，视线不用往下找，也不用自己拿滚轮翻。
  /// 页首几道题滚不到中间（上面没有内容可让），就停在原位，那本来就在眼前。
  void _centerOn(int index, {bool animate = true}) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final target = _blockKeys[index]?.currentContext;
      if (!mounted || target == null) return;
      Scrollable.ensureVisible(
        target,
        alignment: 0.5,
        duration: animate ? const Duration(milliseconds: 300) : Duration.zero,
        curve: Curves.easeOut,
      );
    });
  }

  /// 全对的一页停一下再翻；这期间人已经自己翻走了（点按钮、回车、方向键）就不再翻第二次。
  void _autoAdvance() {
    final start = _start;
    Future.delayed(_autoAdvanceDelay, () {
      if (!mounted || _start != start || _result != null) return;
      _nextGroup();
    });
  }

  /// 新解锁的成就/里程碑弹一条提示条——记了不给人看，等于没记（主仓库 ADR 0052）。
  void _announce(List<Notice> notices) {
    if (!mounted || notices.isEmpty) return;
    final messenger = ScaffoldMessenger.of(context);
    for (final notice in notices) {
      messenger.showSnackBar(
        SnackBar(
          content: Text("${notice.title} · ${notice.body}"),
          backgroundColor: Bs.success,
          duration: const Duration(seconds: 3),
        ),
      );
    }
  }

  ButtonStyle _voiceButtonStyle(Color color) {
    return FilledButton.styleFrom(
      backgroundColor: color,
      foregroundColor: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
      minimumSize: const Size(128, 48),
      maximumSize: const Size(160, 48),
      textStyle: const TextStyle(fontSize: Bs.bodySize, fontWeight: FontWeight.w600),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Bs.radius)),
    );
  }

  Future<void> _speak(Question question) => _speaker.speak(question.speakText);

  Future<void> _stopSpeaking() => _speaker.stop();

  void _jumpTo(int index) {
    final start = _groupStartContaining(index);
    if (start == _start) {
      _centerOn(index);
      return;
    }
    setState(() {
      _start = start;
      _focus = null;
      _shownAt = DateTime.now();
    });
    _scrollToTop(center: index);
  }

  void _prevGroup() {
    if (_start == 0) return;
    setState(() {
      _start = _groupStartContaining(_start - 1);
      _focus = null;
      _shownAt = DateTime.now();
    });
    _scrollToTop();
  }

  Future<void> _nextGroup() async {
    await _speaker.stop();
    if (_lastGroup) {
      if (_isExam) return;
      await _finishPractice();
      return;
    }
    if (!mounted) return;
    setState(() {
      _start = _end;
      _focus = null;
      _busy = false;
      _shownAt = DateTime.now();
    });
    _scrollToTop();
  }

  /// 换页后 ListView 复用同一个控制器，滚动位置会留在上一页的底部，要手动拉回页首；
  /// 本页有答过的题（跳页、回看）就直接把第一道没答的摆到中间。
  void _scrollToTop({int? center}) {
    if (_scroll.hasClients) _scroll.jumpTo(0);
    final target = center ?? _pending;
    if (target != null) _centerOn(target, animate: false);
  }

  /// 退出不等于交卷：练习本来就逐题落盘，退出不丢东西，不用问；模拟考/章节测试
  /// 退出只是把草稿留着（ADR 0016），没提交、没判分、不算完成一次测试，说清楚
  /// 再退，免得以为「退出」等于「交了」。
  Future<void> _confirmExit(BuildContext context) async {
    if (!_isExam) {
      widget.onClose();
      return;
    }
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text("退出测试"),
        content: const Text(
          "退出不会交卷、不会判分，答案会存成草稿，下次进来可以选择续上。确定现在退出吗？",
          style: TextStyle(fontSize: Bs.bodySize, height: 1.45),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(dialogContext).pop(false), child: const Text("继续测试")),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            style: FilledButton.styleFrom(backgroundColor: Bs.danger, foregroundColor: Colors.white),
            child: const Text("退出"),
          ),
        ],
      ),
    );
    if (ok == true) widget.onClose();
  }

  Future<void> _confirmSubmit(BuildContext context) async {
    final left = _total - _answeredCount;
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text("交卷"),
        content: Text(
          left == 0
              ? "$_total 题都答完了，交卷后一次性判分。"
              : "还有 $left 题没答，没答的按答错计。确定交卷吗？",
          style: const TextStyle(fontSize: Bs.bodySize, height: 1.45),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(dialogContext).pop(false), child: const Text("再检查一下")),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            style: FilledButton.styleFrom(backgroundColor: Bs.success, foregroundColor: Colors.white),
            child: const Text("确定交卷"),
          ),
        ],
      ),
    );
    if (ok == true) await _submitExam();
  }

  /// 交卷：整卷一次判分、一次入库，跟考场一样。
  Future<void> _submitExam({bool auto = false}) async {
    if (_submitting) return;
    _submitting = true;
    _timer?.cancel();
    await _speaker.stop();
    final notices = <Notice>[];
    for (var i = 0; i < _total; i++) {
      final question = _launch.questions[i];
      final chosen = _picked[i] ?? const <String>{};
      final ok = chosen.isNotEmpty && answersMatch(question, chosen);
      if (ok) _correct.add(i);
      _judged.add(i);
      notices.addAll(await widget.store.recordAttempt(
        questionId: question.id,
        topicId: question.topicId,
        subjectId: _launch.subjectId,
        correct: ok,
        durationMs: 0,
      ));
    }
    // 交了卷草稿就没用了；没交就留着，回到首页还能续上。
    final draftKey = _launch.draftKey;
    if (draftKey != null) await widget.store.clearExamDraft(draftKey);
    // 模拟考中途弹提示条会被结果页立刻盖掉，攒起来一起显示在结果页上。
    await _finish(autoSubmitted: auto, notices: notices);
  }

  Future<void> _finishPractice() async {
    _timer?.cancel();
    await _speaker.stop();
    await _finish();
  }

  Future<void> _finish({bool autoSubmitted = false, List<Notice> notices = const []}) async {
    final correct = _correct.length;
    final score = _launch.paper?.scaledScore(correct) ??
        (_total == 0 ? 0 : ((correct / _total) * 100).round());
    final passed = score >= (_launch.paper?.rules.passScore ?? 90);
    final allNotices = [...notices];
    if (_launch.timed) {
      allNotices.addAll(await widget.store.recordExam(
        subjectId: _launch.subjectId,
        score: score,
        passed: passed,
      ));
    }
    final missed = <_Missed>[
      for (var i = 0; i < _total; i++)
        if (_judged.contains(i) && !_correct.contains(i))
          _Missed(
            number: i + 1,
            question: _launch.questions[i],
            picked: {...?_picked[i]},
          ),
    ];
    if (!mounted) return;
    setState(() {
      _result = _Result(
        title: _launch.title,
        correct: correct,
        total: _total,
        score: score,
        passed: passed,
        timed: _launch.timed,
        fullBank: _launch.paper?.fullBank ?? true,
        want: _launch.paper?.rules.questionCount,
        autoSubmitted: autoSubmitted,
        missed: missed,
        notices: allNotices,
      );
    });
  }

  String _clock(Duration value) {
    final m = value.inMinutes.remainder(60).toString().padLeft(2, "0");
    final s = value.inSeconds.remainder(60).toString().padLeft(2, "0");
    return "$m:$s";
  }
}

class _Result {
  const _Result({
    required this.title,
    required this.correct,
    required this.total,
    required this.score,
    required this.passed,
    required this.timed,
    required this.fullBank,
    this.want,
    this.autoSubmitted = false,
    this.missed = const [],
    this.notices = const [],
  });

  final String title;
  final int correct;
  final int total;
  final int score;
  final bool passed;
  final bool timed;
  final bool fullBank;
  final int? want;

  /// 时间到了系统替你交的卷——结果页要说一声，不然会以为是自己点的。
  final bool autoSubmitted;

  /// 交卷这一路（含 recordExam 自己产的那条）新解锁的成就——中途弹的提示条
  /// 会被结果页立刻盖掉，攒到这里跟结果一起看。
  final List<Notice> notices;

  /// 这一卷答错的题：交卷后最该看的就是它们。
  final List<_Missed> missed;
}

/// 一道答错的题，连同「我当时选的」——只报分不告诉错在哪，等于白考一次。
class _Missed {
  const _Missed({required this.number, required this.question, required this.picked});

  final int number;
  final Question question;
  final Set<String> picked;

  String labelsOf(Set<String> ids) {
    final labels = [
      for (final choice in question.choices)
        if (ids.contains(choice.id)) "${choice.id}. ${choice.label}",
    ];
    return labels.isEmpty ? "（没作答）" : labels.join("；");
  }
}

class _ResultPane extends StatelessWidget {
  const _ResultPane({required this.result, required this.onClose});

  final _Result result;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    final headline = result.timed ? (result.passed ? "及格" : "未及格") : "本轮结束";
    return Padding(
      padding: const EdgeInsets.fromLTRB(36, 32, 36, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(result.title, style: Theme.of(context).textTheme.labelLarge),
          const SizedBox(height: 12),
          Text(headline, style: Theme.of(context).textTheme.displaySmall),
          const SizedBox(height: 12),
          Text(
            "答对 ${result.correct} / ${result.total}，折合 ${result.score} 分",
            style: Theme.of(context).textTheme.titleMedium,
          ),
          if (result.autoSubmitted) ...[
            const SizedBox(height: 12),
            Text(
              "时间到，已自动交卷。",
              style: Theme.of(context).textTheme.titleMedium?.copyWith(color: Bs.danger),
            ),
          ],
          if (result.timed && !result.fullBank && result.want != null) ...[
            const SizedBox(height: 12),
            Text(
              "本题库还少于考场的 ${result.want} 题，按现有题目折合百分制，90 分及格。",
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
          if (result.notices.isNotEmpty) ...[
            const SizedBox(height: 16),
            BsAlert(
              color: Bs.success,
              icon: Icons.military_tech,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  for (final notice in result.notices)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Text("${notice.title} · ${notice.body}"),
                    ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 20),
          FilledButton(onPressed: onClose, child: const Text("回到章节")),
          if (result.missed.isNotEmpty) ...[
            const SizedBox(height: 24),
            Text(
              "错了 ${result.missed.length} 题，趁热看一遍：",
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            Expanded(
              child: ListView.separated(
                itemCount: result.missed.length,
                separatorBuilder: (_, _) => const SizedBox(height: 12),
                itemBuilder: (context, i) => _MissedCard(item: result.missed[i]),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// 错题卡：题干、我选了什么、正确答案是什么，再跟一段条文。
class _MissedCard extends StatelessWidget {
  const _MissedCard({required this.item});

  final _Missed item;

  @override
  Widget build(BuildContext context) {
    final q = item.question;
    final right = {for (final c in q.choices) if (c.ok) c.id};
    final muted = Theme.of(context).textTheme.bodyMedium?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
      height: 1.45,
    );
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      decoration: BoxDecoration(
        color: Bs.body,
        border: Border.all(color: Bs.border),
        borderRadius: BorderRadius.circular(Bs.radius),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              BsBadge(text: "第${item.number}题", icon: Icons.tag, color: Bs.danger),
              const SizedBox(width: 10),
              Expanded(
                child: PromptText(
                  q.prompt,
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.4),
                ),
              ),
            ],
          ),
          if (q.image != null) ...[
            const SizedBox(height: 10),
            QuestionImage(path: q.image!, maxWidth: 360),
          ],
          const SizedBox(height: 10),
          Text("你选的：${item.labelsOf(item.picked)}", style: muted?.copyWith(color: Bs.danger)),
          Text("正确答案：${item.labelsOf(right)}", style: muted?.copyWith(color: Bs.success)),
          if (q.explain.trim().isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(q.explain, style: muted),
          ],
          if (q.articleLines.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(q.articleLines.join("\n"), style: muted),
          ],
        ],
      ),
    );
  }
}

class _EmptyPane extends StatelessWidget {
  const _EmptyPane({required this.message, required this.onClose});

  final String message;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(36, 32, 36, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(message, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 20),
          TextButton(onPressed: onClose, child: const Text("返回")),
        ],
      ),
    );
  }
}
