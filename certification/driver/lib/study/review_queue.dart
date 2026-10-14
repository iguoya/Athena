import "../core/models.dart";

/// 考前复习队列（ADR 0033、0128）：累计答错够次数的题里，还没「已修补」的那些，按该先练的顺序排好。
///
/// 全部由作答记录派生，不另存一张表。独立成纯函数，是为了把排序规则单独测起来——
/// 以前它埋在首页 `_reload()` 里，只能靠整页 widget 测试间接碰到。
class ReviewQueue {
  const ReviewQueue(this.items, this.graduated);

  /// 还留在考前复习里的题，该先练的在前。
  final List<Question> items;

  /// 曾经够格进来、现在已修补移出的题数（再错会自动回来）。
  final int graduated;
}

/// [wrongCounts] 每道题累计答错几次；[attempts] 累计作答几次；[streaks] 最后一次答错之后连对几次。
/// 三者缺省的题按 0 算。
ReviewQueue buildReviewQueue({
  required Iterable<Question> questions,
  required Map<String, int> wrongCounts,
  required Map<String, int> attempts,
  required Map<String, int> streaks,
}) {
  int wrongOf(Question q) => wrongCounts[q.id] ?? 0;
  int correctOf(Question q) => (attempts[q.id] ?? 0) - wrongOf(q);
  bool stillWrong(Question q) => (streaks[q.id] ?? 0) == 0;
  int left(Question q) => correctsToRepair(wrong: wrongOf(q), correct: correctOf(q), lastCorrect: !stillWrong(q));

  final eligible = [
    for (final q in questions)
      if (wrongOf(q) >= reviewMinWrong) q,
  ];
  final review = [
    for (final q in eligible)
      if (inReview(wrongCount: wrongOf(q), correctCount: correctOf(q), streak: streaks[q.id] ?? 0)) q,
  ]..sort((a, b) {
      // 还错着的先练；同样状态下离移出还差得越多越靠前，再按错的次数。
      final byOpen = (stillWrong(b) ? 1 : 0).compareTo(stillWrong(a) ? 1 : 0);
      if (byOpen != 0) return byOpen;
      final byLeft = left(b).compareTo(left(a));
      if (byLeft != 0) return byLeft;
      return wrongOf(b).compareTo(wrongOf(a));
    });
  return ReviewQueue(review, eligible.length - review.length);
}
