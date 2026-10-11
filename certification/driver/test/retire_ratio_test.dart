import "dart:math";

import "package:athena_driver/core/models.dart";
import "package:athena_driver/study/reinforce.dart";
import "package:flutter_test/flutter_test.dart";

Question _q(String id) => Question(
      id: id,
      topicId: "drive.s1.rules",
      kind: "judge",
      prompt: "题 $id",
      band: QuestionBand.common,
      choices: const [
        Choice(id: "T", label: "对", ok: true),
        Choice(id: "F", label: "错", ok: false),
      ],
      explain: "",
      sourceRefs: const [],
    );

final _day0 = DateTime(2026, 10, 1, 9);

AttemptView _a(String id, bool ok, int day, {String kind = "practice"}) => AttemptView(
      questionId: id,
      topicId: "drive.s1.rules",
      correct: ok,
      at: DateTime(_day0.year, _day0.month, _day0.day + day, 9),
      kind: kind,
    );

/// 先错 [wrong] 次，再答对 [right] 次。
List<AttemptView> _history(String id, int wrong, int right, {String kind = "practice"}) => [
      for (var i = 0; i < wrong; i++) _a(id, false, i),
      for (var i = 0; i < right; i++) _a(id, true, wrong + i, kind: kind),
    ];

void main() {
  // 本应用 ADR 0079：对的次数达到错的次数的 2 倍，就移出强化练习的备选库；动态，再答错会回来。
  group("强化练习移出规则：对的比错的多一倍（ADR 0079）", () {
    test("临界值：错 1 对 1 不移出，错 1 对 2 移出；错 3 对 5 不移出，错 3 对 6 移出", () {
      bool retired(int wrong, int right) =>
          HistorySet.build(_history("a", wrong, right)).of("a")!.retiredFromWrongPool;
      expect(retired(1, 1), isFalse);
      expect(retired(1, 2), isTrue);
      expect(retired(2, 3), isFalse);
      expect(retired(2, 4), isTrue);
      expect(retired(3, 5), isFalse);
      expect(retired(3, 6), isTrue);
    });

    test("不看在哪里答对：练习、模拟考、强化练习里的答对一视同仁", () {
      for (final kind in ["practice", "exam", "reinforce"]) {
        final h = HistorySet.build(_history("a", 1, 2, kind: kind)).of("a")!;
        expect(h.retiredFromWrongPool, isTrue, reason: kind);
      }
    });

    test("再答错一次，比例掉下去，题自动回到备选库", () {
      final out = HistorySet.build(_history("a", 1, 2)).of("a")!;
      expect(out.retiredFromWrongPool, isTrue);
      final back = HistorySet.build([..._history("a", 1, 2), _a("a", false, 10)]).of("a")!;
      expect(back.wrong, 2);
      expect(back.correct, 2);
      expect(back.retiredFromWrongPool, isFalse);
      expect(back.correctsToRetire, 2);
    });

    test("没答错过的题不在备选库里，也不算移出", () {
      final h = HistorySet.build(_history("a", 0, 5)).of("a")!;
      expect(h.retiredFromWrongPool, isFalse);
      expect(h.correctsToRetire, 0);
    });

    test("计划里：备选库、已移出的计数对得上，抽题只从备选库出", () {
      final pool = [for (var i = 0; i < 6; i++) _q("q$i")];
      final histories = HistorySet.build([
        ..._history("q0", 1, 2), // 移出
        ..._history("q1", 1, 1), // 还要练
        ..._history("q2", 3, 5), // 还要练（差 1 次）
        ..._history("q3", 3, 6), // 移出
        ..._history("q4", 2, 0), // 还要练
      ]);
      final plan = planReinforcement(
        pool: pool,
        histories: histories,
        now: DateTime(2026, 10, 20),
        random: Random(1),
        count: 3,
      );
      expect(plan.wrongPool, 3);
      expect(plan.retired, 2);
      final retest = {for (final p in plan.picks) if (p.reason == "retest") p.question.id};
      expect(retest, {"q1", "q2", "q4"});
    });

    test("反复错题清单：已修补就是已移出，还在错的带「还差几次」", () {
      final byId = {for (final q in [_q("a"), _q("b")]) q.id: q};
      final h = HistorySet.build([..._history("a", 3, 6), ..._history("b", 2, 1)]);
      final list = {for (final s in stubbornQuestions(h, byId)) s.question.id: s};
      expect(list["a"]!.repaired, isTrue);
      expect(list["a"]!.correctsToRetire, 0);
      expect(list["b"]!.repaired, isFalse);
      expect(list["b"]!.correctsToRetire, 3, reason: "错 2 次要对 4 次，已经对了 1 次，还差 3 次");
    });
  });
}
