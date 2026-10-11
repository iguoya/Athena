import "dart:math";

import "cloze.dart";
import "../core/models.dart";
import "numbers_cards.dart";
import "quiz_options.dart";
import "speed_topics.dart";
// 速记卡的统一定义（ADR 0094）：自测界面的条目、题库里的「速记题」都从它生成，两边一致。
//
// 自测的每次作答要和练习、模拟考一样记进作答记录——这样错题本、考前复习、强化练习不用改逻辑，
// 就能带出自测里答错的内容。要让这些功能认得它，每张卡得是一道有稳定编号的题：
// `drive.recall.<页>.<键哈希>`。题的出处取各速记文件的文件级出处（条目有逐条出处的用逐条的）。

/// 速记题的知识点号前缀：不在课表里，所以科目一 / 科目四的日常题、章节练习、模拟考、解锁判断都不会带上它；
/// 错题本、考前复习、强化练习按这个前缀把它并进来。
const recallTopicPrefix = "drive.recall.";

/// 题号是不是速记题。
bool isRecallQuestionId(String id) => id.startsWith(recallTopicPrefix);

/// 稳定的短哈希（FNV-1a 32 位）：条目键里有中文、斜杠，不能直接拼进题号。
String _fnv(String text) {
  var hash = 0x811c9dc5;
  for (final unit in text.codeUnits) {
    hash ^= unit;
    hash = (hash * 0x01000193) & 0xffffffff;
  }
  return hash.toRadixString(16).padLeft(8, "0");
}

/// 一张速记卡对应的题号。
String recallQuestionId(String page, String entryKey) => "$recallTopicPrefix$page.${_fnv(entryKey)}";

/// 一张速记卡：没有任何界面对象，纯数据。
class RecallCard {
  const RecallCard({
    required this.page,
    required this.id,
    required this.name,
    required this.meaning,
    required this.sourceId,
    this.locator = "",
    this.answerTexts = const [],
    this.group,
    this.confuseName,
    this.confuseNote,
    this.stemText,
    this.prompt,
    this.stem,
    this.imagePath,
    this.typed,
    this.kind,
    this.nearOnly = false,
    this.inputLabel,
    this.distractors = const [],
  });

  /// 速记页的键（[RecallPage]）与页内稳定的条目键。
  final String page;
  final String id;

  /// 答案标题与答后说明。
  final String name;
  final String meaning;

  /// 出处：文件级的 `source_id`，逐条有出处的再带条款位置。
  final String sourceId;
  final String locator;

  /// 选择题的正确答案候选（空则用 [name]）与干扰项的组键、易混对方。
  final List<String> answerTexts;
  final String? group;
  final String? confuseName;
  final String? confuseNote;

  /// 题干文字：要点类页面的情景原文（干扰项选取据此）；图片类页面没有。
  final String? stemText;

  /// 本卡自己的提问句；空则用页面默认的。
  final String? prompt;

  /// 题干（要点类是情景、数字类是挖空后的情形），与题图二选一。
  final String? stem;
  final String? imagePath;

  /// 数值卡（易混数字）的值结构：只用来决定题干怎么挖空；自测与题库里都是四选一（ADR 0118 起不再手输）。
  final TypedAnswer? typed;

  /// 干扰项来源的种类与是否只用同组，见 [QuizSource]。
  final String? kind;
  final bool nearOnly;

  /// 输入框前的小标签（组名）。
  final String? inputLabel;

  /// 手工指定的干扰项（ADR 0104）。
  final List<String> distractors;

  String get questionId => recallQuestionId(page, id);

  QuizSource get source => QuizSource(
    id: id,
    name: name,
    answerTexts: answerTexts,
    group: group,
    stemText: stemText,
    confuseName: confuseName,
    kind: kind,
    nearOnly: nearOnly,
    distractors: distractors,
  );
}

// ------------------------------------------------------------ 符号四页

List<RecallCard> recallCardsOfSigns(String page, List<RoadSign> signs) => [
  for (final s in signs)
    RecallCard(
      page: page,
      id: s.id,
      name: s.name,
      meaning: s.meaning,
      sourceId: "gb5768-2",
      group: s.kind,
      confuseName: signs.where((o) => o.id == s.confuseWith).firstOrNull?.name,
      confuseNote: s.confuseNote,
      imagePath: s.image,
      prompt: "想一想：这是什么标志？选一个。",
    ),
];

