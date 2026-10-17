/// 科目二其余三项的分步俯视草表（T-009/T-101）：侧方停车、曲线行驶、直角转弯。
///
/// 尺寸锚定（T-101，GA 1029 系/GB/T 30341-2013 的场地公式，核对记录见
/// `comms/driver/artifacts/T-101/`），基准考试车车长 L=4.5 m、车宽 W=1.7 m、
/// 轴距 2.6 m：
/// - 侧方停车：库长 1.5L+1 = 7.75 m，库宽 W+0.8 = 2.5 m，路宽 1.5W+0.8 = 3.35 m。
///   库内单侧余量 = (2.5 − 1.7) / 2 = 0.4 m。
/// - 曲线行驶：外圆半径 R = 7.5 m，路宽 3.5 m（中心线半径 5.75 m），每弯 3/8 圆周。
/// - 直角转弯：路宽 = 轴距 + 1 = 3.6 m，路长 ≥ 1.5L = 6.75 m。
///
/// 坐标 x 向右、y 向下，heading 弧度、0 朝 +x、顺时针为正，后轴中心为原点。
/// 位姿是教学示意，但比例真实。
library;

import "dart:math" as math;

import "package:flutter/material.dart";

import "field_map.dart";

/// 侧方停车 7 步：路边平行库（库沿 x 轴长条），车道 y∈[0,3.35]，库 y∈[3.35,5.85]。
const sideParkingSketch = <FieldMapStep>[
  // 1 摆位：库前方与库平行，右车身距库线约 30 cm。
  FieldMapStep(
    x: 6.5,
    y: 2.2,
    heading: 0,
    steerDegrees: 0,
    lines: _sideLines,
    labels: _sideLabels,
    marks: [FieldMark(Offset(5.55, 3.35))],
  ),
  // 2 挂倒挡向右打满：库前角刚过肩就打；打晚了车头甩向外侧路缘。
  FieldMapStep(
    x: 4,
    y: 2.2,
    heading: 0,
    steerDegrees: 45,
    lines: _sideLines,
    labels: _sideLabels,
    marks: [FieldMark(Offset(5.55, 3.35))],
    risks: [
      FieldRisk([Offset(4.9, 1.5), Offset(5.3, 2.5), Offset(5.5, 3.35)]),
    ],
  ),
  // 3 中段回正：车尾已甩进库口，左后轮沿库左线走。
  FieldMapStep(
    x: -0.5,
    y: 2.9,
    heading: -0.44,
    steerDegrees: 0,
    lines: _sideLines,
    labels: _sideLabels,
    marks: [FieldMark(Offset(-2.2, 3.35))],
  ),
  // 4 再向左打满入库：盯左后轮即将贴库左线；打早了右后轮逼库前角。
  FieldMapStep(
    x: -3.2,
    y: 3.6,
    heading: -0.61,
    steerDegrees: -45,
    lines: _sideLines,
    labels: _sideLabels,
    marks: [FieldMark(Offset(-2.2, 5.85))],
    risks: [
      FieldRisk([Offset(0.6, 3.5), Offset(2.8, 3.4), Offset(5.5, 3.4)]),
    ],
  ),
  // 5 停：车身与库平行即停、回正。
  FieldMapStep(
    x: -0.8,
    y: 4.6,
    heading: 0,
    steerDegrees: 0,
    lines: _sideLines,
    labels: _sideLabels,
    marks: [FieldMark(Offset(-2.2, 5.85)), FieldMark(Offset(5.55, 5.85))],
  ),
  // 6 出库：开左转向灯，向右打满驶出。
  FieldMapStep(
    x: 2,
    y: 3.9,
    heading: 0.35,
    steerDegrees: 45,
    lines: _sideLines,
    labels: _sideLabels,
    marks: [FieldMark(Offset(5.55, 3.35))],
  ),
  // 7 驶离：回正、关灯。
  FieldMapStep(
    x: 7.5,
    y: 2,
    heading: 0,
    steerDegrees: 0,
    lines: _sideLines,
    labels: _sideLabels,
    marks: [],
  ),
];

