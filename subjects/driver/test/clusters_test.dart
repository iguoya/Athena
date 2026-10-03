import "package:athena_driver/clusters.dart";
import "package:athena_driver/content.dart";
import "package:athena_driver/models.dart";
import "package:flutter_test/flutter_test.dart";

Question _q(
  String id,
  String prompt,
  String answer, {
  String topic = "drive.s1.rules",
  String kind = "single",
  String? image,
  List<SourceRef> refs = const [],
}) {
  final judge = kind == "judge";
  return Question(
    id: id,
    topicId: topic,
    kind: kind,
    prompt: prompt,
    image: image,
    choices: judge
        ? [Choice(id: "T", label: "正确", ok: answer == "正确"), Choice(id: "F", label: "错误", ok: answer == "错误")]
        : [Choice(id: "A", label: answer, ok: true), const Choice(id: "B", label: "其他说法一", ok: false), const Choice(id: "C", label: "其他说法二", ok: false)],
    explain: "",
    sourceRefs: refs,
  );
}

/// 一批互不相干的题，让 idf 有意义（语料太小时 idf 都是 0）。
List<Question> _filler() => [
      for (var i = 0; i < 14; i++)
        _q("f$i", "第${"甲乙丙丁戊己庚辛壬癸子丑寅卯"[i]}类事项：${["夜间", "雨天", "隧道", "桥梁", "山路", "弯道", "坡道", "路口", "学校", "医院", "广场", "车站", "码头", "市场"][i]}附近的特别注意事项是什么", "注意事项$i号", topic: "drive.s1.rules"),
    ];

