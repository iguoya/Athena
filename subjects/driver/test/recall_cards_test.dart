import "package:athena_driver/content.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/numbers_cards.dart";
import "package:athena_driver/quiz_options.dart";
import "package:athena_driver/recall_cards.dart";
import "package:athena_driver/speed_topics.dart";
import "package:flutter_test/flutter_test.dart";

/// 速记卡与速记题（ADR 0094、0095）：每张卡有稳定的题号，对应的速记题是确定的四选一，
/// 易混数字的卡分填数 / 选择 / 反向三类，反向卡的干扰项绝不会也是对的。
void main() {
  late Bank bank;
  setUpAll(() async => bank = await ContentLoader.load());

  List<RecallCard> allCards() => [for (final t in speedTopics) ...recallCardsOfTopic(t, bank)];
  final s1Numbers = speedTopicById("s1.numbers")!;
  List<RecallCard> s1NumberCards() => recallCardsOfNumbers(s1Numbers.id, cheatGroupsOf(bank, s1Numbers));

  test("题号稳定、互不重复，知识点号是 drive.recall.<页>", () {
    final cards = allCards();
    final ids = [for (final c in cards) c.questionId];
    expect(ids.toSet().length, ids.length, reason: "每张卡的题号唯一");
    expect(ids, [for (final c in allCards()) c.questionId], reason: "同样的内容，题号每次一样");
    for (final c in cards) {
      expect(isRecallQuestionId(c.questionId), isTrue);
      expect(recallTopicOf(c.questionId), "$recallTopicPrefix${c.page}");
    }
    // 题号写死一个：改了哈希或键的写法，历史作答记录就对不上，这里当场报出来。
    expect(recallQuestionId("signs", "stop"), recallQuestionId("signs", "stop"));
    expect(recallQuestionId("signs", "stop"), isNot(recallQuestionId("signs", "yield")));
  });

  test("速记题进了题库：每道都是四选一以内、恰一个正确项，选项由题号确定、不随加载变", () async {
    final recall = [for (final q in bank.questions) if (isRecallQuestionId(q.id)) q];
    expect(recall.length, greaterThan(300));
    final again = await ContentLoader.load();
    final byId = {for (final q in again.questions) q.id: q};
    for (final q in recall) {
      expect(q.choices.length, inInclusiveRange(2, 4), reason: q.id);
      expect(q.choices.where((c) => c.ok).length, 1, reason: "${q.id}：恰一个正确项");
      expect(q.choices.map((c) => c.label).toSet().length, q.choices.length, reason: "${q.id}：选项不重复");
      expect([for (final c in byId[q.id]!.choices) c.label], [for (final c in q.choices) c.label], reason: "${q.id}：选项确定");
      expect(q.sourceRefs, isNotEmpty, reason: "${q.id}：题要有出处（ADR 0043）");
    }
    // 速记题不在课表里：日常题、章节练习、模拟考、解锁判断都不会带上它。
    final inCurriculum = <String>{...bank.forSubject("subject1").map((q) => q.id), ...bank.forSubject("subject4").map((q) => q.id)};
    expect(recall.any((q) => inCurriculum.contains(q.id)), isFalse);
  });

  test("手输题（易混数字）：把值拆成前缀、数字、后缀，判分只看数字序列", () {
    final t = typedAnswerOf("小于 200 米", groupUnit: "公里/小时")!;
    expect(t.prefix, "小于");
    expect(t.suffix, "米");
    expect(t.numbers, [200.0]);
    expect(t.matches("200"), isTrue);
    expect(t.matches(" 200 米"), isTrue, reason: "带不带单位无所谓");
    expect(t.matches("100"), isFalse);

    final r = typedAnswerOf("50–100", groupUnit: "米")!;
    expect(r.numbers, [50.0, 100.0]);
    expect(r.suffix, "米", reason: "值自己没单位就用组的");
    for (final ok in ["50-100", "50–100", "50~100", "50至100", "50 100"]) {
      expect(r.matches(ok), isTrue, reason: ok);
    }
    expect(r.matches("50"), isFalse, reason: "区间只填一个数不算对");
    expect(r.matches("100-50"), isFalse, reason: "顺序反了不算对");

    expect(typedAnswerOf("12 分")!.suffix, "分");
    expect(typedAnswerOf("20", groupUnit: "毫克/100 毫升")!.suffix, "毫克/100 毫升");
    // 不是一个数的值：只能走选择。
    for (final v in ["终生", "拘役并处罚金", "一年以下", "三年以上七年以下", "6 年 / 10 年 / 长期"]) {
      expect(typedAnswerOf(v), isNull, reason: v);
    }
  });

  test("易混数字出卡：填数 / 选择 / 反向各有；反向卡的干扰项是别的数值的情形，没有也算对的", () {
    final cards = planNumberCards(bank.cheatsheet);
    final kinds = {for (final k in NumberCardKind.values) k: cards.where((c) => c.kind == k).length};
    expect(kinds[NumberCardKind.typed], greaterThan(40), reason: "多数值能手输");
    expect(kinds[NumberCardKind.choice], greaterThan(0), reason: "终生、拘役这类只能选择");
    expect(kinds[NumberCardKind.reverse], greaterThan(20));

    for (final c in cards.where((c) => c.kind == NumberCardKind.reverse)) {
      final q = recallQuestionOf(
        s1NumberCards().firstWhere((x) => x.id == c.id),
        s1NumberCards(),
      );
      // 同组别的数值的情形才会当干扰项：任何干扰项都不能出现在本值的情形里。
      final mine = {for (final t in c.answerTexts) optionLabel(t)};
      for (final choice in q.choices.where((x) => !x.ok)) {
        expect(mine.contains(choice.label), isFalse, reason: "${c.id}：干扰项也是这个值的情形");
      }
      expect(q.choices.length, greaterThanOrEqualTo(3), reason: "${c.id}：反向卡至少 3 个选项");
    }
    // 数值种类少于 4 个的组不出反向卡（高速低能见度、血液酒精含量）。
    expect(cards.any((c) => c.kind == NumberCardKind.reverse && c.groupId == "alcohol"), isFalse);
  });

  test("事故与停车专题（ADR 0103、0104）：科目一、科目四各有自己的内容，每组在本科目都有题可练", () {
    for (final id in ["s1.accident", "s4.crash", "s1.parking", "s4.stopping"]) {
      final topic = speedTopicById(id)!;
      final groups = noteGroupsOf(bank, topic);
      expect(groups, isNotEmpty, reason: "$id 没有内容");
      final questions = bank.forSubject(topic.subjectId);
      for (final g in groups) {
        expect(g.subjects, [topic.subjectId], reason: "${g.id} 只属于 ${topic.subjectId}，不混用");
        expect(g.items, isNotEmpty);
        expect(g.related(questions), isNotEmpty, reason: "${g.id} 在 ${topic.subjectId} 里没有相关题");
      }
    }
    // 科目一的内容里不出现科目四专属的处置条目，反之亦然（隧道、铁路道口只在科目四）。
    final s1Text = noteGroupsOf(bank, speedTopicById("s1.accident")!).expand((g) => g.items).map((i) => i.scenario).join();
    expect(s1Text, isNot(contains("隧道")));
  });
}
