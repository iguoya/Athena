import "dart:math";

import "package:athena_driver/content.dart";
import "package:athena_driver/quiz_options.dart";
import "package:flutter_test/flutter_test.dart";

/// 自测四选一的选项生成（ADR 0085、0094）：去掉只挂在正确项上的解释括号、干扰项长度与题干重合接近正确项、
/// 长句不与本条目要点近似；易混对永远排最前，同组优先，短名称的易混（限制速度 40 / 60）照留。
void main() {
  test("解释性括号去掉，名称里的括号（ABS、ESC）留着", () {
    expect(optionLabel("未悬挂警示标志并采取必要的安全措施：6 分（不是 9 分）"), "未悬挂警示标志并采取必要的安全措施：6 分");
    expect(optionLabel("醉酒驾驶：吊销驾驶证，5 年内不得重新取得（不是终生）"), "醉酒驾驶：吊销驾驶证，5 年内不得重新取得");
    expect(optionLabel("实施条例原文：6 年内每 2 年 1 次（考题按条文答）"), "实施条例原文：6 年内每 2 年 1 次");
    expect(optionLabel("所有权转让：交付之日起 30 日内申请转让登记（第二十五条）"), "所有权转让：交付之日起 30 日内申请转让登记");
    expect(optionLabel("防抱死制动系统（ABS）故障灯"), "防抱死制动系统（ABS）故障灯");
    expect(optionLabel("致人轻伤以上事故后逃逸（尚不构成犯罪）"), "致人轻伤以上事故后逃逸（尚不构成犯罪）");
  });

  test("四个选项、含正确项、互不相同、同一个种子结果一样；同组优先", () {
    const texts = [
      "先停车查明水情，确认安全后再低速通过漫水路面",
      "开近光灯、示廓灯、后位灯，同向近距离跟车不用远光",
      "向侧滑的相反方向修正方向盘，不要急踩制动踏板",
      "夹板要超过伤口上下的关节，让伤处的关节不能活动",
      "第一时间远离毒气源头，再组织人员施救和报警",
      "立即停车熄火断电，组织人员撤离并用灭火器扑救",
      "先按住流血的位置压迫止血，再看情况进一步处理",
      "车尾往哪边甩就往哪边适量打方向，缓踩制动",
    ];
    final pool = [
      for (var i = 0; i < 8; i++) QuizSource(id: "e$i", name: "名称$i", answerTexts: [texts[i]], group: i < 4 ? "a" : "b"),
    ];
    final first = buildQuiz(pool[0], pool, random: Random(7));
    final again = buildQuiz(pool[0], pool, random: Random(7));
    expect(first.options, again.options, reason: "同一个种子，选项一样");
    expect(first.options.length, 4);
    expect(first.options.toSet().length, 4);
    expect(first.options, contains(first.answer));
    // 同组（a 组共 4 个条目）优先：3 个干扰项应全部来自同组。
    final sameGroup = {for (var i = 1; i < 4; i++) texts[i]};
    expect(first.options.where((o) => o != first.answer).every(sameGroup.contains), isTrue);
  });

  test("只差数字的模板句是好易混，留着当干扰项（车速不超过 40 对 60）", () {
    const answer = "车速不超过 60 公里/小时，与前车保持 100 米以上距离";
    const template = "车速不超过 40 公里/小时，与前车保持 50 米以上距离";
    final pool = [
      const QuizSource(id: "a", name: "能见度低于 200 米", answerTexts: [answer], group: "g"),
      const QuizSource(id: "b", name: "能见度低于 100 米", answerTexts: [template], group: "g"),
      const QuizSource(id: "c", name: "别处", answerTexts: ["先停车查明水情，确认安全后再低速通过漫水路面"], group: "g"),
      const QuizSource(id: "d", name: "别处二", answerTexts: ["夹板要超过伤口上下的关节，让伤处的关节不能活动"], group: "g"),
    ];
    final q = buildQuiz(pool[0], pool, random: Random(3));
    expect(q.options, contains(template), reason: "同模板只差数字：靠题干条件区分，是要考的易混");
  });

  test("易混对永远排最前；候选不足四个就按实际个数出", () {
    final pool = [
      const QuizSource(id: "a", name: "禁止停车", group: "g", confuseName: "禁止停放车辆"),
      const QuizSource(id: "b", name: "禁止停放车辆", group: "g"),
      const QuizSource(id: "c", name: "禁止掉头", group: "g"),
    ];
    for (var seed = 0; seed < 20; seed++) {
      final q = buildQuiz(pool[0], pool, random: Random(seed));
      expect(q.options, contains("禁止停放车辆"), reason: "易混对方一定出现");
      expect(q.options.length, 3, reason: "只有 3 个候选就出 3 个选项");
    }
  });

  test("短名称的易混（限制速度 40 / 60）不被近似过滤", () {
    final pool = [
      const QuizSource(id: "s40", name: "限制速度 40", group: "p"),
      const QuizSource(id: "s60", name: "限制速度 60", group: "p"),
      const QuizSource(id: "s80", name: "限制速度 80", group: "p"),
      const QuizSource(id: "ye", name: "减速让行", group: "p"),
    ];
    final q = buildQuiz(pool[0], pool, random: Random(1));
    expect(q.options, containsAll(["限制速度 40", "限制速度 60", "限制速度 80"]));
  });

  test("长句：与本条目另一条要点意思重叠的不当干扰项（选对选错说不清）", () {
    const own1 = "高速行驶时紧急制动容易翻车，控制车速果断减速";
    const own2 = "紧握方向盘保持直线，不要猛打方向";
    const overlapping = "高速行驶时紧急制动和猛打方向都容易翻车被追尾";
    final pool = [
      const QuizSource(id: "t", name: "转向失控", answerTexts: [own1, own2], group: "g"),
      const QuizSource(id: "u", name: "别处", answerTexts: [overlapping], group: "g"),
      const QuizSource(id: "v", name: "别处二", answerTexts: ["先停车查明水情，确认安全后低速通过再慢慢开"], group: "g"),
      const QuizSource(id: "w", name: "别处三", answerTexts: ["开近光灯、示廓灯、后位灯，同向近距离跟车不用远光"], group: "g"),
      const QuizSource(id: "x", name: "别处四", answerTexts: ["向侧滑的相反方向修正方向盘，不要急踩制动"], group: "g"),
    ];
    expect(similarity(own1, overlapping), greaterThanOrEqualTo(0.3), reason: "前提：这条确实与要点近似");
    for (var seed = 0; seed < 30; seed++) {
      final q = buildQuiz(pool[0], pool, random: Random(seed));
      expect(q.options, isNot(contains(overlapping)), reason: "种子 $seed：近似的长句不能当干扰项");
    }
  });

  test("全部真实的证照速记：生成的选项里没有解释性括号，也没有与正确答案相同的干扰项", () async {
    final bank = await ContentLoader.load();
    final pool = [
      for (final g in bank.licenseGroups)
        for (final item in g.items)
          QuizSource(id: "${g.id}/${item.scenario}", name: "要点", answerTexts: item.points, group: g.id, stemText: item.scenario),
    ];
    final hint = RegExp(r"（(?:不是|考题按|第[^）]{0,14}条|实施条例)");
    for (final source in pool) {
      for (var seed = 0; seed < 3; seed++) {
        final q = buildQuiz(source, pool, random: Random(seed));
        expect(q.options.length, 4, reason: source.id);
        expect(q.options.toSet().length, 4, reason: "${source.id}：选项不能重复");
        expect(q.options.any(hint.hasMatch), isFalse, reason: "${source.id}：选项里不该有解释性括号：${q.options}");
      }
    }
  });

  test("别组撞了同一个值（两组都有「30 日」）时，nearOnly 的卡仍然拿到同组的干扰项", () {
    QuizSource card(String id, String name, String group) =>
        QuizSource(id: id, name: name, group: group, kind: "f", nearOnly: true);
    // 池里别组的条目排在前面：它们先占了「30 日」「3 日」，同组的同值条目不能因此被吃掉。
    final pool = [
      card("a1", "30 日", "f:accident"),
      card("a2", "3 日", "f:accident"),
      card("r1", "30 日", "f:registration"),
      card("r2", "15 日", "f:registration"),
      card("r3", "3 日", "f:registration"),
    ];
    final quiz = buildQuiz(pool[3], pool, random: Random(1));
    expect(quiz.options.toSet(), {"15 日", "30 日", "3 日"}, reason: "同组三个值各一个，不因别组撞值丢选项");
  });
}
