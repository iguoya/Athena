import "dart:math" as math;

import "package:flutter/material.dart";

/// 车内符号示意（ADR 0067）：深色灯底 + 红/黄报警、蓝/绿指示的几何符号，
/// 表盘画表盘弧加指针。只求一格认出一个符号、记住它的颜色语义。
class GaugeView extends StatelessWidget {
  const GaugeView({super.key, required this.id, this.size = 120});

  final String id;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: "车内符号示意 $id",
      child: CustomPaint(
        size: Size.square(size),
        painter: _GaugePainter(id),
      ),
    );
  }
}

/// `_GaugePainter` 画得出来的全部 id（ADR 0067）：加新符号时，这个清单与下面
/// switch 的 case 同步加。`content/gauges.json` 的每条 id 都必须落在这个集合里，
/// test/gauges_page_test.dart 守住——漏画就会落到 switch 兜底的问号图。
const paintableGaugeIds = {
  // 报警灯
  "seat_belt",
  "abs_fault",
  "oil_pressure",
  "coolant_temp",
  "brake_system",
  "airbag_fault",
  "fuel_low",
  "door_open",
  "battery",
  "parking_brake",
  "trunk_open",
  "hood_open",
  "engine_fault",
  "tire_pressure",
  "esc_fault",
  // 指示灯
  "high_beam",
  "low_beam",
  "turn_signal",
  "hazard",
  "position_lamp",
  "front_fog",
  "rear_fog",
  // 仪表表盘
  "speedometer",
  "tachometer",
  "water_temp_gauge",
  "fuel_gauge",
  // 开关与操纵件
  "wiper_switch",
  "light_switch",
  "hvac_fan",
  "air_cycle",
  "ignition",
  "parking_lever",
  "gear_lever",
  "pedals",
};

class _GaugePainter extends CustomPainter {
  _GaugePainter(this.id);

  final String id;

