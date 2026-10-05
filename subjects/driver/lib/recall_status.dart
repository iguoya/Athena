import "package:flutter/material.dart";

import "look.dart";
import "models.dart";
import "reinforce.dart";

// 速记条目、专题与速记组的「作答状态」（ADR 0077、0094、0101、0109、0110）：状态枚举、
// 由作答记录判档的纯函数，以及按状态上色的小部件（状态圆、「练这组」按钮样式）。
// 自测的界面（卡片流、输入、收尾）在 recall.dart，这里不碰界面流程。

/// 格子条目的状态微点（ADR 0077 决策 3 起用；ADR 0101 统一为三态、放大为实心圆加黑心，
/// 放在图标下方、条目文字左侧）：红 = 相关题最近答错过、未掌握；绿 = 答对过（哪怕只
/// 答对一部分）；灰 = 没作答过。与易混数字的行点同一套样式。
class StatusDot extends StatelessWidget {
  const StatusDot({super.key, required this.status, this.tooltip});

  final SymbolStatus status;

  /// 覆盖悬停说明的措辞（易混数字的行点写「这一行」，格子默认写「相关题」）。
  final String? tooltip;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      // 答对用亮翠绿：全局 success 色在小圆点上偏暗（使用者反馈）。
      SymbolStatus.wrong => Bs.danger,
      SymbolStatus.mastered || SymbolStatus.partial => const Color(0xFF2ECC71),
      SymbolStatus.fresh => const Color(0xFFADB5BD),
    };
    return Tooltip(
      message: tooltip ??
          switch (status) {
            SymbolStatus.wrong => "相关题最近答错过，还没掌握",
            SymbolStatus.mastered => "相关题已答对掌握",
            SymbolStatus.partial => "相关题答对过一部分",
            SymbolStatus.fresh => "相关题还没做过",
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

/// 条目相关题的作答状态。
enum SymbolStatus { wrong, partial, mastered, fresh }

/// 由相关题集合算微点状态：答错优先红，全掌握绿，其余黄，没做过灰。
SymbolStatus statusOf({
  required List<Question> related,
  required Set<String> mastered,
  required HistorySet histories,
}) {
  if (related.isEmpty) return SymbolStatus.fresh;
  final touched = [for (final q in related) if (histories.byQuestion.containsKey(q.id)) q];
  if (touched.isEmpty) return SymbolStatus.fresh;
  if (touched.any((q) => (histories.byQuestion[q.id]?.wrong ?? 0) > 0 && !mastered.contains(q.id))) {
    return SymbolStatus.wrong;
  }
  return related.every((q) => mastered.contains(q.id)) ? SymbolStatus.mastered : SymbolStatus.partial;
}

/// 一张速记卡现在属于哪一档（ADR 0094）。**只看作答记录**——速记卡对应一道有稳定编号的速记题，
/// 自测的每次作答和练习、模拟考一样记进作答记录，错题本、考前复习、强化练习用的是同一份记录：
/// - [wrong]：这张卡的题答错过、且还在错题库里（累计答对没达到答错的 2 倍，ADR 0079）；或者它关联的
///   真题答错过——最该考；
/// - [fresh]：没有任何记录——还没考过；
/// - [partial]：关联的真题只做了一部分、没答错——次之；
/// - [done]：这张卡答对过且没答错过，或错题已经移出错题库，或关联的真题全部答对掌握——不再出现。
enum RecallBucket { wrong, fresh, partial, done }

/// 自测会抽的档位，按先后顺序。
const recallDrawOrder = [RecallBucket.wrong, RecallBucket.fresh, RecallBucket.partial];

/// 判一张卡的档位：先看这张卡自己的作答记录，没有再看关联真题的记录。
RecallBucket classifyEntry({
  required String questionId,
  required List<Question> related,
  required Set<String> mastered,
  required HistorySet histories,
}) {
  final own = classifyOwn(questionId, histories);
  if (own != null) return own;
  if (related.isEmpty) return RecallBucket.fresh;
  return switch (statusOf(related: related, mastered: mastered, histories: histories)) {
    SymbolStatus.wrong => RecallBucket.wrong,
    SymbolStatus.mastered => RecallBucket.done,
    SymbolStatus.partial => RecallBucket.partial,
    SymbolStatus.fresh => RecallBucket.fresh,
  };
}

/// 只按这张卡**自己**的作答记录判档：答错过且还在错题库里（[RecallBucket.wrong]）、
/// 答对过或已移出错题库（[RecallBucket.done]）、没答过返回 null——不看关联真题。
/// 进度反馈用它计数：关联真题的掌握是「这组内容你会」，不是「这张卡你测过」，
/// 混进来会把「已答对」灌成满格（ADR 0097 分科目后易混数字页实际发生过）。
RecallBucket? classifyOwn(String questionId, HistorySet histories) {
  final own = histories.byQuestion[questionId];
  if (own == null || own.attempts == 0) return null;
  // 答错过的卡和错题一个规矩：累计答对达到答错的 2 倍才移出错题库（ADR 0079）。
  if (own.wrong > 0) return own.retiredFromWrongPool ? RecallBucket.done : RecallBucket.wrong;
  return RecallBucket.done;
}

/// 速记组右上角「练这组」按钮的颜色（ADR 0109）：随这一组相关题的作答结果变——
/// 有答错过且还没掌握的 → 红；全部掌握 → 绿；其余（没做过、只做了一部分）→ 灰。
ButtonStyle practiceButtonStyle(SymbolStatus status) {
  final color = switch (status) {
    SymbolStatus.wrong => Bs.danger,
    SymbolStatus.mastered => const Color(0xFF2ECC71),
    SymbolStatus.partial || SymbolStatus.fresh => const Color(0xFF8A939B),
  };
  return FilledButton.styleFrom(backgroundColor: color, foregroundColor: Colors.white);
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
      SymbolStatus.mastered || SymbolStatus.partial => const Color(0xFF2ECC71),
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

/// 一组的「练这组」按钮状态：相关真题与这一组的自测卡**一起**看（ADR 0110）。
/// 任何一道有答错过且最近还没答对 → 红；全部最近答对 → 绿；一道没碰过 → 灰；其余（做了一部分）→ 灰。
SymbolStatus groupStatus({
  required Iterable<String> ids,
  required Set<String> mastered,
  required HistorySet histories,
}) {
  final all = ids.toList();
  if (all.isEmpty) return SymbolStatus.fresh;
  final touched = [for (final id in all) if (histories.byQuestion.containsKey(id)) id];
  if (touched.isEmpty) return SymbolStatus.fresh;
  if (touched.any((id) => (histories.byQuestion[id]?.wrong ?? 0) > 0 && !mastered.contains(id))) {
    return SymbolStatus.wrong;
  }
  return all.every(mastered.contains) ? SymbolStatus.mastered : SymbolStatus.partial;
}