List<RecallCard> recallCardsOfMarkings(String page, List<Marking> markings) => [
  for (final m in markings)
    RecallCard(
      page: page,
      id: m.id,
      name: m.name,
      meaning: m.meaning,
      sourceId: "gb5768-3",
      group: m.kind,
      confuseName: markings.where((o) => o.id == m.confuseWith).firstOrNull?.name,
      confuseNote: m.confuseNote,
      imagePath: m.image,
      prompt: "想一想：图里圈出的是什么标线？选一个。",
    ),
];

List<RecallCard> recallCardsOfGauges(String page, List<Gauge> gauges) => [
  for (final g in gauges)
    RecallCard(
      page: page,
      id: g.id,
      name: g.name,
      meaning: g.meaning,
      sourceId: "gb-4094",
      group: g.kind,
      confuseName: gauges.where((o) => o.id == g.confuseWith).firstOrNull?.name,
      confuseNote: g.confuseNote,
      imagePath: g.image,
      prompt: "想一想：这个符号是什么？选一个。",
    ),
];

List<RecallCard> recallCardsOfGestures(String page, List<TrafficGesture> gestures) => [
  for (final g in gestures)
    // 「手势的效力」是总则，没有规范动画，不出卡。
    if (g.kind != "general")
      RecallCard(
        page: page,
        id: g.id,
        name: g.name,
        meaning: g.meaning,
        sourceId: "road-safety-regulation",
        group: g.kind,
        confuseName: gestures.where((o) => o.id == g.confuseWith).firstOrNull?.name,
        confuseNote: g.confuseNote,
        imagePath: g.image,
        prompt: "想一想：这是什么手势信号？选一个。",
      ),
];

// ------------------------------------------------------------ 要点三页

/// 考点速记 / 河南速记 / 记分证照速记共用：情景 → 要点。[page] 是各页自己的键。
List<RecallCard> recallCardsOfNotes(String page, List<NoteGroup> groups) => [
  for (final group in groups)
    for (final item in group.items)
      RecallCard(
        page: page,
        // 键用情景原文而不是序号：以后在组里插条目，旧记录不会错位到别的条目上。
        id: "${group.id}/${item.scenario}",
        name: "要点",
        meaning: [for (final point in item.points) "· $point"].join("\n"),
        sourceId: item.sourceId,
        locator: item.locator,
        answerTexts: item.points,
        group: group.id,
        stemText: item.scenario,
        stem: item.scenario,
        inputLabel: group.title,
        prompt: "想一想：碰到这个情景该怎么做？选一条对的。",
      ),
];

// ------------------------------------------------------------ 易混数字

List<RecallCard> recallCardsOfNumbers(String page, List<CheatGroup> groups) {
  return [
    for (final c in planNumberCards(groups))
      RecallCard(
        page: page,
        id: c.id,
        name: c.value,
        meaning: c.kind == NumberCardKind.reverse
            ? "「${c.value}」下的情形：\n${[for (final t in c.answerTexts) "· $t"].join("\n")}\n${c.locator}".trim()
            : "原文：${c.caseText}\n${c.locator}".trim(),
        sourceId: c.sourceId,
        locator: c.locator,
        // 反向卡的答案是单条情形（同值的行合并，随机抽一条）；填数、选择卡的答案是值。
        answerTexts: c.kind == NumberCardKind.reverse ? c.answerTexts : const [],
        group: c.optionGroup,
        kind: c.optionKind,
        nearOnly: true,
        stem: c.stem,
        inputLabel: c.groupTitle,
        typed: c.typed,
        distractors: c.distractors,
        prompt: switch (c.kind) {
          NumberCardKind.typed => "想一想：括号里该是几？选一个。",
          NumberCardKind.choice => "想一想：括号里该填什么？选一个。",
          NumberCardKind.reverse => "想一想：下面哪一项对应它？选一个。",
        },
      ),
  ];
}

// ------------------------------------------------------------ 速记题

/// 没有题图的符号卡（仪表里的胎压、ESC 故障灯）改用文字问：说明写成「外观：含义」的，取冒号前的外观描述当题干
/// （「看到『黄色蹄形加感叹号』，这是什么？」）。说明里没有外观描述的出不了题，返回 null（ADR 0118）。
String? textStemOf(RecallCard card) {
  if (card.imagePath != null || card.stem != null) return null;
  final cut = card.meaning.indexOf("：");
  if (cut <= 0 || cut > 30) return null;
  return "看到「${card.meaning.substring(0, cut)}」，这是什么？";
}

