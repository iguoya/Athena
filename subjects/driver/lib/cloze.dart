// 易混数字自测的出题（ADR 0092）：把要考的数字从题干里挖掉，改成括号。
//
// 原来题干直接用「情形」原文，而原文里常常就写着答案——距离一组「警告标志设在来车方向
// 150 米以外」，答案选项里就有 150，等于送分；记分一组的情形又是五六条违法行为的长清单，
// 不是一个能考记忆的问题。所以：长清单按「；」拆成单条，每条自成一题；题干里属于答案的
// 那个数字换成括号，原文里没有数字可挖的，就在句尾补一个括号。

/// 题干里挖掉数字的位置。全角空格撑出一点宽度，一眼看出是空。
const clozeBlank = "（　　）";

/// 把一行「情形」按「；」拆成单条情形（去空白、去空串）。没有「；」就是它自己。
List<String> splitCase(String caseText) => [
  for (final part in caseText.split(RegExp(r"[；;]")))
    if (part.trim().isNotEmpty) part.trim(),
];

final _number = RegExp(r"\d+(?:\.\d+)?");

/// 答案值自带的单位：`小于 200 米` → 米，`12 分` → 分；纯数字或区间（`50–100`）没有。
String? _unitOf(String value) {
  final m = RegExp(r"[\d.]+\s*([^\d.\s–—\-~～至到]+)\s*$").firstMatch(value);
  return m?[1];
}

/// 题干：把 [caseText] 里**属于答案**的数字挖成括号。
///
/// 只挖带着答案单位的数字（单位取答案值自带的，没有就用组的 [groupUnit]）：同一句里
/// 别的数字是条件、不是答案，不能一起挖——`高速车速超过 100 公里/小时：与同车道前车保持
/// 100 米以上`，答案 100 米，就只挖后面那个 100，速度条件留着。没有可挖的数字（或者单位对不上），
/// 就在句尾补一个括号，题干里绝不会留着答案。
String clozeStem(String caseText, String value, {String groupUnit = ""}) {
  final unit = _unitOf(value) ?? groupUnit;
  final numbers = {for (final m in _number.allMatches(value)) m[0]!};
  var stem = caseText;
  var masked = false;
  if (unit.isNotEmpty) {
    // 长的数字先换，免得 100 里的 10 被先动了。
    for (final n in numbers.toList()..sort((a, b) => b.length - a.length)) {
      // 数字两侧的空格一起吃掉：「方向 150 米」→「方向（　　）米」，中文里不需要那些空格。
      final re = RegExp("\\s*(?<![\\d.])${RegExp.escape(n)}\\s*(?=${RegExp.escape(unit)})");
      if (re.hasMatch(stem)) {
        stem = stem.replaceAll(re, clozeBlank);
        masked = true;
      }
    }
  }
  return masked ? stem : "$stem →$clozeBlank";
}
