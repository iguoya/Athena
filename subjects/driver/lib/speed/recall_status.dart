import "package:flutter/material.dart";

import "../ui/look.dart";
import "../study/reinforce.dart";
// 速记条目、专题与速记组的「作答状态」（ADR 0077、0094、0101、0109、0112）：状态枚举、
// 由作答记录判档的纯函数，以及按状态上色的小部件（状态圆、「练这组」按钮样式）。
// 自测的界面（卡片流、输入、收尾）在 recall.dart，这里不碰界面流程。
//
// 口径（ADR 0112）：专题掌握只由**专题自测**的作答决定——判一张卡、一个条目、一组、
// 一个专题，都只看速记题（`drive.recall.*`）自己的作答记录；关联真题（日常练习）的
// 作答不参与任何掌握判定，真题只是「去做这几个的题」的练习入口。

/// 格子条目的状态微点（ADR 0077 决策 3 起用；ADR 0101 统一为三态、放大为实心圆加黑心，
/// 放在图标下方、条目文字左侧）：红 = 这条的自测题答错过、还在错题库里；绿 = 答对过；
/// 灰 = 没自测过。与易混数字的行点同一套样式。
class StatusDot extends StatelessWidget {
  const StatusDot({super.key, required this.status, this.tooltip});

  final SymbolStatus status;

  /// 覆盖悬停说明的措辞（易混数字的行点写「这一行」，格子默认写「这一条」）。
  final String? tooltip;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      // 答对用亮翠绿：全局 success 色在小圆点上偏暗（使用者反馈）。
      SymbolStatus.wrong => Bs.danger,
      SymbolStatus.mastered => const Color(0xFF2ECC71),
      SymbolStatus.fresh => const Color(0xFFADB5BD),
    };
    return Tooltip(
      message: tooltip ??
          switch (status) {
            SymbolStatus.wrong => "这一条的自测题答错过，还没掌握",
            SymbolStatus.mastered => "这一条的自测题全部答对过",
            SymbolStatus.fresh => "这一条还没测完",
          },
      child: Container(
        width: 28,
        height: 28,
        decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        alignment: Alignment.center,
        child: Container(
          width: 10,
          height: 10,
          decoration: const BoxDecoration(color: Colors.black, shape: BoxShape.circle),
        ),
      ),
    );
  }
}

/// 条目自测题的作答状态。
enum SymbolStatus { wrong, mastered, fresh }

/// 由一组自测题号算状态（ADR 0109、0112、0113）：有答错过且还在错题库里（累计答对没到答错的
/// 2 倍，ADR 0079）→ 红；**每一张都答对过**（整组测完）→ 绿；其余（一张没答过，或只测了一
/// 部分）→ 灰。只答对一部分不算掌握——没测完的组不能写「已掌握」。**只看这些题号自己的
/// 作答**，关联真题（日常练习）不参与。侧栏专题圆、组标题圆、条目微点、「练这组」按钮
/// 都用它，全站一个口径。
SymbolStatus statusOfIds({
  required Iterable<String> ids,
  required HistorySet histories,
}) {
  var total = 0;
  var answered = 0;
  for (final id in ids) {
    total++;
    final h = histories.byQuestion[id];
    if (h == null) continue;
    answered++;
    if (h.wrong > 0 && !h.retiredFromWrongPool) return SymbolStatus.wrong;
  }
  return total > 0 && answered == total ? SymbolStatus.mastered : SymbolStatus.fresh;
}

/// 一组自测卡里「已掌握」的张数与总张数（ADR 0113）：答过且没有未移出错题库的错才算一张。
/// 组圆只有整组测完才绿，进度靠这个「掌握 a/b」看。
({int done, int total}) masteryOf({
  required Iterable<String> ids,
  required HistorySet histories,
}) {
  var total = 0;
  var done = 0;
  for (final id in ids) {
    total++;
    final h = histories.byQuestion[id];
    if (h != null && !(h.wrong > 0 && !h.retiredFromWrongPool)) done++;
  }
  return (done: done, total: total);
}

/// 组标题行里的「掌握 a/b」。
class MasteryTag extends StatelessWidget {
  const MasteryTag({super.key, required this.ids, required this.histories});

