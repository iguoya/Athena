import "package:athena_driver/study/diagnosis.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/study/reinforce.dart";
import "package:flutter_test/flutter_test.dart";

Question _q(
  String id, {
  String topic = "drive.s1.rules",
  String kind = "single",
  double? rate,
  String ok = "B",
}) {
  final ids = kind == "judge" ? const ["T", "F"] : const ["A", "B", "C", "D"];
  final right = ok.split(",").toSet();
  return Question(
    id: id,
    topicId: topic,
    kind: kind,
    prompt: "题目 $id 的题干",
    errorRate: rate,
    choices: [for (final c in ids) Choice(id: c, label: "选项$c", ok: right.contains(c))],
    explain: "",
    sourceRefs: const [],
  );
}

final _t0 = DateTime(2026, 10, 1, 9);

AttemptView _a(
  String id,
  bool ok, {
  int day = 0,
  int minute = 0,
  int ms = 0,
  String? chosen,
  String kind = "practice",
  String? reason,
  String topic = "drive.s1.rules",
}) =>
    AttemptView(
      questionId: id,
      topicId: topic,
      correct: ok,
      at: DateTime(_t0.year, _t0.month, _t0.day + day, 9, minute),
      durationMs: ms,
      chosen: chosen,
      kind: kind,
      reason: reason,
    );

