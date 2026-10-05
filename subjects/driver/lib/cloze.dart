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

/// 把 [text] 里属于答案的数字挖成括号（单位取答案值自带的，没有用 [fallbackUnit]）。
/// [clozeStem] 与 [clozeStemByAsk] 共用：模板代入情形前也要过这一道，免得情形原文里
/// 印着答案（ADR 0103 的泄漏反馈）。
String _maskAnswer(String text, String value, String fallbackUnit) {
  final unit = _unitOf(value) ?? fallbackUnit;
  final numbers = {for (final m in _number.allMatches(value)) m[0]!};
  if (unit.isEmpty) return text;
  var out = text;
  // 长的数字先换，免得 100 里的 10 被先动了。
  for (final n in numbers.toList()..sort((a, b) => b.length - a.length)) {
    // 数字两侧的空格一起吃掉：「方向 150 米」→「方向（　　）米」，中文里不需要那些空格。
    final re = RegExp("\\s*(?<![\\d.])${RegExp.escape(n)}\\s*(?=${RegExp.escape(unit)})");
    out = out.replaceAll(re, clozeBlank);
  }
  return out;
}

/// 题干：把 [caseText] 里**属于答案**的数字挖成括号。
///
/// 只挖带着答案单位的数字（单位取答案值自带的，没有就用组的 [groupUnit]）：同一句里
/// 别的数字是条件、不是答案，不能一起挖——`高速车速超过 100 公里/小时：与同车道前车保持
/// 100 米以上`，答案 100 米，就只挖后面那个 100，速度条件留着。没有可挖的数字（或者单位对不上），
/// 就在句尾补一个括号，题干里绝不会留着答案。
String clozeStem(String caseText, String value, {String groupUnit = "", bool appendBlank = true}) {
  final stem = _maskAnswer(caseText, value, groupUnit);
  final masked = stem != caseText;
  // 手输题下面自己带输入框，不需要在句尾再补括号（appendBlank 为假）。
  return masked || !appendBlank ? stem : "$stem →$clozeBlank";
}

/// 按问法模板出题（ADR 0103）：`{case}` 换成单条情形，`{blank}` 换成挖空。
/// 模板把括号放进句子该在的位置（「饮酒后驾驶，一次记（　　）分。」），不再句尾硬贴
/// 「→（　　）」；情形代入前先做答案挖除——情形原文里印着答案的（酒精组「达到 20、
/// 不到 80」），进题干前挖掉。没有模板的组走 [clozeStem] 老路。
String clozeStemByAsk(String ask, String caseText, String value, {String groupUnit = ""}) {
  return ask.replaceAll("{case}", _maskAnswer(caseText, value, groupUnit)).replaceAll("{blank}", clozeBlank);
}