  final List<String> ids;
  final HistorySet histories;

  @override
  Widget build(BuildContext context) {
    final m = masteryOf(ids: ids, histories: histories);
    return Padding(
      padding: const EdgeInsets.only(left: 12, top: 6),
      child: Text(
        "掌握 ${m.done}/${m.total}",
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
          color: m.done == m.total && m.total > 0 ? const Color(0xFF2ECC71) : Colors.grey.shade600,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

/// 一张速记卡现在属于哪一档（ADR 0094；ADR 0112 收敛为只看这张卡自己）。**只看作答记录**
/// ——速记卡对应一道有稳定编号的速记题，自测的每次作答和练习、模拟考一样记进作答记录，
/// 错题本、考前复习、强化练习用的是同一份记录；关联真题的作答不参与判档：
/// - [wrong]：这张卡的题答错过、且还在错题库里（累计答对没达到答错的 2 倍，ADR 0079）——最该考；
/// - [fresh]：没有任何记录——还没考过；
/// - [done]：这张卡答对过且没答错过，或错题已经移出错题库——不再出现。
enum RecallBucket { wrong, fresh, done }

/// 自测会抽的档位，按先后顺序。
const recallDrawOrder = [RecallBucket.wrong, RecallBucket.fresh];

/// 判一张卡的档位：只看这张卡自己的作答记录，没答过就是 [RecallBucket.fresh]。
RecallBucket classifyEntry({
  required String questionId,
  required HistorySet histories,
}) {
  return classifyOwn(questionId, histories) ?? RecallBucket.fresh;
}

/// 只按这张卡**自己**的作答记录判档：答错过且还在错题库里（[RecallBucket.wrong]）、
/// 答对过或已移出错题库（[RecallBucket.done]）、没答过返回 null。
/// 专题掌握只由专题自测写入（ADR 0112）：练习里把关联真题全做对不算这张卡掌握，
/// 那是「这组内容你会」，不是「这张卡你在专题里测过」。
RecallBucket? classifyOwn(String questionId, HistorySet histories) {
  final own = histories.byQuestion[questionId];
  if (own == null || own.attempts == 0) return null;
  // 答错过的卡和错题一个规矩：累计答对达到答错的 2 倍才移出错题库（ADR 0079）。
  if (own.wrong > 0) return own.retiredFromWrongPool ? RecallBucket.done : RecallBucket.wrong;
  return RecallBucket.done;
}

/// 速记组右上角「练这组」按钮的颜色（ADR 0109、0112）：随这一组自测卡的作答结果变——
/// 有答错过且还在错题库里 → 红；全部不在错题库（答对过）→ 绿；一张没做过 → 灰。
ButtonStyle practiceButtonStyle(SymbolStatus status) {
  final color = switch (status) {
    SymbolStatus.wrong => Bs.danger,
    SymbolStatus.mastered => const Color(0xFF2ECC71),
    SymbolStatus.fresh => const Color(0xFF8A939B),
  };
  return FilledButton.styleFrom(
    backgroundColor: color,
    foregroundColor: Colors.white,
    // 没有待练题时按钮置灰但保持原色调，不另起一种灰。
    disabledBackgroundColor: color.withValues(alpha: 0.55),
    disabledForegroundColor: Colors.white,
  );
}

/// 侧栏里专题与专题分组左边的状态圆（ADR 0109）：样式同 [StatusDot]（实心圆加黑心、三态色），
/// 只是小一号。红 = 答错过未掌握，绿 = 答对过，灰 = 没做过。
class TopicDot extends StatelessWidget {
  const TopicDot({super.key, required this.status, required this.tooltip, this.size = 16});

  final SymbolStatus status;
  final String tooltip;
  final double size;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      SymbolStatus.wrong => Bs.danger,
      SymbolStatus.mastered => const Color(0xFF2ECC71),
      SymbolStatus.fresh => const Color(0xFFADB5BD),
    };
    return Tooltip(
      message: tooltip,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        alignment: Alignment.center,
        child: Container(
          width: size * 10 / 28,
          height: size * 10 / 28,
          decoration: const BoxDecoration(color: Colors.black, shape: BoxShape.circle),
        ),
      ),
    );
  }
}
