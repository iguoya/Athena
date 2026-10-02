import "dart:async";
import "dart:math";

import "package:flutter/material.dart";

import "glyphs.dart";
import "exam.dart";
import "look.dart";
import "models.dart";
import "progress.dart";
import "subject2.dart";
import "session.dart";

class HomePage extends StatefulWidget {
  const HomePage({
    super.key,
    required this.bank,
    required this.store,
    this.onReady,
  });

  final Bank bank;
  final ProgressStore store;


  /// 第一次从进度库读完统计后调一次；测试靠它等首页就绪，不按固定时长等。
  final VoidCallback? onReady;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  static const _wrongId = "wrong";
  static const _reviewId = "review";
  static const _numbersId = "numbers";

  String _place = "subject1";
  SessionLaunch? _session;
  Set<String> _mastered = {};
  Map<String, int> _attempts = {};
  int _avgMs = 0;
  int _wrongCount = 0;
  List<Question> _wrongQuestions = const [];
  List<Question> _reviewQuestions = const [];
  List<DrillRun> _drillRuns = const [];
  Map<String, int> _reviewStreaks = const {};
  int _reviewGraduated = 0;
  Map<String, int> _wrongCounts = const {};
  List<ExamRecord> _exams = const [];
  List<ExamRecord> _s1Exams = const [];
  List<Notice> _notices = const [];
  List<DailyCount> _daily = const [];
  Map<String, TopicStats> _topicStats = const {};

  /// 侧栏里展开着的科目。默认展开科目一；点科目名进去顺手展开，点右侧箭头只展开/收起、不换页。
  final Set<String> _expanded = {"subject1"};


  Set<String> get _wrongIds => {for (final q in _wrongQuestions) q.id};

  List<Question> get _subject1All => widget.bank.forSubject("subject1");


  bool get _s1Done => allMastered(_subject1All, _mastered);

  /// 最近几场科目一模拟考都在 95 分以上（ADR 0047）。
  bool get _s1Steady => ProgressStore.subject1Steady(_s1Exams);

  /// 科目二要等科目一模拟考稳定在 95 分以上（ADR 0047），科目四要等科目一日常题
  /// 全部掌握（ADR 0006 第 4 条）。两把锁都由作答和交卷记录推导，没有手动开关。
  bool _locked(String subjectId) => switch (subjectId) {
        "subject2" => !_s1Steady,
        "subject4" => !_s1Done,
        _ => false,
      };

  /// 锁着的科目，它的题不进错题本和考前复习——题干都不该先看到（ADR 0006 后果）。
  static bool _hiddenTopic(String topicId, {required bool s1Done, required bool s1Steady}) =>
      (!s1Steady && topicId.startsWith("drive.s2.")) || (!s1Done && topicId.startsWith("drive.s4."));

  bool _keepInPractice(Question q) {
    return q.appearsInPractice(
      mastered: _mastered.contains(q.id),
      wrong: _wrongIds.contains(q.id),
      attempts: _attempts[q.id] ?? 0,
    );
  }

  List<Question> _pending(List<Question> questions) {
    return [
      for (final q in questions)
        if (_keepInPractice(q)) q,
    ];
  }

  List<Question> _practiceQueue(List<Question> questions) {
    return practiceQueue(_pending(questions), _wrongIds);
  }

  List<Question> _openPool(Subject subject) {
    // 科目一不设解锁（ADR 0044）：四个阶段只是按内容分的四组，全部开放。
    return dailyQuestions(widget.bank.forSubject(subject.id));
  }

  List<Question> _openTopic(Subject subject, Topic topic) {
    final questions = widget.bank.forTopic(topic.id);
    return dailyQuestions(questions);
  }

  @override
  void initState() {
    super.initState();
    // 第一次从进度库读完统计后调一次 onReady；测试靠它等首页就绪。
    _reload().then((_) => widget.onReady?.call());
  }

  @override
  void dispose() {
    super.dispose();
  }



