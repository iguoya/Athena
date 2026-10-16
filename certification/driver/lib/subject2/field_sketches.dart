/// 科目二其余三项的分步俯视草表（T-009）：侧方停车、曲线行驶、直角转弯。
///
/// 数据形态与 T-008 的 `reverseParkSketch` 一致：坐标 x 向右、y 向下（路在上），
/// heading 弧度、0 朝 +x、顺时针为正，后轴中心为原点；量级是教学示意，
/// 不是测绘——教学重点是车身与线、角的相对关系。
library;

import "dart:math" as math;

import "package:flutter/material.dart";

import "field_map.dart";

/// 侧方停车 7 步：路边平行库（库沿 x 轴长条），车道 y∈[0,7]，库 y∈[7,9.4]。
const sideParkingSketch = <FieldMapStep>[
  // 1 摆位：库前方与库平行，右车身距库线约 30 cm。
  FieldMapStep(
    x: 6,
    y: 5.9,
    heading: 0,
    steerDegrees: 0,
    lines: _sideLines,
    marks: [FieldMark(Offset(3.4, 7))],
  ),
  // 2 挂倒挡向右打满：库前角刚过肩就打；打晚了车头甩向外侧路缘。
  FieldMapStep(
    x: 3.5,
    y: 5.9,
    heading: 0,
    steerDegrees: 45,
    lines: _sideLines,
    marks: [FieldMark(Offset(3.4, 7))],
    risks: [
      FieldRisk([Offset(4.3, 5.4), Offset(4.7, 6.3), Offset(4.9, 7)]),
    ],
  ),
  // 3 中段回正：车尾已甩进库口，左后轮沿库左线走。
  FieldMapStep(
    x: -0.5,
    y: 6.6,
    heading: -0.44,
    steerDegrees: 0,
    lines: _sideLines,
    marks: [FieldMark(Offset(-2, 7))],
  ),
  // 4 再向左打满入库：盯左后轮即将贴库左线；打早了右后轮逼库前角。
  FieldMapStep(
    x: -3.2,
    y: 7.4,
    heading: -0.61,
    steerDegrees: -45,
    lines: _sideLines,
    marks: [FieldMark(Offset(-2, 9.4))],
    risks: [
      FieldRisk([Offset(0.8, 7.5), Offset(2.2, 7.15), Offset(3.4, 7.05)]),
    ],
  ),
  // 5 停：车身与库平行即停、回正。
  FieldMapStep(
    x: -1,
    y: 8.2,
    heading: 0,
    steerDegrees: 0,
    lines: _sideLines,
    marks: [FieldMark(Offset(-2, 9.4)), FieldMark(Offset(3.4, 9.4))],
  ),
  // 6 出库：开左转向灯，向右打满驶出。
  FieldMapStep(
    x: 1.5,
    y: 7.6,
    heading: 0.35,
    steerDegrees: 45,
    lines: _sideLines,
    marks: [FieldMark(Offset(3.4, 7))],
  ),
  // 7 驶离：回正、关灯。
  FieldMapStep(
    x: 7,
    y: 5.5,
    heading: 0,
    steerDegrees: 0,
    lines: _sideLines,
    marks: [],
  ),
];

const _sideLines = <FieldLine>[
  FieldLine([Offset(-14, 0), Offset(14, 0)]),
  FieldLine([Offset(-14, 7), Offset(-2, 7)]),
  FieldLine([Offset(3.4, 7), Offset(14, 7)]),
  FieldLine([
    Offset(-2, 7),
    Offset(3.4, 7),
    Offset(3.4, 9.4),
    Offset(-2, 9.4),
    Offset(-2, 7),
  ], bay: true),
];

