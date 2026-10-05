import "package:athena_driver/content.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/recall.dart";
import "package:athena_driver/reinforce.dart";
import "package:flutter_test/flutter_test.dart";

/// 自测里一张卡还要不要考（ADR 0094）：只看作答记录。速记卡对应一道有稳定编号的题，自测作答
/// 和练习、模拟考一样是作答记录；答错过的卡和错题一个规矩（累计答对达到答错的 2 倍才移出错题库，
/// ADR 0079），答对的不再出现。没有这张卡自己的记录时，再看它关联的真题答得怎么样。
void main() {
  late List<Question> related;
  setUpAll(() async {
    final bank = await ContentLoader.load();
    related = [for (final q in bank.questions) if (q.sign != null) q].take(2).toList();
  });

  const card = "drive.recall.signs.deadbeef";
  final t0 = DateTime(2026, 10, 1, 9);

  AttemptView attempt(String id, bool ok, int minute) =>
      AttemptView(questionId: id, topicId: "t", correct: ok, at: t0.add(Duration(minutes: minute)));

  RecallBucket classify(List<AttemptView> attempts, {List<Question> rel = const [], Set<String> mastered = const {}}) =>
      classifyEntry(
        questionId: card,
        related: rel,
        mastered: mastered,
        histories: HistorySet.build(attempts),
      );

  test("这张卡自己的记录：没考过 fresh，答对过且没答错 done", () {
    expect(classify([]), RecallBucket.fresh);
    expect(classify([attempt(card, true, 0)]), RecallBucket.done);
    expect(classify([attempt(card, true, 0), attempt(card, true, 1)]), RecallBucket.done);
  });

  test("答错过的卡和错题一个规矩：累计答对达到答错的 2 倍才移出，之后再错又回来", () {
    expect(classify([attempt(card, false, 0)]), RecallBucket.wrong);
    // 答错一次、重现后答对一次：1 < 2 倍，还在错题库里，下次自测还要再考。
    expect(classify([attempt(card, false, 0), attempt(card, true, 1)]), RecallBucket.wrong);
    // 再答对一次：2 ≥ 2 倍，移出，不再出现。
    expect(classify([attempt(card, false, 0), attempt(card, true, 1), attempt(card, true, 2)]), RecallBucket.done);
    // 移出之后又答错：比例掉下去，自动回来。
    expect(
      classify([attempt(card, false, 0), attempt(card, true, 1), attempt(card, true, 2), attempt(card, false, 3)]),
      RecallBucket.wrong,
    );
  });

  test("没有这张卡自己的记录时看关联真题：答错的 wrong、全掌握的 done、做了一部分 partial、没做过 fresh", () {
    final a = related[0];
    final b = related[1];
    expect(classify([], rel: related), RecallBucket.fresh);
    expect(classify([attempt(a.id, true, 0)], rel: related), RecallBucket.partial);
    expect(classify([attempt(a.id, false, 0)], rel: related), RecallBucket.wrong);
    expect(
      classify([attempt(a.id, true, 0), attempt(b.id, true, 1)], rel: related, mastered: {a.id, b.id}),
      RecallBucket.done,
    );
  });

  test("这张卡自己的记录优先于关联真题：卡答对过就不再出现，卡答错过就在错题库里", () {
    final a = related[0];
    expect(classify([attempt(card, true, 0), attempt(a.id, false, 1)], rel: related), RecallBucket.done);
    expect(classify([attempt(card, false, 0), attempt(a.id, true, 1)], rel: related, mastered: {a.id}), RecallBucket.wrong);
  });

  test("速记题的作答记录就是普通作答记录：能进强化练习的错题库", () async {
    final bank = await ContentLoader.load();
    final recall = bank.questions.firstWhere((q) => q.id.startsWith("drive.recall.gestures."));
    final histories = HistorySet.build([attempt(recall.id, false, 0)]);
    final plan = planReinforcement(
      pool: [for (final q in bank.questions) if (q.id == recall.id || q.topicId.startsWith("drive.s1.")) q],
      histories: histories,
      now: t0.add(const Duration(days: 1)),
      clusters: null,
      count: 20,
    );
    expect(plan.wrongPool, 1, reason: "答错的速记题进错题库");
    expect(plan.questions.any((q) => q.id == recall.id), isTrue, reason: "强化练习会抽到它");
  });
}