/// 这张卡出不出得了题：有题图、有题干，或能用文字问（[textStemOf]）。
bool askable(RecallCard card) => card.imagePath != null || card.stem != null || textStemOf(card) != null;

/// 一张卡对应的题：四选一，选项由 [buildQuiz] 按题号做种子**确定地**生成（同一张卡每次打开
/// 都是同样的题，错题本、强化练习里看到的都一致）。自测不用这份，现场另出（[freshRecallQuestionOf]）。
Question recallQuestionOf(RecallCard card, List<RecallCard> pagePool, {Map<String, String> sourceUrls = const {}}) =>
    _questionOf(card, pagePool, _SeededRandom(int.parse(_fnv(card.questionId), radix: 16)), sourceUrls[card.sourceId] ?? "");

/// 自测现场出题（ADR 0118）：按这张卡（条目）自己的内容出，**不依赖练习题库**——正确项从条目的要点里随机抽一条，
/// 干扰项从同页别的条目随机取，每次自测都重新出。题号沿用这张卡的，作答记录、错题库、掌握判定照旧对得上。
Question freshRecallQuestionOf(RecallCard card, List<RecallCard> pagePool, Random random, {String sourceUrl = ""}) =>
    _questionOf(card, pagePool, random, sourceUrl);

Question _questionOf(RecallCard card, List<RecallCard> pagePool, Random random, String sourceUrl) {
  final quiz = buildQuiz(card.source, [for (final c in pagePool) c.source], random: random);
  const letters = ["A", "B", "C", "D"];
  // 数值题（易混数字）在题里也是四选一，题干得有个括号标出填哪里。
  var stem = card.stem ?? textStemOf(card);
  if (stem != null && card.typed != null && !stem.contains(clozeBlank)) stem = "$stem →$clozeBlank";
  final prompt = switch ((stem, card.inputLabel)) {
    (final s?, final label?) => "$label：$s",
    (final s?, null) => s,
    _ => (card.prompt ?? "这是什么？").replaceFirst("想一想：", "").replaceFirst("选一个。", "").trim(),
  };
  return Question(
    id: card.questionId,
    topicId: "$recallTopicPrefix${card.page}",
    kind: "single",
    prompt: prompt,
    choices: [
      for (final (i, text) in quiz.options.indexed) Choice(id: letters[i], label: text, ok: text == quiz.answer),
    ],
    explain: card.meaning,
    sourceRefs: [
      SourceRef(
        sourceId: card.sourceId,
        relation: "authored",
        locator: card.locator,
        url: sourceUrl,
        note: "速记卡按内容文件出题，选项取自同页其他条目",
      ),
    ],
    image: card.imagePath,
    band: QuestionBand.regular,
  );
}

/// 一个专题的全部速记卡（ADR 0096）：卡按专题出，页键就是专题 id（`s1.signs`、`s4.gestures`）。
List<RecallCard> recallCardsOfTopic(SpeedTopic topic, Bank bank) => switch (topic.kind) {
  SpeedKind.numbers => recallCardsOfNumbers(topic.id, cheatGroupsOf(bank, topic)),
  SpeedKind.signs => recallCardsOfSigns(topic.id, bank.signs),
  SpeedKind.markings => recallCardsOfMarkings(topic.id, bank.markings),
  SpeedKind.gauges => recallCardsOfGauges(topic.id, bank.gauges),
  SpeedKind.gestures => recallCardsOfGestures(topic.id, gesturesOf(bank, topic)),
  SpeedKind.notes => recallCardsOfNotes(topic.id, noteGroupsOf(bank, topic)),
};

/// 全部速记题：每个专题一份卡，选项在本专题的卡里取。错题本、强化练习、考前复习按题号从这里找题面；
/// 出不了题的卡（[askable] 为假）跳过。
List<Question> recallQuestionsOf(Bank bank, {Map<String, String> sourceUrls = const {}}) {
  final out = <Question>[];
  for (final topic in speedTopics) {
    final cards = recallCardsOfTopic(topic, bank);
    for (final card in cards) {
      if (askable(card)) out.add(recallQuestionOf(card, cards, sourceUrls: sourceUrls));
    }
  }
  return out;
}