  Future<void> _reload() async {
    final mastered = await widget.store.masteredQuestionIds();
    final attempts = await widget.store.attemptCounts();
    final avgMs = await widget.store.averageDurationMs();
    final ids = await widget.store.wrongQuestionIds();
    final wrongCounts = await widget.store.wrongCounts();
    final streaks = await widget.store.correctStreaksSinceWrong();
    final drillRuns = await widget.store.drillRuns();
    final exams = await widget.store.recentExams();
    // 单独取科目一的：混着取的最近 12 场可能被科目四挤掉，科目二的解锁线就算不准了。
    final s1Exams = await widget.store.recentExams(subjectId: "subject1", limit: ProgressStore.steadyRuns);
    final notices = await widget.store.notices(limit: 5);
    final daily = await widget.store.dailyAttempts();
    final topicStats = await widget.store.topicStats();
    final s1Done = allMastered(widget.bank.forSubject("subject1"), mastered);
    final wrong = [
      for (final id in ids)
        if (widget.bank.questions.any((q) => q.id == id)) widget.bank.byId(id),
    ];
    final s1Steady = ProgressStore.subject1Steady(s1Exams);
    wrong.removeWhere((q) => _hiddenTopic(q.topicId, s1Done: s1Done, s1Steady: s1Steady));
    // 错得越多的排越前：考前该先啃反复栽跟头的那几道。
    wrong.sort(
      (a, b) => (wrongCounts[b.id] ?? 0).compareTo(wrongCounts[a.id] ?? 0),
    );
    // 考前复习：累计错够次数进来；最近一次答对、且累计答对比答错多 1～2 次才出去，
    // 再错又回来（ADR 0033、0035）。全部从作答记录派生，不另存一张表。
    final eligible = [
      for (final q in widget.bank.questions)
        if ((wrongCounts[q.id] ?? 0) >= reviewMinWrong &&
            !_hiddenTopic(q.topicId, s1Done: s1Done, s1Steady: s1Steady))
          q,
    ];
    int correctOf(Question q) => (attempts[q.id] ?? 0) - (wrongCounts[q.id] ?? 0);
    int left(Question q) => reviewExitCorrect(wrongCounts[q.id] ?? 0) - correctOf(q);
    bool stillWrong(Question q) => (streaks[q.id] ?? 0) == 0;
    final review = [
      for (final q in eligible)
        if (inReview(
          wrongCount: wrongCounts[q.id] ?? 0,
          correctCount: correctOf(q),
          streak: streaks[q.id] ?? 0,
        ))
          q,
    ]..sort((a, b) {
        // 还错着的先练；同样状态下离移出还差得越多越靠前，再按错的次数。
        final byOpen = (stillWrong(b) ? 1 : 0).compareTo(stillWrong(a) ? 1 : 0);
        if (byOpen != 0) return byOpen;
        final byLeft = left(b).compareTo(left(a));
        if (byLeft != 0) return byLeft;
        return (wrongCounts[b.id] ?? 0).compareTo(wrongCounts[a.id] ?? 0);
      });
    if (!mounted) return;
    // 作答数比上次看到的还多，说明这段时间人真的在做题，刷新一下活动时间戳。
    setState(() {
      _mastered = mastered;
      _attempts = attempts;
      _avgMs = avgMs;
      _wrongCount = wrong.length;
      _wrongQuestions = wrong;
      _reviewQuestions = review;
      _drillRuns = drillRuns;
      _reviewStreaks = streaks;
      _reviewGraduated = eligible.length - review.length;
      _wrongCounts = wrongCounts;
      _exams = exams;
      _s1Exams = s1Exams;
      _notices = notices;
      _daily = daily;
      _topicStats = topicStats;
    });
    // 看过了就标已读——本机单人用，没有「谁看过」的问题，进首页就算看到了。
    await widget.store.markAllRead();
  }

