import "dart:math";

import "package:athena_driver/models.dart";
import "package:athena_driver/reinforce.dart";
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

AttemptView _a(String id, bool ok, {int day = 0, String kind = "practice"}) => AttemptView(
      questionId: id,
      topicId: "drive.s1.rules",
      correct: ok,
      at: DateTime(_day0.year, _day0.month, _day0.day + day, 9),
      kind: kind,
    );

/// 错 [wrong] 次后，在强化练习里测过且答对（按 ADR 0086 本来足以移出备选库）。
List<AttemptView> _wrongThenReinforced(String id, int wrong) => [
      for (var i = 0; i < wrong; i++) _a(id, false, day: i),
      _a(id, true, day: wrong, kind: "reinforce"),
    ];

void main() {
  // 本应用 ADR 0075：累计答错 3 次（含）以上的题常驻强化练习的备选库。
  group("顽固题常驻强化练习（ADR 0075）", () {
    test("错 2 次、强化练习里答对：照旧移出备选库", () {
      final h = HistorySet.build(_wrongThenReinforced("a", 2));
      expect(h.of("a")!.retiredFromWrongPool, isTrue);
    });

    test("错 3 次、强化练习里答对：不移出，仍在备选库里", () {
      final h = HistorySet.build(_wrongThenReinforced("a", 3));
      expect(h.of("a")!.wrong, 3);
      expect(h.of("a")!.retiredFromWrongPool, isFalse);
    });

    test("计划里：错 3 次的题进备选库，错 2 次已验收的题不进，且备选库计数与移出计数对得上", () {
      final pool = [_q("pinned"), _q("normal"), _q("other")];
      final h = HistorySet.build([
        ..._wrongThenReinforced("pinned", 3),
        ..._wrongThenReinforced("normal", 2),
      ]);
      final plan = planReinforcement(
        pool: pool,
        histories: h,
        now: DateTime(2026, 10, 10),
        random: Random(1),
        count: 3,
      );
      expect(plan.wrongPool, 1, reason: "只有 pinned 在备选库");
      expect(plan.retired, 1, reason: "normal 已验收移出");
      final retest = [for (final p in plan.picks) if (p.reason == "retest") p.question.id];
      expect(retest, ["pinned"]);
    });

    test("反复错题清单：错 3 次以上标 pinned，错 2 次不标", () {
      final byId = {for (final q in [_q("a"), _q("b")]) q.id: q};
      final h = HistorySet.build([..._wrongThenReinforced("a", 3), ..._wrongThenReinforced("b", 2)]);
      final list = {for (final s in stubbornQuestions(h, byId)) s.question.id: s};
      expect(list["a"]!.pinned, isTrue);
      expect(list["b"]!.pinned, isFalse);
    });
  });
}