/// 易混数字一行名下的卡（ADR 0101、0119）：每条情形一张正向卡（f/），这个值一张反向卡（r/）；
/// 反向卡按值合并，同值的行共用一张。反向卡不是每个值都有（组里不同的值不足 4 个、或区间值挖完整条
/// 都是括号，`planNumberCards` 不出），所以只取 [existing] 里**真实存在**的卡——否则这一行永远有一张
/// 测不到的幽灵卡，整行答对也算不上掌握。
List<String> numberRowIds(String page, CheatGroup group, CheatRow row, Set<String> existing) => [
  for (final id in [
    for (final single in splitCase(row.caseText)) recallQuestionId(page, "f/${group.id}/$single|${row.value}"),
    recallQuestionId(page, "r/${group.id}/${row.value}"),
  ])
    if (existing.contains(id)) id,
];

/// 一个专题的条目（ADR 0119）：每条是它名下的卡的题号。易混数字按行（一行可能有好几张卡），
/// 其余页面一条一张卡。「掌握 a/b」的分母就是这里的条数，与页面上看到的条目数一致。
List<List<String>> recallEntriesOfTopic(SpeedTopic topic, Bank bank) {
  final cards = recallCardsOfTopic(topic, bank);
  if (topic.kind != SpeedKind.numbers) return [for (final c in cards) [c.questionId]];
  final existing = {for (final c in cards) c.questionId};
  return [
    for (final group in cheatGroupsOf(bank, topic))
      for (final row in group.rows) numberRowIds(topic.id, group, row, existing),
  ];
}

/// 一个专题页面上的大类（ADR 0122）：每项是这一大类名下全部卡的题号，顺序同卡的顺序。易混数字、要点类按组，
/// 标志、标线、仪表按种类（禁令、警告……），手势页只有「8 个法定动作」一组。侧栏专题右侧的「a/b」数的就是它。
List<List<String>> recallGroupsOfTopic(SpeedTopic topic, Bank bank) {
  final cards = recallCardsOfTopic(topic, bank);
  if (topic.kind == SpeedKind.gestures) return [if (cards.isNotEmpty) [for (final c in cards) c.questionId]];
  if (topic.kind == SpeedKind.numbers) {
    return [
      for (final g in cheatGroupsOf(bank, topic))
        [for (final c in cards) if (c.group != null && c.group!.substring(2) == g.id) c.questionId],
    ];
  }
  final byGroup = <String, List<String>>{};
  for (final c in cards) {
    byGroup.putIfAbsent(c.group ?? "", () => []).add(c.questionId);
  }
  return byGroup.values.toList();
}

/// 易混数字一个组的专属题（ADR 0102）：组内每条情形的正向卡加每个值的反向卡，
/// 各自就是一道有稳定题号的题——行与题因此一对一，组按钮与自测深链练的是它们，
/// 不再是组级正则捞出来的一锅真题。
List<Question> recallQuestionsOfNumberGroup(String page, List<CheatGroup> groups, String groupId) {
  final cards = recallCardsOfNumbers(page, groups);
  final own = [
    for (final card in cards)
      if (card.group != null && card.group!.substring(2) == groupId) card,
  ];
  return [
    for (final card in own)
      if (card.stem != null) recallQuestionOf(card, cards),
  ];
}

/// `Random(seed)` 在不同 Dart 版本之间不保证同一个序列；这里自带一个简单的线性同余发生器，
/// 题的选项只依赖题号，换 SDK 也不变（作答记录里存的是选项字母，选项一变就对不上了）。
class _SeededRandom implements Random {
  _SeededRandom(int seed) : _state = seed & 0x7fffffff;
  int _state;

  int _next() {
    _state = (_state * 1103515245 + 12345) & 0x7fffffff;
    return _state;
  }

  @override
  int nextInt(int max) => (_next() >> 8) % max;

  @override
  double nextDouble() => (_next() >> 8) / 0x800000;

  @override
  bool nextBool() => nextInt(2) == 1;
}

/// 速记题的知识点号：题号去掉最后一段哈希，`drive.recall.signs.1a2b3c4d` → `drive.recall.signs`。
String recallTopicOf(String questionId) => questionId.substring(0, questionId.lastIndexOf("."));
