import "dart:math";

import "package:flutter/material.dart";

import "exam.dart";
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
  Map<String, TopicStats> _stats = {};
  int _wrongCount = 0;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  Future<void> _reload() async {
    final stats = await widget.store.topicStats();
    final wrong = await widget.store.wrongQuestionIds();
    if (!mounted) return;
    setState(() {
      _stats = stats;
      _wrongCount = wrong.length;
    });
  }

  @override
  Widget build(BuildContext context) {
    final curriculum = widget.bank.curriculum;
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar.large(title: Text(curriculum.title)),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(24, 0, 24, 32),
            sliver: SliverList.list(
              children: [
                Text(curriculum.plainTitle, style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                Text(
                  curriculum.scopeNote,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 24),
                Wrap(
                  spacing: 16,
                  runSpacing: 16,
                  children: [
                    for (final subject in curriculum.subjects)
                      _SubjectCard(
                        subject: subject,
                        count: widget.bank.forSubject(subject.id).length,
                        onOpen: () => _openSubject(subject),
                      ),
                    _WrongCard(count: _wrongCount, onOpen: _openWrongBook),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _openSubject(Subject subject) async {
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (context) => SubjectPage(
          bank: widget.bank,
          store: widget.store,
          subject: subject,
          stats: _stats,
        ),
      ),
    );
    await _reload();
  }

  Future<void> _openWrongBook() async {
    final ids = await widget.store.wrongQuestionIds();
    final questions = [
      for (final id in ids)
        if (widget.bank.questions.any((q) => q.id == id)) widget.bank.byId(id),
    ];
    if (!mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (context) => SessionPage(
          title: "错题本",
          subjectId: "wrong",
          questions: questions,
          store: widget.store,
          timed: false,
          revealImmediately: true,
        ),
      ),
    );
    await _reload();
  }
}

class _SubjectCard extends StatelessWidget {
  const _SubjectCard({
    required this.subject,
    required this.count,
    required this.onOpen,
  });

  final Subject subject;
  final int count;
  final VoidCallback onOpen;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 420,
      child: Card(
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onOpen,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(subject.code, style: Theme.of(context).textTheme.labelLarge),
                const SizedBox(height: 6),
                Text(subject.title, style: Theme.of(context).textTheme.titleLarge),
                if (subject.officialName != null) ...[
                  const SizedBox(height: 4),
                  Text("法规名称：${subject.officialName}", style: Theme.of(context).textTheme.bodySmall),
                ],
                const SizedBox(height: 12),
                Text(
                  "本期 $count 道有出处的题 · 考场 ${subject.exam.questionCount} 题 / ${subject.exam.minutes} 分钟 / ${subject.exam.passScore} 分及格",
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _WrongCard extends StatelessWidget {
  const _WrongCard({required this.count, required this.onOpen});

  final int count;
  final VoidCallback onOpen;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 280,
      child: Card(
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: count == 0 ? null : onOpen,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("错题本", style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                Text(count == 0 ? "最近一次都做对了" : "还有 $count 道最近一次答错"),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class SubjectPage extends StatelessWidget {
  const SubjectPage({
    super.key,
    required this.bank,
    required this.store,
    required this.subject,
    required this.stats,
  });

  final Bank bank;
  final ProgressStore store;
  final Subject subject;
  final Map<String, TopicStats> stats;

  @override
  Widget build(BuildContext context) {
    final all = bank.forSubject(subject.id);
    return Scaffold(
      appBar: AppBar(title: Text("${subject.code} ${subject.title}")),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
        children: [
          FilledButton.icon(
            onPressed: () {
              final paper = Paper.draw(all, subject.exam, Random());
              Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (context) => SessionPage(
                    title: "${subject.code} 模拟考试",
                    subjectId: subject.id,
                    questions: paper.questions,
                    store: store,
                    timed: true,
                    minutes: subject.exam.minutes,
                    revealImmediately: false,
                    paper: paper,
                  ),
                ),
              );
            },
            icon: const Icon(Icons.timer_outlined),
            label: const Text("模拟考试"),
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (context) => SessionPage(
                    title: "${subject.code} 全部练习",
                    subjectId: subject.id,
                    questions: all,
                    store: store,
                    timed: false,
                    revealImmediately: true,
                  ),
                ),
              );
            },
            icon: const Icon(Icons.menu_book_outlined),
            label: Text("顺序练习全部 ${all.length} 题"),
          ),
          const SizedBox(height: 24),
          for (final topic in subject.topics)
            Card(
              child: ListTile(
                title: Text(topic.title),
                subtitle: Text(_topicLine(topic, bank.forTopic(topic.id).length)),
                trailing: const Icon(Icons.chevron_right),
                onTap: bank.forTopic(topic.id).isEmpty
                    ? null
                    : () {
                        Navigator.of(context).push(
                          MaterialPageRoute<void>(
                            builder: (context) => SessionPage(
                              title: topic.title,
                              subjectId: subject.id,
                              questions: bank.forTopic(topic.id),
                              store: store,
                              timed: false,
                              revealImmediately: true,
                            ),
                          ),
                        );
                      },
              ),
            ),
        ],
      ),
    );
  }

  String _topicLine(Topic topic, int count) {
    final stat = stats[topic.id];
    final rate = stat == null ? "尚未作答" : "正确率 ${(stat.rate * 100).round()}% · ${stat.attempts} 次";
    return "$count 题 · ${topic.masteryGoal} · $rate";
  }
}
