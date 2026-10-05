import "package:athena_driver/cloze.dart";
import "package:athena_driver/content.dart";
import "package:flutter_test/flutter_test.dart";

/// 易混数字自测的出题（ADR 0092）：要考的数字挖成括号，题干里不留答案；长清单拆成单条。
void main() {
  test("题干里写着答案的，把答案数字挖成括号（带单位的才挖，别的条件留着）", () {
    // 距离：原文就写着 150，答案是 150。
    expect(
      clozeStem("高速公路故障：警告标志设在来车方向 150 米以外", "150", groupUnit: "米"),
      "高速公路故障：警告标志设在来车方向（　　）米以外",
    );
    // 同一句里有两个 100：速度条件留着，只挖距离那个。
    expect(
      clozeStem("高速车速超过 100 公里/小时：与同车道前车保持 100 米以上", "100", groupUnit: "米"),
      "高速车速超过 100 公里/小时：与同车道前车保持（　　）米以上",
    );
    // 区间：两个端点都是答案，都挖。
    expect(
      clozeStem("一般道路故障难以移动：警告标志设在车后 50 米至 100 米", "50–100", groupUnit: "米"),
      "一般道路故障难以移动：警告标志设在车后（　　）米至（　　）米",
    );
  });

  test("原文里没有可挖的数字：句尾补括号，不动题干里别的数字", () {
    expect(clozeStem("饮酒后驾驶", "12 分", groupUnit: "分"), "饮酒后驾驶 →（　　）");
    // 答案自带单位（米）与组单位（公里/小时）不同：按答案自己的单位，题干里的 60、100 不是答案，不动。
    final fog = clozeStem("车速不超过 60，车距 100 米以上", "小于 200 米", groupUnit: "公里/小时");
    expect(fog, "车速不超过 60，车距 100 米以上 →（　　）");
    // 单位对不上的数字不挖：答案 30（公里/小时），题干里的 30 米是另一回事。
    expect(
      clozeStem("公共汽车站及其 30 米以内不得停车", "30", groupUnit: "公里/小时"),
      "公共汽车站及其 30 米以内不得停车 →（　　）",
    );
  });

  test("长清单按「；」拆成单条，每条自成一题", () {
    expect(splitCase("A；B；C"), ["A", "B", "C"]);
    expect(splitCase("没有分号的情形"), ["没有分号的情形"]);
    expect(splitCase("A；；  B ；"), ["A", "B"], reason: "空段与首尾空白去掉");
  });

  test("全部真实数据：每一条拆出来的题干都有括号，答案数字不会留在题干里", () async {
    final bank = await ContentLoader.load();
    var singles = 0;
    for (final group in bank.cheatsheet) {
      for (final row in group.rows) {
        final unit = RegExp(r"[\d.]+\s*([^\d.\s–—\-~～至到]+)\s*$").firstMatch(row.value)?[1] ?? group.unit;
        final numbers = {for (final m in RegExp(r"\d+(?:\.\d+)?").allMatches(row.value)) m[0]!};
        for (final single in splitCase(row.caseText)) {
          singles++;
          final stem = clozeStem(single, row.value, groupUnit: group.unit);
          expect(stem, contains(clozeBlank), reason: "${group.id} / $single：题干里必须有括号");
          if (unit.isNotEmpty) {
            for (final n in numbers) {
              final leak = RegExp("(?<![\\d.])${RegExp.escape(n)}(?=\\s*${RegExp.escape(unit)})");
              expect(leak.hasMatch(stem), isFalse, reason: "${group.id} / $single：题干里还留着答案 $n $unit：$stem");
            }
          }
        }
      }
    }
    // 50 行情形拆成更多单条；不拆就没有逐条考的意义。
    expect(singles, greaterThan(50));
  });
}
