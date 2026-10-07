import "package:athena_driver/core/content.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/speed/recall_status.dart";
import "package:athena_driver/study/reinforce.dart";
import "package:flutter_test/flutter_test.dart";

/// 自测里一张卡还要不要考（ADR 0094、0112）：只看这张速记卡**自己**的作答记录。
/// 速记卡对应一道有稳定编号的题，自测作答和练习、模拟考一样是作答记录；答错过的卡和错题
/// 一个规矩（累计答对达到答错的 2 倍才移出错题库，ADR 0079），答对的不再出现。
/// 关联真题（日常练习）的作答**不参与**判档——专题掌握只由专题自测写入（ADR 0112）。
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

  RecallBucket classify(List<AttemptView> attempts) =>
      classifyEntry(questionId: card, histories: HistorySet.build(attempts));

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

  test("自测收尾的待练题 speedPending：没做过的与错题库里的，偏难一视同仁，做对过一次就不再出（ADR 0115）", () async {
    final bank = await ContentLoader.load();
    final rare = bank.questions.firstWhere((q) => q.isRare);
    final plain = bank.questions.firstWhere((q) => q.isRegular && q.id != rare.id);
    final missed = bank.questions.firstWhere((q) => q.isHot);
    final retired = bank.questions.firstWhere((q) => q.isCommon);
    final histories = HistorySet.build([
      attempt(plain.id, true, 0),
      attempt(missed.id, false, 1),
      attempt(missed.id, true, 2),
      attempt(retired.id, false, 3),
      attempt(retired.id, true, 4),
      attempt(retired.id, true, 5),
    ]);
    final pending = speedPending([rare, plain, missed, retired], histories);
    expect(pending.map((q) => q.id), [missed.id, rare.id], reason: "错题库里的在前、没做过的偏难题其次；做对过的与已移出的不出");
  });

  test("组状态 statusOfIds：整组每张卡都答对才算掌握，只测了一部分是灰（ADR 0113）", () {
    const a = "drive.recall.signs.a";
    const b = "drive.recall.signs.b";
    SymbolStatus status(List<AttemptView> attempts) =>
        statusOfIds(ids: [a, b], histories: HistorySet.build(attempts));

    expect(status([]), SymbolStatus.fresh);
    expect(status([attempt(a, true, 0)]), SymbolStatus.fresh, reason: "只答对一张：没测完");
    expect(status([attempt(a, true, 0), attempt(b, true, 1)]), SymbolStatus.mastered);
    expect(status([attempt(a, true, 0), attempt(b, false, 1)]), SymbolStatus.wrong);
    expect(
      statusOfIds(ids: const [], histories: HistorySet.build([])),
      SymbolStatus.fresh,
      reason: "空组不算掌握",
    );
  });

  test("关联真题的作答不影响判档（ADR 0112）：练得再熟，没在自测里测过的卡照样要考", () {
    final a = related[0];
    final b = related[1];
    // 真题只答对过一部分（未掌握）：卡没自己的记录 → fresh，照样出。
    expect(classify([attempt(a.id, true, 0)]), RecallBucket.fresh);
    // 真题答错过：卡不受牵连 → fresh。
    expect(classify([attempt(a.id, false, 0)]), RecallBucket.fresh);
    // 真题全部掌握：卡没在自测里测过 → 还是 fresh，只有自测能证明掌握。
    expect(
      classify([attempt(a.id, true, 0), attempt(b.id, true, 1)]),
      RecallBucket.fresh,
    );
  });

  test("速记题的作答记录就是普通作答记录：能进强化练习的错题库", () async {
    final bank = await ContentLoader.load();
    final recall = bank.questions.firstWhere((q) => q.id.startsWith("drive.recall.s1.gestures."));
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