const _sideLabels = <FieldLabel>[
  FieldLabel(Offset(-11.5, 3.35), "路缘"),
  FieldLabel(Offset(1.4, 4.6), "库位"),
];

const _sideLines = <FieldLine>[
  FieldLine([Offset(-14, 0), Offset(14, 0)]),
  FieldLine([Offset(-14, 3.35), Offset(-2.2, 3.35)]),
  FieldLine([Offset(5.55, 3.35), Offset(14, 3.35)]),
  FieldLine([
    Offset(-2.2, 3.35),
    Offset(5.55, 3.35),
    Offset(5.55, 5.85),
    Offset(-2.2, 5.85),
    Offset(-2.2, 3.35),
  ], bay: true),
];

/// 曲线行驶 4 步：S 弯，外圆半径 7.5 m、路宽 3.5 m，每弯 3/8 圆周（135°）。
/// 中心线半径 = 7.5 − 3.5/2 = 5.75 m，由两段相切圆弧生成，边线沿法向偏移。
final curveSketch = _buildCurve();

List<FieldMapStep> _buildCurve() {
  final center = _curveCenter;
  const laneHalf = 1.75;

  FieldMapStep pose(
    double frac, {
    List<FieldMark> marks = const [],
    List<FieldRisk> risks = const [],
  }) {
    final at = (center.length - 1) * frac;
    final i = at.floor().clamp(0, center.length - 2);
    final t = at - i;
    final p = Offset(
      center[i].dx + (center[i + 1].dx - center[i].dx) * t,
      center[i].dy + (center[i + 1].dy - center[i].dy) * t,
    );
    final a = center[i == 0 ? 0 : i - 1];
    final b = center[i == center.length - 1 ? i : i + 1];
    final d = (b - a) / (b - a).distance;
    return FieldMapStep(
      x: p.dx,
      y: p.dy,
      heading: math.atan2(d.dy, d.dx),
      steerDegrees: 0,
      lines: _curveLines,
      bounds: _curveBounds,
      labels: _curveLabels,
      marks: marks,
      risks: risks,
    );
  }

  return [
    // 1 进弯：居中略偏外，怠速匀速。
    pose(0.06),
    // 2 第一弯向左：左车角「追」右边线；打少了线往车角中间跑。
    pose(
      0.30,
      marks: [_offsetMark(_curveCenter, 9, -laneHalf)],
      risks: [
        FieldRisk([
          _offsetAt(_curveCenter, 10, -laneHalf),
          _offsetAt(_curveCenter, 11, -laneHalf),
          _offsetAt(_curveCenter, 12, -laneHalf),
        ]),
      ],
    ),
    // 3 换向：先回正再向右打，换右车角追左边线。
    pose(0.62, marks: [_offsetMark(_curveCenter, 20, laneHalf)]),
    // 4 出弯：车头对正出口，后视镜确认后轮不压线。
    pose(0.94),
  ];
}

FieldMark _offsetMark(List<Offset> center, int i, double half) =>
    FieldMark(_offsetAt(center, i, half));

/// S 弯中心线：进直段 + 左弯 135°（逆时针）+ 右弯 135°（顺时针）+ 出直段。
final List<Offset> _curveCenter = _curveCenterPoints();

List<Offset> _curveCenterPoints() {
  const r = 5.75;
  const c1 = Offset(0, -r);
  final c2 = Offset(
    2 * r * math.sin(math.pi / 4),
    -r - 2 * r * math.cos(math.pi / 4),
  );
  Offset arcPoint(
    Offset center,
    double startDirDeg,
    double sweepDeg,
    double frac,
  ) {
    final rad = startDirDeg * math.pi / 180 + sweepDeg * math.pi / 180 * frac;
    return center + Offset(r * math.cos(rad), r * math.sin(rad));
  }

  return <Offset>[
    const Offset(-5, 0),
    const Offset(0, 0),
    for (var i = 1; i <= 14; i++) arcPoint(c1, 90, -135, i / 14),
    for (var i = 1; i <= 14; i++) arcPoint(c2, -135, 135, i / 14),
    arcPoint(c2, -135, 135, 1) + const Offset(5, 0),
  ];
}

