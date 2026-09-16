import "dart:math";

import "package:flutter/material.dart";

import "exam.dart";
import "look.dart";
import "models.dart";
import "progress.dart";
import "session.dart";

class HomePage extends StatefulWidget {
  const HomePage({super.key, required this.bank, required this.store});

  final Bank bank;
  final ProgressStore store;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  static const _wrongId = "wrong";

  String _place = "subject1";
  SessionLaunch? _session;
  Set<String> _mastered = {};
  Map<String, int> _attempts = {};
  int _avgMs = 0;
  int _wrongCount = 0;
  List<Question> _wrongQuestions = const [];
  Map<String, int> _wrongCounts = const {};
  List<ExamRecord> _exams = const [];

  Set<String> get _wrongIds => {for (final q in _wrongQuestions) q.id};

  List<Question> get _subject1All => widget.bank.forSubject("subject1");

  int get _s1Open => unlockedThrough(_subject1All, _mastered);

  bool get _s1Done => allMastered(_subject1All, _mastered);

  bool _keepInPractice(Question q) {
    return q.appearsInPractice(
      mastered: _mastered.contains(q.id),
      wrong: _wrongIds.contains(q.id),
      attempts: _attempts[q.id] ?? 0,
    );
  }

  List<Question> _pending(List<Question> questions) {
    return [for (final q in questions) if (_keepInPractice(q)) q];
  }

  List<Question> _practiceQueue(List<Question> questions) {
    final pending = _pending(questions);
    final wrong = [for (final q in pending) if (_wrongIds.contains(q.id)) q];
    final hot = [for (final q in pending) if (!_wrongIds.contains(q.id) && q.isHot) q];
    final common = [for (final q in pending) if (!_wrongIds.contains(q.id) && q.isCommon) q];
    final regular = [for (final q in pending) if (!_wrongIds.contains(q.id) && q.isRegular) q];
    return [...wrong, ...hot, ...common, ...regular, ...wrong, ...hot];
  }

  List<Question> _openPool(Subject subject) {
    final raw = subject.id == "subject1" ? widget.bank.unlocked("subject1", _s1Open) : widget.bank.forSubject(subject.id);
    return dailyQuestions(raw);
  }

  List<Question> _openTopic(Subject subject, Topic topic) {
    final questions = widget.bank.forTopic(topic.id);
    return dailyQuestions([for (final q in questions) if (subject.id != "subject1" || q.phase <= _s1Open) q]);
  }

  @override
  void initState() {
    super.initState();
    _reload();
  }

  Future<void> _reload() async {
    final mastered = await widget.store.masteredQuestionIds();
    final attempts = await widget.store.attemptCounts();
    final avgMs = await widget.store.averageDurationMs();
    final ids = await widget.store.wrongQuestionIds();
    final wrongCounts = await widget.store.wrongCounts();
    final exams = await widget.store.recentExams();
    final s1Done = allMastered(widget.bank.forSubject("subject1"), mastered);
    final wrong = [
      for (final id in ids)
        if (widget.bank.questions.any((q) => q.id == id)) widget.bank.byId(id),
    ];
    if (!s1Done) {
      wrong.removeWhere((q) => q.topicId.startsWith("drive.s4."));
    }
    // 错得越多的排越前：考前该先啃反复栽跟头的那几道。
    wrong.sort((a, b) => (wrongCounts[b.id] ?? 0).compareTo(wrongCounts[a.id] ?? 0));
    if (!mounted) return;
    setState(() {
      _mastered = mastered;
      _attempts = attempts;
      _avgMs = avgMs;
      _wrongCount = wrong.length;
      _wrongQuestions = wrong;
      _wrongCounts = wrongCounts;
      _exams = exams;
    });
  }