  Subject? get _subject {
    if (_place == _wrongId || _place == _reviewId || _place == _numbersId) return null;
    return widget.bank.curriculum.subject(_place);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          SizedBox(width: 312, child: _sidebar(context)),
          const VerticalDivider(width: 1, color: Bs.border),
          Expanded(
            child: _session == null ? _overview(context) : _sessionPane(),
          ),
        ],
      ),
    );
  }

  Widget _sidebar(BuildContext context) {
    final s1Daily = dailyQuestions(_subject1All);
    final s1Mastered = s1Daily.where((q) => _mastered.contains(q.id)).length;
    return ColoredBox(
      color: Bs.nav,
      child: Column(
        children: [
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 20, 12, 12),
              children: [
                const Row(
                  children: [
                    AppMark(),
                    SizedBox(width: 8),
                    Text(
                      "驾考学习",
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: Bs.bodySize,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                BsBadge(
                  text: _s1Done ? "科目一已全部掌握" : "科目一 已掌握 $s1Mastered/${s1Daily.length}",
                  color: _s1Done ? Bs.success : Bs.warning,
                  icon: Glyph.goal,
                ),
                const SizedBox(height: 20),
                // 三个科目是一级目录，各自的模拟考、待练和章节挂在自己底下（ADR 0050）。
                ..._subjectBranch(
                  "subject1",
                  icon: Glyph.subject1,
                  label: "科目一",
                ),
                ..._subjectBranch(
                  "subject2",
                  icon: _s1Steady ? Glyph.subject2 : Glyph.locked,
                  label: _s1Steady ? "科目二（C2）" : "科目二（未解锁）",
                ),
                ..._subjectBranch(
                  "subject4",
                  icon: _s1Done ? Glyph.subject4 : Glyph.locked,
                  label: _s1Done ? "科目四" : "科目四（未解锁）",
                ),
              ],
            ),
          ),
          // 跨科目的几个入口钉在侧栏底部，不跟科目目录一起滚：科目展开得再长，
          // 错题本、考前复习也一直看得见（ADR 0051）。
          const Divider(height: 1, color: Colors.white30),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 12, 8),
            child: Column(
              children: [
                _navLine(
                  icon: Glyph.wrongBook,
                  selected: _place == _wrongId && _session == null,
                  label: _wrongCount == 0 ? "错题本" : "错题本 $_wrongCount",
                  onTap: () => _go(_wrongId),
                ),
                _navLine(
                  icon: Glyph.review,
                  selected: _place == _reviewId && _session == null,
                  label: _reviewQuestions.isEmpty ? "考前复习" : "考前复习 ${_reviewQuestions.length}",
                  onTap: () => _go(_reviewId),
                ),
                _navLine(
                  icon: Glyph.numbers,
                  selected: _place == _numbersId && _session == null,
                  label: "易混数字",
                  onTap: () => _go(_numbersId),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// 一个科目在侧栏里的一枝：科目本身一行，展开时下面缩进挂模拟考、待练和各章节。
  /// 锁着的科目没有子项——题干都不该先看到（ADR 0006 后果、ADR 0047）。
  List<Widget> _subjectBranch(String id, {required IconData icon, required String label}) {
    final subject = widget.bank.curriculum.subject(id);
    final locked = _locked(id);
    final expanded = !locked && _expanded.contains(id);
    final session = _session;
    bool inSession(String title) => session != null && session.subjectId == id && session.title == title;
    return [
      _navLine(
        icon: icon,
        selected: _place == id && _session == null,
        label: label,
        muted: locked,
        onTap: () {
          if (!locked) _expanded.add(id);
          _go(id);
        },
        trailing: locked
            ? null
            : InkWell(
                borderRadius: BorderRadius.circular(Bs.radius),
                onTap: () => setState(() {
                  if (!_expanded.remove(id)) _expanded.add(id);
                }),
                child: Tooltip(
                  message: expanded ? "收起" : "展开",
                  child: Icon(
                    expanded ? Glyph.collapse : Glyph.expand,
                    size: Bs.bodySize,
                    color: Colors.white70,
                  ),
                ),
              ),
      ),
      if (expanded) ...[
        // 科目二没有笔试（ADR 0036）。
        if (subject.exam != null)
          _navLine(
            icon: Glyph.mockExam,
            selected: session != null && session.draftKey == "$id.exam",
            label: "模拟考试",
            indent: true,
            onTap: () => _startExam(subject),
          ),
        () {
          final n = _pending(_openPool(subject)).length;
          return _navLine(
            icon: Glyph.practice,
            selected: inSession("${subject.code} · 待练"),
            label: n == 0 ? "全部练习（已掌握）" : "待练 $n 题",
            muted: n == 0,
            indent: true,
            onTap: () => _startPractice(subject, _openPool(subject), "待练"),
          );
        }(),
        for (final topic in subject.topics)
          () {
            final questions = _openTopic(subject, topic);
            final pending = _pending(questions);
            return _navLine(
              icon: Glyph.topic,
              selected: inSession("${subject.code} · ${topic.title}"),
              label: pending.isEmpty ? topic.title : "${topic.title}  ${pending.length}",
              muted: pending.isEmpty,
              indent: true,
              onTap: pending.isEmpty ? null : () => _startPractice(subject, questions, topic.title),
            );
          }(),
        const SizedBox(height: 6),
      ],
    ];
  }

  Widget _navLine({
    required IconData icon,
    required bool selected,
    required String label,
    VoidCallback? onTap,
    bool muted = false,
    bool indent = false,
    Widget? trailing,
  }) {
    // 蓝底上：没选中的也要看得清，选中的用白色半透明底 + 左侧黄条顶出来
    final color = muted
        ? Colors.white54
        : (selected ? Colors.white : const Color(0xFFDCE9FF));
    // 子项往右缩一个图标宽，一眼看出挂在哪个科目底下。行距收紧、侧栏放宽到章节名不折行：
    // 底部钉住跨科目入口后，科目一展开 13 行，科目二、科目四仍要留在一屏里（ADR 0051）。
    return InkWell(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        margin: EdgeInsets.only(left: indent ? 24 : 0),
        padding: EdgeInsets.symmetric(horizontal: 8, vertical: indent ? 4 : 8),
        decoration: BoxDecoration(
          color: selected ? Colors.white.withValues(alpha: 0.18) : null,
          borderRadius: BorderRadius.circular(Bs.radius),
          border: Border(
            left: BorderSide(
              color: selected ? Bs.warning : Colors.transparent,
              width: 4,
            ),
          ),
        ),
        child: Row(
          children: [
            Icon(icon, size: Bs.bodySize, color: color),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  color: color,
                  fontSize: Bs.bodySize,
                  fontWeight: selected ? FontWeight.w700 : FontWeight.w400,
                ),
              ),
            ),
            ?trailing,
          ],
        ),
      ),
    );
  }

  Widget _overview(BuildContext context) {
    if (_place == _wrongId) return _wrongOverview(context);
    if (_place == _reviewId) return _reviewOverview(context);
    if (_locked(_place)) return _lockedSubject(context, widget.bank.curriculum.subject(_place));
    if (_place == "subject2") {
      final subject2 = widget.bank.curriculum.subject("subject2");
      return Subject2Page(
        bank: widget.bank,
        store: widget.store,
        mastered: _mastered,
        runs: _drillRuns,
        onPractice: (questions, title) => _startPractice(subject2, questions, title),
        onChanged: _reload,
      );
    }
    if (_place == _numbersId) return _numbersOverview(context);
    final subject = _subject!;
    if (subject.id == "subject1") return _subject1Overview(context, subject);
    return _subjectOverview(context, subject);
  }

  Widget _lockedSubject(BuildContext context, Subject subject) {
    final String why;
    final String todo;
    if (subject.id == "subject2") {
      final scores = [for (final e in _s1Exams) e.score];
      why = "科目二是场地驾驶技能考，科目一考过才能约。科目一模拟考最近 ${ProgressStore.steadyRuns} 场"
          "都在 ${ProgressStore.steadyScore} 分以上之前，先不开放。";
      todo = scores.isEmpty
          ? "还没考过科目一模拟考。"
          : "科目一最近 ${scores.length} 场：${scores.join("、")} 分（新的在前）。"
              "要连着 ${ProgressStore.steadyRuns} 场都不低于 ${ProgressStore.steadyScore} 分。";
    } else {
      final left = _pending(dailyQuestions(_subject1All)).length;
      why = "科目四是单独一卷、单独记分的文明驾驶常识考，跟路考不是同一张成绩。科目一日常题全部掌握之前，先不开放。";
      todo = "科目一还有 $left 题没掌握。先把科目一练完。";
    }
    return Padding(
      padding: const EdgeInsets.fromLTRB(36, 28, 36, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Glyph.locked, color: Bs.paper),
              const SizedBox(width: 8),
              Text(
                "${subject.code}未解锁",
                style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w600),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(why, style: Theme.of(context).textTheme.bodyLarge),
          const SizedBox(height: 16),
          BsAlert(
            color: Bs.warning,
            icon: Glyph.goal,
            child: Text(todo),
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
    final visible = _openPool(subject);
    final pending = _pending(visible);
    // 整页用 ListView：塞进去的卡片越来越多，固定高度的 Column + Expanded
    // 会把最下面的章节列表挤没了，改成能滚动就不会有「东西被挤没」这回事。
    return ListView(
      padding: const EdgeInsets.fromLTRB(28, 24, 28, 28),
      children: [
        // 用 Wrap 而不是 Row：窗口窄时标题和徽章挤不下，换行而不是溢出。
        Wrap(
          crossAxisAlignment: WrapCrossAlignment.center,
          spacing: 12,
          runSpacing: 8,
          children: [
            CircleAvatar(
              backgroundColor: Bs.paper.withValues(alpha: 0.15),
              child: const Icon(Glyph.subject1, color: Bs.paper),
            ),
            Text(
              subject.code,
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            if (_s1Done)
              const BsBadge(
                text: "已全部掌握",
                color: Bs.success,
                icon: Glyph.correct,
              ),
          ],
        ),
        const SizedBox(height: 8),
        Text(subject.title, style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 16),
        BsAlert(
          color: Bs.paper,
          icon: Glyph.info,
          child: Text(
            _s1Done
                ? "科目一日常题都掌握了，科目四已经开放。模拟考随时可以考；连着 ${ProgressStore.steadyRuns} 场 ${ProgressStore.steadyScore} 分以上开放科目二。"
                : "四个阶段按内容分组，全部开放，想练哪组点哪组；「练习待练题」从错题、高频、常考、常规依次出。偏难怪默认不出。模拟考随时可以考；科目二要等模拟考连着 ${ProgressStore.steadyRuns} 场 ${ProgressStore.steadyScore} 分以上，科目四要等科目一全部掌握。",
          ),
        ),
        const SizedBox(height: 16),
        _examTrend(context, subject),
        _progressCharts(context, subject),
        _topicAccuracyCard(context, subject),
        _recentNotices(context),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            StatTile(
              icon: Glyph.pending,
              label: "待练",
              value: "${pending.length}",
              color: Bs.paper,
            ),
            StatTile(
              icon: Glyph.correct,
              label: "已掌握",
              value:
                  "${visible.where((q) => _mastered.contains(q.id)).length}/${visible.length}",
              color: Bs.success,
            ),
            StatTile(
              icon: Glyph.question,
              label: "日常题",
              value: "${visible.length}",
              color: Bs.secondary,
            ),
          ],
        ),
        const SizedBox(height: 16),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            FilledButton(
              onPressed: pending.isEmpty
                  ? null
                  : () => _startPractice(subject, visible, "待练"),
              child: const Text("练习待练题"),
            ),
            FilledButton.tonal(
              onPressed: () => _startExam(subject),
              child: const Text("科目一模拟考"),
            ),
          ],
        ),
        const SizedBox(height: 20),
        for (final item in subject.phases)
          _phaseRow(context, subject, item, _phaseTitleWidth(context, subject)),
        const SizedBox(height: 16),
        _topicHead(context, _topicTitleWidth(context, subject)),
        for (final topic in subject.topics)
          _topicRow(context, subject, topic, _topicTitleWidth(context, subject)),
      ],
    );
  }

  /// 章节/阶段这一列的宽度按「最长的那个标题（带最长的后缀）」量出来：
  /// 短标题不用跟着遭殃换行或截断，长标题也不用撑爆布局——跟 ADR 0015
  /// 里章节正确率图表的标题列是同一个思路。
  double _phaseTitleWidth(BuildContext context, Subject subject) {
    final style = Theme.of(context).textTheme.bodyLarge;
    var width = 0.0;
    for (final phase in subject.phases) {
      final painter = TextPainter(
        text: TextSpan(text: "第${phase.id}阶段 ${phase.title}", style: style),
        textDirection: Directionality.of(context),
        maxLines: 1,
      )..layout();
      if (painter.width > width) width = painter.width;
    }
    return width;
  }

  double _topicTitleWidth(BuildContext context, Subject subject) {
    final style = Theme.of(context).textTheme.bodyLarge;
    var width = 0.0;
    for (final topic in subject.topics) {
      final painter = TextPainter(
        text: TextSpan(text: "${topic.title}（已掌握）", style: style),
        textDirection: Directionality.of(context),
        maxLines: 1,
      )..layout();
      if (painter.width > width) width = painter.width;
    }
    return width;
  }

  Widget _phaseRow(BuildContext context, Subject subject, StudyPhase phase, double titleWidth) {
    final questions = widget.bank.forPhase(subject.id, phase.id);
    // 偏难题默认不练、不挡掌握，也就不进分母，否则明明练完了，进度条却永远差那几道。
    final daily = dailyQuestions(questions);
    final rare = questions.length - daily.length;
    final mastered = daily.where((q) => _mastered.contains(q.id)).length;
    final ratio = daily.isEmpty ? 0.0 : mastered / daily.length;
    return InkWell(
      onTap: () => _startPractice(subject, questions, "第${phase.id}阶段"),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Row(
          children: [
            Icon(
              ratio >= 1 ? Glyph.correct : Glyph.goal,
              size: 18,
              color: ratio >= 1 ? Bs.success : Bs.warning,
            ),
            const SizedBox(width: 8),
            SizedBox(
              width: titleWidth,
              child: Text(
                "第${phase.id}阶段 ${phase.title}",
                maxLines: 1,
                style: Theme.of(context).textTheme.bodyLarge,
              ),
            ),
            const SizedBox(width: 12),
            SizedBox(
              width: 90,
              child: rare == 0
                  ? Text("$mastered/${daily.length}")
                  : Tooltip(
                      message: "另有偏难 $rare 道：默认不练、不挡过关，不计入进度",
                      child: Text("$mastered/${daily.length}"),
                    ),
            ),
            const SizedBox(width: 12),
            _percent(ratio),
            const SizedBox(width: 12),
            Expanded(
              child: BsProgress(
                value: ratio,
                color: ratio >= 1 ? Bs.success : Bs.paper,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 进度条左边的百分比。向下取整：差一道没掌握时不该显示成 100%。
  Widget _percent(double ratio) {
    return SizedBox(
      width: 44,
      child: Text(
        "${(ratio * 100).floor()}%",
        textAlign: TextAlign.right,
        style: const TextStyle(fontFeatures: [FontFeature.tabularFigures()]),
      ),
    );
  }

  Widget _subjectOverview(BuildContext context, Subject subject) {
    final all = _openPool(subject);
    final pending = _pending(all);
    final mastered = all.where((q) => _mastered.contains(q.id)).length;
    final avg = _avgMs == 0 ? "—" : "${(_avgMs / 1000).toStringAsFixed(1)}秒";
    final exam = subject.exam!;
    // 整页用 ListView：理由同科目一概览——固定高度会把章节列表挤没。
    return ListView(
      padding: const EdgeInsets.fromLTRB(28, 24, 28, 28),
      children: [
        Wrap(
          crossAxisAlignment: WrapCrossAlignment.center,
          spacing: 12,
          runSpacing: 8,
          children: [
            CircleAvatar(
              backgroundColor: Bs.paper.withValues(alpha: 0.15),
              child: const Icon(Glyph.subject4, color: Bs.paper),
            ),
            Text(
              subject.code,
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const BsBadge(
              text: "科目一已过关",
              color: Bs.success,
              icon: Glyph.unlocked,
            ),
          ],
        ),
        const SizedBox(height: 8),
        Text(subject.title, style: Theme.of(context).textTheme.titleMedium),
        if (subject.officialName != null) ...[
          const SizedBox(height: 4),
          Text(
            "法规名称：${subject.officialName}",
            style: const TextStyle(color: Bs.secondary),
          ),
        ],
        const SizedBox(height: 16),
        BsAlert(
          color: Bs.paper,
          icon: Glyph.info,
          child: Text("科目一已经掌握。科目四 50 题、45 分钟，折合 90 分及格，跟路考分开记分。"),
        ),
        const SizedBox(height: 16),
        _progressCharts(context, subject),
        _topicAccuracyCard(context, subject),
        _recentNotices(context),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            StatTile(
              icon: Glyph.correct,
              label: "已掌握",
              value: "$mastered",
              color: Bs.success,
            ),
            StatTile(
              icon: Glyph.pending,
              label: "待练",
              value: "${pending.length}",
              color: Bs.paper,
            ),
            StatTile(
              icon: Glyph.wrongBook,
              label: "错题",
              value: "$_wrongCount",
              color: Bs.danger,
            ),
            StatTile(
              icon: Glyph.speed,
              label: "均速",
              value: avg,
              color: Bs.secondary,
            ),
            StatTile(
              icon: Glyph.question,
              label: "题库",
              value: "${all.length}",
              color: Bs.secondary,
            ),
            StatTile(
              icon: Glyph.mockExam,
              label: "考场",
              value: "${exam.questionCount}题/${exam.minutes}分",
              color: Bs.warning,
            ),
          ],
        ),
        const SizedBox(height: 20),
        _topicHead(context, _topicTitleWidth(context, subject)),
        for (final topic in subject.topics)
          _topicRow(context, subject, topic, _topicTitleWidth(context, subject)),
      ],
    );
  }

  Widget _topicHead(BuildContext context, double titleWidth) {
    final style = Theme.of(context).textTheme.labelMedium
        ?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant);
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          // 数据行标题前面还有个图标（18 + 间距 8），表头得让出同样的宽度，
          // 不然「待练/已掌握/进度」会跟下面的数字、进度条对不上。
          const SizedBox(width: 26),
          SizedBox(width: titleWidth, child: Text("章节", style: style)),
          const SizedBox(width: 12),
          SizedBox(width: 90, child: Text("待练", style: style)),
          const SizedBox(width: 12),
          SizedBox(width: 90, child: Text("已掌握", style: style)),
          const SizedBox(width: 12),
          Expanded(child: Text("进度", style: style)),
        ],
      ),
    );
  }

  Widget _topicRow(BuildContext context, Subject subject, Topic topic, double titleWidth) {
    final questions = _openTopic(subject, topic);
    final pending = _pending(questions);
    final mastered = questions.where((q) => _mastered.contains(q.id)).length;
    final ratio = questions.isEmpty ? 0.0 : mastered / questions.length;
    final enabled = pending.isNotEmpty;
    return InkWell(
      onTap: enabled
          ? () => _startPractice(subject, questions, topic.title)
          : null,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Row(
          children: [
            Icon(
              Glyph.topic,
              size: 18,
              color: enabled ? Bs.paper : Bs.success,
            ),
            const SizedBox(width: 8),
            SizedBox(
              width: titleWidth,
              child: Text(
                pending.isEmpty ? "${topic.title}（已掌握）" : topic.title,
                maxLines: 1,
                style: Theme.of(context).textTheme.bodyLarge
                    ?.copyWith(color: enabled ? null : Bs.secondary),
              ),
            ),
            const SizedBox(width: 12),
            SizedBox(
              width: 90,
              child: Text("${pending.length}"),
            ),
            const SizedBox(width: 12),
            SizedBox(
              width: 90,
              child: Text("$mastered/${questions.length}"),
            ),
            const SizedBox(width: 12),
            _percent(ratio),
            const SizedBox(width: 12),
            Expanded(
              child: BsProgress(
                value: ratio,
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
    final mine = [
      for (final e in _exams)
        if (e.subjectId == subject.id) e,
    ];
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
              const Icon(Glyph.examHistory, size: 22, color: Bs.paper),
              const SizedBox(width: 8),
              Text("模拟考战绩", style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(width: 16),
              Text(
                "考了 ${mine.length} 次 · 最好 $best 分"
                "${streak >= 2 ? " · 连续 $streak 次及格" : ""}",
                style: Theme.of(context).textTheme.bodyMedium
                    ?.copyWith(color: Bs.secondary),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ExamTrend(scores: scores, passScore: subject.exam!.passScore),
        ],
      ),
    );
  }

  static const _noticeIcons = {
    "streak": Glyph.streak,
    "topic": Glyph.topicDone,
    "wrongbook": Glyph.wrongBookCleared,
    "exam-pass": Glyph.achievement,
    "exam-fail": Glyph.examFailed,
  };

  /// 最近解锁的成就/提醒——记了不给人看，等于没记（主仓库 ADR 0052）。
  Widget _recentNotices(BuildContext context) {
    if (_notices.isEmpty) return const SizedBox.shrink();
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
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
              const Icon(Glyph.notice, size: 22, color: Bs.paper),
              const SizedBox(width: 8),
              Text("最近提醒", style: Theme.of(context).textTheme.titleMedium),
            ],
          ),
          const SizedBox(height: 8),
          for (final notice in _notices)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    _noticeIcons[notice.kind] ?? Glyph.notice,
                    size: 18,
                    color: Bs.secondary,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      "${notice.title} · ${notice.body}",
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  /// 掌握度环 + 每日练习柱状图，摆一排——环看整体进度，柱子看有没有断更（ADR 0056）。
  Widget _progressCharts(BuildContext context, Subject subject) {
    final pool = _openPool(subject);
    var mastered = 0;
    var pending = 0;
    var untouched = 0;
    for (final q in pool) {
      if (_mastered.contains(q.id)) {
        mastered++;
      } else if ((_attempts[q.id] ?? 0) > 0) {
        pending++;
      } else {
        untouched++;
      }
    }
    final streak = DailyActivityChart.dayStreak(_daily);
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
      decoration: BoxDecoration(
        color: Bs.body,
        border: Border.all(color: Bs.border),
        borderRadius: BorderRadius.circular(Bs.radius),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          MasteryRing(
            mastered: mastered,
            pending: pending,
            untouched: untouched,
          ),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(
                      Glyph.recentDays,
                      size: 20,
                      color: Bs.paper,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      "最近 14 天",
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(width: 12),
                    Text(
                      streak >= 1 ? "连续练习 $streak 天" : "今天还没练",
                      style: Theme.of(context).textTheme.bodyMedium
                          ?.copyWith(color: Bs.secondary),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                DailyActivityChart(days: _daily),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// 各章节正确率横向对比，最弱的排最上面——该补哪一章一眼看出来（ADR 0056）。
  Widget _topicAccuracyCard(BuildContext context, Subject subject) {
    final ranked = [
      for (final topic in subject.topics)
        (topic, _topicStats[topic.id] ?? const TopicStats(attempts: 0, correct: 0)),
    ]..sort((a, b) => a.$2.rate.compareTo(b.$2.rate));
    if (ranked.isEmpty) return const SizedBox.shrink();
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
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
              const Icon(Glyph.topicAccuracy, size: 20, color: Bs.paper),
              const SizedBox(width: 8),
              Text("各章节正确率", style: Theme.of(context).textTheme.titleMedium),
            ],
          ),
          const SizedBox(height: 12),
          TopicAccuracyChart(
            items: [for (final (topic, stats) in ranked) (topic.title, stats)],
          ),
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
              Icon(Glyph.wrongBook, color: Bs.danger),
              SizedBox(width: 8),
              Text(
                "错题本",
                style: TextStyle(fontSize: 32, fontWeight: FontWeight.w600),
              ),
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
                        icon: times >= 3 ? Glyph.stubborn : Glyph.wrong,
                        color: times >= 3 ? Bs.danger : Bs.warning,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: PromptText(
                          q.prompt,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context).textTheme.bodyLarge,
                        ),
                      ),
                      const SizedBox(width: 12),
                      SerialBadge(q.serial),
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

  /// 考前复习：累计答错 [reviewMinWrong] 次以上的题（ADR 0033）。
  /// 跟错题本的区别：错题本答对一次就移走；这里要最近一次答对、且累计答对
  /// 够 [reviewExitCorrect] 次（比答错多 1～2 次）才移出，再错又回来（ADR 0035）。
  Widget _reviewOverview(BuildContext context) {
    final items = _reviewQuestions;
    final open = [for (final q in items) if (_wrongIds.contains(q.id)) q];
    final fixing = items.length - open.length;
    final s1 = items.where((q) => q.topicId.startsWith("drive.s1.")).length;
    final s4 = items.length - s1;
    final body = Theme.of(context).textTheme.bodyLarge;

    void start(String title, List<Question> questions) => _openSession(
          SessionLaunch(
            title: title,
            subjectId: _reviewId,
            questions: questions,
            timed: false,
            revealImmediately: true,
          ),
        );

    return Padding(
      padding: const EdgeInsets.fromLTRB(36, 28, 36, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Glyph.review, color: Bs.paper),
              SizedBox(width: 8),
              Text(
                "考前复习",
                style: TextStyle(fontSize: 32, fontWeight: FontWeight.w600),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            items.isEmpty
                ? (_reviewGraduated == 0
                    ? "还没有累计答错 $reviewMinWrong 次以上的题。"
                    : "反复错过的 $_reviewGraduated 道都已连对够次数移出了；再错会自动回来。")
                : "累计答错 $reviewMinWrong 次以上的题进这里。答对次数要比答错多 1～2 次（错 2 次对 3 次，错 3 次以上多对 2 次）、且最近一次答对才移出；移出后再错会自动回来。",
            style: body,
          ),
          if (items.isNotEmpty) ...[
            const SizedBox(height: 16),
            Wrap(
              spacing: 10,
              runSpacing: 8,
              children: [
                BsBadge(text: "共 ${items.length} 道", icon: Glyph.review, color: Bs.paper),
                BsBadge(text: "还错着 ${open.length} 道", icon: Glyph.wrong, color: Bs.danger),
                BsBadge(text: "订正中 $fixing 道", icon: Glyph.improving, color: Bs.warning),
                if (_reviewGraduated > 0)
                  BsBadge(text: "已移出 $_reviewGraduated 道", icon: Glyph.graduated, color: Bs.success),
                if (s4 > 0) BsBadge(text: "科目一 $s1 · 科目四 $s4", icon: Glyph.bySubject, color: Bs.secondary),
              ],
            ),
            const SizedBox(height: 20),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                FilledButton(
                  onPressed: () => start("考前复习", items),
                  child: Text("全部复习 ${items.length}"),
                ),
                FilledButton.tonal(
                  onPressed: open.isEmpty ? null : () => start("考前复习 · 还错着的", open),
                  child: Text("只练还错着的 ${open.length}"),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Expanded(
              child: ListView.separated(
                itemCount: items.length,
                separatorBuilder: (_, _) => const Divider(height: 18),
                itemBuilder: (context, i) {
                  final q = items[i];
                  final times = _wrongCounts[q.id] ?? reviewMinWrong;
                  final streak = _reviewStreaks[q.id] ?? 0;
                  final correct = (_attempts[q.id] ?? 0) - times;
                  final need = reviewExitCorrect(times);
                  return Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      SizedBox(
                        width: 150,
                        child: BsBadge(
                          text: times >= 3 ? "错 $times 次 · 顽固" : "错 $times 次",
                          icon: times >= 3 ? Glyph.stubborn : Glyph.wrong,
                          color: times >= 3 ? Bs.danger : Bs.warning,
                        ),
                      ),
                      const SizedBox(width: 8),
                      SizedBox(
                        width: 150,
                        child: BsBadge(
                          text: streak == 0 ? "还错着 · 对 $correct/$need" : "对 $correct/$need",
                          icon: streak == 0 ? Glyph.wrong : Glyph.improving,
                          color: streak == 0 ? Bs.danger : Bs.warning,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: PromptText(
                          q.prompt,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: body,
                        ),
                      ),
                      const SizedBox(width: 12),
                      SerialBadge(q.serial),
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

  /// 易混数字：同类数字并排，配横条比大小，每组能直接练相关题（ADR 0028）。
  Widget _numbersOverview(BuildContext context) {
    final subject = widget.bank.curriculum.subject("subject1");
    final open = dailyQuestions(_subject1All);
    final all = dailyQuestions(_subject1All);
    final muted = Theme.of(context).textTheme.bodyMedium?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
      height: 1.45,
    );
    return ListView(
      padding: const EdgeInsets.fromLTRB(36, 28, 36, 32),
      children: [
        const Row(
          children: [
            Icon(Glyph.numbers, color: Bs.paper),
            SizedBox(width: 8),
            Text("易混数字", style: TextStyle(fontSize: 32, fontWeight: FontWeight.w600)),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          "科目一丢分多在硬数字上。同类数字放在一起看，记住的是它们之间的区别；每组都能直接练相关的题。",
          style: Theme.of(context).textTheme.bodyLarge,
        ),
        for (final group in widget.bank.cheatsheet) ...[
          const SizedBox(height: 28),
          _numberGroup(context, subject, group, open, all, muted),
        ],
      ],
    );
  }

  Widget _numberGroup(
    BuildContext context,
    Subject subject,
    CheatGroup group,
    List<Question> open,
    List<Question> all,
    TextStyle? muted,
  ) {
    final related = group.related(open);
    final pending = _pending(related);
    final locked = group.related(all).length - related.length;
    final maxAmount = group.maxAmount;
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),
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
              Text(group.title, style: Theme.of(context).textTheme.titleLarge),
              if (group.unit.isNotEmpty) ...[
                const SizedBox(width: 10),
                Text(group.unit, style: muted),
              ],
              const Spacer(),
              FilledButton.icon(
                onPressed: pending.isEmpty
                    ? null
                    : () => _startPractice(subject, related, "易混数字 · ${group.title}"),
                icon: const Icon(Glyph.practice, size: 20),
                label: Text(pending.isEmpty ? "这组已掌握" : "练这组 ${pending.length} 题"),
              ),
            ],
          ),
          if (group.note.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(group.note, style: muted),
          ],
          if (locked > 0) ...[
            const SizedBox(height: 4),
            Text("还有 $locked 题在没解锁的阶段里，过关后会加进来。", style: muted),
          ],
          const SizedBox(height: 12),
          for (final row in group.rows)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 190,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          row.value,
                          style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: Bs.paper),
                        ),
                        if (row.amount != null && maxAmount > 0) ...[
                          const SizedBox(height: 4),
                          // 横条长度按本组最大值换算：高低一眼看出来（仓库 ADR 0056）。
                          FractionallySizedBox(
                            alignment: Alignment.centerLeft,
                            widthFactor: (row.amount! / maxAmount).clamp(0.04, 1.0),
                            child: Container(
                              height: 8,
                              decoration: BoxDecoration(
                                color: Bs.paper.withValues(alpha: 0.75),
                                borderRadius: BorderRadius.circular(4),
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(row.caseText, style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.45)),
                        const SizedBox(height: 2),
                        Text("${Bs.sourceShort(row.sourceId)} ${row.locator}", style: muted),
                      ],
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  /// 跨机器同步：日常走云盘文件夹（iCloud Drive 这类），GitHub 那条留着当
  /// 版本历史与异地备份（ADR 0010）。
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

  /// 点了才发现是手误，至少还能反悔——真去抽题、开始计时之前先问一句
  /// （ADR 0019）。有草稿就直接续上（ADR 0043），不走这里。
  Future<bool> _confirmStartTest(String title, int minutes) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text("开始测试"),
        content: Text(
          "「$title」考场时长 $minutes 分钟，这里只计时、到点不收卷。答一题交一题，交了不能改；不及格也继续答完整卷。确定现在开始吗？",
          style: const TextStyle(fontSize: Bs.bodySize, height: 1.45),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(dialogContext).pop(false), child: const Text("再看看")),
          FilledButton(onPressed: () => Navigator.of(dialogContext).pop(true), child: const Text("开始")),
        ],
      ),
    );
    return ok == true;
  }

  Future<void> _startExam(Subject subject) async {
    if (_locked(subject.id)) return;
    final draftKey = "${subject.id}.exam";
    final resumed = await _resumeDraft(draftKey);
    if (resumed != null) {
      _openSession(resumed);
      return;
    }
    if (!mounted) return;
    if (!await _confirmStartTest("${subject.code} 模拟考试", subject.exam!.minutes)) return;
    if (!mounted) return;
    // 不经 dailyQuestions：偏难怪由组卷按上限少量放进来（ADR 0032）。
    final all = widget.bank.forSubject(subject.id);
    final paper = Paper.draw(all, subject.exam!, Random());
    _openSession(
      SessionLaunch(
        title: "${subject.code} 模拟考试",
        subjectId: subject.id,
        questions: paper.questions,
        timed: true,
        minutes: subject.exam!.minutes,
        revealImmediately: false,
        paper: paper,
        draftKey: draftKey,
      ),
    );
  }

  /// 有没有一场没交的模拟考草稿：有就直接续上，不问（ADR 0043）；没有就返回 null，
  /// 照常抽新卷。想换一卷就把这一卷交了。
  Future<SessionLaunch?> _resumeDraft(String draftKey) async {
    final draft = await widget.store.loadExamDraft(draftKey);
    if (draft == null || !mounted) return null;
    final questions = [
      for (final id in draft.questionIds)
        if (widget.bank.questions.any((q) => q.id == id)) widget.bank.byId(id),
    ];
    if (questions.isEmpty) {
      // 题库变了、草稿里的题一道都找不到了——没法续，只能重新开始。
      await widget.store.clearExamDraft(draftKey);
      return null;
    }
    final rules = ExamRules(
      questionCount: draft.questionCount,
      minutes: draft.minutes,
      passScore: draft.passScore,
      pointsPerQuestion: draft.pointsPerQuestion,
      mix: draft.mix,
    );
    return SessionLaunch(
      title: draft.title,
      subjectId: draft.subjectId,
      questions: questions,
      timed: true,
      minutes: draft.minutes,
      revealImmediately: false,
      paper: Paper(
        questions: questions,
        rules: rules,
        fullBank: draft.fullBank,
      ),
      draftKey: draftKey,
      resumePicked: draft.picked,
      // 开考时刻平移到「现在减去上次已用的时间」：挂起的那段不算进用时（ADR 0043）。
      resumeStartedAt: DateTime.now().subtract(draft.spent),
    );
  }

  void _startPractice(Subject subject, List<Question> questions, String title) {
    if (_locked(subject.id)) return;
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
