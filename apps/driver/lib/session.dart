import "dart:async";

import "package:flutter/material.dart";
import "package:url_launcher/url_launcher.dart";

import "exam.dart";
import "models.dart";
import "progress.dart";
import "sign.dart";

class SessionPage extends StatefulWidget {
  const SessionPage({
    super.key,
    required this.title,
    required this.subjectId,
    required this.questions,
    required this.store,
    required this.timed,
    required this.revealImmediately,
    this.minutes,
    this.paper,
  });

  final String title;
  final String subjectId;
  final List<Question> questions;
  final ProgressStore store;
  final bool timed;
  final bool revealImmediately;
  final int? minutes;
  final Paper? paper;

  @override
  State<SessionPage> createState() => _SessionPageState();
}

class _SessionPageState extends State<SessionPage> {
  var _index = 0;
  final _selected = <String>{};
  var _revealed = false;
  final _correct = <int>{};
  Timer? _timer;
  late Duration _left;

  @override
  void initState() {
    super.initState();
    if (widget.timed && widget.minutes != null) {
      _left = Duration(minutes: widget.minutes!);
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
    super.dispose();
  }

  Question get _question => widget.questions[_index];

  @override
  Widget build(BuildContext context) {
    if (widget.questions.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: Text(widget.title)),
        body: const Center(child: Text("这里还没有题目。")),
      );
    }
    final q = _question;
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
        actions: [
          if (widget.timed)
            Center(
              child: Padding(
                padding: const EdgeInsets.only(right: 16),
                child: Text(_clock(_left), style: Theme.of(context).textTheme.titleMedium),
              ),
            ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
        children: [
          Text("第 ${_index + 1} / ${widget.questions.length} 题"),
          const SizedBox(height: 12),
          if (q.sign != null) Center(child: SignView(id: q.sign!, size: 140)),
          const SizedBox(height: 12),
          Text(q.prompt, style: Theme.of(context).textTheme.titleLarge),
          if (q.isMulti)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text("多选题，选齐再确认。", style: Theme.of(context).textTheme.bodySmall),
            ),
          const SizedBox(height: 16),
          for (final choice in q.choices) _choiceTile(q, choice),
          const SizedBox(height: 16),
          if (!_revealed)
            FilledButton(
              onPressed: _selected.isEmpty ? null : _confirm,
              child: const Text("确认"),
            )
          else ...[
            Text(q.explain, style: Theme.of(context).textTheme.bodyLarge),
            const SizedBox(height: 8),
            for (final ref in q.sourceRefs)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: InkWell(
                  onTap: ref.url.isEmpty ? null : () => launchUrl(Uri.parse(ref.url)),
                  child: Text(
                    "${ref.locator} · ${ref.note}",
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.primary,
                      decoration: TextDecoration.underline,
                    ),
                  ),
                ),
              ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _next,
              child: Text(_index + 1 >= widget.questions.length ? "结束" : "下一题"),
            ),
          ],
        ],
      ),
    );
  }

  Widget _choiceTile(Question question, Choice choice) {
    final selected = _selected.contains(choice.id);
    Color? color;
    if (_revealed) {
      if (choice.ok) color = Colors.green.shade50;
      if (selected && !choice.ok) color = Colors.red.shade50;
    }
    return Card(
      color: color,
      child: ListTile(
        leading: Icon(
          question.isMulti
              ? (selected ? Icons.check_box : Icons.check_box_outline_blank)
              : (selected ? Icons.radio_button_checked : Icons.radio_button_off),
        ),
        title: Text("${choice.id}. ${choice.label}"),
        onTap: _revealed
            ? null
            : () {
                setState(() {
                  if (question.isMulti) {
                    if (selected) {
                      _selected.remove(choice.id);
                    } else {
                      _selected.add(choice.id);
                    }
                  } else {
                    _selected
                      ..clear()
                      ..add(choice.id);
                  }
                });
              },
      ),
    );
  }

  Future<void> _confirm() async {
    final ok = answersMatch(_question, _selected);
    if (ok) _correct.add(_index);
    await widget.store.recordAttempt(
      questionId: _question.id,
      topicId: _question.topicId,
      subjectId: widget.subjectId,
      correct: ok,
    );
    if (widget.revealImmediately) {
      setState(() => _revealed = true);
      return;
    }
    await _advance();
  }

  Future<void> _next() => _advance();

  Future<void> _advance() async {
    if (_index + 1 >= widget.questions.length) {
      await _finish();
      return;
    }
    setState(() {
      _index += 1;
      _selected.clear();
      _revealed = false;
    });
  }

  Future<void> _finish() async {
    _timer?.cancel();
    final correct = _correct.length;
    final score = widget.paper?.scaledScore(correct) ??
        (widget.questions.isEmpty ? 0 : ((correct / widget.questions.length) * 100).round());
    final passed = score >= (widget.paper?.rules.passScore ?? 90);
    if (widget.timed) {
      await widget.store.recordExam(
        subjectId: widget.subjectId,
        score: score,
        passed: passed,
      );
    }
    if (!mounted) return;
    await Navigator.of(context).pushReplacement(
      MaterialPageRoute<void>(
        builder: (context) => ResultPage(
          title: widget.title,
          correct: correct,
          total: widget.questions.length,
          score: score,
          passed: passed,
          timed: widget.timed,
          fullBank: widget.paper?.fullBank ?? true,
          want: widget.paper?.rules.questionCount,
        ),
      ),
    );
  }

  String _clock(Duration value) {
    final m = value.inMinutes.remainder(60).toString().padLeft(2, "0");
    final s = value.inSeconds.remainder(60).toString().padLeft(2, "0");
    return "$m:$s";
  }
}

class ResultPage extends StatelessWidget {
  const ResultPage({
    super.key,
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  timed ? (passed ? "及格" : "未及格") : "本轮结束",
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 12),
                Text("答对 $correct / $total，折合 $score 分"),
                if (timed && !fullBank && want != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    "本题库还少于考场的 $want 题，按现有题目折合百分制，90 分及格。",
                    textAlign: TextAlign.center,
                  ),
                ],
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text("返回"),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
