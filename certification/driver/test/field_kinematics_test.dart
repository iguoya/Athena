/// 科目二「迹象」的运动学核验（T-103）：用简单自行车模型验证 cursor 写进
/// subject2.json 的操作参照是否与真实尺寸自洽。基准车：轴距 2.6、车长 4.5、
/// 车宽 1.7（不含后视镜）、前悬（后轴到车头角纵向）3.5。
///
/// 方向盘传动比取常见紧凑车的约 14.4:1——「一圈」≈ 前轮 25°。
library;

import "dart:math" as math;

import "package:flutter/material.dart";

import "package:athena_driver/subject2/field_map.dart";
import "package:athena_driver/subject2/field_sketches.dart";
import "package:flutter_test/flutter_test.dart";

const wheelbase = 2.6;
const steeringRatio = 14.4; // 方向盘转角 : 前轮转角
const bodyWidth = 1.7;
const frontOverhang = 3.5; // 后轴中心到车头角（纵向）

/// 曲线场地几何：中心线半径（外圆 7.5 − 路半宽 1.75）。
const curveCenterlineRadius = 5.75;
const curveOuterEdgeRadius = 7.5;

/// 倒库：满舵（前轮 33°）从草表第 2 步位姿倒车，数值积分自行车模型，
/// 返回「右后视镜壳越过库口线 y=6.75」时刻的车尾右角位置。
({Offset tailCorner, double heading}) _reverseUntilMirrorCrosses() {
  var x = 5.4, y = 3.6, heading = -0.35;
  const delta = 33 * math.pi / 180;
  const dt = 0.001; // 每步 1 mm
  Offset frontAxle() => Offset(
    x + wheelbase * math.cos(heading),
    y + wheelbase * math.sin(heading),
  );
  Offset mirrorShell() {
    final f = frontAxle();
    // 右后视镜壳：前轴右侧 0.85 m（车宽一半）。
    return f + Offset(-math.sin(heading), math.cos(heading)) * (bodyWidth / 2);
  }

  var tail = Offset.zero;
  for (var i = 0; i < 10000; i++) {
    heading += -math.tan(delta) / wheelbase * dt; // 倒车（v<0）右打：heading 减小
    x += -math.cos(heading) * dt;
    y += -math.sin(heading) * dt;
    tail = Offset(
      x + -1.0 * math.cos(heading) - 0.85 * -math.sin(heading),
      y + -1.0 * math.sin(heading) + 0.85 * math.cos(heading),
    );
    if (mirrorShell().dy >= 6.75) break;
  }
  return (tailCorner: tail, heading: heading);
}

void main() {
  test("曲线「向左大约一圈」：满一圈的转弯半径与场地中心线吻合", () {
    final frontWheelDeg = 360 / steeringRatio;
    final radius = wheelbase / math.tan(frontWheelDeg * math.pi / 180);
    expect(
      radius,
      closeTo(curveCenterlineRadius, curveCenterlineRadius * 0.05),
      reason: "一圈 ≈ $radius m，场地中心线 $curveCenterlineRadius m，偏差应在 5% 内",
    );
  });

  test("曲线「加减四分之一圈」：微调范围覆盖场地半径", () {
    double radiusForWheelTurns(double turns) =>
        wheelbase / math.tan((360 * turns / steeringRatio) * math.pi / 180);
    final tight = radiusForWheelTurns(1.25); // 多打四分之一圈，半径变小
    final loose = radiusForWheelTurns(0.75); // 少打四分之一圈，半径变大
    expect(tight, lessThan(curveCenterlineRadius), reason: "收紧四分之一圈应变小");
    expect(loose, greaterThan(curveCenterlineRadius), reason: "放松四分之一圈应变大");
  });

  test("曲线「左车头角沿着右边线走」：中心线行驶时左前角弧径恰好贴外边线", () {
    // 左前角绕弯心的半径 = sqrt((中心线半径 + 半车宽)² + 前悬²)。
    final cornerRadius = math.sqrt(
      math.pow(curveCenterlineRadius + bodyWidth / 2, 2) +
          math.pow(frontOverhang, 2),
    );
    expect(
      cornerRadius,
      closeTo(curveOuterEdgeRadius, 0.1),
      reason:
          "左前角弧径 $cornerRadius m vs 外边线 $curveOuterEdgeRadius m——"
          "「沿着右边线走」在运动学上自洽",
    );
  });

  test("倒库「后视镜壳刚过库口边线」时，车尾右角距库角尚有充分余量", () {
    const bayCorner = Offset(1.15, 6.75); // 库口右角（T-101 真实尺寸）
    final result = _reverseUntilMirrorCrosses();
    final gap = (result.tailCorner - bayCorner).distance;
    expect(
      gap,
      greaterThan(3.0),
      reason:
          "镜壳刚过线时车尾距库角 ${gap.toStringAsFixed(2)} m——"
          "迹象是打满时机信号，此刻无刮碰风险；真正贴近发生在后续入库中段"
          "（对应 fix「库角快被车尾挡住」）",
    );
  });

  test("草表关键位姿在场地尺寸内（倒库库口、侧方路缘）", () {
    expect(reverseParkSketch[2].y, lessThan(6.75), reason: "倒库第 3 步车身应还在路口");
    expect(sideParkingSketch[0].y, lessThan(3.35), reason: "侧方摆位应在车道内、路缘外侧");
  });
}
