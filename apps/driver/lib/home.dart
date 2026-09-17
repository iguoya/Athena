import "dart:math";

import "package:flutter/material.dart";

import "exam.dart";
import "look.dart";
import "models.dart";
import "progress.dart";
import "sync.dart";
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
  static const _syncId = "sync";

  String _place = "subject1";
  SessionLaunch? _session;
  Set<String> _mastered = {};
  Map<String, int> _attempts = {};
  int _avgMs = 0;
  int _wrongCount = 0;
  List<Question> _wrongQuestions = const [];
  Map<String, int> _wrongCounts = const {};
  List<ExamRecord> _exams = const [];
  SyncConfig? _sync = SyncConfig.load();
  var _syncBusy = false;
  SyncResult? _syncResult;
  int _attemptTotal = 0;

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
    final attemptTotal = await widget.store.attemptTotal();
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
      _attemptTotal = attemptTotal;
    });
  }

  Subject? get _subject {
    if (_place == _wrongId || _place == _syncId) return null;
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
          _navLine(
            icon: Icons.cloud_sync,
            selected: _place == _syncId && _session == null,
            label: _sync?.usable == true ? "跨机器同步" : "跨机器同步（未配置）",
            muted: _sync?.usable != true,
            onTap: () => _go(_syncId),
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
    if (_place == _syncId) return _syncOverview(context);
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

  /// 跨机器同步：日常走云盘文件夹（iCloud Drive 这类），GitHub 那条留着当
  /// 版本历史与异地备份（ADR 0010）。
  Widget _syncOverview(BuildContext context) {
    final config = _sync;
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(36, 28, 36, 32),
      child: ListView(
        children: [
          const Row(
            children: [
              Icon(Icons.cloud_sync, color: Bs.primary),
              SizedBox(width: 8),
              Text("跨机器同步", style: TextStyle(fontSize: 32, fontWeight: FontWeight.w600)),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            "作答记录是只追加的事件流，两台机器按「题号 + 时间」取并集合并——只增不改，"
            "不会互相覆盖。本机现有 $_attemptTotal 条。",
            style: theme.textTheme.bodyLarge,
          ),
          const SizedBox(height: 20),
          _folderSyncCard(context, config),
          const SizedBox(height: 16),
          _githubSyncCard(context, config),
          if (_syncResult != null) ...[
            const SizedBox(height: 16),
            BsAlert(
              color: _syncResult!.ok ? Bs.success : Bs.danger,
              icon: _syncResult!.ok ? Icons.check_circle : Icons.error,
              child: Text(
                _syncResult!.ok
                    ? "${_syncResult!.message}；合并后共 ${_syncResult!.total} 条记录"
                    : _syncResult!.message,
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _syncCard({
    required BuildContext context,
    required IconData icon,
    required Color color,
    required String title,
    required String subtitle,
    required List<Widget> rows,
    required List<Widget> actions,
  }) {
    return Container(
      padding: const EdgeInsets.fromLTRB(18, 16, 18, 16),
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
              Icon(icon, color: color, size: 24),
              const SizedBox(width: 8),
              Text(title, style: Theme.of(context).textTheme.titleLarge),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            subtitle,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Bs.secondary, height: 1.45),
          ),
          const SizedBox(height: 12),
          ...rows,
          const SizedBox(height: 12),
          Wrap(spacing: 10, runSpacing: 10, children: actions),
        ],
      ),
    );
  }

  Widget _syncLine(BuildContext context, String label, String value, {Color? color}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 92,
            child: Text(label, style: const TextStyle(color: Bs.secondary, fontSize: 16)),
          ),
          Expanded(
            child: Text(
              value,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: color ?? Bs.dark,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _folderSyncCard(BuildContext context, SyncConfig? config) {
    final ready = config?.folderUsable == true;
    final device = (config?.device.isEmpty ?? true) ? SyncConfig.defaultDevice() : config!.device;
    return _syncCard(
      context: context,
      icon: Icons.cloud_done,
      color: Bs.primary,
      title: "云盘文件夹（日常同步）",
      subtitle: "指向一个云盘目录，由云盘客户端搬运。每台机器只写自己那份文件，"
          "所以不会有写冲突；读的时候把目录里所有机器的记录并起来。",
      rows: [
        _syncLine(context, "同步目录", ready ? config!.folder : "未选择",
            color: ready ? null : Bs.warning),
        _syncLine(context, "本机代号", device),
        _syncLine(context, "上次同步", _agoLabel(config?.folderSyncedAt)),
      ],
      actions: [
        FilledButton.icon(
          onPressed: ready && !_syncBusy ? _runFolderSync : null,
          style: FilledButton.styleFrom(minimumSize: const Size(150, 48)),
          icon: _syncBusy
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : const Icon(Icons.sync, size: 20),
          label: Text(_syncBusy ? "同步中…" : "立即同步"),
        ),
        OutlinedButton.icon(
          onPressed: _syncBusy ? null : () => _editFolder(context),
          icon: const Icon(Icons.folder_open, size: 20),
          label: Text(ready ? "换个目录" : "选择同步目录"),
          style: OutlinedButton.styleFrom(minimumSize: const Size(150, 48)),
        ),
      ],
    );
  }

  Widget _githubSyncCard(BuildContext context, SyncConfig? config) {
    final ready = config?.usable == true;
    return _syncCard(
      context: context,
      icon: Icons.history,
      color: Bs.teal,
      title: "GitHub 私有仓库（版本历史与异地备份）",
      subtitle: "每次同步留下一个可回滚的提交。不依赖任何客户端软件，三个平台一视同仁——"
          "云盘那条走不通时它还在。",
      rows: [
        _syncLine(context, "远端仓库", ready ? "${config!.owner}/${config.repo}" : "未配置",
            color: ready ? null : Bs.warning),
        _syncLine(context, "文件", config?.path ?? "driver-progress.jsonl"),
        _syncLine(context, "上次同步", _agoLabel(config?.lastSyncedAt)),
      ],
      actions: [
        FilledButton.icon(
          onPressed: ready && !_syncBusy ? _runSync : null,
          style: FilledButton.styleFrom(
            backgroundColor: Bs.teal,
            foregroundColor: Colors.white,
            minimumSize: const Size(150, 48),
          ),
          icon: const Icon(Icons.backup, size: 20),
          label: const Text("推一份备份"),
        ),
        OutlinedButton.icon(
          onPressed: _syncBusy ? null : () => _editSync(context),
          icon: const Icon(Icons.key, size: 20),
          label: Text(ready ? "修改配置" : "配置仓库与令牌"),
          style: OutlinedButton.styleFrom(minimumSize: const Size(150, 48)),
        ),
      ],
    );
  }

  String _agoLabel(String? raw) {
    if (raw == null) return "还没同步过";
    final at = DateTime.tryParse(raw);
    if (at == null) return "还没同步过";
    final diff = DateTime.now().difference(at);
    if (diff.inMinutes < 1) return "刚刚";
    if (diff.inHours < 1) return "${diff.inMinutes} 分钟前";
    if (diff.inDays < 1) return "${diff.inHours} 小时前";
    return "${diff.inDays} 天前";
  }

  Future<void> _runFolderSync() async {
    final config = _sync;
    if (config == null || !config.folderUsable) return;
    setState(() {
      _syncBusy = true;
      _syncResult = null;
    });
    final result = await FolderSync(config).run(widget.store);
    if (!mounted) return;
    if (result.ok) {
      final updated = config.withFolderSynced(DateTime.now());
      updated.save();
      _sync = updated;
      await _reload();
    }
    if (!mounted) return;
    setState(() {
      _syncBusy = false;
      _syncResult = result;
    });
  }

  Future<void> _editFolder(BuildContext context) async {
    final current = _sync;
    final folder = TextEditingController(
      text: current?.folder.isNotEmpty == true
          ? current!.folder
          : (SyncConfig.defaultCloudFolder() ?? ""),
    );
    final device = TextEditingController(
      text: current?.device.isNotEmpty == true ? current!.device : SyncConfig.defaultDevice(),
    );
    final saved = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text("同步文件夹"),
        content: SizedBox(
          width: 560,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                controller: folder,
                decoration: const InputDecoration(
                  labelText: "目录路径",
                  helperText: "iCloud Drive、OneDrive、坚果云的同步目录都行，两台机器挂同一个账号即可",
                ),
              ),
              const SizedBox(height: 8),
              if (SyncConfig.defaultCloudFolder() != null)
                TextButton.icon(
                  onPressed: () => folder.text = SyncConfig.defaultCloudFolder()!,
                  icon: const Icon(Icons.cloud, size: 18),
                  label: const Text("用 iCloud Drive 里的 Athena 目录"),
                ),
              TextField(
                controller: device,
                decoration: const InputDecoration(
                  labelText: "本机代号",
                  helperText: "决定这台机器写哪个文件，两台不能重名",
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(dialogContext).pop(null), child: const Text("取消")),
          FilledButton(onPressed: () => Navigator.of(dialogContext).pop(true), child: const Text("保存")),
        ],
      ),
    );
    if (saved != true) return;
    final base = current ?? const SyncConfig(owner: "", repo: "", token: "");
    final updated = base.copyWith(
      folder: folder.text.trim(),
      device: device.text.trim().isEmpty ? SyncConfig.defaultDevice() : device.text.trim(),
    );
    updated.save();
    setState(() {
      _sync = updated;
      _syncResult = null;
    });
  }

  Future<void> _runSync() async {
    final config = _sync;
    if (config == null || !config.usable) return;
    setState(() {
      _syncBusy = true;
      _syncResult = null;
    });
    final result = await GithubSync(config).run(widget.store);
    if (!mounted) return;
    if (result.ok) {
      final updated = config.withLastSynced(DateTime.now());
      updated.save();
      _sync = updated;
      await _reload();
    }
    if (!mounted) return;
    setState(() {
      _syncBusy = false;
      _syncResult = result;
    });
  }

  Future<void> _editSync(BuildContext context) async {
    final current = _sync;
    final owner = TextEditingController(text: current?.owner ?? "");
    final repo = TextEditingController(text: current?.repo ?? "");
    final path = TextEditingController(text: current?.path ?? "driver-progress.jsonl");
    final branch = TextEditingController(text: current?.branch ?? "main");
    final token = TextEditingController(text: current?.token ?? "");
    final saved = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text("同步配置"),
        content: SizedBox(
          width: 520,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: owner,
                  decoration: const InputDecoration(labelText: "GitHub 用户名", hintText: "例如 iguoya"),
                ),
                TextField(
                  controller: repo,
                  decoration: const InputDecoration(labelText: "私有仓库名", hintText: "例如 athena-progress"),
                ),
                TextField(
                  controller: path,
                  decoration: const InputDecoration(labelText: "文件路径"),
                ),
                TextField(
                  controller: branch,
                  decoration: const InputDecoration(labelText: "分支"),
                ),
                TextField(
                  controller: token,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: "访问令牌（fine-grained PAT）",
                    hintText: "只给这个仓库的 Contents 读写权限",
                  ),
                ),
              ],
            ),
          ),
        ),
        actions: [
          if (current != null)
            TextButton(
              onPressed: () {
                SyncConfig.clear();
                Navigator.of(dialogContext).pop(false);
              },
              child: const Text("清除配置", style: TextStyle(color: Bs.danger)),
            ),
          TextButton(onPressed: () => Navigator.of(dialogContext).pop(null), child: const Text("取消")),
          FilledButton(onPressed: () => Navigator.of(dialogContext).pop(true), child: const Text("保存")),
        ],
      ),
    );
    if (saved == null) return;
    if (!saved) {
      setState(() {
        _sync = null;
        _syncResult = null;
      });
      return;
    }
    final config = SyncConfig(
      owner: owner.text.trim(),
      repo: repo.text.trim(),
      token: token.text.trim(),
      path: path.text.trim().isEmpty ? "driver-progress.jsonl" : path.text.trim(),
      branch: branch.text.trim().isEmpty ? "main" : branch.text.trim(),
      lastSyncedAt: current?.lastSyncedAt,
    );
    config.save();
    setState(() {
      _sync = config;
      _syncResult = null;
    });
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
