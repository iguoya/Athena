import "dart:math";

// 自测四选一的选项生成（ADR 0085、0094）：纯函数，不碰界面，可以单测。
//
// 审查各页真实选项（335 张卡）发现文字类页面的几处硬伤：解释性括号只挂在正确项上（「不是 9 分」
// 「不是终生」），一看就知道选哪个；干扰项又长又离题，光看题干和选项有没有重复字就能猜中近半；
// 干扰项里混着与正确答案意思重叠的，选对选错说不清。这里据此处理：去掉解释性括号、选长度和与题干
// 字面重合都接近正确项的干扰项、排除与本条目任一要点近似的长句。

/// 出题用的条目素材：只含选项生成要的字段，不依赖界面。
class QuizSource {
  const QuizSource({
    required this.id,
    required this.name,
    this.answerTexts = const [],
    this.group,
    this.stemText,
    this.confuseName,
    this.kind,
    this.nearOnly = false,
    this.distractors = const [],
  });

  final String id;

  /// 答案文本（没有 [answerTexts] 时用它）。
  final String name;

  /// 一个情景有多条要点时，每次抽一条考。
  final List<String> answerTexts;

  /// 干扰项的组键：同组优先。
  final String? group;

  /// 题干文字（文字类页面才有）：用来让干扰项与正确项对题干的字面重合接近，免得靠「哪个选项
  /// 和题干重复字多」就能猜中。
  final String? stemText;

  /// 易混对方的名称，永远排在干扰项最前。
  final String? confuseName;

  /// 选项来源的种类：只有种类相同的条目才互相当干扰项（易混数字的「填空选择」与「反向选情形」
  /// 答案一个是数、一个是情形，不能混着当选项）。
  final String? kind;

  /// 只用同组做干扰、不跨组补位：别的组的值放进来是胡扯（把「12 分」放进限速的选项里），
  /// 宁可选项少几个。
  final bool nearOnly;

  /// 内容作者手工指定的干扰项（ADR 0104）：答案格式在组内独一份时（「拘役并处罚金」混在
  /// 刑期选项里），机器选的干扰项盖不住格式差，由作者补同格式的假选项。永远优先入选。
  final List<String> distractors;
}

/// 生成好的一道选择题：正确答案与（已打乱的）选项，两者都是去掉解释括号后的显示文字。
class Quiz {
  const Quiz(this.answer, this.options);
  final String answer;
  final List<String> options;
}

/// 选项上不该出现的解释性括号：只挂在某些条目上的「（不是 9 分）」「（考题按条文答）」「（第二十五条）」，
/// 正确项带、干扰项不带就成了提示。答后右栏仍显示完整原文，这里只管选项。
final _hint = RegExp(r"（(?:不是|考题按|第[^）]{0,14}条|实施条例[^）]{0,14}|注意)[^）]*）");

/// 选项的显示文字：去掉解释性括号和多余空白。
String optionLabel(String text) => text.replaceAll(_hint, "").replaceAll(RegExp(r"\s+"), " ").trim();

Set<String> _grams(String text) {
  final t = text.replaceAll(RegExp(r"[\s，。：；、（）()\-–—/·]"), "");
  return {for (var i = 0; i + 1 < t.length; i++) t.substring(i, i + 2)};
}

/// 两段文字的字面相似度（字二元组的 Jaccard），0～1。
double similarity(String a, String b) {
  final x = _grams(a);
  final y = _grams(b);
  if (x.isEmpty || y.isEmpty) return 0;
  return x.intersection(y).length / x.union(y).length;
}

/// 长句选项的近似门槛：这么像就当成同一个意思，不能互相当干扰项（短名称不受限，
/// 「限制速度 40 / 60」正是要的易混）。
const _nearDuplicate = 0.3;

/// 只差数字的同一个模板句（「车速不超过 40 公里/小时，与前车保持 50 米以上」对「……60……100 米……」）
/// 不算近似：它们由题干里的条件区分，正是要考的易混，要留着。
bool _sameTemplateOtherNumbers(String a, String b) {
  String strip(String t) => t.replaceAll(RegExp(r"[\d.]+"), "");
  return similarity(strip(a), strip(b)) >= 0.85;
}

/// [label] 与 [own]（本条目的某条要点）是不是意思重叠：长句、字面相似、又不是只差数字的模板句。
bool _overlapsMeaning(String own, String label) =>
    own.length >= _shortLabel &&
    label.length >= _shortLabel &&
    similarity(own, label) >= _nearDuplicate &&
    !_sameTemplateOtherNumbers(own, label);

/// 短到不过滤的字数：名称类选项（禁止停车、导流线）不做近似过滤。
const _shortLabel = 12;

class _Candidate {
  _Candidate(this.label, this.score, this.near);
  final String label;
  final double score;
  final bool near;
}