final _curveLines = <FieldLine>[
  FieldLine(_offsetLine(_curveCenter, 1.75)),
  FieldLine(_offsetLine(_curveCenter, -1.75)),
];

const _curveBounds = Rect.fromLTRB(-8, -21, 18, 3);

final _curveLabels = <FieldLabel>[
  FieldLabel(_offsetAt(_curveCenter, 7, -1.75) + const Offset(6, -2), "边线"),
];

/// 中心线沿法向偏移 [half]：车道边线。折线短段近似，公式半径下足够圆滑。
List<Offset> _offsetLine(List<Offset> center, double half) => [
  for (var i = 0; i < center.length; i++) _offsetAt(center, i, half),
];

Offset _offsetAt(List<Offset> center, int i, double half) {
  final prev = center[i == 0 ? 0 : i - 1];
  final next = center[i == center.length - 1 ? i : i + 1];
  final dir = (next - prev) / (next - prev).distance;
  return center[i] + Offset(-dir.dy, dir.dx) * half;
}

/// 直角转弯 5 步：L 形，进口沿 +x（车道 y∈[6.75,10.35]，路宽 3.6 m），
/// 左转朝 -y 出去；内角 (10.35, 6.75)。
const rightAngleTurnSketch = <FieldMapStep>[
  // 1 进弯姿态：车靠弯外侧走，给内侧后轮留内轮差。
  FieldMapStep(
    x: -8,
    y: 9.5,
    heading: 0,
    steerDegrees: 0,
    lines: _turnLines,
    labels: _turnLabels,
    bounds: _turnBounds,
    marks: [FieldMark(Offset(10.35, 10.35))],
  ),
  // 2 开转向灯：与转弯方向一致，提前够一秒再动方向。
  FieldMapStep(
    x: -3,
    y: 9.5,
    heading: 0,
    steerDegrees: 0,
    lines: _turnLines,
    labels: _turnLabels,
    bounds: _turnBounds,
    marks: [FieldMark(Offset(10.35, 10.35))],
  ),
  // 3 找打方向时机：内角与门把手/后视镜平齐，一把匀速打满；打早了内后轮扫内角。
  FieldMapStep(
    x: 6.5,
    y: 9.5,
    heading: 0,
    steerDegrees: -45,
    lines: _turnLines,
    labels: _turnLabels,
    bounds: _turnBounds,
    marks: [FieldMark(Offset(10.35, 6.75))],
    risks: [
      FieldRisk([Offset(8.5, 7.5), Offset(9.6, 6.9), Offset(10.4, 6.8)]),
    ],
  ),
  // 4 打满后：盯内侧后轮与内角的距离。
  FieldMapStep(
    x: 11,
    y: 8.6,
    heading: -1.22,
    steerDegrees: -45,
    lines: _turnLines,
    labels: _turnLabels,
    bounds: _turnBounds,
    marks: [FieldMark(Offset(10.35, 6.75))],
  ),
  // 5 回正出弯：车身与新车道边线平行即匀速回正。
  FieldMapStep(
    x: 12,
    y: -1.5,
    heading: -math.pi / 2,
    steerDegrees: 0,
    lines: _turnLines,
    labels: _turnLabels,
    bounds: _turnBounds,
    marks: [],
  ),
];

const _turnLabels = <FieldLabel>[
  FieldLabel(Offset(-11.5, 10.35), "进口道"),
  FieldLabel(Offset(10.35, 5.9), "内角"),
];

const _turnLines = <FieldLine>[
  FieldLine([Offset(-14, 10.35), Offset(14, 10.35), Offset(14, -10)]),
  FieldLine([Offset(-14, 6.75), Offset(10.35, 6.75), Offset(10.35, -10)]),
];

const _turnBounds = Rect.fromLTRB(-16, -12, 16, 12);
