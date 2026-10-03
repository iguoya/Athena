import "dart:math";

import "package:athena_driver/clusters.dart";
import "package:athena_driver/content.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/reinforce.dart";
import "package:flutter_test/flutter_test.dart";

Question _q(String id, {String topic = "drive.s1.rules", String band = QuestionBand.common, double? rate}) {
  return Question(
    id: id,
    topicId: topic,
    kind: "judge",
    prompt: "题 $id",
    band: band,
    errorRate: rate,
    choices: const [Choice(id: "T", label: "对", ok: true), Choice(id: "F", label: "错", ok: false)],
    explain: "",
    sourceRefs: const [],
  );
}

final _day0 = DateTime(2026, 10, 1, 9);

/// 在 [day] 天后的 [hour] 点作答。
AttemptView _a(String id, bool ok, {int day = 0, int hour = 9, String topic = "drive.s1.rules"}) => AttemptView(
      questionId: id,
      topicId: topic,
      correct: ok,
      at: DateTime(_day0.year, _day0.month, _day0.day + day, hour),
    );

List<AttemptView> _a2() => [_a("q50", true, day: -3)];

void main() {
  group("掌握度四级", () {
    test("没做过是新题；答错是学习中", () {
      final h = HistorySet.build([_a("a", false)]);
      expect(levelOf(h.of("a")), MasteryLevel.learning);
      expect(levelOf(h.of("没做过")), MasteryLevel.fresh);
    });

    test("同一天连对 2 次是巩固，还不算稳固；隔天后仍对才是稳固", () {
      final sameDay = HistorySet.build([_a("a", true, hour: 9), _a("a", true, hour: 10)]);
      expect(levelOf(sameDay.of("a")), MasteryLevel.consolidating);
      final nextDay = HistorySet.build([_a("a", true), _a("a", true, day: 1)]);
      expect(levelOf(nextDay.of("a")), MasteryLevel.solid);
    });

    test("答错一次，连对清零、稳固作废", () {
      final h = HistorySet.build([_a("a", true), _a("a", true, day: 1), _a("a", false, day: 2), _a("a", true, day: 3)]);
      expect(h.of("a")!.trailingCorrect, 1);
      expect(levelOf(h.of("a")), MasteryLevel.learning);
    });

    test("输入乱序也按时间折叠", () {
      final h = HistorySet.build([_a("a", true, day: 2), _a("a", false, day: 0), _a("a", true, day: 1)]);
      expect(h.of("a")!.lastCorrect, isTrue);
      expect(h.of("a")!.trailingCorrect, 2);
    });

    test("漏斗按题池统计", () {
      final pool = [_q("a"), _q("b"), _q("c"), _q("d")];
      final h = HistorySet.build([_a("a", false), _a("b", true), _a("b", true, day: 1)]);
      final funnel = masteryFunnel(pool, h);
      expect(funnel[MasteryLevel.fresh], 2);
      expect(funnel[MasteryLevel.learning], 1);
      expect(funnel[MasteryLevel.solid], 1);
    });
  });

  group("间隔到期", () {
    test("间隔随连对翻倍：1、2、4、8、16、32，封顶 32", () {
      expect([for (var s = 0; s < 8; s++) intervalFor(s)], [1, 2, 4, 8, 16, 32, 32, 32]);
    });

    test("连对 2 次、隔 4 天到期，隔 3 天还没到", () {
      final h = HistorySet.build([_a("a", true), _a("a", true, hour: 10)]).of("a");
      expect(dueRatio(h, DateTime(2026, 10, 4, 8))!, lessThan(1));
      expect(dueRatio(h, DateTime(2026, 10, 5, 8))!, greaterThanOrEqualTo(1));
    });

    test("按日历天算：昨晚答的题今早就算隔了一天", () {
      final h = HistorySet.build([_a("a", false, hour: 23)]).of("a");
      expect(dueRatio(h, DateTime(2026, 10, 2, 7)), 1.0);
    });

    test("没做过的题没有到期一说", () {
      expect(dueRatio(null, _day0), isNull);
    });
  });

  group("估计量", () {
    test("错题转正率：上一次错、这一次对的比例（样本少时向 0.6 收缩）", () {
      final h = HistorySet.build([
        _a("a", false), _a("a", true, day: 1),
        _a("b", false), _a("b", false, day: 1),
      ]);
      // 2 次机会、1 次转正：(1 + 5*0.6) / (2 + 5)
      expect(h.recoveryRate, closeTo(4 / 7, 1e-9));
      expect(HistorySet.build(const []).recoveryRate, closeTo(0.6, 1e-9));
    });

    test("题目答对概率：近 5 次加章节先验；没做过就是先验", () {
      final h = HistorySet.build([for (var i = 0; i < 5; i++) _a("a", true, day: i)]);
      expect(questionProbability(h.of("a"), 0.5), closeTo((5 + 2 * 0.5) / 7, 1e-9));
      expect(questionProbability(null, 0.62), 0.62);
    });

    test("章节先验：首答错得多的章节更低", () {
      final h = HistorySet.build([
        for (var i = 0; i < 20; i++) _a("x$i", false, topic: "drive.s1.penalty"),
        for (var i = 0; i < 20; i++) _a("y$i", true, topic: "drive.s1.lights"),
      ]);
      final priors = h.chapterPriors();
      expect(priors["drive.s1.penalty"]!, lessThan(priors["drive.s1.lights"]!));
    });
  });

  group("强化练习选题", () {
    final pool = [for (var i = 0; i < 60; i++) _q("q$i", topic: i < 30 ? "drive.s1.penalty" : "drive.s1.lights", rate: i.toDouble())];

    test("新学习者没有任何记录：全部按公开错误率补足，不空手", () {
      final plan = planReinforcement(pool: pool, histories: HistorySet.build(const []), now: _day0, random: Random(1));
      // 没作答的题属于「薄弱」候选（新题），所以新人拿到的是薄弱章节的题而不是 fill。
      expect(plan.picks, hasLength(20));
      expect({for (final p in plan.picks) p.question.id}, hasLength(20), reason: "每题只出一次");
    });

    test("复测优先错得多的；配额是复测 8、薄弱 6、到期 6", () {
      final attempts = <AttemptView>[
        // 8 道错题，其中 q0 错了 3 次
        for (var i = 0; i < 8; i++) _a("q$i", false, topic: "drive.s1.penalty"),
        for (var n = 1; n <= 2; n++) _a("q0", false, day: n, topic: "drive.s1.penalty"),
        // 10 道早就连对 2 次的题，现在到期（隔了 10 天）
        for (var i = 40; i < 50; i++) ...[_a("q$i", true, topic: "drive.s1.lights"), _a("q$i", true, hour: 10, topic: "drive.s1.lights")],
      ];
      final plan = planReinforcement(
        pool: pool,
        histories: HistorySet.build(attempts),
        now: DateTime(2026, 10, 12, 9),
        random: Random(2),
      );
      expect(plan.byReason["retest"], 8);
      expect(plan.byReason["weak"], 6);
      expect(plan.byReason["due"], 6);
      expect(plan.picks.where((p) => p.reason == "retest").map((p) => p.question.id), contains("q0"));
      expect({for (final p in plan.picks) p.question.id}, hasLength(20));
    });

    test("某一类不够，别的类补上，总数仍是 20", () {
      // 没有任何错题、没有到期：全靠薄弱候选
      final h = HistorySet.build([_a("q1", true), _a("q1", true, hour: 10)]);
      final plan = planReinforcement(pool: pool, histories: h, now: _day0, random: Random(3));
      expect(plan.picks, hasLength(20));
      expect(plan.byReason.keys, everyElement(anyOf("weak", "fill")));
    });

    test("题池比题数少就有多少给多少", () {
      final tiny = [_q("a"), _q("b"), _q("c")];
      final plan = planReinforcement(pool: tiny, histories: HistorySet.build(const []), now: _day0, random: Random(4));
      expect(plan.picks, hasLength(3));
    });

    test("薄弱章节的题比强项章节的题更容易被选", () {
      // penalty 章几乎全错，lights 章几乎全对；各章留一批没做过的新题
      final attempts = [
        for (var i = 0; i < 20; i++) _a("q$i", false, topic: "drive.s1.penalty"),
        for (var i = 30; i < 50; i++) _a("q$i", true, topic: "drive.s1.lights"),
      ];
      var weakPenalty = 0;
      var weakLights = 0;
      for (var seed = 0; seed < 30; seed++) {
        final plan = planReinforcement(
          pool: pool,
          histories: HistorySet.build(attempts),
          now: _day0,
          random: Random(seed),
        );
        for (final p in plan.picks.where((p) => p.reason == "weak")) {
          if (p.question.topicId == "drive.s1.penalty") weakPenalty++;
          if (p.question.topicId == "drive.s1.lights") weakLights++;
        }
      }
      expect(weakPenalty, greaterThan(weakLights));
    });
  });

  group("优先章节", () {
    test("弱的章节预计丢分更多，再练 30 分钟挽回得更多", () {
      final pool = [
        for (var i = 0; i < 40; i++) _q("p$i", topic: "drive.s1.penalty"),
        for (var i = 0; i < 40; i++) _q("l$i", topic: "drive.s1.lights"),
      ];
      final h = HistorySet.build([
        for (var i = 0; i < 40; i++) _a("p$i", false, topic: "drive.s1.penalty"),
        for (var i = 0; i < 40; i++) ...[
          _a("l$i", true, topic: "drive.s1.lights"),
          _a("l$i", true, hour: 10, topic: "drive.s1.lights"),
        ],
      ]);
      final ranked = chapterPriorities(pool: pool, histories: h, questionsPerSession: 60);
      expect(ranked.first.topicId, "drive.s1.penalty");
      expect(ranked.first.expectedLoss, greaterThan(ranked.last.expectedLoss));
      expect(ranked.first.unsettled, 40);
      expect(ranked.last.unsettled, 0, reason: "全部巩固的章节没有可挽回的空间");
      expect(ranked.last.recoverable, 0);
    });

    test("预计丢分之和不超过 100", () {
      final pool = [for (var i = 0; i < 50; i++) _q("p$i", topic: i.isEven ? "drive.s1.penalty" : "drive.s1.lights")];
      final ranked = chapterPriorities(pool: pool, histories: HistorySet.build(const []), questionsPerSession: 50);
      expect(ranked.fold<double>(0, (s, c) => s + c.expectedLoss), lessThanOrEqualTo(100));
    });

    test("空题池返回空", () {
      expect(chapterPriorities(pool: const [], histories: HistorySet.build(const []), questionsPerSession: 50), isEmpty);
    });
  });

  group("通过概率", () {
    const rules = ExamRules(questionCount: 100, minutes: 45, passScore: 90, pointsPerQuestion: 1);
    final bank = [for (var i = 0; i < 150; i++) _q("b$i")];

    test("全部稳稳答对：几乎一定及格；全错：几乎一定不及格", () {
      final good = HistorySet.build([
        for (final q in bank)
          for (var d = 0; d < 5; d++) _a(q.id, true, day: d),
      ]);
      final bad = HistorySet.build([
        for (final q in bank)
          for (var d = 0; d < 5; d++) _a(q.id, false, day: d),
      ]);
      final up = estimatePass(bank: bank, rules: rules, histories: good, trials: 100, random: Random(1));
      final down = estimatePass(bank: bank, rules: rules, histories: bad, trials: 100, random: Random(1));
      expect(up.probability, greaterThan(0.95));
      expect(up.coverage, 1.0);
      expect(down.probability, 0.0);
      // 成绩分布很偏时（大多数卷子满分），第 10 百分位可以高于平均值，所以只要求区间有序。
      expect(up.low, lessThanOrEqualTo(up.high));
    });

    test("没有任何记录：覆盖率为 0（说明结果全靠先验，不可信）", () {
      final blank = estimatePass(bank: bank, rules: rules, histories: HistorySet.build(const []), trials: 50, random: Random(1));
      expect(blank.coverage, 0.0);
    });
  });

  group("同考点变式（考点簇，ADR 0079）", () {
    ClusterIndex index(List<List<String>> clusters) => ClusterIndex(clusters, {
          for (var i = 0; i < clusters.length; i++)
            for (final id in clusters[i]) id: i,
        });
    final pool = [for (var i = 0; i < 60; i++) _q("q$i", topic: i < 30 ? "drive.s1.penalty" : "drive.s1.lights", rate: i.toDouble())];
    // q0～q7 答错；它们各有一个同簇的、没做过的变式 q40～q47
    final wrongAttempts = [for (var i = 0; i < 8; i++) _a("q$i", false, topic: "drive.s1.penalty")];
    final clusters = index([for (var i = 0; i < 8; i++) ["q$i", "q${40 + i}"]]);

    test("没有考点簇：和以前一样，没有变式", () {
      final plan = planReinforcement(pool: pool, histories: HistorySet.build(wrongAttempts), now: _day0, random: Random(1));
      expect(plan.byReason.containsKey("variant"), isFalse);
      final empty = planReinforcement(
        pool: pool,
        histories: HistorySet.build(wrongAttempts),
        now: _day0,
        random: Random(1),
        clusters: ClusterIndex.empty,
      );
      expect(empty.byReason.containsKey("variant"), isFalse);
    });

    test("错了的题，各出一个同簇的变式；变式不是错题本身，也没有重复", () {
      final plan = planReinforcement(
        pool: pool,
        histories: HistorySet.build(wrongAttempts),
        now: _day0,
        random: Random(2),
        clusters: clusters,
      );
      final variants = plan.picks.where((p) => p.reason == "variant").map((p) => p.question.id).toList();
      expect(variants.length, greaterThanOrEqualTo(4), reason: "复测配额 8 的一半让给变式");
      for (final id in variants) {
        expect(int.parse(id.substring(1)), inInclusiveRange(40, 47), reason: "$id 是某道错题的同簇变式");
      }
      final ids = plan.picks.map((p) => p.question.id).toList();
      expect(ids.toSet(), hasLength(ids.length), reason: "每题只出一次");
      expect(plan.picks, hasLength(20));
      // 8 道错题仍然都在复测里（配额不够的由补足拿走）
      expect(plan.picks.where((p) => p.reason == "retest"), hasLength(8));
    });

    test("轮流出：4 个变式名额分给 4 道不同的错题，而不是都出自同一道", () {
      final plan = planReinforcement(
        pool: pool,
        histories: HistorySet.build(wrongAttempts),
        now: _day0,
        random: Random(3),
        clusters: index([
          ["q0", "q40", "q41", "q42", "q43"], // 一道错题有很多变式
          for (var i = 1; i < 8; i++) ["q$i", "q${43 + i}"],
        ]),
      );
      final firstFour = plan.picks.where((p) => p.reason == "variant").map((p) => p.question.id).toSet();
      expect(firstFour.where((id) => ["q40", "q41", "q42", "q43"].contains(id)).length, lessThanOrEqualTo(2),
          reason: "不能把名额都给 q0 的变式");
    });

    test("同簇的另一道题本身也是错题：它在复测里，不重复当变式", () {
      final plan = planReinforcement(
        pool: pool,
        histories: HistorySet.build(wrongAttempts),
        now: _day0,
        random: Random(4),
        clusters: index([
          ["q0", "q1"], // 两道都是错题
        ]),
      );
      expect(plan.picks.where((p) => p.reason == "variant"), isEmpty);
    });

    test("没做过的变式排在答对过的前面（新角度更能检验是否真懂）", () {
      final seenCorrect = [_a("q41", true, day: -5), ..._a2()];
      final plan = planReinforcement(
        pool: pool,
        histories: HistorySet.build([_a("q0", false, topic: "drive.s1.penalty"), ...seenCorrect]),
        now: _day0,
        random: Random(5),
        clusters: index([
          ["q0", "q41", "q42"],
        ]),
      );
      final variants = plan.picks.where((p) => p.reason == "variant").map((p) => p.question.id).toList();
      expect(variants.first == "q42" || variants.length == 1 && variants.single == "q42", isTrue,
          reason: "q42 没做过，q41 答对过：先出 q42，得到：$variants");
    });

    test("簇里的变式不在题池里（比如锁着的科目）就不出", () {
      final plan = planReinforcement(
        pool: pool.where((q) => q.id != "q40").toList(),
        histories: HistorySet.build([_a("q0", false, topic: "drive.s1.penalty")]),
        now: _day0,
        random: Random(6),
        clusters: index([
          ["q0", "q40"],
        ]),
      );
      expect(plan.picks.any((p) => p.question.id == "q40"), isFalse);
    });
  });

  testWidgets("真实题库上通过概率几秒内能算完，且新人（无记录）几乎不及格", (tester) async {
    late Bank bank;
    await tester.runAsync(() async => bank = await ContentLoader.load());
    final subject = bank.curriculum.subject("subject1");
    final pool = bank.forSubject("subject1");
    final watch = Stopwatch()..start();
    final estimate = estimatePass(
      bank: pool,
      rules: subject.exam!,
      histories: HistorySet.build(const []),
      trials: 300,
      random: Random(7),
    );
    watch.stop();
    // ignore: avoid_print
    print("真实题库 ${pool.length} 题、300 次抽卷：${watch.elapsedMilliseconds} ms，"
        "及格概率 ${estimate.probability}，平均 ${estimate.mean.toStringAsFixed(1)} 分");
    expect(watch.elapsed, lessThan(const Duration(seconds: 20)));
    expect(estimate.probability, lessThan(0.2));
  });
}
