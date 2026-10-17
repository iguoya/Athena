import "dart:math" as math;

import "package:athena_driver/subject2/field_map.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

FieldMapStep _step(
  double x,
  double y,
  double heading, {
  List<FieldRisk> risks = const [],
  List<FieldLabel> labels = const [],
}) => FieldMapStep(
  x: x,
  y: y,
  heading: heading,
  steerDegrees: 0,
  lines: const [
    FieldLine([Offset(-16, 0), Offset(16, 0)]),
  ],
  marks: const [],
  risks: risks,
  labels: labels,
);

void main() {
  test("插值：t=0 是起点步，t=1 是目标步，t=0.5 在中点", () {
    final a = _step(0, 0, 0);
    final b = _step(4, 8, math.pi / 2);
    final mid = lerpFieldStep(a, b, 0.5);
    expect(lerpFieldStep(a, b, 0).x, 0);
    expect(lerpFieldStep(a, b, 1).y, 8);
    expect(mid.x, 2);
    expect(mid.y, 4);
    expect(mid.heading, closeTo(math.pi / 4, 1e-9));
    expect(mid.lines, same(b.lines), reason: "场地随目标步取，不插值");
  });

  test("heading 走最短角差：从 -π 附近到 +π 附近不绕整圈", () {
    final a = _step(0, 0, -math.pi + 0.1);
    final b = _step(0, 0, math.pi - 0.1);
    final mid = lerpFieldStep(a, b, 0.5);
    expect(
      mid.heading.abs(),
      greaterThan(math.pi / 2),
      reason: "应穿过 ±π 而不是绕经 0",
    );
  });

  test("risks：默认为空，构造后进步骤", () {
    expect(_step(0, 0, 0).risks, isEmpty);
    final risky = _step(
      0,
      0,
      0,
      risks: [
        FieldRisk([const Offset(1, 1), const Offset(2, 2)]),
      ],
    );
    expect(risky.risks, hasLength(1));
  });

  testWidgets("FieldMapAnimated：autoPlay 演示一轮、外部 index 变化平滑过渡，不抛异常", (
    tester,
  ) async {
    final steps = [_step(0, 0, 0), _step(4, 2, 0.5), _step(8, 4, 1.0)];
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SizedBox.expand(
            child: FieldMapAnimated(steps: steps, index: 0, autoPlay: true),
          ),
        ),
      ),
    );
    // 演示一轮：900ms 起步 + 2 次推进（650ms 动画 + 1500ms 间隔）。
    await tester.pump(const Duration(milliseconds: 1000));
    await tester.pump(const Duration(milliseconds: 2200));
    await tester.pump(const Duration(milliseconds: 2200));
    await tester.pump(const Duration(milliseconds: 800));
    // 演示结束回到受控模式：外部 index 变化触发过渡，不抛异常。
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SizedBox.expand(
            child: FieldMapAnimated(steps: steps, index: 2, autoPlay: true),
          ),
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 700));
    await tester.pump(const Duration(milliseconds: 100));
  });

  test("插值保留目标步的文字标注（T-103 回归：lerp 曾漏 labels）", () {
    final a = _step(0, 0, 0);
    final b = _step(
      4,
      2,
      0.5,
      risks: [
        FieldRisk([const Offset(1, 1), const Offset(2, 2)]),
      ],
      labels: const [FieldLabel(Offset(8, 1), "控制线")],
    );
    final mid = lerpFieldStep(a, b, 0.5);
    expect(mid.labels, same(b.labels), reason: "lerp 曾漏 labels，插值结果必须保留目标步标注");
  });
}