/// 曲线行驶 4 步：S 弯，边线由中心线沿法向偏移生成（车道宽 4 m）。
final curveSketch = <FieldMapStep>[
  // 1 进弯：居中略偏外，怠速匀速。
  FieldMapStep(
    x: -12,
    y: 1.3,
    heading: -0.15,
    steerDegrees: 0,
    lines: _curveLines,
    bounds: _curveBounds,
    marks: [FieldMark(Offset(-9, -3.4))],
  ),
  // 2 第一弯向左：左车角「追」右边线；打少了线往车角中间跑。
  FieldMapStep(
    x: -6.5,
    y: -1.9,
    heading: -0.26,
    steerDegrees: -40,
    lines: _curveLines,
    bounds: _curveBounds,
    marks: [FieldMark(Offset(-5.9, -4.5))],
    risks: [
      FieldRisk([Offset(-4.6, -3.4), Offset(-3.4, -3.6), Offset(-2.2, -3.3)]),
    ],
  ),
  // 3 换向：先回正再向右打，换右车角追左边线。
  FieldMapStep(
    x: 3,
    y: 0.6,
    heading: 0.55,
    steerDegrees: 40,
    lines: _curveLines,
    bounds: _curveBounds,
    marks: [FieldMark(Offset(5.2, 2.9))],
  ),
  // 4 出弯：车头对正出口，后视镜确认后轮不压线。
  FieldMapStep(
    x: 12,
    y: 5.8,
    heading: 0.28,
    steerDegrees: 0,
    lines: _curveLines,
    bounds: _curveBounds,
    marks: [],
  ),
];

/// S 弯中心线：先向上（-y）弯再向下弯，量级对齐半径约 8 m 的考场示意。
const _curveCenter = <Offset>[
  Offset(-14, 2),
  Offset(-9, -1),
  Offset(-4, -2.5),
  Offset(1, -1),
  Offset(5, 2),
  Offset(9, 5),
  Offset(14, 6.5),
];

final _curveLines = <FieldLine>[
  FieldLine(_offsetLine(_curveCenter, 2)),
  FieldLine(_offsetLine(_curveCenter, -2)),
];

const _curveBounds = Rect.fromLTRB(-16, -6, 16, 10);

/// 中心线沿法向偏移 [half]：车道边线。折线短段近似，教学示意够用。
List<Offset> _offsetLine(List<Offset> center, double half) => [
  for (var i = 0; i < center.length; i++) _offsetAt(center, i, half),
];

Offset _offsetAt(List<Offset> center, int i, double half) {
  final prev = center[i == 0 ? 0 : i - 1];
  final next = center[i == center.length - 1 ? i : i + 1];
  final dir = (next - prev) / (next - prev).distance;
  return center[i] + Offset(-dir.dy, dir.dx) * half;
}

/// 直角转弯 5 步：L 形，进口沿 +x（车道 y∈[7,11]），左转朝 -y 出去。
const rightAngleTurnSketch = <FieldMapStep>[
  // 1 进弯姿态：车靠弯外侧走，给内侧后轮留内轮差。
  FieldMapStep(
    x: -8,
    y: 10.2,
    heading: 0,
    steerDegrees: 0,
    lines: _turnLines,
    bounds: _turnBounds,
    marks: [FieldMark(Offset(10, 11))],
  ),
  // 2 开转向灯：与转弯方向一致，提前够一秒再动方向。
  FieldMapStep(
    x: -3,
    y: 10.2,
    heading: 0,
    steerDegrees: 0,
    lines: _turnLines,
    bounds: _turnBounds,
    marks: [FieldMark(Offset(10, 11))],
  ),
  // 3 找打方向时机：内角与门把手/后视镜平齐，一把匀速打满；打早了内后轮扫内角。
  FieldMapStep(
    x: 6.5,
    y: 10.2,
    heading: 0,
    steerDegrees: -45,
    lines: _turnLines,
    bounds: _turnBounds,
    marks: [FieldMark(Offset(10, 7))],
    risks: [
      FieldRisk([Offset(8.1, 7.9), Offset(9.2, 7.2), Offset(10.05, 7.05)]),
    ],
  ),
  // 4 打满后：盯内侧后轮与内角的距离。
  FieldMapStep(
    x: 11,
    y: 8.5,
    heading: -1.22,
    steerDegrees: -45,
    lines: _turnLines,
    bounds: _turnBounds,
    marks: [FieldMark(Offset(10, 7))],
  ),
  // 5 回正出弯：车身与新车道边线平行即匀速回正。
  FieldMapStep(
    x: 12,
    y: -2,
    heading: -math.pi / 2,
    steerDegrees: 0,
    lines: _turnLines,
    bounds: _turnBounds,
    marks: [],
  ),
];

const _turnLines = <FieldLine>[
  FieldLine([Offset(-14, 11), Offset(14, 11), Offset(14, -10)]),
  FieldLine([Offset(-14, 7), Offset(10, 7), Offset(10, -10)]),
];

const _turnBounds = Rect.fromLTRB(-16, -12, 16, 13);
