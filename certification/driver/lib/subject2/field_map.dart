/// 科目二静态分步俯视图（T-008）。只吃几何数据，不写步骤说明。
///
/// 坐标：x 向右，y 向下（路在上、库在下），和倒库动画的场地朝向一致。
/// 车身位姿的原点在后轴中心，heading 0 朝 +x，顺时针为正。
library;

import "dart:math" as math;

import "package:flutter/material.dart";

/// 一条场地线。控制线画成虚线，库位线用库位色，其余是边线。
class FieldLine {
  const FieldLine(this.points, {this.control = false, this.bay = false});

  final List<Offset> points;
  final bool control;
  final bool bay;
}

/// 这一步要看的点。只画高亮，不写字。
class FieldMark {
  const FieldMark(this.at);

  final Offset at;
}

/// 一步的车身位姿、方向盘角度和这一步要画的场地。
class FieldMapStep {
  const FieldMapStep({
    required this.x,
    required this.y,
    required this.heading,
    required this.steerDegrees,
    required this.lines,
    required this.marks,
    this.bounds = const Rect.fromLTRB(-16, -1, 16, 14),
  });

  /// 后轴中心。
  final double x;
  final double y;

  /// 车头朝向，弧度，0 朝右，顺时针为正。
  final double heading;

  /// 方向盘相对摆正的角度。正数是向右打。示意用，不是圈数。
  final double steerDegrees;

  final List<FieldLine> lines;
  final List<FieldMark> marks;
  final Rect bounds;
}

/// 倒车入库右倒再换到左倒的 7 步草表。量级对齐现有倒库场地
/// （路宽 7 m、库宽 2.4 m、控制线在 ±10 m），位姿是相对关系，不是测绘。
const reverseParkSketch = <FieldMapStep>[
  FieldMapStep(
    x: 7.6,
    y: 3.2,
    heading: 0,
    steerDegrees: 0,
    lines: _reverseLines,
    marks: [FieldMark(Offset(10, 3.2))],
  ),
  FieldMapStep(
    x: 5.6,
    y: 3.6,
    heading: -0.35,
    steerDegrees: 40,
    lines: _reverseLines,
    marks: [FieldMark(Offset(1.2, 7))],
  ),
  FieldMapStep(
    x: 3.0,
    y: 5.8,
    heading: -0.9,
    steerDegrees: 40,
    lines: _reverseLines,
    marks: [FieldMark(Offset(1.2, 7)), FieldMark(Offset(-1.2, 7))],
  ),
  FieldMapStep(
    x: 0.6,
    y: 8.6,
    heading: -1.35,
    steerDegrees: 8,
    lines: _reverseLines,
    marks: [FieldMark(Offset(0, 9.4))],
  ),
  FieldMapStep(
    x: 0,
    y: 10.8,
    heading: -math.pi / 2,
    steerDegrees: 0,
    lines: _reverseLines,
    marks: [FieldMark(Offset(0, 12.1))],
  ),
  FieldMapStep(
    x: -8.2,
    y: 3.2,
    heading: math.pi,
    steerDegrees: 0,
    lines: _reverseLines,
    marks: [FieldMark(Offset(-10, 3.2))],
  ),
  FieldMapStep(
    x: -3.0,
    y: 5.8,
    heading: math.pi + 0.9,
    steerDegrees: -40,
    lines: _reverseLines,
    marks: [FieldMark(Offset(-1.2, 7))],
  ),
];

const _reverseLines = <FieldLine>[
  FieldLine([Offset(-16, 0), Offset(16, 0)]),
  FieldLine([
    Offset(-16, 7),
    Offset(-1.2, 7),
    Offset(-1.2, 12.1),
    Offset(1.2, 12.1),
    Offset(1.2, 7),
    Offset(16, 7),
  ], bay: true),
  FieldLine([Offset(10, 0), Offset(10, 7)], control: true),
  FieldLine([Offset(-10, 0), Offset(-10, 7)], control: true),
];

class FieldMap extends StatelessWidget {
  const FieldMap({super.key, required this.steps, required this.index});

  final List<FieldMapStep> steps;
  final int index;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      painter: FieldMapPainter(steps[index]),
      child: const SizedBox.expand(),
    );
  }
}

class FieldMapPainter extends CustomPainter {
  const FieldMapPainter(this.step);

  final FieldMapStep step;

  @override
  void paint(Canvas canvas, Size size) {
    final bounds = step.bounds;
    final scale = math.min(
      size.width / bounds.width,
      size.height / bounds.height,
    );
    final origin = Offset(
      (size.width - bounds.width * scale) / 2 - bounds.left * scale,
      (size.height - bounds.height * scale) / 2 - bounds.top * scale,
    );
    Offset map(Offset p) => origin + p * scale;

    canvas.drawRect(
      Offset.zero & size,
      Paint()..color = const Color(0xFF1B2430),
    );

    for (final line in step.lines) {
      if (line.points.length < 2) continue;
      final paint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = line.control ? 1.5 : 2.5
        ..color = line.bay ? const Color(0xFFE6C15A) : const Color(0xFFE8EEF4);
      final pts = [for (final p in line.points) map(p)];
      if (line.control) {
        _dash(canvas, pts.first, pts.last, paint);
      } else {
        canvas.drawPath(Path()..addPolygon(pts, false), paint);
      }
    }

    for (final mark in step.marks) {
      final at = map(mark.at);
      canvas.drawCircle(
        at,
        8,
        Paint()..color = const Color(0xFF00E5FF).withValues(alpha: 0.25),
      );
      canvas.drawCircle(at, 4, Paint()..color = const Color(0xFF00E5FF));
    }

    _car(canvas, map(Offset(step.x, step.y)), scale);
  }

  void _car(Canvas canvas, Offset axle, double scale) {
    canvas.save();
    canvas.translate(axle.dx, axle.dy);
    canvas.rotate(step.heading);
    canvas.scale(scale);
    final body = Paint()..color = const Color(0xFF8FD0FF);
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(-0.9, -0.9, 4.4, 1.8),
        const Radius.circular(0.25),
      ),
      body,
    );
    const discCenter = Offset(2.7, 0);
    canvas.drawCircle(
      discCenter,
      0.42,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 0.08
        ..color = const Color(0xFF102033),
    );
    final spoke = step.steerDegrees * math.pi / 180;
    canvas.drawLine(
      discCenter,
      discCenter + Offset(math.cos(spoke), math.sin(spoke)) * 0.36,
      Paint()
        ..strokeWidth = 0.1
        ..strokeCap = StrokeCap.round
        ..color = const Color(0xFF102033),
    );
    canvas.restore();
  }

  @override
  bool shouldRepaint(FieldMapPainter oldDelegate) {
    final old = oldDelegate.step;
    return old.x != step.x ||
        old.y != step.y ||
        old.heading != step.heading ||
        old.steerDegrees != step.steerDegrees ||
        old.marks.length != step.marks.length;
  }
}

void _dash(Canvas canvas, Offset a, Offset b, Paint paint) {
  final delta = b - a;
  final len = delta.distance;
  if (len == 0) return;
  final dir = delta / len;
  const dash = 8.0;
  const gap = 6.0;
  var t = 0.0;
  while (t < len) {
    final end = math.min(t + dash, len);
    canvas.drawLine(a + dir * t, a + dir * end, paint);
    t = end + gap;
  }
}