  static const _lamp = Color(0xFF171C21);
  static const _red = Color(0xFFE53935);
  static const _yellow = Color(0xFFFDD835);
  static const _green = Color(0xFF43A047);
  static const _blue = Color(0xFF1E88E5);
  static const _white = Color(0xFFE8ECEE);

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width, h = size.height;
    canvas.drawRRect(
      RRect.fromRectAndRadius(Offset.zero & size, Radius.circular(w * 0.16)),
      Paint()..color = _lamp,
    );
    canvas.translate(w / 2, h / 2);
    switch (id) {
      case "seat_belt":
        _person(canvas, w * 0.16, _red);
        canvas.drawLine(Offset(-w * 0.10, -h * 0.20), Offset(w * 0.26, h * 0.30), _stroke(_red, w * 0.07));
      case "abs_fault":
        _ring(canvas, _yellow, w * 0.30, w * 0.055);
        _label(canvas, "ABS", w * 0.17, _yellow);
      case "oil_pressure":
        _oilCan(canvas, _red, w);
      case "coolant_temp":
        _thermometer(canvas, _red, w);
        _waves(canvas, Offset(0, h * 0.24), w * 0.26, _stroke(_red, w * 0.045));
      case "brake_system":
        _brakeCircle(canvas, _red, w);
      case "airbag_fault":
        _person(canvas, w * 0.14, _red);
        canvas.drawCircle(Offset(w * 0.20, -h * 0.04), w * 0.11, Paint()..style = PaintingStyle.stroke..color = _red..strokeWidth = w * 0.045);
      case "fuel_low":
        _pump(canvas, _yellow, w, h);
      case "door_open":
        _carTop(canvas, _red, w, h, doors: true);
      case "battery":
        _battery(canvas, _red, w);
      case "parking_brake":
        _brakeCircle(canvas, _red, w, letter: "P");
      case "trunk_open":
        _carTop(canvas, _red, w, h, trunk: true);
      case "hood_open":
        _carTop(canvas, _red, w, h, hood: true);
      case "engine_fault":
        _engineBlock(canvas, _yellow, w);
      case "tire_pressure":
        _horseshoe(canvas, _yellow, w);
        _label(canvas, "!", w * 0.13, _yellow);
      case "esc_fault":
        _carSide(canvas, _yellow, w);
        final skid = Path()
          ..moveTo(-w * 0.34, h * 0.30)
          ..quadraticBezierTo(-w * 0.16, h * 0.12, -w * 0.30, h * 0.02);
        canvas.drawPath(skid, _stroke(_yellow, w * 0.045));
      case "high_beam":
        _beam(canvas, _blue, w, slant: false);
      case "low_beam":
        _beam(canvas, _green, w, slant: true);
      case "turn_signal":
        _arrowLeft(canvas, _green, w);
      case "hazard":
        _triangleAt(canvas, Offset(-w * 0.15, 0), w * 0.26, _red);
        _triangleAt(canvas, Offset(w * 0.15, 0), w * 0.26, _red);
      case "position_lamp":
        _lampRays(canvas, _green, w, count: 3, spread: 0.35);
      case "front_fog":
        _fogLamp(canvas, _green, w);
      case "rear_fog":
        _fogLamp(canvas, _yellow, w);
      case "speedometer":
        _dial(canvas, w, caption: "km/h");
      case "tachometer":
        _dial(canvas, w, caption: "r/min");
      case "water_temp_gauge":
        _dial(canvas, w, caption: "℃");
      case "fuel_gauge":
        _dial(canvas, w, caption: null);
        _pump(canvas, _white, w * 0.62, h * 0.62);
      case "wiper_switch":
        _wiper(canvas, _white, w);
      case "light_switch":
        _bulb(canvas, _white, w);
      case "hvac_fan":
        _fan(canvas, _white, w);
      case "air_cycle":
        _cycleArrow(canvas, _white, w);
      case "ignition":
        _ignition(canvas, _white, w);
      case "parking_lever":
        _parkingLever(canvas, _white, w);
      case "gear_lever":
        _gearGate(canvas, _white, w, h);
      case "pedals":
        _pedals(canvas, _white, w, h);
      default:
        _label(canvas, "？", w * 0.5, _white);
    }
  }

  Paint _stroke(Color color, double width) => Paint()
    ..color = color
    ..style = PaintingStyle.stroke
    ..strokeWidth = width
    ..strokeCap = StrokeCap.round;

  void _ring(Canvas canvas, Color color, double radius, double width) =>
      canvas.drawCircle(Offset.zero, radius, _stroke(color, width));

  void _triangleAt(Canvas canvas, Offset center, double size, Color color) {
    final path = Path()
      ..moveTo(center.dx, center.dy - size * 0.62)
      ..lineTo(center.dx - size * 0.62, center.dy + size * 0.5)
      ..lineTo(center.dx + size * 0.62, center.dy + size * 0.5)
      ..close();
    canvas.drawPath(path, Paint()..color = color);
  }

  void _label(Canvas canvas, String text, double fontSize, Color color) {
    final painter = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(fontSize: fontSize, color: color, fontWeight: FontWeight.w800, height: 1.0),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    painter.paint(canvas, Offset(-painter.width / 2, -painter.height / 2));
  }

  /// 侧坐小人：圆头 + 躯干弧 + 座位线。
  void _person(Canvas canvas, double r, Color color) {
    final paint = _stroke(color, r * 0.42);
    canvas.drawCircle(Offset(-r * 0.9, -r * 1.1), r * 0.62, Paint()..color = color);
    final body = Path()
      ..moveTo(-r * 0.9, -r * 0.2)
      ..quadraticBezierTo(-r * 0.7, r * 0.8, -r * 1.3, r * 1.5);
    canvas.drawPath(body, paint);
    canvas.drawLine(Offset(-r * 1.9, r * 1.5), Offset(r * 1.6, r * 1.5), paint);
  }

  /// 油壶：壶体 + 壶嘴 + 一滴油。
  void _oilCan(Canvas canvas, Color color, double w) {
    final body = RRect.fromRectAndRadius(
      Rect.fromLTWH(-w * 0.28, -w * 0.10, w * 0.44, w * 0.34),
      Radius.circular(w * 0.05),
    );
    canvas.drawRRect(body, Paint()..color = color);
    final spout = Path()
      ..moveTo(w * 0.14, -w * 0.06)
      ..lineTo(w * 0.38, -w * 0.24)
      ..lineTo(w * 0.40, -w * 0.10)
      ..close();
    canvas.drawPath(spout, Paint()..color = color);
    canvas.drawCircle(Offset(-w * 0.40, w * 0.22), w * 0.05, Paint()..color = color);
    canvas.drawLine(Offset(-w * 0.16, -w * 0.10), Offset(-w * 0.16, -w * 0.26), _stroke(color, w * 0.06));
  }

  /// 温度计：竖管 + 底球。
  void _thermometer(Canvas canvas, Color color, double w) {
    final paint = _stroke(color, w * 0.05);
    canvas.drawLine(Offset(0, -w * 0.30), Offset(0, w * 0.10), paint);
    canvas.drawCircle(Offset(0, w * 0.18), w * 0.09, Paint()..color = color);
    canvas.drawCircle(Offset(0, w * 0.18), w * 0.09, paint);
  }

  void _waves(Canvas canvas, Offset center, double width, Paint paint) {
    for (var row = 0; row < 2; row++) {
      final path = Path()..moveTo(center.dx - width / 2, center.dy + row * width * 0.34);
      for (var i = 0; i < 3; i++) {
        final x0 = center.dx - width / 2 + i * width / 3;
        path.quadraticBezierTo(x0 + width / 6, center.dy + row * width * 0.34 + width * 0.18, x0 + width / 3, center.dy + row * width * 0.34);
      }
      canvas.drawPath(path, paint);
    }
  }

  /// 制动 / 驻车制动：两侧括号 + 圆 + 感叹号或 P。
  void _brakeCircle(Canvas canvas, Color color, double w, {String letter = "!"}) {
    final paint = _stroke(color, w * 0.05);
    _ring(canvas, color, w * 0.20, w * 0.05);
    _label(canvas, letter, w * 0.20, color);
    for (final side in [-1.0, 1.0]) {
      final path = Path()
        ..moveTo(side * w * 0.26, -w * 0.26)
        ..quadraticBezierTo(side * w * 0.40, 0, side * w * 0.26, w * 0.26);
      canvas.drawPath(path, paint);
    }
  }

  /// 加油机：机身 + 油枪臂。
  void _pump(Canvas canvas, Color color, double w, double h) {
    final scale = w / 120;
    final body = RRect.fromRectAndRadius(
      Rect.fromLTWH(-46 * scale, -44 * scale, 60 * scale, 88 * scale),
      Radius.circular(6 * scale),
    );
    canvas.drawRRect(body, _stroke(color, 7 * scale));
    canvas.drawRect(Rect.fromLTWH(-32 * scale, -30 * scale, 32 * scale, 22 * scale), _stroke(color, 5 * scale));
    final arm = Path()
      ..moveTo(14 * scale, -6 * scale)
      ..lineTo(40 * scale, -6 * scale)
      ..lineTo(40 * scale, 22 * scale);
    canvas.drawPath(arm, _stroke(color, 6 * scale));
    canvas.drawCircle(Offset(40 * scale, 26 * scale), 5 * scale, Paint()..color = color);
  }

  /// 俯视车 + 门 / 舱盖开启线。
  void _carTop(Canvas canvas, Color color, double w, double h, {bool doors = false, bool trunk = false, bool hood = false}) {
    final paint = _stroke(color, w * 0.045);
    final body = RRect.fromRectAndRadius(
      Rect.fromLTWH(-w * 0.20, -h * 0.36, w * 0.40, h * 0.72),
      Radius.circular(w * 0.12),
    );
    canvas.drawRRect(body, paint);
    if (doors) {
      canvas.drawLine(Offset(-w * 0.30, -h * 0.16), Offset(-w * 0.20, -h * 0.10), paint);
      canvas.drawLine(Offset(-w * 0.30, h * 0.16), Offset(-w * 0.20, h * 0.10), paint);
      canvas.drawLine(Offset(w * 0.30, -h * 0.16), Offset(w * 0.20, -h * 0.10), paint);
      canvas.drawLine(Offset(w * 0.30, h * 0.16), Offset(w * 0.20, h * 0.10), paint);
    }
    if (trunk) canvas.drawLine(Offset(-w * 0.14, h * 0.36), Offset(w * 0.14, h * 0.36), _stroke(color, w * 0.06));
    if (hood) canvas.drawLine(Offset(-w * 0.14, -h * 0.36), Offset(w * 0.14, -h * 0.36), _stroke(color, w * 0.06));
  }

  void _battery(Canvas canvas, Color color, double w) {
    final paint = _stroke(color, w * 0.05);
    canvas.drawRRect(
      RRect.fromRectAndRadius(Rect.fromLTWH(-w * 0.30, -w * 0.18, w * 0.60, w * 0.36), Radius.circular(w * 0.04)),
      paint,
    );
    canvas.drawRect(Rect.fromLTWH(-w * 0.36, -w * 0.08, w * 0.06, w * 0.16), Paint()..color = color);
    canvas.drawRect(Rect.fromLTWH(w * 0.30, -w * 0.08, w * 0.06, w * 0.16), Paint()..color = color);
    _label(canvas, "+ −", w * 0.14, color);
  }

  /// 发动机侧轮廓：锯齿形缸体。
  void _engineBlock(Canvas canvas, Color color, double w) {
    final path = Path()
      ..moveTo(-w * 0.30, w * 0.16)
      ..lineTo(-w * 0.30, -w * 0.04)
      ..lineTo(-w * 0.16, -w * 0.04)
      ..lineTo(-w * 0.10, -w * 0.20)
      ..lineTo(w * 0.08, -w * 0.20)
      ..lineTo(w * 0.14, -w * 0.04)
      ..lineTo(w * 0.30, -w * 0.04)
      ..lineTo(w * 0.30, w * 0.10)
      ..lineTo(w * 0.16, w * 0.10)
      ..lineTo(w * 0.10, w * 0.24)
      ..lineTo(-w * 0.16, w * 0.24)
      ..lineTo(-w * 0.22, w * 0.16)
      ..close();
    canvas.drawPath(path, _stroke(color, w * 0.05));
  }

  /// 蹄形（轮胎剖面）。
  void _horseshoe(Canvas canvas, Color color, double w) {
    final path = Path()
      ..arcTo(Rect.fromCircle(center: Offset.zero, radius: w * 0.26), 0.6, math.pi * 1.8, false);
    canvas.drawPath(path, _stroke(color, w * 0.09));
  }

  /// 侧视车 + 打滑轨迹。
  void _carSide(Canvas canvas, Color color, double w) {
    final paint = _stroke(color, w * 0.045);
    final body = Path()
      ..moveTo(-w * 0.30, w * 0.10)
      ..lineTo(-w * 0.20, -w * 0.02)
      ..quadraticBezierTo(-w * 0.05, -w * 0.16, w * 0.12, -w * 0.04)
      ..lineTo(w * 0.30, w * 0.02)
      ..close();
    canvas.drawPath(body, paint);
    canvas.drawCircle(Offset(-w * 0.16, w * 0.12), w * 0.05, Paint()..color = color);
    canvas.drawCircle(Offset(w * 0.18, w * 0.12), w * 0.05, Paint()..color = color);
  }

  /// 灯束：灯座半圆 + 平行线（远光直、近光斜下）。
  void _beam(Canvas canvas, Color color, double w, {required bool slant}) {
    final paint = _stroke(color, w * 0.045);
    final lamp = Path()
      ..arcTo(
        Rect.fromCircle(center: Offset(-w * 0.16, 0), radius: w * 0.16),
        -math.pi / 2,
        math.pi,
        false,
      )
      ..close();
    canvas.drawPath(lamp, paint);
    for (var i = -1; i <= 1; i++) {
      final y = i * w * 0.15;
      if (slant) {
        canvas.drawLine(Offset(w * 0.02, y - w * 0.04), Offset(w * 0.34, y + w * 0.10), paint);
      } else {
        canvas.drawLine(Offset(w * 0.02, y), Offset(w * 0.36, y), paint);
      }
    }
  }

  void _arrowLeft(Canvas canvas, Color color, double w) {
    final path = Path()
      ..moveTo(-w * 0.30, 0)
      ..lineTo(-w * 0.02, -w * 0.20)
      ..lineTo(-w * 0.02, -w * 0.08)
      ..lineTo(w * 0.30, -w * 0.08)
      ..lineTo(w * 0.30, w * 0.08)
      ..lineTo(-w * 0.02, w * 0.08)
      ..lineTo(-w * 0.02, w * 0.20)
      ..close();
    canvas.drawPath(path, Paint()..color = color);
  }

  void _lampRays(Canvas canvas, Color color, double w, {required int count, required double spread}) {
    final paint = _stroke(color, w * 0.05);
    final lamp = Path()
      ..arcTo(Rect.fromCircle(center: Offset(-w * 0.14, 0), radius: w * 0.15), -math.pi / 2, math.pi, false)
      ..close();
    canvas.drawPath(lamp, paint);
    for (var i = 0; i < count; i++) {
      final angle = -spread + (2 * spread) * i / (count - 1);
      final dir = Offset(math.cos(angle), math.sin(angle));
      canvas.drawLine(
        dir * w * 0.20 + Offset(-w * 0.14, 0) * 0.2,
        dir * w * 0.38 + Offset(-w * 0.14, 0) * 0.2,
        paint,
      );
    }
  }

  void _fogLamp(Canvas canvas, Color color, double w) {
    final paint = _stroke(color, w * 0.045);
    final lamp = Path()
      ..arcTo(Rect.fromCircle(center: Offset(-w * 0.14, 0), radius: w * 0.15), -math.pi / 2, math.pi, false)
      ..close();
    canvas.drawPath(lamp, paint);
    canvas.drawLine(Offset(-w * 0.14, -w * 0.15), Offset(-w * 0.14, w * 0.15), _stroke(color, w * 0.05));
    for (var i = 0; i < 2; i++) {
      final path = Path()
        ..moveTo(w * (0.06 + i * 0.12), -w * 0.20)
        ..quadraticBezierTo(w * (0.0 + i * 0.12), 0, w * (0.06 + i * 0.12), w * 0.20);
      canvas.drawPath(path, paint);
    }
  }

  /// 表盘：下半圆刻度弧 + 指针 + 底部小字。
  void _dial(Canvas canvas, double w, {required String? caption}) {
    final paint = _stroke(_white, w * 0.045);
    canvas.drawArc(Rect.fromCircle(center: Offset(0, w * 0.10), radius: w * 0.30), math.pi, math.pi, false, paint);
    for (var i = 0; i <= 6; i++) {
      final angle = math.pi + math.pi * i / 6;
      final outer = Offset(math.cos(angle) * w * 0.30, w * 0.10 + math.sin(angle) * w * 0.30);
      final inner = Offset(math.cos(angle) * w * 0.24, w * 0.10 + math.sin(angle) * w * 0.24);
      canvas.drawLine(outer, inner, paint);
    }
    final needle = Paint()..color = _red..strokeWidth = w * 0.05..strokeCap = StrokeCap.round;
    canvas.drawLine(Offset(0, w * 0.10), Offset(-w * 0.10, -w * 0.20), needle);
    canvas.drawCircle(Offset(0, w * 0.10), w * 0.045, Paint()..color = _white);
    if (caption != null) _labelAt(canvas, caption, Offset(0, w * 0.36), w * 0.11, _white);
  }

  void _labelAt(Canvas canvas, String text, Offset center, double fontSize, Color color) {
    final painter = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(fontSize: fontSize, color: color, fontWeight: FontWeight.w700, height: 1.0),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    painter.paint(canvas, center - Offset(painter.width / 2, painter.height / 2));
  }

  void _wiper(Canvas canvas, Color color, double w) {
    final paint = _stroke(color, w * 0.05);
    canvas.drawArc(
      Rect.fromCircle(center: Offset(0, w * 0.34), radius: w * 0.42),
      -math.pi * 0.82,
      math.pi * 0.64,
      false,
      paint,
    );
    canvas.drawLine(Offset(-w * 0.10, w * 0.06), Offset(-w * 0.02, -w * 0.32), _stroke(color, w * 0.06));
    canvas.drawLine(Offset(-w * 0.02, -w * 0.32), Offset(w * 0.10, -w * 0.26), _stroke(color, w * 0.045));
  }

  void _bulb(Canvas canvas, Color color, double w) {
    final paint = _stroke(color, w * 0.05);
    canvas.drawCircle(Offset(0, -w * 0.06), w * 0.15, paint);
    canvas.drawCircle(Offset(0, -w * 0.06), w * 0.06, Paint()..color = color);
    canvas.drawLine(Offset(0, w * 0.09), Offset(0, w * 0.24), paint);
    for (var i = 0; i < 4; i++) {
      final angle = -math.pi * 0.9 + math.pi * 1.8 * i / 3;
      final dir = Offset(math.cos(angle), math.sin(angle));
      canvas.drawLine(dir * w * 0.21, dir * w * 0.32, paint);
    }
  }

  void _fan(Canvas canvas, Color color, double w) {
    final paint = Paint()..color = color;
    for (var i = 0; i < 3; i++) {
      canvas.save();
      canvas.rotate(2 * math.pi * i / 3);
      final blade = Path()
        ..moveTo(0, 0)
        ..quadraticBezierTo(w * 0.26, -w * 0.10, w * 0.10, -w * 0.32)
        ..quadraticBezierTo(w * 0.04, -w * 0.12, 0, 0);
      canvas.drawPath(blade, paint);
      canvas.restore();
    }
    canvas.drawCircle(Offset.zero, w * 0.06, Paint()..color = _lamp);
    canvas.drawCircle(Offset.zero, w * 0.06, _stroke(color, w * 0.03));
  }

  void _cycleArrow(Canvas canvas, Color color, double w) {
    final paint = _stroke(color, w * 0.06);
    final path = Path()
      ..moveTo(-w * 0.22, -w * 0.14)
      ..quadraticBezierTo(0, -w * 0.40, w * 0.24, -w * 0.12)
      ..quadraticBezierTo(w * 0.30, 0, w * 0.22, w * 0.10)
      ..quadraticBezierTo(0, w * 0.34, -w * 0.24, w * 0.10)
      ..quadraticBezierTo(-w * 0.30, 0, -w * 0.24, -w * 0.10)
      ..close();
    canvas.drawPath(path, paint);
    final head = Path()
      ..moveTo(-w * 0.24, -w * 0.28)
      ..lineTo(-w * 0.24, -w * 0.06)
      ..lineTo(-w * 0.02, -w * 0.14)
      ..close();
    canvas.drawPath(head, Paint()..color = color);
  }

  void _ignition(Canvas canvas, Color color, double w) {
    final paint = _stroke(color, w * 0.055);
    _ring(canvas, color, w * 0.22, w * 0.055);
    canvas.drawLine(Offset(w * 0.16, -w * 0.16), Offset(w * 0.34, -w * 0.34), paint);
    canvas.drawCircle(Offset(w * 0.38, -w * 0.38), w * 0.05, Paint()..color = color);
    final arrow = Path()
      ..moveTo(-w * 0.34, w * 0.10)
      ..quadraticBezierTo(-w * 0.30, w * 0.30, -w * 0.06, w * 0.36);
    canvas.drawPath(arrow, paint);
  }

  void _parkingLever(Canvas canvas, Color color, double w) {
    final paint = _stroke(color, w * 0.07);
    canvas.drawLine(Offset(-w * 0.26, w * 0.22), Offset(w * 0.20, -w * 0.22), paint);
    canvas.drawCircle(Offset(w * 0.26, -w * 0.28), w * 0.08, Paint()..color = color);
    canvas.drawLine(Offset(-w * 0.36, w * 0.26), Offset(-w * 0.10, w * 0.26), _stroke(color, w * 0.06));
  }

  void _gearGate(Canvas canvas, Color color, double w, double h) {
    final paint = _stroke(color, w * 0.05);
    canvas.drawLine(Offset(-w * 0.14, -h * 0.22), Offset(-w * 0.14, h * 0.22), paint);
    canvas.drawLine(Offset(w * 0.14, -h * 0.10), Offset(w * 0.14, h * 0.22), paint);
    canvas.drawLine(Offset(-w * 0.14, 0), Offset(w * 0.14, 0), paint);
    canvas.drawCircle(Offset(-w * 0.14, -h * 0.22), w * 0.06, Paint()..color = color);
    _labelAt(canvas, "R", Offset(w * 0.30, -h * 0.10), w * 0.13, color);
  }

  void _pedals(Canvas canvas, Color color, double w, double h) {
    final paint = Paint()..color = color;
    for (var i = 0; i < 3; i++) {
      final x = -w * 0.22 + i * w * 0.22;
      final height = i == 2 ? h * 0.26 : h * 0.38;
      canvas.drawRRect(
        RRect.fromRectAndRadius(Rect.fromLTWH(x - w * 0.06, -height, w * 0.12, height * 2), Radius.circular(w * 0.05)),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _GaugePainter old) => old.id != id;
}