void main() {
  group("个人遗忘率", () {
    test("只取相邻两次，前一次答对才算，按日历天数分档", () {
      final buckets = forgettingCurve([
        _a("a", true), // 第 0 天对
        _a("a", true, day: 1), // 隔 1 天：对
        _a("a", false, day: 10), // 隔 9 天：错（落在 8～14 天档）
        _a("a", true, day: 11), // 前一次是错的，不算
      ]);
      final byLabel = {for (final b in buckets) b.label: b};
      expect((byLabel["隔 1 天"]!.n, byLabel["隔 1 天"]!.correct), (1, 1));
      expect((byLabel["隔 8～14 天"]!.n, byLabel["隔 8～14 天"]!.correct), (1, 0));
      expect(buckets.fold(0, (s, b) => s + b.n), 2, reason: "总共只有两对相邻且前一次答对");
    });

    test("同一天再答一次算「同一天」档", () {
      final buckets = forgettingCurve([_a("a", true), _a("a", true, minute: 30)]);
      expect(buckets.first.label, "同一天");
      expect((buckets.first.n, buckets.first.correct), (1, 1));
    });

    test("样本不到 15 的档标「样本不足」，不拿来下结论", () {
      final buckets = forgettingCurve([
        for (var i = 0; i < 14; i++) ...[_a("q$i", true), _a("q$i", true, day: 1)],
      ]);
      final d1 = buckets.firstWhere((b) => b.label == "隔 1 天");
      expect(d1.n, 14);
      expect(d1.enough, isFalse);
      final more = forgettingCurve([
        for (var i = 0; i < 15; i++) ...[_a("q$i", true), _a("q$i", false, day: 1)],
      ]).firstWhere((b) => b.label == "隔 1 天");
      expect((more.enough, more.rate), (true, 0.0));
    });

    test("不同题互不串", () {
      final buckets = forgettingCurve([_a("a", true), _a("b", true, day: 1)]);
      expect(buckets.fold(0, (s, b) => s + b.n), 0);
    });
  });

  group("错因分类", () {
    List<AttemptView> baseline() => [for (var i = 0; i < 20; i++) _a("ok$i", true, ms: 10000, minute: i)];

    test("答对的题不到 20 道，没有标尺，不分类", () {
      final report = errorCauses([for (var i = 0; i < 19; i++) _a("ok$i", true, ms: 10000)]);
      expect(report.medianMs, isNull);
      expect(report.wrongTotal, 0);
    });

    test("按自己的中位数分：快而错=粗心，慢而错=不会，居中而错=一般错，答对但慢=不熟", () {
      final report = errorCauses([
        ...baseline(),
        _a("w1", false, ms: 5000, topic: "drive.s1.lights"), // ≤ 6000 → 粗心
        _a("w2", false, ms: 20000, topic: "drive.s1.lights"), // ≥ 16000 → 不会
        _a("w3", false, ms: 10000), // 居中 → 一般错
        _a("s1", true, ms: 20000), // 答对但慢 → 不熟
        _a("s2", true, ms: 12000), // 答对且正常 → 不计
      ]);
      expect(report.medianMs, 10000);
      expect(report.counts[ErrorCause.careless], 1);
      expect(report.counts[ErrorCause.unknown], 1);
      expect(report.counts[ErrorCause.ordinary], 1);
      expect(report.counts[ErrorCause.shaky], 1);
      expect(report.byTopic["drive.s1.lights"]![ErrorCause.careless], 1);
      expect(report.wrongTotal, 3);
    });

    test("用时无效（0 或超过 5 分钟封顶）的作答不参与", () {
      final report = errorCauses([
        ...baseline(),
        _a("w1", false, ms: 0),
        _a("w2", false, ms: 400000),
      ]);
      expect(report.wrongTotal, 0);
      expect(report.sample, 20);
    });
  });

  group("选错的方式", () {
    final bank = {
      "s1": _q("s1", ok: "B"),
      "j1": _q("j1", kind: "judge", ok: "T"),
      "m1": _q("m1", kind: "multi", ok: "A,C"),
    };
    Question? lookup(String id) => bank[id];

    test("没记所选选项的老记录只计入答错总数，不参与分析", () {
      final report = analyzeConfusion([_a("s1", false), _a("s1", false, minute: 1)], lookup);
      expect((report.wrongTotal, report.withChosen, report.hasData), (2, 0, false));
    });

    test("单选题反复选同一个错选项：至少 2 次才算，次数多的在前", () {
      final report = analyzeConfusion([
        _a("s1", false, chosen: "C"),
        _a("s1", false, chosen: "C", minute: 1),
        _a("s1", false, chosen: "C", minute: 2),
        _a("j1", false, chosen: "F"),
        _a("j1", false, chosen: "F", minute: 1),
      ], lookup);
      expect(report.repeated.map((r) => (r.question.id, r.chosen, r.times)), [("s1", "C", 3), ("j1", "F", 2)]);
    });

    test("选了不同的错选项不算反复", () {
      final report = analyzeConfusion([_a("s1", false, chosen: "A"), _a("s1", false, chosen: "C", minute: 1)], lookup);
      expect(report.repeated, isEmpty);
    });

    test("多选题：漏选、多选、两者都有", () {
      final report = analyzeConfusion([
        _a("m1", false, chosen: "A"), // 漏了 C
        _a("m1", false, chosen: "A,B,C", minute: 1), // 多了 B
        _a("m1", false, chosen: "A,B", minute: 2), // 漏 C 且多 B
      ], lookup);
      expect((report.multiMissed, report.multiExtra, report.multiBoth), (1, 1, 1));
    });

    test("答对的和题库里已不存在的题跳过", () {
      final report = analyzeConfusion([_a("s1", true, chosen: "B"), _a("gone", false, chosen: "A")], lookup);
      expect((report.wrongTotal, report.withChosen), (1, 0));
    });
  });

  group("与全国错误率对照", () {
    test("盲区：全国错误率低、我错了至少 2 次；强项：全国易错、我答对 3 次以上", () {
      final bank = {
        "easy": _q("easy", rate: 5),
        "hard": _q("hard", rate: 35),
        "own": _q("own"), // 自编题没有错误率
      };
      final c = publicComparison([
        _a("easy", false), _a("easy", false, minute: 1), _a("easy", true, minute: 2),
        _a("hard", true), _a("hard", true, minute: 1), _a("hard", true, minute: 2),
        _a("own", false),
      ], (id) => bank[id]);
      expect(c.blindSpots.map((g) => g.question.id), ["easy"]);
      expect(c.blindSpots.single.wrong, 2);
      expect(c.strengths.map((g) => g.question.id), ["hard"]);
      expect(c.totalAttempts, 7);
      expect(c.coveredAttempts, 6, reason: "自编题没有全国错误率，不参与比较");
      expect(c.coverage, closeTo(6 / 7, 1e-9));
    });

    test("强项要全对：错过一次就不算；盲区要错够 2 次", () {
      final bank = {"hard": _q("hard", rate: 35), "easy": _q("easy", rate: 5)};
      final c = publicComparison([
        _a("hard", true), _a("hard", true, minute: 1), _a("hard", false, minute: 2),
        _a("easy", false), _a("easy", true, minute: 1),
      ], (id) => bank[id]);
      expect(c.strengths, isEmpty);
      expect(c.blindSpots, isEmpty);
    });

    test("各章相对全国：错得比全国多的排前，样本不到 20 的章不比", () {
      final bank = {for (var i = 0; i < 25; i++) "p$i": _q("p$i", topic: "drive.s1.penalty", rate: 10), "t": _q("t", topic: "drive.s1.tiny", rate: 10)};
      final attempts = [
        // 处罚章：25 次里错 10 次（40%），全国平均 10%
        for (var i = 0; i < 25; i++) _a("p$i", i >= 10, topic: "drive.s1.penalty"),
        _a("t", false, topic: "drive.s1.tiny"),
      ];
      final c = publicComparison(attempts, (id) => bank[id]);
      expect(c.chapters.map((g) => g.topicId), ["drive.s1.penalty"], reason: "tiny 章只有 1 次，不比");
      expect(c.chapters.single.mine, closeTo(0.4, 1e-9));
      expect(c.chapters.single.national, closeTo(0.1, 1e-9));
      expect(c.chapters.single.diff, closeTo(0.3, 1e-9));
    });
  });

  group("强化练习成效", () {
    test("只算强化练习里记了理由的作答，按选题理由分别给答对比例", () {
      final outcomes = reasonOutcomes([
        _a("a", true, kind: "reinforce", reason: "retest"),
        _a("b", false, kind: "reinforce", reason: "retest"),
        _a("c", true, kind: "reinforce", reason: "due"),
        _a("d", true, kind: "practice", reason: "retest"), // 不是强化练习，不算
        _a("e", true, kind: "reinforce"), // 没记理由（升级前），不算
      ]);
      final byReason = {for (final o in outcomes) o.reason: o};
      expect((byReason["retest"]!.n, byReason["retest"]!.correct, byReason["retest"]!.rate), (2, 1, 0.5));
      expect((byReason["due"]!.n, byReason["due"]!.rate), (1, 1.0));
      expect(byReason.containsKey("weak"), isFalse);
      expect(outcomes.map((o) => o.reason), ["retest", "due"], reason: "按固定顺序，不随记录顺序");
    });

    test("没有记录就是空", () {
      expect(reasonOutcomes(const []), isEmpty);
    });

    test("变式差距：复测原题答对率减去同考点变式答对率；两类都有才算得出", () {
      final outcomes = reasonOutcomes([
        for (var i = 0; i < 10; i++) _a("r$i", i < 8, kind: "reinforce", reason: "retest", minute: i), // 8/10
        for (var i = 0; i < 10; i++) _a("v$i", i < 4, kind: "reinforce", reason: "variant", minute: 20 + i), // 4/10
      ]);
      final gap = variantGap(outcomes)!;
      expect(gap.gap, closeTo(0.4, 1e-9), reason: "原题 80%，变式 40%：差 40 个百分点，说明在背题");
      expect(gap.enough, isTrue);
      expect(variantGap(reasonOutcomes([_a("r", true, kind: "reinforce", reason: "retest")])), isNull);
      expect(variantGap(const []), isNull);
      final small = variantGap(reasonOutcomes([
        _a("r", true, kind: "reinforce", reason: "retest"),
        _a("v", false, kind: "reinforce", reason: "variant", minute: 1),
      ]))!;
      expect(small.enough, isFalse, reason: "不到 10 次只当线索");
    });

    test("选题理由的顺序固定：复测、变式、薄弱、到期", () {
      final outcomes = reasonOutcomes([
        _a("a", true, kind: "reinforce", reason: "due"),
        _a("b", true, kind: "reinforce", reason: "variant", minute: 1),
        _a("c", true, kind: "reinforce", reason: "retest", minute: 2),
      ]);
      expect(outcomes.map((o) => o.reason), ["retest", "variant", "due"]);
    });
  });

  test("汇总：一次算出全部统计", () {
    final data = DiagnosisData.build([_a("a", true)], (id) => null);
    expect(data.attempts, 1);
    expect(data.retention, hasLength(6));
    expect(data.causes.medianMs, isNull);
    expect(data.confusion.hasData, isFalse);
    expect(data.comparison.coveredAttempts, 0);
    expect(data.outcomes, isEmpty);
  });

  test("seconds：不到 10 秒留一位小数", () {
    expect(seconds(4200), "4.2 秒");
    expect(seconds(15000), "15 秒");
  });
}
