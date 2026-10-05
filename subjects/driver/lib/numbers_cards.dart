import "cloze.dart";
import "models.dart";
import "quiz_options.dart";

// 易混数字自测的出卡规划（ADR 0095）：纯函数，不碰界面，可以单测。
//
// 原来只有一种卡——「情形 → 从同组数字里选一个」。它考的是认出来，不是想起来：四个候选数字摆在眼前，
// 蒙都能蒙对一半；而且只考了一个方向，易混数字最要紧的「这个数对应哪几种情形」从没考过。重新规划成
// 三类卡：
//
// 1. 填数（[NumberCardKind.typed]）：题干把数字挖空，下面一个输入框，前后带值自己的前缀和单位
//    （「小于 [　] 米」「记 [　] 分」），自己把数敲进去，不给选项——这才是想起来。
// 2. 选择（[NumberCardKind.choice]）：值不是一个数（终生、拘役并处罚金、「6 年 / 10 年 / 长期」）
//    没法打字，退回同组选择。
// 3. 反向（[NumberCardKind.reverse]）：「12 分」对应的是哪一项？四个选项是同组**别的数值**的单条
//    情形，所以没有也算对的选项。数值种类少于 4 个的组（高速低能见度、血液酒精含量）不出反向卡。

enum NumberCardKind { typed, choice, reverse }

/// 一张易混数字卡的出题素材。
class NumberCard {
  const NumberCard({
    required this.id,
    required this.kind,
    required this.groupId,
    required this.groupTitle,
    required this.stem,
    required this.value,
    required this.caseText,
    required this.sourceId,
    required this.locator,
    this.typed,
    this.answerTexts = const [],
    this.distractors = const [],
  });

  /// 页内稳定的键：「f/组/单条情形|值」（填数、选择）、「r/组/值」（反向）。
  final String id;
  final NumberCardKind kind;
  final String groupId;
  final String groupTitle;

  /// 题干：填数与选择卡是挖空后的单条情形；反向卡是「『12 分』对应的是哪一项？」。
  final String stem;

  /// 填数、选择卡的答案值；反向卡是题面上的值。
  final String value;

  /// 答后给的原文：填数、选择卡是这一行的完整情形；反向卡是这个值下的全部情形。
  final String caseText;
  final String sourceId;
  final String locator;

  /// 填数卡的手输答案；其余为空。
  final TypedAnswer? typed;

  /// 手工指定的干扰项（ADR 0104）。
  final List<String> distractors;

  /// 反向卡的正确答案候选：这个值下所有行的单条情形。
  final List<String> answerTexts;

  /// 选项来源的种类：选择卡之间互相当干扰，反向卡之间互相当干扰，两类不混。
  String get optionKind => kind == NumberCardKind.reverse ? "r" : "f";

  /// 干扰项的组键，只在同组里取。
  String get optionGroup => "$optionKind:$groupId";
}

/// 值加上组单位，反向卡题面用：「12 分」、「30 公里/小时」。值自己带单位就不再补。
String valueWithUnit(String value, String groupUnit) {
  final hasUnit = RegExp(r"[^\d\s.–—\-~～/]").hasMatch(value);
  return hasUnit || groupUnit.isEmpty ? value : "$value $groupUnit";
}

/// 把整份易混数字规划成卡：每行情形按「；」拆成单条，每条一张填数 / 选择卡；每个数值（同值的行
/// 合并）再出一张反向卡。
List<NumberCard> planNumberCards(List<CheatGroup> groups) {
  final cards = <NumberCard>[];
  for (final group in groups) {
    for (final row in group.rows) {
      final typed = typedAnswerOf(row.value, groupUnit: group.unit);
      // 问法：行模板优先，组模板次之；都没有走老路（挖数字、挖不中句尾补）。
      // 手输题同样用模板——括号留在题干里标出空位，答案在下面的输入框里填。
      // 没有模板的手输题题干保持情形原句（appendBlank 为假，输入框就是空）。
      final ask = row.ask ?? group.ask;
      for (final single in splitCase(row.caseText)) {
        cards.add(
          NumberCard(
            id: "f/${group.id}/$single|${row.value}",
            kind: typed != null ? NumberCardKind.typed : NumberCardKind.choice,
            groupId: group.id,
            groupTitle: group.title,
            stem: ask != null
                ? clozeStemByAsk(ask, single, row.value, groupUnit: group.unit)
                : clozeStem(single, row.value, groupUnit: group.unit, appendBlank: typed == null),
            value: row.value,
            caseText: row.caseText,
            sourceId: row.sourceId,
            locator: row.locator,
            typed: typed,
            distractors: row.distractors,
          ),
        );
      }
    }
    // 反向卡：按值合并，同值的行（限速 30、距离 150）的单条情形都算这个值的正确答案。
    // 情形原文里印着这个值时（「现场学习…一次扣减 2 分」），把值挖成括号再当选项——选项
    // 不再自带答案；区间值（50–100）挖完整条都是括号，这种值不出反向卡（ADR 0104）。
    final byValue = <String, List<CheatRow>>{};
    for (final row in group.rows) {
      byValue.putIfAbsent(row.value, () => []).add(row);
    }
    if (byValue.length < 4) continue;
    for (final MapEntry(key: value, value: rows) in byValue.entries) {
      final cases = <String>{for (final row in rows) ...splitCase(row.caseText)}.toList();
      final merged = cases.join("\n");
      final multiNumber = RegExp(r"\d+(?:\.\d+)?").allMatches(value).length > 1;
      if (textContainsValueNumber(merged, value) && multiNumber) continue;
      final maskedCases = [
        for (final t in cases)
          textContainsValueNumber(t, value) ? clozeStem(t, value, groupUnit: group.unit, appendBlank: false) : t,
      ];
      cards.add(
        NumberCard(
          id: "r/${group.id}/$value",
          kind: NumberCardKind.reverse,
          groupId: group.id,
          groupTitle: group.title,
          stem: "「${valueWithUnit(value, group.unit)}」对应的是哪一项？",
          value: value,
          caseText: [for (final row in rows) row.caseText].join("\n"),
          sourceId: rows.first.sourceId,
          locator: rows.first.locator,
          answerTexts: maskedCases,
        ),
      );
    }
  }
  return cards;
}
