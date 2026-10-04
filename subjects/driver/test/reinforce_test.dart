import "dart:math";

import "package:athena_driver/clusters.dart";
import "package:athena_driver/content.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/reinforce.dart";
import "package:flutter_test/flutter_test.dart";

Question _q(
  String id, {
  String topic = "drive.s1.rules",
  String band = QuestionBand.common,
  double? rate,
}) {
  return Question(
    id: id,
    topicId: topic,
    kind: "judge",
    prompt: "题 $id",
    band: band,
    errorRate: rate,
    choices: const [
      Choice(id: "T", label: "对", ok: true),
      Choice(id: "F", label: "错", ok: false),
    ],
    explain: "",
    sourceRefs: const [],
  );
}

final _day0 = DateTime(2026, 10, 1, 9);

/// 在 [day] 天后的 [hour] 点作答。
AttemptView _a(
  String id,
  bool ok, {
  int day = 0,
  int hour = 9,
  String topic = "drive.s1.rules",
  String kind = "practice",
  String? reason,
}) => AttemptView(
  questionId: id,
  topicId: topic,
  correct: ok,
  at: DateTime(_day0.year, _day0.month, _day0.day + day, hour),
  kind: kind,
  reason: reason,
);

List<AttemptView> _a2() => [_a("q50", true, day: -3)];