  Subject? get _subject {
    if (_place == _wrongId) return null;
    return widget.bank.curriculum.subject(_place);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          SizedBox(width: 272, child: _sidebar(context)),
          const VerticalDivider(width: 1, color: Bs.border),
          Expanded(child: _session == null ? _overview(context) : _sessionPane()),
        ],
      ),
    );
  }

  Widget _sidebar(BuildContext context) {
    final current = _subject;
    final open = current != null && (current.id != "subject4" || _s1Done);
    final phase = current?.id == "subject1" ? current!.phaseById(_s1Open) : null;
    return ColoredBox(
      color: Bs.nav,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 20, 12, 24),
        children: [
          const Row(
            children: [
              Icon(Icons.directions_car, color: Colors.white),
              SizedBox(width: 8),
              Text("驾考学习", style: TextStyle(color: Colors.white, fontSize: Bs.bodySize, fontWeight: FontWeight.w700)),
            ],
          ),
          const SizedBox(height: 12),
          BsBadge(
            text: phase == null ? "科目一未完成" : "科目一 · 第${phase.id}阶段 ${phase.title}",
            color: Bs.warning,
            icon: Icons.flag,
          ),
          const SizedBox(height: 20),
          _navLine(
            icon: Icons.gavel,
            selected: _place == "subject1" && _session == null,
            label: "科目一",
            onTap: () => _go("subject1"),
          ),
          _navLine(
            icon: _s1Done ? Icons.health_and_safety : Icons.lock,
            selected: _place == "subject4" && _session == null,
            label: _s1Done ? "科目四" : "科目四（未解锁）",
            muted: !_s1Done,
            onTap: () => _go("subject4"),
          ),
          _navLine(
            icon: Icons.bookmark,
            selected: _place == _wrongId && _session == null,
            label: _wrongCount == 0 ? "错题本" : "错题本 $_wrongCount",
            onTap: () => _go(_wrongId),
          ),
          if (open) ...[
            const SizedBox(height: 16),
            const Divider(color: Colors.white30),
            const SizedBox(height: 8),
            if (current.id == "subject1") ...[
              _navLine(
                icon: Icons.list_alt,
                selected: false,
                label: () {
                  final n = _pending(_openPool(current)).length;
                  return n == 0 ? "本阶段练习（已掌握）" : "本阶段练习 $n";
                }(),
                muted: _pending(_openPool(current)).isEmpty,
                onTap: () => _startPractice(current, widget.bank.forPhase("subject1", _s1Open), "第$_s1Open阶段"),
              ),
              _navLine(
                icon: Icons.fact_check,
                selected: false,
                label: "本阶段测试",
                onTap: () => _startPhaseTest(current, _s1Open),
              ),
            ],
            _navLine(
              icon: Icons.timer,
              selected: false,
              label: current.id == "subject1" && !_s1Done ? "模拟考试（完成本科后）" : "模拟考试",
              muted: current.id == "subject1" && !_s1Done,
              onTap: current.id == "subject1" && !_s1Done ? null : () => _startExam(current),
            ),
            if (current.id == "subject4")
              _navLine(
                icon: Icons.list_alt,
                selected: false,
                label: () {
                  final n = _pending(_openPool(current)).length;
                  return n == 0 ? "全部练习（已掌握）" : "待练 $n 题";
                }(),
                muted: _pending(_openPool(current)).isEmpty,
                onTap: () => _startPractice(current, _openPool(current), "待练"),
              ),
            const SizedBox(height: 8),
            for (final topic in current.topics)
              () {
                final questions = _openTopic(current, topic);
                final pending = _pending(questions);
                final locked = current.id == "subject1" && widget.bank.forTopic(topic.id).every((q) => q.phase > _s1Open);
                return _navLine(
                  icon: locked ? Icons.lock : Icons.article_outlined,
                  selected: _session?.title.endsWith(topic.title) ?? false,
                  label: locked ? "${topic.title}（未解锁）" : (pending.isEmpty ? topic.title : "${topic.title}  ${pending.length}"),
                  muted: pending.isEmpty,
                  onTap: pending.isEmpty ? null : () => _startPractice(current, questions, topic.title),
                );
              }(),
          ],
        ],
      ),
    );
  }

  Widget _navLine({
    required IconData icon,
    required bool selected,
    required String label,
    VoidCallback? onTap,
    bool muted = false,
  }) {
    // 蓝底上：没选中的也要看得清，选中的用白色半透明底 + 左侧黄条顶出来
    final color = muted ? Colors.white54 : (selected ? Colors.white : const Color(0xFFDCE9FF));
    return InkWell(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
        decoration: BoxDecoration(
          color: selected ? Colors.white.withValues(alpha: 0.18) : null,
          borderRadius: BorderRadius.circular(Bs.radius),
          border: Border(
            left: BorderSide(color: selected ? Bs.warning : Colors.transparent, width: 4),
          ),
        ),
        child: Row(
          children: [
            Icon(icon, size: Bs.bodySize, color: color),
            const SizedBox(width: 10),
            Expanded(child: Text(label, style: TextStyle(color: color, fontSize: Bs.bodySize, fontWeight: selected ? FontWeight.w700 : FontWeight.w400))),
          ],
        ),
      ),
    );
  }

  Widget _overview(BuildContext context) {
    if (_place == _wrongId) return _wrongOverview(context);
    if (_place == "subject4" && !_s1Done) return _lockedSubject4(context);
    final subject = _subject!;
    if (subject.id == "subject1") return _subject1Overview(context, subject);
    return _subjectOverview(context, subject);
  }

  Widget _lockedSubject4(BuildContext context) {
    final open = _s1Open;
    final phase = widget.bank.curriculum.subject("subject1").phaseById(open);
    final current = widget.bank.forPhase("subject1", open);
    final left = _pending(current).length;
    return Padding(
      padding: const EdgeInsets.fromLTRB(36, 28, 36, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.lock, color: Bs.paper),
              SizedBox(width: 8),
              Text("科目四未解锁", style: TextStyle(fontSize: 32, fontWeight: FontWeight.w600)),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            "科目四是单独一卷、单独记分的文明驾驶常识考，跟路考不是同一张成绩。科目一四个阶段都掌握之前，先不开放。",
            style: Theme.of(context).textTheme.bodyLarge,
          ),
          const SizedBox(height: 16),
          BsAlert(
            color: Bs.warning,
            icon: Icons.flag,
            child: Text("现在在科目一第$open阶段「${phase?.title ?? ""}」，还剩 $left 题。先把科目一练完。"),
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: () => _go("subject1"),
            child: const Text("回到科目一"),
          ),
        ],
      ),
    );
  }

  Widget _subject1Overview(BuildContext context, Subject subject) {
    final open = _s1Open;
    final visible = _openPool(subject);
    final pending = _pending(visible);
    final current = widget.bank.forPhase("subject1", open);
    final phase = subject.phaseById(open);
    return Padding(
      padding: const EdgeInsets.fromLTRB(28, 24, 28, 28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(backgroundColor: Bs.paper.withValues(alpha: 0.15), child: const Icon(Icons.gavel, color: Bs.paper)),
              const SizedBox(width: 12),
              Text(subject.code, style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(width: 12),
              BsBadge(text: "第$open/${subject.phases.length}阶段", color: Bs.warning, icon: Icons.flag),
              if (_s1Done) ...[
                const SizedBox(width: 8),
                const BsBadge(text: "已全部掌握", color: Bs.success, icon: Icons.lock_open),
              ],
            ],
          ),
          const SizedBox(height: 8),
          Text(subject.title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 16),
          BsAlert(
            color: Bs.paper,
            icon: Icons.menu_book,
            child: Text(
              _s1Done
                  ? "科目一四阶段都掌握了，可以开科目四和科目一全库模拟考。"
                  : "当前第$open阶段「${phase?.title ?? ""}」：${phase?.plain ?? ""}。练路上会碰到的场面：高频、常考多出，偏难怪默认不出。本阶段日常题掌握后解锁下一阶段。科目四要等科目一全部完成。",
            ),
          ),
          const SizedBox(height: 16),
          _examTrend(context, subject),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              StatTile(icon: Icons.flag, label: "当前阶段", value: "$open", color: Bs.warning),
              StatTile(icon: Icons.pending_actions, label: "本阶段待练", value: "${_pending(current).length}", color: Bs.paper),
              StatTile(icon: Icons.check_circle, label: "已开放掌握", value: "${visible.where((q) => _mastered.contains(q.id)).length}/${visible.length}", color: Bs.success),
              StatTile(icon: Icons.quiz, label: "已开放题", value: "${visible.length}", color: Bs.secondary),
            ],
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              FilledButton(
                onPressed: pending.isEmpty ? null : () => _startPractice(subject, current, "第$open阶段"),
                child: const Text("本阶段练习"),
              ),
              FilledButton.tonal(
                onPressed: current.isEmpty ? null : () => _startPhaseTest(subject, open),
                child: const Text("本阶段测试"),
              ),
              if (_s1Done)
                FilledButton.tonal(
                  onPressed: () => _startExam(subject),
                  child: const Text("科目一模拟考"),
                ),
            ],
          ),
          const SizedBox(height: 20),
          Expanded(
            child: ListView(
              children: [
                for (final item in subject.phases) _phaseRow(context, subject, item),
                const SizedBox(height: 16),
                _topicHead(context),
                for (final topic in subject.topics) _topicRow(context, subject, topic),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _phaseRow(BuildContext context, Subject subject, StudyPhase phase) {
    final questions = widget.bank.forPhase(subject.id, phase.id);
    final mastered = questions.where((q) => _mastered.contains(q.id)).length;
    final locked = phase.id > _s1Open;
    final current = phase.id == _s1Open && !_s1Done;
    final ratio = questions.isEmpty ? 0.0 : mastered / questions.length;
    return InkWell(
      onTap: locked ? null : () => _startPractice(subject, questions, "第${phase.id}阶段"),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Row(
          children: [
            Icon(
              locked ? Icons.lock : (ratio >= 1 ? Icons.lock_open : Icons.flag),
              size: 18,
              color: locked ? Bs.secondary : (current ? Bs.warning : Bs.success),
            ),
            const SizedBox(width: 8),
            Expanded(
              flex: 6,
              child: Text(
                locked ? "第${phase.id}阶段 ${phase.title}（未解锁）" : "第${phase.id}阶段 ${phase.title}",
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: locked ? Bs.secondary : null),
              ),
            ),
            SizedBox(width: 88, child: Text(locked ? "—" : "$mastered/${questions.length}")),
            SizedBox(
              width: 160,
              child: BsProgress(
                value: locked ? 0 : ratio,
                color: ratio >= 1 ? Bs.success : Bs.paper,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _subjectOverview(BuildContext context, Subject subject) {
    final all = _openPool(subject);
    final pending = _pending(all);
    final mastered = all.where((q) => _mastered.contains(q.id)).length;
    final avg = _avgMs == 0 ? "—" : "${(_avgMs / 1000).toStringAsFixed(1)}秒";
    final exam = subject.exam;
    return Padding(
      padding: const EdgeInsets.fromLTRB(28, 24, 28, 28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(backgroundColor: Bs.paper.withValues(alpha: 0.15), child: const Icon(Icons.health_and_safety, color: Bs.paper)),
              const SizedBox(width: 12),
              Text(subject.code, style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(width: 12),
              const BsBadge(text: "科目一已过关", color: Bs.success, icon: Icons.lock_open),
            ],
          ),
          const SizedBox(height: 8),
          Text(subject.title, style: Theme.of(context).textTheme.titleMedium),
          if (subject.officialName != null) ...[
            const SizedBox(height: 4),
            Text("法规名称：${subject.officialName}", style: const TextStyle(color: Bs.secondary)),
          ],
          const SizedBox(height: 16),
          BsAlert(
            color: Bs.paper,
            icon: Icons.menu_book,
            child: Text("科目一已经掌握。科目四 50 题、45 分钟，折合 90 分及格，跟路考分开记分。"),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              StatTile(icon: Icons.check_circle, label: "已掌握", value: "$mastered", color: Bs.success),
              StatTile(icon: Icons.pending_actions, label: "待练", value: "${pending.length}", color: Bs.paper),
              StatTile(icon: Icons.bookmark, label: "错题", value: "$_wrongCount", color: Bs.danger),
              StatTile(icon: Icons.speed, label: "均速", value: avg, color: Bs.secondary),
              StatTile(icon: Icons.quiz, label: "题库", value: "${all.length}", color: Bs.secondary),
              StatTile(icon: Icons.timer, label: "考场", value: "${exam.questionCount}题/${exam.minutes}分", color: Bs.warning),
            ],
          ),
          const SizedBox(height: 20),
          Expanded(
            child: ListView(
              children: [
                _topicHead(context),
                for (final topic in subject.topics) _topicRow(context, subject, topic),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _topicHead(BuildContext context) {
    final style = Theme.of(context).textTheme.labelMedium?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
    );
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Expanded(flex: 6, child: Text("章节", style: style)),
          SizedBox(width: 72, child: Text("待练", style: style)),
          SizedBox(width: 72, child: Text("已掌握", style: style)),
          SizedBox(width: 160, child: Text("进度", style: style)),
        ],
      ),
    );
  }

  Widget _topicRow(BuildContext context, Subject subject, Topic topic) {
    final questions = _openTopic(subject, topic);
    final total = widget.bank.forTopic(topic.id);
    final locked = subject.id == "subject1" && total.isNotEmpty && questions.isEmpty;
    final pending = _pending(questions);
    final mastered = questions.where((q) => _mastered.contains(q.id)).length;
    final ratio = questions.isEmpty ? 0.0 : mastered / questions.length;
    final enabled = pending.isNotEmpty;
    return InkWell(
      onTap: enabled ? () => _startPractice(subject, questions, topic.title) : null,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Row(
          children: [
            Icon(locked ? Icons.lock : Icons.article, size: 18, color: locked ? Bs.secondary : (enabled ? Bs.paper : Bs.success)),
            const SizedBox(width: 8),
            Expanded(
              flex: 6,
              child: Text(
                locked
                    ? "${topic.title}（未解锁）"
                    : pending.isEmpty
                    ? "${topic.title}（已掌握）"
                    : topic.title,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: enabled ? null : Bs.secondary,
                ),
              ),
            ),
            SizedBox(width: 72, child: Text(locked ? "—" : "${pending.length}")),
            SizedBox(width: 72, child: Text(locked ? "—" : "$mastered/${questions.length}")),
            SizedBox(
              width: 160,
              child: BsProgress(
                value: locked ? 0 : ratio,
                color: ratio >= 1 ? Bs.success : Bs.paper,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 模拟考战绩：每次一根柱、90 分线横着，连续及格几次写在旁边（主仓库 ADR 0052）。
  Widget _examTrend(BuildContext context, Subject subject) {
    final mine = [for (final e in _exams) if (e.subjectId == subject.id) e];
    if (mine.isEmpty) return const SizedBox.shrink();
    final scores = [for (final e in mine.reversed) e.score];
    final best = scores.reduce((a, b) => a > b ? a : b);
    final streak = ProgressStore.passStreak(mine);
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 10),
      decoration: BoxDecoration(
        color: Bs.body,
        border: Border.all(color: Bs.border),
        borderRadius: BorderRadius.circular(Bs.radius),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.timeline, size: 22, color: Bs.paper),
              const SizedBox(width: 8),
              Text("模拟考战绩", style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(width: 16),
              Text(
                "考了 ${mine.length} 次 · 最好 $best 分"
                "${streak >= 2 ? " · 连续 $streak 次及格" : ""}",
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Bs.secondary),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ExamTrend(scores: scores, passScore: subject.exam.passScore),
        ],
      ),
    );
  }

  Widget _wrongOverview(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(36, 28, 36, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.bookmark, color: Bs.danger),
              SizedBox(width: 8),
              Text("错题本", style: TextStyle(fontSize: 32, fontWeight: FontWeight.w600)),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            _wrongCount == 0
                ? "最近一次都做对了。"
                : "最近一次答错 $_wrongCount 道，按错过的次数排好了——排在前面的是反复栽跟头的题。",
            style: Theme.of(context).textTheme.bodyLarge,
          ),
          if (_wrongCount > 0) ...[
            const SizedBox(height: 20),
            FilledButton(
              onPressed: () => _openSession(
                SessionLaunch(
                  title: "错题本",
                  subjectId: _wrongId,
                  questions: _wrongQuestions,
                  timed: false,
                  revealImmediately: true,
                ),
              ),
              child: const Text("开始订正"),
            ),
            const SizedBox(height: 20),
            Expanded(
              child: ListView.separated(
                itemCount: _wrongQuestions.length,
                separatorBuilder: (_, _) => const Divider(height: 18),
                itemBuilder: (context, i) {
                  final q = _wrongQuestions[i];
                  final times = _wrongCounts[q.id] ?? 1;
                  return Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      BsBadge(
                        text: times >= 3 ? "错 $times 次 · 顽固" : "错 $times 次",
                        icon: times >= 3 ? Icons.priority_high : Icons.close,
                        color: times >= 3 ? Bs.danger : Bs.warning,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          q.prompt,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context).textTheme.bodyLarge,
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _sessionPane() {
    return SessionStage(
      key: ObjectKey(_session),
      launch: _session!,
      store: widget.store,
      onClose: () async {
        setState(() => _session = null);
        await _reload();
      },
    );
  }

  void _go(String place) {
    setState(() {
      _place = place;
      _session = null;
    });
  }

  void _startExam(Subject subject) {
    if (subject.id == "subject4" && !_s1Done) return;
    if (subject.id == "subject1" && !_s1Done) return;
    final all = _openPool(subject);
    final paper = Paper.draw(all, subject.exam, Random());
    _openSession(
      SessionLaunch(
        title: "${subject.code} 模拟考试",
        subjectId: subject.id,
        questions: paper.questions,
        timed: true,
        minutes: subject.exam.minutes,
        revealImmediately: false,
        paper: paper,
      ),
    );
  }

  void _startPhaseTest(Subject subject, int phase) {
    final questions = widget.bank.forPhase(subject.id, phase);
    if (questions.isEmpty) return;
    final spec = subject.phaseById(phase);
    final rules = ExamRules(
      questionCount: questions.length,
      minutes: phaseTestMinutes(questions.length),
      passScore: subject.exam.passScore,
      pointsPerQuestion: 1,
    );
    final paper = Paper.draw(questions, rules, Random());
    _openSession(
      SessionLaunch(
        title: "${subject.code} · 第$phase阶段测试${spec == null ? "" : " · ${spec.title}"}",
        subjectId: subject.id,
        questions: paper.questions,
        timed: true,
        minutes: rules.minutes,
        revealImmediately: false,
        paper: paper,
      ),
    );
  }

  void _startPractice(Subject subject, List<Question> questions, String title) {
    if (subject.id == "subject4" && !_s1Done) return;
    final pending = _practiceQueue(questions);
    if (pending.isEmpty) return;
    _openSession(
      SessionLaunch(
        title: "${subject.code} · $title",
        subjectId: subject.id,
        questions: pending,
        timed: false,
        revealImmediately: true,
      ),
    );
  }

  void _openSession(SessionLaunch launch) {
    setState(() => _session = launch);
  }
}
