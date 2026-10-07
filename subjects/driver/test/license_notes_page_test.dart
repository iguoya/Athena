import "package:athena_driver/core/content.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  const groupIds = [
    "score-pairs",
    "score-cycle",
    "license-terms",
    "license-types",
    "license-fines",
    "license-bans",
    "plates-registration",
  ];

  // 内容契约（ADR 0076）：七组齐备；每条有情景、要点与指到条款的出处——
  // 记分分值、罚款档位、期限都是硬规定，出处必须到条（沿用 0028、0064）。
  test("license_notes.json 七组齐备，每条都有情景、要点与条款定位", () async {
    final bank = await ContentLoader.load();
    expect([for (final g in bank.licenseGroups) g.id], groupIds);
    const sources = {
      "penalty-order-163",
      "license-order-162",
      "registration-order-164",
      "road-safety-law",
      "road-safety-regulation",
    };
    for (final group in bank.licenseGroups) {
      expect(group.items, isNotEmpty, reason: "${group.id} 没有条目");
      expect(group.items.length, lessThanOrEqualTo(10), reason: "${group.id} 条目过多，速记页每组不超过 10 条");
      for (final item in group.items) {
        expect(sources, contains(item.sourceId), reason: "${group.id} 的「${item.scenario}」出处不在登记过的法规里");
        expect(item.locator, isNotEmpty, reason: "${group.id} 的「${item.scenario}」缺条款号");
        expect(item.scenario, isNotEmpty);
        expect(item.points, isNotEmpty, reason: "${group.id} 的「${item.scenario}」没有要点");
      }
    }
  });

  // 按题面找相关题的正则（ADR 0076 决策 3）：每组都要抓得到题，合起来覆盖
  // 记分、证照、登记三个知识点的绝大多数题；不能是空壳。
  test("组 match 都抓得到题，合起来覆盖记分、证照、登记题的八成以上", () async {
    final bank = await ContentLoader.load();
    final subject1 = bank.forSubject("subject1");
    const topics = {"drive.s1.penalty", "drive.s1.license", "drive.s1.registration"};
    final topicQuestions = [for (final q in subject1) if (topics.contains(q.topicId)) q];
    final covered = <String>{};
    for (final group in bank.licenseGroups) {
      final related = group.related(subject1);
      expect(related.length, greaterThanOrEqualTo(30), reason: "${group.id} 抓到的题太少");
      covered.addAll([for (final q in related) if (topics.contains(q.topicId)) q.id]);
    }
    expect(covered.length / topicQuestions.length, greaterThan(0.8), reason: "组 match 对三个知识点的覆盖不足");
  });

}
