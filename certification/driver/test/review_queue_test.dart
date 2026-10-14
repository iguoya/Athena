import "package:athena_driver/core/models.dart";
import "package:athena_driver/study/review_queue.dart";
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

void main() {
  // 参数：答错 [w] 次，作答共 [n] 次，最后一次答错之后连对 [s] 次。
  ReviewQueue queue(Map<String, (int w, int n, int s)> facts) => buildReviewQueue(
        questions: [for (final id in facts.keys) _q(id)],
        wrongCounts: {for (final e in facts.entries) e.key: e.value.$1},
        attempts: {for (final e in facts.entries) e.key: e.value.$2},
        streaks: {for (final e in facts.entries) e.key: e.value.$3},
      );

  test("只错一次的不进；累计答错 2 次才进", () {
    final out = queue({"once": (1, 1, 0), "twice": (2, 2, 0)});
    expect(out.items.map((q) => q.id), ["twice"]);
    expect(out.graduated, 0);
  });

  test("已修补的移出并计入已移出数：错 2 次、对 4 次且最近一次答对", () {
    final out = queue({"done": (2, 6, 4), "open": (2, 3, 1)});
    expect(out.items.map((q) => q.id), ["open"]);
    expect(out.graduated, 1);
  });

  test("累计答对够数但刚答错：先留着（最近一次答错不放出去）", () {
    final out = queue({"late": (2, 8, 0)});
    expect(out.items.map((q) => q.id), ["late"]);
    expect(out.graduated, 0);
  });

  test("排序：还错着的先练，再按离移出还差几次降序，最后按答错次数降序", () {
    final out = queue({
      "wrong-now": (2, 2, 0), // 还错着，差 4 次
      "close": (2, 5, 3), // 最近答对，对 3 次，差 1 次
      "far": (3, 4, 1), // 最近答对，对 1 次，差 5 次
      "tie-few": (2, 3, 1), // 最近答对，对 1 次，差 3 次
      "tie-many": (3, 7, 1), // 最近答对，对 4 次，差 2 次
    });
    expect(out.items.map((q) => q.id), ["wrong-now", "far", "tie-few", "tie-many", "close"]);
  });

  test("同状态同差距时，答错次数多的在前", () {
    // 都还错着、都没答对过：错 3 次要对 6 次、错 2 次要对 4 次，差得多的在前。
    final out = queue({"two": (2, 2, 0), "three": (3, 3, 0)});
    expect(out.items.map((q) => q.id), ["three", "two"]);
  });

  test("没有任何记录的题不出现", () {
    final out = buildReviewQueue(
      questions: [_q("x")],
      wrongCounts: const {},
      attempts: const {},
      streaks: const {},
    );
    expect(out.items, isEmpty);
    expect(out.graduated, 0);
  });
}
