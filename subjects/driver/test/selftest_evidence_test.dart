import "package:athena_driver/content.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/recall.dart";
import "package:athena_driver/reinforce.dart";
import "package:athena_driver/selftest_store.dart";
import "package:flutter_test/flutter_test.dart";

/// 自测里「认得」的客观依据（ADR 0083）：有相关题的条目，认得只看作答记录；
/// 自测里答对最多得到「自测答对，待做题确认」，答错过的自测答得再对也还是要考；
/// 没有相关题的条目才退回自测作答（ADR 0085 起是选择题对错），同样按间隔回头确认。
void main() {
  late Bank bank;
  late List<Question> related;
  setUpAll(() async {
    bank = await ContentLoader.load();
    related = [for (final q in bank.questions) if (q.sign == "stop") q].take(2).toList();
  });

  final day1 = DateTime(2026, 10, 1, 9);
  HistorySet history(Map<Question, List<(bool, DateTime)>> byQuestion) => HistorySet.build([
    for (final MapEntry(key: q, value: list) in byQuestion.entries)
      for (final (ok, at) in list) AttemptView(questionId: q.id, topicId: "t", correct: ok, at: at),
  ]);

  RecallBucket classify(
    List<Question> rel,
    HistorySet h,
    SelfTestStore store, {
    Set<String> mastered = const {},
  }) => classifyEntry(
    related: rel,
    mastered: mastered,
    histories: h,
    store: store,
    page: "signs",
    id: "stop",
  );

  test("有相关题：没做过是 fresh，只做了一部分是 partial，答错过是 wrong", () {
    final store = SelfTestStore(clock: () => day1);
    expect(classify(related, history({}), store), RecallBucket.fresh);
    expect(
      classify(related, history({related[0]: [(true, day1)]}), store),
      RecallBucket.partial,
      reason: "答对了一道、另一道没做过，不算掌握",
    );
    expect(
      classify(related, history({related[0]: [(false, day1)]}), store),
      RecallBucket.wrong,
    );
  });

  test("自测答对只能得到 selfOnly；作答记录答错过的，自测答得再对也还是 wrong", () {
    final store = SelfTestStore(clock: () => day1);
    store.record("signs", "stop", remembered: true, firstTry: true);
    expect(classify(related, history({}), store), RecallBucket.selfOnly, reason: "自测答对但没有作答证明，先不出");
    expect(
      classify(related, history({related[0]: [(false, day1)]}), store),
      RecallBucket.wrong,
      reason: "客观证据压过自测作答",
    );
  });

  test("作答记录证明掌握才是 known，而且隔多久都还是 known——答对的不再出现（ADR 0090）", () {
    final q = related[0];
    // 先错一次，之后连着两天答对。
    final h = history({
      q: [(false, day1), (true, day1.add(const Duration(days: 1))), (true, day1.add(const Duration(days: 2)))],
    });
    final lastAt = day1.add(const Duration(days: 2));
    for (final later in [2, 30, 400]) {
      final store = SelfTestStore(clock: () => lastAt.add(Duration(days: later)));
      expect(classify([q], h, store, mastered: {q.id}), RecallBucket.known, reason: "隔 $later 天也不回头");
    }
  });

  test("按记录区分：自测答错过的下次再考（wrong），第一次就答对的不再出（selfOnly）", () {
    final store = SelfTestStore(clock: () => day1);
    store.record("signs", "stop", remembered: false, firstTry: true);
    expect(classify(related, history({}), store), RecallBucket.wrong, reason: "答错过，第二次自测再考");
    store.record("signs", "stop", remembered: true, firstTry: true);
    expect(classify(related, history({}), store), RecallBucket.selfOnly, reason: "第二次一次答对，以后不再出");
    expect(recallDrawOrder, isNot(contains(RecallBucket.selfOnly)));
    expect(recallDrawOrder, isNot(contains(RecallBucket.known)));
  });

  test("没有相关题：退回自测作答——答错过 wrong，答对 known 且隔多久都不再出，没考过 fresh", () {
    var now = day1;
    final store = SelfTestStore(clock: () => now);
    final h = history({});
    expect(classify(const [], h, store), RecallBucket.fresh);
    store.record("signs", "stop", remembered: false, firstTry: true);
    expect(classify(const [], h, store), RecallBucket.wrong);
    store.record("signs", "stop", remembered: true, firstTry: true);
    expect(classify(const [], h, store), RecallBucket.known);
    now = now.add(const Duration(days: 400));
    expect(classify(const [], h, store), RecallBucket.known);
  });
}
