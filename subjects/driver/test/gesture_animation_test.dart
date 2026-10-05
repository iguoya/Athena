import "dart:math";

import "package:athena_driver/core/content.dart";
import "package:athena_driver/speed/gesture_animation.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

/// 两条手臂方向向量的夹角（度）。
double _angle((double, double, double) a, (double, double, double) b) {
  final dot = a.$1 * b.$1 + a.$2 * b.$2 + a.$3 * b.$3;
  return acos(dot.clamp(-1.0, 1.0)) * 180 / pi;
}

void main() {
  // 内容契约（ADR 0078）：8 个法定动作都有动画；首尾姿势相同，循环没有跳变；要领文字每步都有姿势对应。
  test("gestures.json 的每个法定动作都有动画，首尾回到同一姿势", () async {
    final bank = await ContentLoader.load();
    for (final g in bank.gestureList.where((g) => g.kind == "action")) {
      final clip = gestureClips[g.id];
      expect(clip, isNotNull, reason: "${g.id} 没有动画");
      expect(clip!.keys.first.pose.sameAs(clip.keys.last.pose), isTrue, reason: "${g.id} 首尾姿势不同，循环会跳变");
      expect(clip.keys.length, greaterThanOrEqualTo(4), reason: "${g.id} 关键姿势太少，不成一段动作");
    }
    expect(gestureClips.length, 8);
  });

  test("每步要领都有姿势对应，每个姿势都指到存在的要领", () {
    for (final entry in gestureClips.entries) {
      final used = {for (final k in entry.value.keys) k.step};
      for (final step in used) {
        expect(step, lessThan(entry.value.captions.length), reason: "${entry.key} 的姿势指到不存在的第 ${step + 1} 步");
      }
      for (var i = 0; i < entry.value.captions.length; i++) {
        expect(used, contains(i), reason: "${entry.key} 的第 ${i + 1} 步要领没有姿势对应");
      }
    }
  });

  // 播放连贯：每 40 毫秒采一帧，手臂任何一个角度的变化都不超过 12°——没有瞬移。
  test("整段动画逐帧连贯，没有瞬移", () {
    for (final entry in gestureClips.entries) {
      final clip = entry.value;
      FigurePose? last;
      for (var ms = 0; ms <= clip.totalMs; ms += 40) {
        final pose = clip.poseAt(ms);
        if (last != null) {
          for (final (a, b) in [(last.left, pose.left), (last.right, pose.right)]) {
            for (final d in [
              (a.upperAz - b.upperAz).abs(),
              (a.upperEl - b.upperEl).abs(),
              (a.foreAz - b.foreAz).abs(),
              (a.foreEl - b.foreEl).abs(),
            ]) {
              expect(d, lessThan(12), reason: "${entry.key} 在 $ms ms 附近角度跳了 ${d.toStringAsFixed(1)}°");
            }
          }
        }
        last = pose;
      }
    }
  });

  // 要领核对：把法定动作要领里的硬数字与方位翻成断言（交警自己的左右）。
  group("动作要领", () {
    FigurePose hold(String id, int keyIndex) => gestureClips[id]!.keys[keyIndex].pose;

    test("停止信号：左臂由前向上直伸，与身体成 135° 角，掌心向前；右臂自然下垂", () {
      final pose = hold("stop", 1);
      // 身体的轴线向下，手臂与它的夹角就是「与身体成多少度」。
      final angle = _angle(pose.left.foreVector, ArmPose.vector(0, -90));
      expect(angle, closeTo(135, 0.01));
      expect(pose.left.palm, Palm.forward);
      expect(pose.left.upperAz, 0, reason: "由前向上：方位角 0 就是朝向观看者的正前方");
      expect(pose.right.sameAs(ArmPose.down), isTrue);
    });

    test("直行信号：两臂左右平伸掌心向前，随后右臂水平摆向身前、掌心向左，左臂仍然侧平", () {
      final out = hold("straight", 1);
      expect(out.left.foreAz, 90);
      expect(out.right.foreAz, -90);
      expect(out.left.foreEl, 0);
      expect(out.right.foreEl, 0);
      final swing = hold("straight", 2);
      expect(swing.right.foreAz, greaterThan(0), reason: "前臂横过身前，指向身体左半边");
      expect(swing.right.upperAz, lessThan(-45), reason: "上臂仍在身体右侧（题图里摆动臂是弯的）");
      expect(swing.right.palm, Palm.left);
      expect(swing.left.sameAs(out.left), isTrue, reason: "左臂仍然侧平");
    });

    test("左转弯信号：右臂向前平伸掌心向前；左臂向右前方摆动，掌心向右", () {
      final a = hold("turn_left", 1), b = hold("turn_left", 2);
      for (final p in [a, b]) {
        expect(p.right.foreAz, 0);
        expect(p.right.foreEl, 0);
        expect(p.right.palm, Palm.forward);
        expect(p.left.palm, Palm.right);
      }
      expect(a.left.foreAz, greaterThan(0), reason: "摆动从左侧开始");
      expect(b.left.foreAz, lessThan(0), reason: "摆到右前方");
    });

    test("右转弯信号：左臂向前平伸掌心向前；右臂向左前方摆动，掌心向左（与左转弯镜像）", () {
      final a = hold("turn_right", 1), b = hold("turn_right", 2);
      for (final p in [a, b]) {
        expect(p.left.foreAz, 0);
        expect(p.left.foreEl, 0);
        expect(p.left.palm, Palm.forward);
        expect(p.right.palm, Palm.left);
      }
      expect(a.right.foreAz, lessThan(0));
      expect(b.right.foreAz, greaterThan(0));
      final l = hold("turn_left", 2);
      expect(b.right.foreAz, -l.left.foreAz, reason: "右转弯的摆动终点与左转弯镜像对称");
    });

    test("左转弯待转信号：左臂向左平伸，掌心向下，向下、向身前摆动；右臂下垂", () {
      final a = hold("turn_left_wait", 1), b = hold("turn_left_wait", 2);
      for (final p in [a, b]) {
        expect(p.left.palm, Palm.down);
        expect(p.right.sameAs(ArmPose.down), isTrue);
      }
      expect(a.left.foreAz, 90, reason: "先向左平伸");
      expect(a.left.foreEl, 0);
      expect(b.left.upperEl, lessThan(a.left.upperEl), reason: "向下摆");
      expect(b.left.foreAz, lessThan(a.left.foreAz), reason: "向身前摆");
    });

    test("变道信号：右臂向前平伸掌心向左，向左水平摆动；左臂下垂", () {
      final a = hold("change_lane", 1), b = hold("change_lane", 2);
      expect(a.right.foreAz, 0);
      expect(a.right.foreEl, 0);
      expect(a.right.palm, Palm.left);
      expect(b.right.foreAz, greaterThan(0), reason: "向左摆（交警自己的左边）");
      expect(b.right.foreEl.abs(), lessThan(10), reason: "前臂近似水平横过身前");
      expect(a.left.sameAs(ArmPose.down), isTrue);
    });

    test("减速慢行信号：右臂向右前方平伸，掌心向下，上下摆动；左臂下垂", () {
      final up = hold("slow_down", 1), down = hold("slow_down", 2);
      for (final p in [up, down]) {
        expect(p.right.foreAz, lessThan(0), reason: "朝右前方");
        expect(p.right.foreAz, greaterThan(-90));
        expect(p.right.palm, Palm.down);
        expect(p.left.sameAs(ArmPose.down), isTrue);
      }
      expect(up.right.foreEl, greaterThan(down.right.foreEl), reason: "上下摆动");
    });

    test("示意车辆靠边停车信号：左臂向前平伸掌心向前；右臂由右向左摆动", () {
      final a = hold("pull_over", 1), b = hold("pull_over", 2);
      for (final p in [a, b]) {
        expect(p.left.foreAz, 0);
        expect(p.left.foreEl, 0);
        expect(p.left.palm, Palm.forward);
      }
      expect(a.right.foreAz, lessThan(0), reason: "从右边开始");
      expect(b.right.foreAz, greaterThan(0), reason: "摆向左边");
    });
  });

  testWidgets("交互版：播放中第 1 步亮起，暂停、跳到下一个姿势都能用", (tester) async {
    await tester.binding.setSurfaceSize(const Size(900, 900));
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: Center(child: GestureAnimation(id: "turn_left", size: 200, interactive: true))),
      ),
    );
    expect(find.textContaining("右臂向前平伸"), findsOneWidget);
    expect(find.text("俯视（看前后方向）"), findsOneWidget);
    // 播放中：时间走过去，跳过暂停按钮之前，动画在跑。
    await tester.pump(const Duration(milliseconds: 1500));
    await tester.tap(find.byTooltip("暂停"));
    await tester.pump();
    expect(find.byTooltip("播放"), findsOneWidget);
    await tester.tap(find.byTooltip("下一个姿势"));
    await tester.pump();
    await tester.tap(find.byTooltip("上一个姿势"));
    await tester.pump();
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });
}
