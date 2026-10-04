import "dart:math" as math;

import "package:flutter/material.dart";

/// 路面俯视的标线示意（ADR 0065）：灰底路面 + 白/黄线形。行车方向朝上，
/// 「路口最前端」的线（停止线、让行线）画在上部。只求一格认出一种线。
class MarkingView extends StatelessWidget {
  const MarkingView({super.key, required this.id, this.size = 120});

  final String id;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: "交通标线示意 $id",
      child: CustomPaint(
        size: Size.square(size),
        painter: _MarkingPainter(id),
      ),
    );
  }
}

/// `_MarkingPainter` 画得出来的全部 id（ADR 0065）：加新标线时，这个清单与下面
/// switch 的 case 同步加。`content/markings.json` 的每条 id 都必须落在这个集合里，
/// test/markings_page_test.dart 守住——漏画就会落到 switch 兜底的问号图。
const paintableMarkingIds = {
  // 指示标线
  "lane_white_dashed",
  "center_yellow_dashed",
  "edge_white_solid",
  "edge_white_dashed",
  "guide_lane",
  "variable_lane",
  "tidal_lane",
  "crosswalk",
  "diamond",
  "left_turn_wait",
  "stop_line",
  "yield_line_stop",
  "yield_line_decel",
  "arrows",
  "bus_lane",
  "hov_lane",
  "parking_space",
  "bus_bay",
  "entrance_exit",
  "intersection_guide",
  "center_circle",
  // 禁止标线
  "double_yellow_solid",
  "yellow_solid_dashed",
  "lane_white_solid",
  "curb_yellow_solid",
  "curb_yellow_dashed",
  "channelization",
  "grid",
  // 警告标线
  "width_gradient",
  "obstacle",
  "decel_ribs",
  "decel_bars",
  "distance_confirm",
};

class _MarkingPainter extends CustomPainter {
  _MarkingPainter(this.id);

  final String id;