void main() {
  group("反复错题（ADR 0069）", () {
    test("错 1 次不进清单；错 2 次以上按还在错在前、已修补在后，各自按错次降序", () {
      final byId = {for (final q in [_q("a"), _q("b"), _q("c"), _q("d"), _q("e")]) q.id: q};
      final h = HistorySet.build([
        _a("b", false),
        _a("b", false, day: 1),
        _a("b", false, day: 2),
        _a("a", false),
        _a("a", false, day: 1),
        _a("c", false),
        _a("c", false, day: 1),
        for (var i = 0; i < 4; i++) _a("c", true, day: 2 + i),
        _a("d", false),
        _a("e", false),
        _a("e", true, day: 1),
      ]);
      final stubborn = stubbornQuestions(h, byId);
      expect([for (final s in stubborn) s.question.id], ["b", "a", "c"], reason: "b 错 3 次还在错最前，c 已修补最后");
      expect(stubborn[0].repaired, isFalse);
      expect(stubborn[0].wrong, 3);
      expect(stubborn[1].wrong, 2);
      expect(stubborn[2].repaired, isTrue, reason: "c 错 2 次、对 4 次，对的达到错的 2 倍，算已修补");
      expect(stubborn[2].serial, endsWith("c"));
      expect(stubborn[0].correctsToRetire, 6, reason: "b 错 3 次还一次没对：要对 6 次才移出");
      expect(stubborn[1].correctsToRetire, 4);
      expect(stubborn[2].correctsToRetire, 0);
    });

    test("题库改版删掉的题不展示", () {
      final h = HistorySet.build([_a("gone", false), _a("gone", false, day: 1)]);
      expect(stubbornQuestions(h, const {}), isEmpty);
    });
  });

  group("掌握度四级", () {
    test("没做过是新题；答错是学习中", () {
      final h = HistorySet.build([_a("a", false)]);
      expect(levelOf(h.of("a")), MasteryLevel.learning);
      expect(levelOf(h.of("没做过")), MasteryLevel.fresh);
    });

    test("同一天连对 2 次是巩固，还不算稳固；隔天后仍对才是稳固", () {
      final sameDay = HistorySet.build([
        _a("a", true, hour: 9),
        _a("a", true, hour: 10),
      ]);
      expect(levelOf(sameDay.of("a")), MasteryLevel.consolidating);
      final nextDay = HistorySet.build([_a("a", true), _a("a", true, day: 1)]);
      expect(levelOf(nextDay.of("a")), MasteryLevel.solid);
    });

    test("答错一次，连对清零、稳固作废", () {
      final h = HistorySet.build([
        _a("a", true),
        _a("a", true, day: 1),
        _a("a", false, day: 2),
        _a("a", true, day: 3),
      ]);
      expect(h.of("a")!.trailingCorrect, 1);
      expect(levelOf(h.of("a")), MasteryLevel.learning);
    });

    test("输入乱序也按时间折叠", () {
      final h = HistorySet.build([
        _a("a", true, day: 2),
        _a("a", false, day: 0),
        _a("a", true, day: 1),
      ]);
      expect(h.of("a")!.lastCorrect, isTrue);
      expect(h.of("a")!.trailingCorrect, 2);
    });

    test("漏斗按题池统计", () {
      final pool = [_q("a"), _q("b"), _q("c"), _q("d")];
      final h = HistorySet.build([
        _a("a", false),
        _a("b", true),
        _a("b", true, day: 1),
      ]);
      final funnel = masteryFunnel(pool, h);
      expect(funnel[MasteryLevel.fresh], 2);
      expect(funnel[MasteryLevel.learning], 1);
      expect(funnel[MasteryLevel.solid], 1);
    });
  });

  group("间隔到期", () {
    test("间隔随连对翻倍：1、2、4、8、16、32，封顶 32", () {
      expect(
        [for (var s = 0; s < 8; s++) intervalFor(s)],
        [1, 2, 4, 8, 16, 32, 32, 32],
      );
    });

    test("连对 2 次、隔 4 天到期，隔 3 天还没到", () {
      final h = HistorySet.build([_a("a", true), _a("a", true, hour: 10)])
          .of("a");
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
        _a("a", false),
        _a("a", true, day: 1),
        _a("b", false),
        _a("b", false, day: 1),
      ]);
      // 2 次机会、1 次转正：(1 + 5*0.6) / (2 + 5)
      expect(h.recoveryRate, closeTo(4 / 7, 1e-9));
      expect(HistorySet.build(const []).recoveryRate, closeTo(0.6, 1e-9));
    });

    test("题目答对概率：近 5 次加章节先验；没做过就是先验", () {
      final h = HistorySet.build([
        for (var i = 0; i < 5; i++) _a("a", true, day: i),
      ]);
      expect(
        questionProbability(h.of("a"), 0.5),
        closeTo((5 + 2 * 0.5) / 7, 1e-9),
      );
      expect(questionProbability(null, 0.62), 0.62);
    });

    test("章节先验：首答错得多的章节更低", () {
      final h = HistorySet.build([
        for (var i = 0; i < 20; i++)
          _a("x$i", false, topic: "drive.s1.penalty"),
        for (var i = 0; i < 20; i++) _a("y$i", true, topic: "drive.s1.lights"),
      ]);
      final priors = h.chapterPriors();
      expect(priors["drive.s1.penalty"]!, lessThan(priors["drive.s1.lights"]!));
    });
  });

  group("强化练习选题", () {
    final pool = [
      for (var i = 0; i < 60; i++)
        _q(
          "q$i",
          topic: i < 30 ? "drive.s1.penalty" : "drive.s1.lights",
          rate: i.toDouble(),
        ),
    ];

    test("新学习者没有任何记录：全部按公开错误率补足，不空手", () {
      final plan = planReinforcement(
        count: 20,
        pool: pool,
        histories: HistorySet.build(const []),
        now: _day0,
        random: Random(1),
      );
      // 没作答的题属于「薄弱」候选（新题），所以新人拿到的是薄弱章节的题而不是 fill。
      expect(plan.picks, hasLength(20));
      expect(
        {for (final p in plan.picks) p.question.id},
        hasLength(20),
        reason: "每题只出一次",
      );
    });

    test("错题池是答错过、对的还没到错的 2 倍的题：答对过但不够的也在里面；不够一轮才用别的补", () {
      final attempts = <AttemptView>[
        // q0～q7：答错，其中 q0 错了 3 次
        for (var i = 0; i < 8; i++) _a("q$i", false, topic: "drive.s1.penalty"),
        for (var n = 1; n <= 2; n++)
          _a("q0", false, day: n, topic: "drive.s1.penalty"),
        // q8～q15：错过一次，后来只对了一次——对的只有错的 1 倍，还没到 2 倍，仍在备选库里
        for (var i = 8; i < 16; i++) ...[
          _a("q$i", false, topic: "drive.s1.penalty"),
          _a("q$i", true, day: 1, topic: "drive.s1.penalty"),
        ],
      ];
      final plan = planReinforcement(
        count: 20,
        pool: pool,
        histories: HistorySet.build(attempts),
        now: DateTime(2026, 10, 12, 9),
        random: Random(2),
      );
      expect(plan.wrongPool, 16, reason: "历史上答错过的一共 16 道");
      expect(plan.byReason["retest"], 16, reason: "错题池不到一轮，全部都在");
      final ids = plan.picks
          .where((p) => p.reason == "retest")
          .map((p) => p.question.id)
          .toSet();
      expect(ids, containsAll([for (var i = 0; i < 16; i++) "q$i"]));
      expect(plan.picks, hasLength(20));
      expect(
        plan.byReason.keys,
        everyElement(anyOf("retest", "weak", "due")),
        reason: "其余 4 道由薄弱或到期补足",
      );
      expect({for (final p in plan.picks) p.question.id}, hasLength(20));
    });

    test("错题池比一轮大：整轮都从池里抽，每次抽到的不一样，轮流覆盖整个池子", () {
      final attempts = [
        for (var i = 0; i < 40; i++)
          _a("q$i", false, topic: "drive.s1.penalty"),
      ];
      final histories = HistorySet.build(attempts);
      Set<String> draw(int seed) => {
        for (final p in planReinforcement(
          count: 20,
          pool: pool,
          histories: histories,
          now: _day0,
          random: Random(seed),
        ).picks)
          p.question.id,
      };
      final first = planReinforcement(
        count: 20,
        pool: pool,
        histories: histories,
        now: _day0,
        random: Random(1),
      );
      expect(first.byReason, {"retest": 20}, reason: "错题池够大：整轮 20 题都来自错题池");
      expect(first.wrongPool, 40);
      expect(draw(1), isNot(equals(draw(2))), reason: "不同的一次抽取不能是同一批题");
      final covered = <String>{
        for (var seed = 0; seed < 8; seed++) ...draw(seed),
      };
      expect(
        covered.length,
        greaterThan(32),
        reason: "多抽几轮，几乎整个错题池都轮得到，不是总盯着前 20 道",
      );
    });

    test("权重：错得多、最近又错的更容易被抽到；稳固了的轻，但不会消失", () {
      final attempts = <AttemptView>[
        for (var i = 2; i < 40; i++)
          _a("q$i", false, topic: "drive.s1.penalty"),
        // q0：错了 4 次，最近一次还是错
        for (var n = 0; n < 4; n++)
          _a("q0", false, day: n, topic: "drive.s1.penalty"),
        // q1：错过两次，之后隔天连对 3 次，已经稳固（但对的才 3 次，不到错的 2 倍，仍在备选库里）
        _a("q1", false, topic: "drive.s1.penalty"),
        _a("q1", false, hour: 10, topic: "drive.s1.penalty"),
        for (var n = 1; n <= 3; n++)
          _a("q1", true, day: n, topic: "drive.s1.penalty"),
      ];
      final histories = HistorySet.build(attempts);
      var hot = 0;
      var settled = 0;
      for (var seed = 0; seed < 300; seed++) {
        final ids = {
          for (final p in planReinforcement(
            count: 20,
            pool: pool,
            histories: histories,
            now: DateTime(2026, 10, 12),
            random: Random(seed),
          ).picks)
            p.question.id,
        };
        if (ids.contains("q0")) hot++;
        if (ids.contains("q1")) settled++;
      }
      expect(hot, greaterThan(settled), reason: "反复错且最近又错的比稳固了的更常被抽到");
      expect(
        hot,
        greaterThan(180),
        reason: "一轮抽 20/40，平均抽中率是 50%；q0 的权重约是别的两倍，应明显高于平均",
      );
      expect(settled, greaterThan(0), reason: "稳固了的也还有机会被抽检，不会彻底消失");
    });

    test("权重函数：最近又错 > 答对一次 > 连对 > 稳固；错得多、隔得久更重", () {
      final h = HistorySet.build([
        _a("wrong", false),
        _a("once", false),
        _a("once", true, hour: 10),
        _a("run", false),
        _a("run", true, hour: 10),
        _a("run", true, hour: 11),
        _a("solid", false),
        _a("solid", true, day: 1),
        _a("solid", true, day: 2),
        _a("solid", true, day: 3),
        _a("many", false),
        _a("many", false, hour: 10),
        _a("many", false, hour: 11),
        _a("old", false, day: -30),
      ]);
      final now = DateTime(2026, 10, 12);
      double w(String id) => wrongWeight(h.of(id)!, now);
      expect(w("wrong"), greaterThan(w("once")));
      expect(w("once"), greaterThan(w("run")));
      expect(w("run"), greaterThan(w("solid")));
      expect(w("many"), greaterThan(w("wrong")), reason: "错三次比错一次重");
      expect(w("old"), greaterThan(w("wrong")), reason: "隔得越久越重，30 天封顶");
    });

    test("对的次数达到错的次数 2 倍才移出：不论在哪答对都算；再答错、比例掉下去自动回来", () {
      final now = DateTime(2026, 10, 12, 9);
      final plan0 = planReinforcement(
        count: 20,
        pool: pool,
        histories: HistorySet.build([
          // q0：错 1 次、对 3 次 -> 对的是错的 3 倍，移出（在练习里答对也算，不必在强化练习里测）
          _a("q0", false),
          _a("q0", true, day: 1),
          _a("q0", true, day: 2),
          _a("q0", true, day: 3),
          // q1：错 1 次、对 2 次 -> 恰好 2 倍，移出（边界）
          _a("q1", false), _a("q1", true, day: 1), _a("q1", true, day: 2, kind: "reinforce"),
          // q2：错 1 次、对 1 次 -> 只有 1 倍，还要练
          _a("q2", false), _a("q2", true, day: 1, kind: "reinforce"),
          // q3：错 2 次、对 3 次 -> 要对 4 次才够，还要练
          _a("q3", false), _a("q3", false, day: 1),
          _a("q3", true, day: 2), _a("q3", true, day: 3), _a("q3", true, day: 4),
        ]),
        now: now,
        random: Random(1),
      );
      final retest = plan0.picks
          .where((p) => p.reason == "retest")
          .map((p) => p.question.id)
          .toSet();
      expect(retest, containsAll(["q2", "q3"]), reason: "对的还不到错的 2 倍，仍在备选库里");
      expect(retest, isNot(contains("q0")), reason: "q0 对的是错的 3 倍，已移出");
      expect(retest, isNot(contains("q1")), reason: "q1 对的恰好是错的 2 倍，已移出");
      expect(plan0.retired, 2);
      expect(plan0.wrongPool, 2);

      // q1 之后又答错一次：错 2 次、对 2 次，比例掉下去，自动回到备选库
      final back = planReinforcement(
        count: 20,
        pool: pool,
        histories: HistorySet.build([
          _a("q1", false),
          _a("q1", true, day: 1),
          _a("q1", true, day: 2),
          _a("q1", false, day: 3),
        ]),
        now: now,
        random: Random(1),
      );
      expect(back.retired, 0);
      expect(
        back.picks.where((p) => p.reason == "retest").map((p) => p.question.id),
        contains("q1"),
      );
    });

    test("错得越多要对得越多：错 3 次要对 6 次；每多答对一次，还差的次数少一次", () {
      QuestionHistory h(int right) => HistorySet.build([
            for (var i = 0; i < 3; i++) _a("x", false, day: i),
            for (var i = 0; i < right; i++) _a("x", true, day: 3 + i),
          ]).of("x")!;
      expect(h(0).correctsToRetire, 6);
      expect(h(5).correctsToRetire, 1);
      expect(h(5).retiredFromWrongPool, isFalse);
      expect(h(6).correctsToRetire, 0);
      expect(h(6).retiredFromWrongPool, isTrue);
      expect(QuestionHistory.retireRatio, 2);
    });

    test("移出的题不占错题名额：备选库缩小后，名额让给薄弱章节", () {
      // 40 道错题全部答对了 2 次（对的达到错的 2 倍）-> 备选库空了
      final attempts = [
        for (var i = 0; i < 40; i++) ...[
          _a("q$i", false),
          _a("q$i", true, day: 1, kind: "reinforce"),
          _a("q$i", true, day: 2),
        ],
      ];
      final plan = planReinforcement(
        count: 20,
        pool: pool,
        histories: HistorySet.build(attempts),
        now: _day0,
        random: Random(1),
      );
      expect(plan.wrongPool, 0);
      expect(plan.retired, 40);
      expect(plan.byReason.containsKey("retest"), isFalse);
      expect(plan.picks, hasLength(20), reason: "名额由薄弱章节等补足，不会空手");
    });

    test("覆盖保证：每轮都优先给没在强化练习里测过的错题留名额，几轮下来每道都测到", () {
      // 60 道错题，一轮 20 题；每轮把抽到的题当作在强化练习里答对（模拟做完一轮）
      var attempts = [for (var i = 0; i < 60; i++) _a("q$i", false)];
      final everDrawn = <String>{};
      var rounds = 0;
      while (rounds < 12) {
        final histories = HistorySet.build(attempts);
        final plan = planReinforcement(
          count: 20,
          pool: pool,
          histories: histories,
          now: _day0,
          random: Random(rounds),
        );
        if (plan.wrongPool == 0) break;
        // 每一轮至少有名额给没测过的题（覆盖名额：一半向上取整 = 10）
        final fresh = plan.picks
            .where(
              (p) =>
                  histories.of(p.question.id)?.reinforced == 0 &&
                  histories.of(p.question.id)?.wrong != 0,
            )
            .length;
        expect(
          fresh,
          greaterThanOrEqualTo(plan.untested >= 10 ? 10 : plan.untested),
          reason: "第 $rounds 轮",
        );
        for (final p in plan.picks) {
          everDrawn.add(p.question.id);
        }
        attempts = [
          ...attempts,
          for (final p in plan.picks) ...[
            _a(p.question.id, true, day: 1 + rounds, kind: "reinforce"),
            _a(p.question.id, true, day: 1 + rounds, kind: "reinforce"),
          ],
        ];
        rounds++;
      }
      expect(
        rounds,
        lessThanOrEqualTo(8),
        reason: "60 道题、每轮至少 10 个新的覆盖名额，几轮就都答对到够次数移出",
      );
      for (var i = 0; i < 60; i++) {
        expect(everDrawn, contains("q$i"), reason: "q$i 从没在强化练习里出现过就不该移出");
      }
    });

    test("某一类不够，别的类补上，总数仍是 20", () {
      // 没有任何错题、没有到期：全靠薄弱候选
      final h = HistorySet.build([_a("q1", true), _a("q1", true, hour: 10)]);
      final plan = planReinforcement(
        count: 20,
        pool: pool,
        histories: h,
        now: _day0,
        random: Random(3),
      );
      expect(plan.picks, hasLength(20));
      expect(plan.byReason.keys, everyElement(anyOf("weak", "fill")));
    });

    test("题池比题数少就有多少给多少", () {
      final tiny = [_q("a"), _q("b"), _q("c")];
      final plan = planReinforcement(
        count: 20,
        pool: tiny,
        histories: HistorySet.build(const []),
        now: _day0,
        random: Random(4),
      );
      expect(plan.picks, hasLength(3));
    });

    test("薄弱章节的题比强项章节的题更容易被选", () {
      // penalty 章几乎全错，lights 章几乎全对；各章留一批没做过的新题
      final attempts = [
        for (var i = 0; i < 20; i++)
          _a("q$i", false, topic: "drive.s1.penalty"),
        for (var i = 30; i < 50; i++) _a("q$i", true, topic: "drive.s1.lights"),
      ];
      var weakPenalty = 0;
      var weakLights = 0;
      for (var seed = 0; seed < 30; seed++) {
        // 20 道错题全进错题池；一轮放大到 40 题，后 20 题由薄弱章节补足，才看得出补的偏向哪一章
        final plan = planReinforcement(
          pool: pool,
          histories: HistorySet.build(attempts),
          now: _day0,
          random: Random(seed),
          count: 40,
        );
        for (final p in plan.picks.where((p) => p.reason == "weak")) {
          if (p.question.topicId == "drive.s1.penalty") weakPenalty++;
          if (p.question.topicId == "drive.s1.lights") weakLights++;
        }
      }
      // penalty 章只有 10 道没做过的候选，lights 章有 30 道：比的是「候选被补中的比例」，不是个数
      final penaltyRate = weakPenalty / (10 * 30);
      final lightsRate = weakLights / (30 * 30);
      expect(penaltyRate, greaterThan(lightsRate), reason: "薄弱章节的候选更容易被补中");
    });
  });

  group("优先章节", () {
    test("弱的章节预计丢分更多，再练 30 分钟挽回得更多", () {
      final pool = [
        for (var i = 0; i < 40; i++) _q("p$i", topic: "drive.s1.penalty"),
        for (var i = 0; i < 40; i++) _q("l$i", topic: "drive.s1.lights"),
      ];
      final h = HistorySet.build([
        for (var i = 0; i < 40; i++)
          _a("p$i", false, topic: "drive.s1.penalty"),
        for (var i = 0; i < 40; i++) ...[
          _a("l$i", true, topic: "drive.s1.lights"),
          _a("l$i", true, hour: 10, topic: "drive.s1.lights"),
        ],
      ]);
      final ranked = chapterPriorities(
        pool: pool,
        histories: h,
        questionsPerSession: 60,
      );
      expect(ranked.first.topicId, "drive.s1.penalty");
      expect(ranked.first.expectedLoss, greaterThan(ranked.last.expectedLoss));
      expect(ranked.first.unsettled, 40);
      expect(ranked.last.unsettled, 0, reason: "全部巩固的章节没有可挽回的空间");
      expect(ranked.last.recoverable, 0);
    });

    test("预计丢分之和不超过 100", () {
      final pool = [
        for (var i = 0; i < 50; i++)
          _q("p$i", topic: i.isEven ? "drive.s1.penalty" : "drive.s1.lights"),
      ];
      final ranked = chapterPriorities(
        pool: pool,
        histories: HistorySet.build(const []),
        questionsPerSession: 50,
      );
      expect(
        ranked.fold<double>(0, (s, c) => s + c.expectedLoss),
        lessThanOrEqualTo(100),
      );
    });

    test("空题池返回空", () {
      expect(
        chapterPriorities(
          pool: const [],
          histories: HistorySet.build(const []),
          questionsPerSession: 50,
        ),
        isEmpty,
      );
    });
  });

  group("通过概率", () {
    const rules = ExamRules(
      questionCount: 100,
      minutes: 45,
      passScore: 90,
      pointsPerQuestion: 1,
    );
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
      final up = estimatePass(
        bank: bank,
        rules: rules,
        histories: good,
        trials: 100,
        random: Random(1),
      );
      final down = estimatePass(
        bank: bank,
        rules: rules,
        histories: bad,
        trials: 100,
        random: Random(1),
      );
      expect(up.probability, greaterThan(0.95));
      expect(up.coverage, 1.0);
      expect(down.probability, 0.0);
      // 成绩分布很偏时（大多数卷子满分），第 10 百分位可以高于平均值，所以只要求区间有序。
      expect(up.low, lessThanOrEqualTo(up.high));
    });

    test("没有任何记录：覆盖率为 0（说明结果全靠先验，不可信）", () {
      final blank = estimatePass(
        bank: bank,
        rules: rules,
        histories: HistorySet.build(const []),
        trials: 50,
        random: Random(1),
      );
      expect(blank.coverage, 0.0);
    });
  });

  group("同考点变式（考点簇，ADR 0079）", () {
    ClusterIndex index(List<List<String>> clusters) => ClusterIndex(clusters, {
      for (var i = 0; i < clusters.length; i++)
        for (final id in clusters[i]) id: i,
    });
    final pool = [
      for (var i = 0; i < 60; i++)
        _q(
          "q$i",
          topic: i < 30 ? "drive.s1.penalty" : "drive.s1.lights",
          rate: i.toDouble(),
        ),
    ];
    // q0～q7 答错；它们各有一个同簇的、没做过的变式 q40～q47
    final wrongAttempts = [
      for (var i = 0; i < 8; i++) _a("q$i", false, topic: "drive.s1.penalty"),
    ];
    final clusters = index([
      for (var i = 0; i < 8; i++) ["q$i", "q${40 + i}"],
    ]);

    test("没有考点簇：和以前一样，没有变式", () {
      final plan = planReinforcement(
        count: 20,
        pool: pool,
        histories: HistorySet.build(wrongAttempts),
        now: _day0,
        random: Random(1),
      );
      expect(plan.byReason.containsKey("variant"), isFalse);
      final empty = planReinforcement(
        count: 20,
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
        count: 20,
        pool: pool,
        histories: HistorySet.build(wrongAttempts),
        now: _day0,
        random: Random(2),
        clusters: clusters,
      );
      final variants = plan.picks
          .where((p) => p.reason == "variant")
          .map((p) => p.question.id)
          .toList();
      expect(
        variants.length,
        greaterThanOrEqualTo(4),
        reason: "复测配额 8 的一半让给变式",
      );
      for (final id in variants) {
        expect(
          int.parse(id.substring(1)),
          inInclusiveRange(40, 47),
          reason: "$id 是某道错题的同簇变式",
        );
      }
      final ids = plan.picks.map((p) => p.question.id).toList();
      expect(ids.toSet(), hasLength(ids.length), reason: "每题只出一次");
      expect(plan.picks, hasLength(20));
      // 8 道错题仍然都在复测里（配额不够的由补足拿走）
      expect(plan.picks.where((p) => p.reason == "retest"), hasLength(8));
    });

    test("轮流出：4 个变式名额分给 4 道不同的错题，而不是都出自同一道", () {
      final plan = planReinforcement(
        count: 20,
        pool: pool,
        histories: HistorySet.build(wrongAttempts),
        now: _day0,
        random: Random(3),
        clusters: index([
          ["q0", "q40", "q41", "q42", "q43"], // 一道错题有很多变式
          for (var i = 1; i < 8; i++) ["q$i", "q${43 + i}"],
        ]),
      );
      final firstFour = plan.picks
          .where((p) => p.reason == "variant")
          .map((p) => p.question.id)
          .toSet();
      expect(
        firstFour
            .where((id) => ["q40", "q41", "q42", "q43"].contains(id))
            .length,
        lessThanOrEqualTo(2),
        reason: "不能把名额都给 q0 的变式",
      );
    });

    test("同簇的另一道题本身也是错题：它在复测里，不重复当变式", () {
      final plan = planReinforcement(
        count: 20,
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
      // 一轮 4 题，变式名额只有 1 个：该给没做过的 q42，而不是答对过的 q41
      final plan = planReinforcement(
        pool: pool,
        histories: HistorySet.build([
          _a("q0", false, topic: "drive.s1.penalty"),
          ...seenCorrect,
        ]),
        now: _day0,
        random: Random(5),
        count: 4,
        clusters: index([
          ["q0", "q41", "q42"],
        ]),
      );
      final variants = plan.picks
          .where((p) => p.reason == "variant")
          .map((p) => p.question.id)
          .toList();
      expect(variants, ["q42"], reason: "q42 没做过，q41 答对过：名额只有一个，先给 q42");
    });

    test("簇里的变式不在题池里（比如锁着的科目）就不出", () {
      final plan = planReinforcement(
        count: 20,
        pool: pool.where((q) => q.id != "q40").toList(),
        histories: HistorySet.build([
          _a("q0", false, topic: "drive.s1.penalty"),
        ]),
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
    print(
      "真实题库 ${pool.length} 题、300 次抽卷：${watch.elapsedMilliseconds} ms，"
      "及格概率 ${estimate.probability}，平均 ${estimate.mean.toStringAsFixed(1)} 分",
    );
    expect(watch.elapsed, lessThan(const Duration(seconds: 20)));
    expect(estimate.probability, lessThan(0.2));
  });
}
