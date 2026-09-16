import "dart:async";
import "dart:math";

import "package:flutter/material.dart";
import "package:flutter/services.dart";
import "package:url_launcher/url_launcher.dart";

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
  });

  final String title;
  final String subjectId;
  final List<Question> questions;
  final bool timed;
  final bool revealImmediately;
  final int? minutes;
  final Paper? paper;
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
  /// 一组四题：答完一题就停下来点一次「下一题」太碎，改成一页做完四题再翻页。
  static const _groupSize = 4;

  var _start = 0;
  final _picked = <int, Set<String>>{};
  final _judged = <int>{};
  final _correct = <int>{};
  final _hesitant = <int>{};
  /// 右栏依据显示哪一题：作答后自动跟到刚答的题，也可以用题干右侧的「解析」调回来。
  int? _focus;
  var _busy = false;
  DateTime _shownAt = DateTime.now();
  Timer? _timer;
  late Duration _left;
  _Result? _result;
  final _speaker = Speaker();

  SessionLaunch get _launch => widget.launch;

  int get _end => min(_start + _groupSize, _launch.questions.length);

  Iterable<int> get _group => [for (var i = _start; i < _end; i++) i];

  bool get _groupDone => _group.every(_judged.contains);

  bool get _lastGroup => _end >= _launch.questions.length;

  /// 练习里作答即揭晓；模拟考只记选择，对错留到交卷（ADR 0005）。
  bool _revealed(int index) => _launch.revealImmediately && _judged.contains(index);

  @override
  void initState() {
    super.initState();
    _shownAt = DateTime.now();
    _speaker.prepare().then((_) {
      if (mounted) setState(() {});
    });
    if (_launch.timed && _launch.minutes != null) {
      _left = Duration(minutes: _launch.minutes!);
      _timer = Timer.periodic(const Duration(seconds: 1), (_) {
        if (!mounted) return;
        if (_left.inSeconds <= 1) {
          _timer?.cancel();
          _finish();
          return;
        }
        setState(() => _left -= const Duration(seconds: 1));
      });
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _speaker.stop();
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
                  Expanded(flex: 5, child: _groupColumn(context)),
                  const VerticalDivider(width: 1),
                  Expanded(flex: 3, child: _evidenceColumn(context)),
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
      if (!_judged.contains(i)) return i;
    }
    return null;
  }

  Map<ShortcutActivator, VoidCallback> _shortcuts() {
    final bindings = <ShortcutActivator, VoidCallback>{
      const SingleActivator(LogicalKeyboardKey.enter): () {
        if (_groupDone) _nextGroup();
      },
      const SingleActivator(LogicalKeyboardKey.space): () {
        if (_groupDone) _nextGroup();
      },
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
    final total = _launch.questions.length;
    return Padding(
      padding: const EdgeInsets.fromLTRB(28, 16, 28, 12),
      child: Row(
        children: [
          Text(_launch.title, style: textTheme.titleMedium),
          const SizedBox(width: 16),
          Text(
            _end - _start == 1 ? "$_end / $total" : "${_start + 1}–$_end / $total",
            style: textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
          const Spacer(),
          SizedBox(
            width: 160,
            child: LinearProgressIndicator(
              value: _judged.length / total,
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

  Widget _groupColumn(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(28, 20, 24, 28),
      children: [
        for (final i in _group) ...[
          _questionBlock(context, i),
          if (i + 1 < _end) const Padding(
            padding: EdgeInsets.symmetric(vertical: 20),
            child: Divider(height: 1),
          ),
        ],
        const SizedBox(height: 24),
        if (_groupDone) ...[
          Center(
            child: FilledButton(
              onPressed: _nextGroup,
              style: FilledButton.styleFrom(
                backgroundColor: Bs.dark,
                foregroundColor: Colors.white,
                minimumSize: const Size(160, 48),
              ),
              child: Text(_lastGroup ? "结束本轮" : "下一组"),
            ),
          ),
          const SizedBox(height: 8),
          Center(
            child: Text(
              _launch.revealImmediately
                  ? "答错的题会自动朗读解释。看完再点下一组或回车。"
                  : "这一组答完了。点下一组或回车继续。",
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ),
        ],
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
            BsBadge(text: "第${index + 1}题", icon: Icons.tag, color: Bs.dark),
            BsBadge(
              text: Bs.kindLabel(q.kind),
              icon: Bs.kindIcon(q.kind),
              color: q.isMulti ? Bs.warning : (q.kind == "judge" ? Bs.secondary : Bs.dark),
            ),
            BsBadge(
              text: QuestionBand.labels[q.band] ?? "常规",
              icon: q.isHot ? Icons.local_fire_department : Icons.route,
              color: q.isHot ? Bs.danger : (q.isCommon ? Bs.warning : Bs.secondary),
            ),
            for (final ref in q.sourceRefs)
              BsBadge(
                text: "${Bs.sourceShort(ref.sourceId)} ${ref.locator}",
                icon: Icons.menu_book,
                color: Bs.secondary,
              ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Text(
                q.prompt,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(height: 1.35),
              ),
            ),
            // 解析按钮只在答完后出现：答之前点得开，等于把答案摆在题面上。
            if (canExplain) ...[
              const SizedBox(width: 16),
              OutlinedButton.icon(
                onPressed: () => setState(() => _focus = index),
                icon: const Icon(Icons.menu_book, size: 20),
                label: const Text("解析"),
                style: OutlinedButton.styleFrom(
                  foregroundColor: _focus == index ? Bs.paper : Bs.secondary,
                  side: BorderSide(color: _focus == index ? Bs.paper : Bs.border),
                  minimumSize: const Size(96, 44),
                ),
              ),
            ],
          ],
        ),
        const SizedBox(height: 16),
        if (q.sign != null) ...[
          SignView(id: q.sign!, size: 160),
          const SizedBox(height: 16),
        ],
        for (final choice in q.choices) _choiceRow(context, index, q, choice),
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
      solid = Bs.paper;
    }
    final fg = solid != null ? Colors.white : (tint ?? Theme.of(context).colorScheme.onSurface);
    final textTheme = Theme.of(context).textTheme;
    final signId = choice.sign;
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Align(
        alignment: Alignment.centerLeft,
        // 块宽占栏宽三分之二：跟题干这一段的长度呼应，又不至于拉成整条。
        child: FractionallySizedBox(
          alignment: Alignment.centerLeft,
          widthFactor: 2 / 3,
          child: Material(
            color: solid ?? tint?.withValues(alpha: 0.12) ?? Bs.body,
            borderRadius: BorderRadius.circular(Bs.radius),
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: _judged.contains(index) ? null : () => _pick(index, question, choice.id),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(12, 12, 12, 12),
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
          Text(
            _launch.revealImmediately
                ? "点选项就出对错。答错的题会自动把解释念出来，答完也能点题干右边的「解析」回看。"
                : "模拟考不显示对错，这一组答完点下一组。",
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
        BsAlert(
          color: Bs.paper,
          icon: Icons.volume_up,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (q.explain.trim().isNotEmpty)
                Text(q.explain, style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.5)),
              if (q.explain.trim().isNotEmpty && q.articleLines.isNotEmpty) const SizedBox(height: 10),
              if (q.articleLines.isNotEmpty)
                Text(
                  q.articleLines.join("\n"),
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.5),
                ),
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
        const SizedBox(height: 16),
        for (final ref in q.sourceRefs)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: InkWell(
              onTap: ref.url.isEmpty ? null : () => launchUrl(Uri.parse(ref.url)),
              child: Text(
                "${ref.locator} · ${ref.note}",
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Bs.paper,
                  height: 1.4,
                ),
              ),
            ),
          ),
      ],
    );
  }

  String _gradeLine(int index) {
    if (!_correct.contains(index)) return "答错";
    if (_hesitant.contains(index)) return "答对 · 迟疑";
    return "答对";
  }

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
    final chosen = _picked[index] ?? const <String>{};
    if (!question.isMulti || chosen.length >= question.correctIds.length) {
      _commit(index, question);
    }
  }

  Future<void> _commit(int index, Question question) async {
    if (_busy || _judged.contains(index)) return;
    final chosen = _picked[index];
    if (chosen == null || chosen.isEmpty) return;
    _busy = true;
    final ok = answersMatch(question, chosen);
    final durationMs = DateTime.now().difference(_shownAt).inMilliseconds;
    final hesitant = lingeredVsPace(durationMs, await widget.store.recentDurations());
    await widget.store.recordAttempt(
      questionId: question.id,
      topicId: question.topicId,
      subjectId: _launch.subjectId,
      correct: ok,
      durationMs: durationMs,
      hesitant: hesitant,
    );
    if (!mounted) return;
    setState(() {
      _judged.add(index);
      if (ok) _correct.add(index);
      if (hesitant) _hesitant.add(index);
      // 下一题的用时从这一题判定的那一刻算起。
      _shownAt = DateTime.now();
      if (_launch.revealImmediately) _focus = index;
      _busy = false;
    });
    // 答错才念：答对还要听完一段解释，反而拖住手上的节奏。
    if (_launch.revealImmediately && !ok) await _speak(question);
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

  Future<void> _nextGroup() async {
    await _speaker.stop();
    if (_lastGroup) {
      await _finish();
      return;
    }
    if (!mounted) return;
    setState(() {
      _start = _end;
      _focus = null;
      _busy = false;
      _shownAt = DateTime.now();
    });
  }

  Future<void> _finish() async {
    _timer?.cancel();
    await _speaker.stop();
    final correct = _correct.length;
    final score = _launch.paper?.scaledScore(correct) ??
        (_launch.questions.isEmpty ? 0 : ((correct / _launch.questions.length) * 100).round());
    final passed = score >= (_launch.paper?.rules.passScore ?? 90);
    if (_launch.timed) {
      await widget.store.recordExam(
        subjectId: _launch.subjectId,
        score: score,
        passed: passed,
      );
    }
    if (!mounted) return;
    setState(() {
      _result = _Result(
        title: _launch.title,
        correct: correct,
        total: _launch.questions.length,
        score: score,
        passed: passed,
        timed: _launch.timed,
        fullBank: _launch.paper?.fullBank ?? true,
        want: _launch.paper?.rules.questionCount,
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
  });

  final String title;
  final int correct;
  final int total;
  final int score;
  final bool passed;
  final bool timed;
  final bool fullBank;
  final int? want;
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
          if (result.timed && !result.fullBank && result.want != null) ...[
            const SizedBox(height: 12),
            Text(
              "本题库还少于考场的 ${result.want} 题，按现有题目折合百分制，90 分及格。",
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
          const SizedBox(height: 28),
          FilledButton(onPressed: onClose, child: const Text("回到章节")),
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
