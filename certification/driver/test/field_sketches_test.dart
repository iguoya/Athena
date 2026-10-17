import "package:athena_driver/subject2/field_map.dart";
import "package:athena_driver/subject2/field_sketches.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  for (final entry in {
    "侧方停车": sideParkingSketch,
    "曲线行驶": curveSketch,
    "直角转弯": rightAngleTurnSketch,
  }.entries) {
    test("${entry.key}草表：每步几何有效", () {
      expect(entry.value, isNotEmpty, reason: "${entry.key}不应是空草表");
      for (final step in entry.value) {
        expect(
          step.bounds.contains(Offset(step.x, step.y)),
          isTrue,
          reason: "${entry.key}车身位姿应在画布内",
        );
        for (final line in step.lines) {
          expect(line.points.length, greaterThanOrEqualTo(2));
        }
      }
    });
  }

  test("曲线行驶的边线由中心线偏移生成，两条边不重合", () {
    final a = curveSketch.first.lines[0].points;
    final b = curveSketch.first.lines[1].points;
    expect(a.length, b.length);
    expect((a.first - b.first).distance, greaterThan(0));
  });

  test("倒库与三项草表均带画布文字标注（T-103）", () {
    for (final sketch in [reverseParkSketch, sideParkingSketch, curveSketch, rightAngleTurnSketch]) {
      expect(sketch.first.labels, isNotEmpty,
          reason: "首步应有标注让学员分清控制线/库位/路缘");
    }
    expect(
      reverseParkSketch.first.labels.map((l) => l.text),
      contains("控制线"),
    );
    expect(sideParkingSketch.first.labels.map((l) => l.text), contains("路缘"));
  });
}
