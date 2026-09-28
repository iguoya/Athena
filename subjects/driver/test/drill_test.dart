import "dart:math";

import "package:athena_driver/drill.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  // 示意动作本身不能是一个会被判不合格的动作（ADR 0036）：逐帧检查判定点都在场地内。
  for (final scene in drillScenes.values) {
    test("${scene.id}：逐帧${scene.judged == Judged.body ? "车身" : "车轮"}都不出线", () {
      final timeline = Timeline(scene);
      for (final frame in timeline.sample()) {
        final points = scene.judged == Judged.body ? frame.pose.outline() : frame.pose.wheelPatches();
        for (final p in points) {
          expect(
            scene.inside(p),
            isTrue,
            reason: "${scene.id} 第 ${frame.step + 1} 步出线：(${p.dx.toStringAsFixed(2)}, ${p.dy.toStringAsFixed(2)})",
          );
        }
      }
    });
  }

  test("倒车入库：起点两前轮在控制线外；第二次倒车前两前轮都越过另一端控制线；两次都停在库里；回到起点", () {
    final timeline = Timeline(reverseScene);
    bool inBay(Pose pose) => pose.outline().every((p) => p.dx.abs() <= 1.2 && p.dy >= 7 && p.dy <= 12.1);
    expect(reverseScene.start.frontWheels().every((w) => w.dx > reverseControlX), isTrue);
    // 第 4 步（下标 3）结束：第一次入库停稳。
    expect(inBay(timeline.frame(timeline.stepEnd(3)).pose), isTrue);
    // 第 5 步结束：两前轮都越过左端控制线。
    expect(timeline.frame(timeline.stepEnd(4)).pose.frontWheels().every((w) => w.dx < -reverseControlX), isTrue);
    // 第 6 步里「倒车」那一段之后：第二次入库停稳。
    expect(inBay(timeline.frame(timeline.stepEnd(5)).pose), isTrue);
    final end = timeline.end;
    expect((end.position - reverseScene.start.position).distance, lessThan(0.01));
    expect(cos(end.heading), closeTo(1, 1e-6));
  });

  test("侧方停车：一次倒车入库后车身在库内且摆正，出库后回到车道", () {
    final timeline = Timeline(parallelScene);
    final parked = timeline.frame(timeline.stepEnd(3)).pose;
    expect(parked.outline().every((p) => p.dx >= 3.4 && p.dx <= 6.0 && p.dy >= 0 && p.dy <= 7.6), isTrue);
    expect(sin(parked.heading), closeTo(-1, 1e-6));
    final out = timeline.end;
    expect(out.outline().every((p) => p.dx > 0 && p.dx < 3.4), isTrue);
    // 出库那一步开着左转向灯，下一步关掉。
    expect(parallelScene.steps[5].signal, Signal.left);
    expect(parallelScene.steps[6].signal, Signal.none);
  });

  test("直角转弯：转弯前开灯、转完关灯，转完车头朝左", () {
    expect(cornerScene.steps[1].signal, Signal.left);
    expect(cornerScene.steps[2].signal, Signal.left);
    expect(cornerScene.steps[3].signal, Signal.none);
    expect(cos(Timeline(cornerScene).end.heading), closeTo(-1, 1e-6));
  });

  test("反例：直角转弯方向打早 2 米，内侧后轮会压到内角——检查真能抓出出线", () {
    final early = DrillScene(
      id: "corner-early",
      start: cornerScene.start,
      judged: Judged.wheels,
      bounds: cornerScene.bounds,
      inside: cornerScene.inside,
      lines: cornerScene.lines,
      steps: const [
        DrillStep([Straight(13 - 3.2 - 2)]),
        DrillStep([Arc(90, leftTurn: true)]),
      ],
    );
    final out = Timeline(early).sample().any((f) => f.pose.wheelPatches().any((p) => !early.inside(p)));
    expect(out, isTrue);
  });

  test("圆弧积分：满舵转 90° 后位置落在以转弯圆心为圆心的圆上", () {
    const start = Pose(0, 0, 0);
    const arc = Arc(90, leftTurn: true);
    final end = arc.at(start, 1);
    // 朝东左转，圆心在北边 R 处，转完朝北、位于圆心正东 R 处。
    expect(end.x, closeTo(car.minRadius, 1e-9));
    expect(end.y, closeTo(-car.minRadius, 1e-9));
    expect(sin(end.heading), closeTo(-1, 1e-9));
  });

  // 画面标注（ADR 0040）：每一步都要指出点什么，标在场地范围里。
  for (final scene in drillScenes.values) {
    test("${scene.id}：每一步都有画面标注，场地标注落在画面里", () {
      for (var i = 0; i < scene.steps.length; i++) {
        final marks = scene.steps[i].marks;
        expect(marks, isNotEmpty, reason: "${scene.id} 第 ${i + 1} 步没有标注");
        for (final m in marks) {
          expect(m.label, isNotEmpty);
          final points = switch (m) {
            LineMark(:final points) => points,
            SpotMark(:final at) => [at],
            CarMark() => const <Offset>[],
          };
          for (final p in points) {
            expect(scene.bounds.inflate(0.5).contains(p), isTrue, reason: "${scene.id} 第 ${i + 1} 步「${m.label}」在画面外");
          }
        }
      }
    });
  }
}