void main() {
  group("考点簇", () {
    test("判断题与选择题互换同一个点：聚成一簇，簇里互为同伴", () {
      final index = buildClusters([
        ..._filler(),
        _q("a", "高速公路限速标志标明的最高时速不得超过多少公里？", "120公里"),
        _q("b", "高速公路限速标志标明的最高时速不得超过120公里。", "正确", kind: "judge"),
      ]);
      expect(index.clusters, [
        ["a", "b"],
      ]);
      expect(index.mates("a"), ["b"]);
      expect(index.mates("b"), ["a"]);
      expect(index.mates("f0"), isEmpty);
      expect(index.mates("不存在"), isEmpty);
    });

    test("两道选择题只是句式和答案相同、讲的是不同的事：不算同一个点（追逐竞驶 vs 醉酒驾驶）", () {
      final index = buildClusters([
        ..._filler(),
        _q("x", "驾驶机动车在道路上追逐竞驶，情节恶劣，会受到什么处罚？", "处拘役，并处罚金"),
        _q("y", "醉酒驾驶机动车在道路上行驶会受到什么处罚？", "处拘役，并处罚金"),
      ]);
      expect(index.isEmpty, isTrue);
    });

    test("两道选择题题干很像、答案却毫不相干（「以下哪种说法正确」）：不算同一个点", () {
      final index = buildClusters([
        ..._filler(),
        _q("x", "机动车上高速公路，以下哪种说法是正确的？", "不准倒车逆行穿越中央分隔带掉头"),
        _q("y", "机动车上高速公路，以下哪种说法是错误的？", "可以在匝道加速车道上超车"),
      ]);
      expect(index.isEmpty, isTrue);
    });

    test("同一个点两种说法的选择题（题干像、答案也像）：聚成一簇", () {
      final index = buildClusters([
        ..._filler(),
        _q("x", "驾驶人连续驾驶机动车超过4小时，应停车休息的时间不得少于多少分钟？", "20分钟"),
        _q("y", "驾驶人连续驾驶机动车超过4小时，应停车休息的时间不得少于多长？", "至少20分钟"),
      ]);
      expect(index.clusters, [
        ["x", "y"],
      ]);
    });

    test("不同章节的题永远不聚到一起", () {
      final index = buildClusters([
        ..._filler(),
        _q("a", "高速公路限速标志标明的最高时速不得超过多少公里？", "120公里", topic: "drive.s1.highway"),
        _q("b", "高速公路限速标志标明的最高时速不得超过120公里。", "正确", kind: "judge", topic: "drive.s4.maneuver"),
      ]);
      expect(index.isEmpty, isTrue);
    });

    test("带图片或自绘标志的题不参与（题干几乎一样，区别全在图上）", () {
      final index = buildClusters([
        ..._filler(),
        _q("a", "高速公路限速标志标明的最高时速不得超过多少公里？", "120公里", image: "images/a.jpg"),
        _q("b", "高速公路限速标志标明的最高时速不得超过120公里。", "正确", kind: "judge"),
      ]);
      expect(index.isEmpty, isTrue);
    });

    test("几乎一模一样的重复题不当作换了问法", () {
      final index = buildClusters([
        ..._filler(),
        _q("a", "高速公路限速标志标明的最高时速不得超过120公里。", "正确", kind: "judge"),
        _q("b", "高速公路限速标志标明的最高时速不得超过120公里。", "正确", kind: "judge"),
      ]);
      expect(index.isEmpty, isTrue);
    });

    test("一簇最多 8 题，再相似也不无限串下去", () {
      final many = [
        for (var i = 0; i < 12; i++)
          _q("m$i", "驾驶人连续驾驶机动车超过${i + 3}小时应当停车休息至少二十分钟并检查车况与轮胎", "休息${i + 3}", kind: "judge"),
      ];
      final index = buildClusters([..._filler(), ...many], linkThreshold: 0.3);
      for (final cluster in index.clusters) {
        expect(cluster.length, lessThanOrEqualTo(clusterMaxSize));
      }
    });

    test("结果是确定的：同样的输入、不同的输入顺序，算出同样的簇", () {
      final questions = [
        ..._filler(),
        _q("a", "高速公路限速标志标明的最高时速不得超过多少公里？", "120公里"),
        _q("b", "高速公路限速标志标明的最高时速不得超过120公里。", "正确", kind: "judge"),
        _q("c", "实习期是多久？初次申领机动车驾驶证后", "12个月"),
        _q("d", "初次申领机动车驾驶证后，实习期为十二个月。", "正确", kind: "judge"),
      ];
      final first = buildClusters(questions).clusters;
      final second = buildClusters(questions.reversed).clusters;
      expect(second, first);
    });

    test("题干太短没有可比性，不入簇", () {
      final index = buildClusters([..._filler(), _q("a", "对吗", "正确", kind: "judge"), _q("b", "对吗", "正确", kind: "judge")]);
      expect(index.isEmpty, isTrue);
    });
  });

  testWidgets("真实题库：聚类质量守门——簇大小、同章节、覆盖率、耗时、确定性", (tester) async {
    late Bank bank;
    await tester.runAsync(() async => bank = await ContentLoader.load());
    final watch = Stopwatch()..start();
    final index = buildClusters(bank.questions);
    watch.stop();
    final byId = {for (final q in bank.questions) q.id: q};
    final textQuestions = bank.questions.where((q) => q.image == null && q.sign == null).length;

    expect(index.clusters, isNotEmpty);
    for (final cluster in index.clusters) {
      expect(cluster.length, inInclusiveRange(2, clusterMaxSize));
      expect({for (final id in cluster) byId[id]!.topicId}, hasLength(1), reason: "簇不跨章节：$cluster");
      expect(cluster.every((id) => byId[id]!.image == null && byId[id]!.sign == null), isTrue);
    }
    final coverage = index.coveredQuestions / textQuestions;
    // 人工抽查 30 个簇：九成以上是真正的同考点换问法。覆盖率在这个量级是合理的——
    // 太低说明门槛过严，太高说明在把不相干的题往一起拉。
    expect(coverage, inInclusiveRange(0.10, 0.35), reason: "覆盖率 ${(coverage * 100).toStringAsFixed(1)}%");
    expect(watch.elapsed, lessThan(const Duration(seconds: 10)));
    expect(buildClusters(bank.questions).clusters, index.clusters, reason: "确定性");
  });
}