  static const _asphalt = Color(0xFF52616B);
  static const _white = Color(0xFFFAFAFA);
  static const _yellow = Color(0xFFFDD835);

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width, h = size.height;
    canvas.drawRRect(
      RRect.fromRectAndRadius(Offset.zero & size, Radius.circular(w * 0.07)),
      Paint()..color = _asphalt,
    );
    final line = Paint()
      ..color = _white
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.butt
      ..strokeWidth = w * 0.055;
    final yellow = Paint()..color = _yellow;
    final white = Paint()..color = _white;
    switch (id) {
      case "lane_white_dashed":
        _dashed(canvas, Offset(w / 2, h * 0.08), Offset(w / 2, h * 0.92), line);
      case "center_yellow_dashed":
        line.color = _yellow;
        _dashed(canvas, Offset(w / 2, h * 0.08), Offset(w / 2, h * 0.92), line);
      case "edge_white_solid":
        canvas.drawLine(Offset(w * 0.14, h * 0.06), Offset(w * 0.14, h * 0.94), line);
        canvas.drawLine(Offset(w * 0.86, h * 0.06), Offset(w * 0.86, h * 0.94), line);
      case "edge_white_dashed":
        canvas.drawLine(Offset(w * 0.14, h * 0.06), Offset(w * 0.14, h * 0.94), line);
        _dashed(canvas, Offset(w * 0.86, h * 0.06), Offset(w * 0.86, h * 0.94), line);
      case "guide_lane":
        canvas.drawLine(Offset(w * 0.30, h * 0.08), Offset(w * 0.30, h * 0.62), line);
        canvas.drawLine(Offset(w * 0.70, h * 0.08), Offset(w * 0.70, h * 0.62), line);
        canvas.drawLine(Offset(w * 0.16, h * 0.72), Offset(w * 0.84, h * 0.72), line);
        _arrow(canvas, Offset(w / 2, h * 0.42), w * 0.30, line);
      case "variable_lane":
        _zigzag(canvas, Offset(w * 0.28, h * 0.08), Offset(w * 0.28, h * 0.92), line);
        _zigzag(canvas, Offset(w * 0.72, h * 0.08), Offset(w * 0.72, h * 0.92), line);
      case "tidal_lane":
        line.color = _yellow;
        _dashed(canvas, Offset(w * 0.32, h * 0.08), Offset(w * 0.32, h * 0.92), line);
        _dashed(canvas, Offset(w * 0.68, h * 0.08), Offset(w * 0.68, h * 0.92), line);
      case "crosswalk":
        for (var i = 0; i < 5; i++) {
          canvas.drawRRect(
            RRect.fromRectAndRadius(
              Rect.fromLTWH(w * (0.10 + i * 0.17), h * 0.20, w * 0.10, h * 0.60),
              Radius.circular(w * 0.02),
            ),
            white,
          );
        }
      case "diamond":
        _diamond(canvas, Offset(w / 2, h / 2), w * 0.30, white);
      case "left_turn_wait":
        _dashed(canvas, Offset(w * 0.38, h * 0.90), Offset(w * 0.22, h * 0.45), line);
        _dashed(canvas, Offset(w * 0.66, h * 0.90), Offset(w * 0.50, h * 0.45), line);
      case "stop_line":
        canvas.drawLine(Offset(w * 0.10, h * 0.26), Offset(w * 0.90, h * 0.26), line);
      case "yield_line_stop":
        canvas.drawLine(Offset(w * 0.10, h * 0.22), Offset(w * 0.90, h * 0.22), line);
        canvas.drawLine(Offset(w * 0.10, h * 0.34), Offset(w * 0.90, h * 0.34), line);
        _label(canvas, "停", Offset(w / 2, h * 0.68), w * 0.34, white);
      case "yield_line_decel":
        _dashed(canvas, Offset(w * 0.10, h * 0.22), Offset(w * 0.90, h * 0.22), line);
        _dashed(canvas, Offset(w * 0.10, h * 0.34), Offset(w * 0.90, h * 0.34), line);
        _triangle(canvas, Offset(w / 2, h * 0.66), w * 0.26, line);
      case "arrows":
        _arrow(canvas, Offset(w / 2, h * 0.52), w * 0.46, line);
      case "bus_lane":
        line.color = _yellow;
        _dashed(canvas, Offset(w * 0.22, h * 0.08), Offset(w * 0.22, h * 0.92), line);
        _dashed(canvas, Offset(w * 0.78, h * 0.08), Offset(w * 0.78, h * 0.92), line);
        _label(canvas, "公交", Offset(w / 2, h / 2), w * 0.30, white);
      case "hov_lane":
        _dashed(canvas, Offset(w * 0.22, h * 0.08), Offset(w * 0.22, h * 0.92), line);
        _dashed(canvas, Offset(w * 0.78, h * 0.08), Offset(w * 0.78, h * 0.92), line);
        _label(canvas, "2+", Offset(w / 2, h / 2), w * 0.34, white);
      case "parking_space":
        canvas.drawRRect(_box(w * 0.14, h * 0.14, w * 0.30, h * 0.72), line);
        canvas.drawRRect(_box(w * 0.56, h * 0.14, w * 0.30, h * 0.72), line);
      case "bus_bay":
        final bay = Path()
          ..moveTo(w * 0.86, h * 0.10)
          ..lineTo(w * 0.86, h * 0.34)
          ..quadraticBezierTo(w * 0.86, h * 0.52, w * 0.62, h * 0.56)
          ..lineTo(w * 0.62, h * 0.74)
          ..quadraticBezierTo(w * 0.62, h * 0.88, w * 0.86, h * 0.90);
        canvas.drawPath(bay, line);
        canvas.drawLine(Offset(w * 0.30, h * 0.10), Offset(w * 0.30, h * 0.90), line);
      case "entrance_exit":
        canvas.drawLine(Offset(w * 0.18, h * 0.06), Offset(w * 0.18, h * 0.94), line);
        final wedge = Path()
          ..moveTo(w * 0.42, h * 0.10)
          ..lineTo(w * 0.86, h * 0.42)
          ..lineTo(w * 0.86, h * 0.82)
          ..close();
        for (var i = 1; i < 5; i++) {
          final t = i / 5;
          canvas.drawLine(
            Offset(w * (0.42 + t * 0.20), h * (0.10 + t * 0.55)),
            Offset(w * (0.42 + t * 0.34), h * (0.10 + t * 0.90)),
            line,
          );
        }
        canvas.drawPath(wedge, line..strokeWidth = w * 0.035);
      case "intersection_guide":
        final guide = Path()
          ..moveTo(w * 0.16, h * 0.30)
          ..quadraticBezierTo(w * 0.52, h * 0.52, w * 0.84, h * 0.74);
        _dashedPath(canvas, guide, line);
      case "center_circle":
        canvas.drawCircle(Offset(w / 2, h / 2), w * 0.24, line);
      case "double_yellow_solid":
        line.color = _yellow;
        canvas.drawLine(Offset(w * 0.40, h * 0.06), Offset(w * 0.40, h * 0.94), line);
        canvas.drawLine(Offset(w * 0.60, h * 0.06), Offset(w * 0.60, h * 0.94), line);
      case "yellow_solid_dashed":
        line.color = _yellow;
        canvas.drawLine(Offset(w * 0.40, h * 0.06), Offset(w * 0.40, h * 0.94), line);
        _dashed(canvas, Offset(w * 0.60, h * 0.06), Offset(w * 0.60, h * 0.94), line);
      case "lane_white_solid":
        canvas.drawLine(Offset(w / 2, h * 0.06), Offset(w / 2, h * 0.94), line);
      case "curb_yellow_solid":
        line.color = _yellow;
        line.strokeWidth = w * 0.08;
        canvas.drawLine(Offset(w * 0.80, h * 0.06), Offset(w * 0.80, h * 0.94), line);
      case "curb_yellow_dashed":
        line.color = _yellow;
        line.strokeWidth = w * 0.08;
        _dashed(canvas, Offset(w * 0.80, h * 0.06), Offset(w * 0.80, h * 0.94), line);
      case "channelization":
        final zone = Path()
          ..moveTo(w * 0.16, h * 0.10)
          ..lineTo(w * 0.84, h * 0.44)
          ..lineTo(w * 0.84, h * 0.90)
          ..lineTo(w * 0.16, h * 0.90)
          ..close();
        canvas.save();
        canvas.clipPath(zone);
        for (var i = -2; i < 8; i++) {
          canvas.drawLine(
            Offset(w * (i * 0.16), h * 0.95),
            Offset(w * (i * 0.16 + 0.4), h * 0.05),
            line,
          );
        }
        canvas.restore();
        canvas.drawPath(zone, line);
      case "grid":
        final zone = Rect.fromLTWH(w * 0.14, h * 0.12, w * 0.72, h * 0.76);
        canvas.save();
        canvas.clipRect(zone);
        for (var i = -4; i < 10; i++) {
          canvas.drawLine(
            Offset(w * (i * 0.12), h * 0.95),
            Offset(w * (i * 0.12 + 0.4), h * 0.05),
            yellow..strokeWidth = w * 0.04,
          );
        }
        canvas.restore();
        canvas.drawRect(zone, yellow..style = PaintingStyle.stroke..strokeWidth = w * 0.05);
      case "width_gradient":
        line.color = _yellow;
        final start = h * 0.10, end = h * 0.90;
        for (var i = 0; i < 6; i++) {
          final t = i / 5;
          final x = w * (0.86 - t * 0.24);
          canvas.drawLine(Offset(x, start + (end - start) * t), Offset(x - w * 0.22, start + (end - start) * t + h * 0.22), line);
        }
        canvas.drawLine(Offset(w * 0.24, end), Offset(w * 0.24, end - h * 0.18), line);
      case "obstacle":
        canvas.save();
        canvas.clipRRect(RRect.fromRectAndRadius(Offset.zero & size, Radius.circular(w * 0.07)));
        final hatch = Paint()..color = _yellow..strokeWidth = w * 0.045;
        for (var i = -2; i < 8; i++) {
          canvas.drawLine(Offset(w * (i * 0.16), h * 0.98), Offset(w * (i * 0.16 + 0.4), h * 0.02), hatch);
        }
        canvas.restore();
        canvas.drawRRect(_box(w * 0.36, h * 0.34, w * 0.28, h * 0.32), Paint()..color = const Color(0xFF8FA3AD));
      case "decel_ribs":
        for (var i = 0; i < 4; i++) {
          final y = h * (0.16 + i * 0.20);
          _diamond(canvas, Offset(w * 0.24, y), w * 0.13, white);
          _diamond(canvas, Offset(w * 0.76, y), w * 0.13, white);
        }
      case "decel_bars":
        for (var i = 0; i < 3; i++) {
          final y = h * (0.26 + i * 0.26);
          canvas.drawLine(Offset(w * 0.16, y), Offset(w * 0.84, y), line);
          canvas.drawLine(Offset(w * 0.16, y + h * 0.06), Offset(w * 0.84, y + h * 0.06), line);
        }
      case "distance_confirm":
        for (var i = 0; i < 3; i++) {
          final rect = Rect.fromCircle(center: Offset(w * (0.28 + i * 0.22), h * 0.70), radius: w * 0.10);
          canvas.drawArc(rect, math.pi, math.pi, false, line);
        }
      default:
        _label(canvas, "？", Offset(w / 2, h / 2), w * 0.5, white);
    }
  }

  RRect _box(double left, double top, double width, double height) =>
      RRect.fromRectAndRadius(Rect.fromLTWH(left, top, width, height), Radius.circular(width * 0.08));

  void _dashed(Canvas canvas, Offset a, Offset b, Paint paint, {double dash = 10, double gap = 7}) {
    final total = (b - a).distance;
    if (total == 0) return;
    final dir = (b - a) / total;
    final step = paint.strokeWidth * dash / 5.5;
    final space = paint.strokeWidth * gap / 5.5;
    var d = 0.0;
    while (d < total) {
      final end = math.min(d + step, total);
      canvas.drawLine(a + dir * d, a + dir * end, paint);
      d = end + space;
    }
  }

  void _dashedPath(Canvas canvas, Path path, Paint paint) {
    for (final metric in path.computeMetrics()) {
      final step = paint.strokeWidth * 1.9;
      final space = paint.strokeWidth * 1.4;
      var d = 0.0;
      while (d < metric.length) {
        final end = math.min(d + step, metric.length);
        canvas.drawPath(metric.extractPath(d, end), paint);
        d = end + space;
      }
    }
  }

  void _zigzag(Canvas canvas, Offset a, Offset b, Paint paint) {
    final path = Path()..moveTo(a.dx, a.dy);
    const teeth = 9;
    final amplitude = paint.strokeWidth * 1.2;
    for (var i = 1; i <= teeth; i++) {
      final t = i / teeth;
      path.lineTo(a.dx + (i.isOdd ? amplitude : -amplitude), a.dy + (b.dy - a.dy) * t);
    }
    canvas.drawPath(path, paint..style = PaintingStyle.stroke);
  }

  void _diamond(Canvas canvas, Offset center, double radius, Paint paint) {
    final path = Path()
      ..moveTo(center.dx, center.dy - radius)
      ..lineTo(center.dx + radius * 0.62, center.dy)
      ..lineTo(center.dx, center.dy + radius)
      ..lineTo(center.dx - radius * 0.62, center.dy)
      ..close();
    canvas.drawPath(path, paint);
  }

  void _arrow(Canvas canvas, Offset center, double height, Paint line) {
    final shaftTop = center.translate(0, -height * 0.5);
    final shaftBottom = center.translate(0, height * 0.5);
    canvas.drawLine(shaftTop.translate(0, height * 0.22), shaftBottom, line);
    final head = Path()
      ..moveTo(center.dx, center.dy - height * 0.5)
      ..lineTo(center.dx - height * 0.26, center.dy - height * 0.10)
      ..lineTo(center.dx + height * 0.26, center.dy - height * 0.10)
      ..close();
    canvas.drawPath(head, Paint()..color = line.color);
  }

  void _triangle(Canvas canvas, Offset apex, double size, Paint line) {
    final path = Path()
      ..moveTo(apex.dx, apex.dy - size * 0.5)
      ..lineTo(apex.dx - size * 0.5, apex.dy + size * 0.5)
      ..lineTo(apex.dx + size * 0.5, apex.dy + size * 0.5)
      ..close();
    canvas.drawPath(path, line);
  }

  void _label(Canvas canvas, String text, Offset center, double fontSize, Paint paint) {
    final painter = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(fontSize: fontSize, color: paint.color, fontWeight: FontWeight.w700, height: 1.0),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    painter.paint(canvas, center - Offset(painter.width / 2, painter.height / 2));
  }

  @override
  bool shouldRepaint(covariant _MarkingPainter old) => old.id != id;
}