/// 为 [target] 出一道四选一（[count] 个选项）。
///
/// - 正确项：从 [QuizSource.answerTexts] 里随机抽一条（没有就用名称）；
/// - 干扰项取 [pool] 里其他条目的答案文本：易混对方永远排最前，同组优先于跨组，同一档里按
///   「长度与对题干的字面重合都接近正确项」排序再加一点随机；
/// - 排除与任何正确答案相同的文本，长句再排除与本条目任一要点近似的（意思重叠，会让选对选错说不清）；
/// - 凑不满 [count] 个就按实际个数出。
Quiz buildQuiz(QuizSource target, List<QuizSource> pool, {Random? random, int count = 4}) {
  final rng = random ?? Random();
  final answers = target.answerTexts.isEmpty ? [target.name] : target.answerTexts;
  final answer = optionLabel(answers[rng.nextInt(answers.length)]);
  final own = [for (final t in answers) optionLabel(t)];
  final stem = _grams(target.stemText ?? "");
  final correctOverlap = stem.isEmpty ? 0 : stem.intersection(_grams(answer)).length;
  final seen = {...own};
  final options = <String>[answer];

  final confuse = target.confuseName == null ? null : optionLabel(target.confuseName!);
  if (confuse != null && confuse.isNotEmpty && seen.add(confuse)) options.add(confuse);

  // 作者指定的干扰项最优先：它们存在的理由就是盖住答案的格式差。
  for (final raw in target.distractors) {
    final label = optionLabel(raw);
    if (label.isNotEmpty && seen.add(label)) options.add(label);
  }

  final near = <_Candidate>[];
  final far = <_Candidate>[];
  // 干扰项文字不重复；同一段文字先被别组的条目占了位、同组条目也有它时，同组的要顶替上来，
  // 否则 nearOnly 的卡会因为别组撞了同样的值（两组都有「30 日」）丢掉同组的干扰项。
  final taken = <String>{};
  for (final other in pool) {
    if (other.id == target.id || other.kind != target.kind) continue;
    final texts = other.answerTexts.isEmpty ? [other.name] : other.answerTexts;
    final sameGroup = other.group != null && other.group == target.group;
    for (final raw in texts) {
      final label = optionLabel(raw);
      if (label.isEmpty || seen.contains(label)) continue;
      if (own.any((o) => _overlapsMeaning(o, label))) continue;
      if (!taken.add(label)) {
        if (!sameGroup || near.any((c) => c.label == label)) continue;
        far.removeWhere((c) => c.label == label);
      }
      final lenGap = (label.length - answer.length).abs() / max(max(label.length, answer.length), 1);
      final overlapGap = stem.isEmpty
          ? 0.0
          : (stem.intersection(_grams(label)).length - correctOverlap).abs() / (correctOverlap + 3);
      final score = lenGap + overlapGap + rng.nextDouble() * 0.5;
      final cand = _Candidate(label, score, other.group != null && other.group == target.group);
      if (cand.near) {
        near.add(cand);
      } else if (!target.nearOnly) {
        far.add(cand);
      }
    }
  }
  near.sort((a, b) => a.score.compareTo(b.score));
  far.sort((a, b) => a.score.compareTo(b.score));
  options.addAll([for (final c in [...near, ...far]) c.label]);
  return Quiz(answer, options.take(count).toList()..shuffle(rng));
}

/// 数值题的手输答案（易混数字，ADR 0095）：把「小于 200 米」「12 分」「50–100」这样的值拆成
/// 前缀、数字、后缀，题面给前缀和后缀（「小于 [　] 米」「记 [　] 分」），自己敲进数字，不给选项。
class TypedAnswer {
  const TypedAnswer({required this.numbers, required this.prefix, required this.suffix, required this.display});

  /// 期望的数字序列：单个数是一个，区间（50–100）是两个。
  final List<double> numbers;

  /// 输入框前面的字（小于）与后面的字（米、分、个月）。
  final String prefix;
  final String suffix;

  /// 答后显示的标准答案，就是值原文。
  final String display;

  /// 输入是否答对：把输入里的数字按顺序取出来，与期望的数字序列逐个相等。「50-100」「50～100」
  /// 「50 至 100」都行，带不带单位无所谓；只填一个数不算对区间。
  bool matches(String input) {
    final got = [for (final m in _numberToken.allMatches(input)) double.parse(m[0]!)];
    if (got.length != numbers.length) return false;
    for (var i = 0; i < got.length; i++) {
      if (got[i] != numbers[i]) return false;
    }
    return true;
  }
}

final _numberToken = RegExp(r"\d+(?:\.\d+)?");

/// 值的结构：前缀 + 数字（可带区间的第二个数）+ 后缀，中间没有斜杠。
final _typedShape = RegExp(r"^\s*([^\d/]*?)\s*(\d+(?:\.\d+)?)\s*(?:[–—\-~～至到]\s*(\d+(?:\.\d+)?))?\s*([^\d/]*?)\s*$");

/// 值能拆成手输题就返回 [TypedAnswer]，否则 null（终生、拘役并处罚金、「6 年 / 10 年 / 长期」
/// 这类不是一个数，只能走选择）。值自己没带单位就用 [groupUnit]。
TypedAnswer? typedAnswerOf(String value, {String groupUnit = ""}) {
  final m = _typedShape.firstMatch(value);
  if (m == null) return null;
  final numbers = [double.parse(m[2]!), if (m[3] != null) double.parse(m[3]!)];
  final suffix = m[4]!.isNotEmpty ? m[4]! : groupUnit;
  return TypedAnswer(numbers: numbers, prefix: m[1]!, suffix: suffix, display: value);
}
