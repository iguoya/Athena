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
  var _index = 0;
  final _selected = <String>{};
  var _revealed = false;
  var _busy = false;
  DateTime _shownAt = DateTime.now();
  var _hesitant = false;
  final _correct = <int>{};
  Timer? _timer;
  late Duration _left;
  _Result? _result;
  final _speaker = Speaker();

  SessionLaunch get _launch => widget.launch;

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

  Question get _question => _launch.questions[_index];

  @override
  Widget build(BuildContext context) {
    if (_launch.questions.isEmpty) {
      return _EmptyPane(message: "这里还没有题目。", onClose: widget.onClose);
    }
    if (_result != null) {
      return _ResultPane(result: _result!, onClose: widget.onClose);
    }
    final q = _question;
    return CallbackShortcuts(
      bindings: _shortcuts(q),
      child: Focus(
        autofocus: true,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _stageHead(context, q),
            const Divider(height: 1),
            Expanded(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Expanded(flex: 5, child: _promptColumn(context, q)),
                  const VerticalDivider(width: 1),
                  Expanded(flex: 3, child: _evidenceColumn(context, q)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Map<ShortcutActivator, VoidCallback> _shortcuts(Question q) {
    final bindings = <ShortcutActivator, VoidCallback>{
      const SingleActivator(LogicalKeyboardKey.enter): () {
        if (_revealed) _next();
      },
      const SingleActivator(LogicalKeyboardKey.space): () {
        if (_revealed) _next();
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
    for (var i = 0; i < min(q.choices.length, 4); i++) {
      void pick() => _pick(q, q.choices[i].id);
      bindings[SingleActivator(letters[i])] = pick;
      bindings[SingleActivator(digits[i])] = pick;
    }
    for (final choice in q.choices) {
      if (choice.id == "T") {
        bindings[const SingleActivator(LogicalKeyboardKey.keyT)] = () => _pick(q, "T");
      }
      if (choice.id == "F") {
        bindings[const SingleActivator(LogicalKeyboardKey.keyF)] = () => _pick(q, "F");
      }
    }
    return bindings;
  }

  Widget _stageHead(BuildContext context, Question q) {
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.fromLTRB(28, 16, 28, 12),
      child: Row(
        children: [
          Text(_launch.title, style: textTheme.titleMedium),
          const SizedBox(width: 16),
          Text(
            "${_index + 1} / ${_launch.questions.length}",
            style: textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
          if (q.isMulti) ...[
            const SizedBox(width: 16),
            Text("多选", style: textTheme.labelMedium),
          ],
          const Spacer(),
          SizedBox(
            width: 160,
            child: LinearProgressIndicator(
              value: (_index + (_revealed ? 1 : 0)) / _launch.questions.length,
              minHeight: 6,
              borderRadius: BorderRadius.circular(4),
              color: Bs.paper,
              backgroundColor: Bs.border,
            ),
          ),
          const SizedBox(width: 16),
          if (_launch.timed)
            Text(_clock(_left), style: textTheme.titleMedium?.copyWith(fontFeatures: const [FontFeature.tabularFigures()])),
        ],
      ),
    );
  }

  Widget _promptColumn(BuildContext context, Question q) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(28, 20, 24, 28),
      children: [
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
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
        if (q.sign != null) ...[
          SignView(id: q.sign!, size: 180),
          const SizedBox(height: 16),
        ],
        Text(q.prompt, style: Theme.of(context).textTheme.headlineSmall?.copyWith(height: 1.35)),
        const SizedBox(height: 20),
        for (final choice in q.choices) _choiceRow(context, q, choice),
        if (_revealed) ...[
          const SizedBox(height: 16),
          FilledButton(
            onPressed: _next,
            style: FilledButton.styleFrom(backgroundColor: Bs.dark, foregroundColor: Colors.white),
            child: Text(_index + 1 >= _launch.questions.length ? "结束本题" : "下一题"),
          ),
          const SizedBox(height: 8),
          Text(
            "看完或听完解释再点下一题或回车。不会按秒数自动跳。",
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ],
    );
  }

  /// 选项块：选中的那一项整块上色、白字，"我选的是哪个"先于对错跳出来。
  /// 答错时正确项只用淡底描边补位，比我的选择弱一档，免得两块同样抢眼。
  Widget _choiceRow(BuildContext context, Question question, Choice choice) {
    final selected = _selected.contains(choice.id);
    Color? solid;
    Color? tint;
    IconData? mark;
    if (_revealed) {
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
    final fg = solid != null
        ? Colors.white
        : (tint ?? Theme.of(context).colorScheme.onSurface);
    final textTheme = Theme.of(context).textTheme;
    final signId = choice.sign;
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: solid ?? tint?.withValues(alpha: 0.12) ?? Bs.body,
        borderRadius: BorderRadius.circular(Bs.radius),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: _revealed ? _next : () => _pick(question, choice.id),
          child: Container(
            decoration: BoxDecoration(
              border: Border.all(
                color: solid ?? tint ?? Bs.border,
                width: solid != null || tint != null ? 2 : 1,
              ),
              borderRadius: BorderRadius.circular(Bs.radius),
            ),
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 12),
            child: Row(
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
                    child: SignView(id: signId, size: _revealed && choice.ok ? 72 : 64),
                  ),
                  const SizedBox(width: 10),
                ],
                Expanded(
                  child: Text(
                    choice.label,
                    style: textTheme.bodyLarge?.copyWith(
                      color: fg,
                      fontWeight: solid != null ? FontWeight.w600 : null,
                    ),
                  ),
                ),
                if (mark != null) Icon(mark, size: Bs.bodySize, color: fg),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _evidenceColumn(BuildContext context, Question q) {
    final muted = Theme.of(context).textTheme.bodyMedium?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
      height: 1.45,
    );
    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 20, 28, 28),
      children: [
        if (q.sign != null) ...[
          SignView(id: q.sign!, size: 180),
          const SizedBox(height: 24),
        ],
        if (!_revealed)
          Text(
            q.isMulti ? "点齐选项就出对错。" : "点选项就出对错。",
            style: muted,
          )
        else ...[
          BsAlert(
            color: _correct.contains(_index) ? Bs.success : Bs.danger,
            icon: _correct.contains(_index) ? Icons.check_circle : Icons.cancel,
            child: Text(
              _gradeLine(),
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
                      onPressed: _speaker.available ? _speakExplain : null,
                      style: _voiceButtonStyle(Bs.success),
                      child: const Text("系统朗读"),
                    ),
                    FilledButton(
                      onPressed: _speaker.available ? _stopExplain : null,
                      style: _voiceButtonStyle(Bs.secondary),
                      child: const Text("停止朗读"),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Align(
            alignment: Alignment.centerLeft,
            child: FilledButton(
              onPressed: _next,
              style: FilledButton.styleFrom(backgroundColor: Bs.dark, foregroundColor: Colors.white),
              child: Text(_index + 1 >= _launch.questions.length ? "结束本题" : "下一题"),
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
      ],
    );
  }

  String _gradeLine() {
    if (!_correct.contains(_index)) return "答错";
    if (_hesitant) return "答对 · 迟疑";
    return "答对";
  }

  void _pick(Question question, String id) {
    if (_revealed || _busy) return;
    setState(() {
      if (question.isMulti) {
        if (_selected.contains(id)) {
          _selected.remove(id);
        } else {
          _selected.add(id);
        }
      } else {
        _selected
          ..clear()
          ..add(id);
      }
    });
    if (!question.isMulti || _selected.length >= question.correctIds.length) {
      _commit();
    }
  }

  Future<void> _commit() async {
    if (_revealed || _busy || _selected.isEmpty) return;
    _busy = true;
    final ok = answersMatch(_question, _selected);
    if (ok) _correct.add(_index);
    final durationMs = DateTime.now().difference(_shownAt).inMilliseconds;
    final hesitant = lingeredVsPace(durationMs, await widget.store.recentDurations());
    await widget.store.recordAttempt(
      questionId: _question.id,
      topicId: _question.topicId,
      subjectId: _launch.subjectId,
      correct: ok,
      durationMs: durationMs,
      hesitant: hesitant,
    );
    if (!mounted) return;
    if (_launch.revealImmediately) {
      setState(() {
        _hesitant = hesitant;
        _revealed = true;
        _busy = false;
      });
      _speakExplain();
      return;
    }
    _busy = false;
    await _advance();
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

  Future<void> _speakExplain() {
    return _speaker.speak(_question.speakText);
  }

  Future<void> _stopExplain() => _speaker.stop();

  Future<void> _next() async {
    await _speaker.stop();
    await _advance();
  }

  Future<void> _advance() async {
    await _speaker.stop();
    if (_index + 1 >= _launch.questions.length) {
      await _finish();
      return;
    }
    setState(() {
      _index += 1;
      _selected.clear();
      _revealed = false;
      _busy = false;
      _hesitant = false;
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
