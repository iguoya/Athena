import "dart:math";

import "package:flutter/material.dart";

const _red = Color(0xFFC62828);
const _yellow = Color(0xFFF9A825);
const _blue = Color(0xFF1565C0);
const _green = Color(0xFF2E7D32);

class SignView extends StatelessWidget {
  const SignView({super.key, required this.id, this.size = 120});

  final String id;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: "交通标志示意 $id",
      child: CustomPaint(
        size: Size.square(size),
        painter: _SignPainter(id),
      ),
    );
  }
}

class _SignPainter extends CustomPainter {
  _SignPainter(this.id);

  final String id;

  @override
  void paint(Canvas canvas, Size size) {
    final side = min(size.width, size.height);
    canvas.translate((size.width - side) / 2, (size.height - side) / 2);
    switch (id) {
      case "no_entry":
        _noEntry(canvas, side);
      case "no_vehicles":
        _noVehicles(canvas, side);
      case "no_parking":
        _blueBan(canvas, side, cross: false);
      case "no_stopping":
        _blueBan(canvas, side, cross: true);
      case "speed_40":
        _speed(canvas, side, "40", _red);
      case "speed_60":
        _speed(canvas, side, "60", _red);
      case "speed_80":
        _speed(canvas, side, "80", _red);
      case "no_horn":
        _banSymbol(canvas, side, _horn);
      case "no_overtaking":
        _banSymbol(canvas, side, _twoCars);
      case "no_left":
        _banSymbol(canvas, side, (c, s) => _arrow(c, s, -pi / 2));
      case "no_right":
        _banSymbol(canvas, side, (c, s) => _arrow(c, s, pi / 2));
      case "no_u_turn":
        _banSymbol(canvas, side, _uTurn);
      case "yield":
        _inverted(canvas, side, null);
      case "stop":
        _octagon(canvas, side);
      case "no_pedestrian":
        _banSymbol(canvas, side, (c, s) => _person(c, Offset(s / 2, s * 0.72), s * 0.42, Colors.black));
      case "warning":
        _warning(canvas, side, (c, box) => _label(c, box.center, "!", box.height * 0.7, Colors.black));
      case "warning_pedestrian":
        _warning(canvas, side, (c, box) => _person(c, Offset(box.center.dx, box.bottom - 2), box.height * 0.85, Colors.black));
      case "warning_children":
        _warning(canvas, side, _children);
      case "warning_cross":
        _warning(canvas, side, _crossroads);
      case "warning_curve":
        _warning(canvas, side, _curve);
      case "warning_slope":
        _warning(canvas, side, _slope);
      case "warning_slip":
        _warning(canvas, side, _slip);
      case "warning_work":
        _warning(canvas, side, (c, box) => _label(c, box.center, "工", box.height * 0.55, Colors.black));
      case "warning_rail":
        _warning(canvas, side, _rail);
      case "warning_village":
        _warning(canvas, side, _house);
      case "indicate":
      case "pedestrian":
        _blueDisk(canvas, side, (c, s) => _person(c, Offset(s / 2, s * 0.74), s * 0.46, Colors.white));
      case "go_straight":
        _blueDisk(canvas, side, (c, s) => _arrow(c, s, 0));
      case "turn_left":
        _blueDisk(canvas, side, (c, s) => _arrow(c, s, -pi / 2));
      case "turn_right":
        _blueDisk(canvas, side, (c, s) => _arrow(c, s, pi / 2));
      case "min_speed":
        _speed(canvas, side, "60", _blue);
      case "roundabout":
        _blueDisk(canvas, side, _roundabout);
      case "motor_lane":
        _blueDisk(canvas, side, (c, s) => _car(c, Offset(s / 2, s * 0.52), s * 0.42, Colors.white));
      case "guide":
        _guide(canvas, side);
      case "diamond":
        _diamond(canvas, side);
      case "headlights":
        _headlights(canvas, side);
      default:
        _speed(canvas, side, "?", _red);
    }
  }

  void _noEntry(Canvas canvas, double side) {
    final center = Offset(side / 2, side / 2);
    final radius = side * 0.42;
    canvas.drawCircle(center, radius, Paint()..color = _red);
    canvas.drawCircle(center, radius * 0.82, Paint()..color = Colors.white);
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromCenter(center: center, width: radius * 1.35, height: radius * 0.28),
        const Radius.circular(4),
      ),
      Paint()..color = _red,
    );
  }

  void _noVehicles(Canvas canvas, double side) {
    final center = Offset(side / 2, side / 2);
    canvas.drawCircle(center, side * 0.42, Paint()..color = _red);
    canvas.drawCircle(center, side * 0.34, Paint()..color = Colors.white);
  }

  void _blueBan(Canvas canvas, double side, {required bool cross}) {
    final center = Offset(side / 2, side / 2);
    canvas.drawCircle(center, side * 0.42, Paint()..color = _red);
    canvas.drawCircle(center, side * 0.34, Paint()..color = _blue);
    final paint = Paint()
      ..color = _red
      ..strokeWidth = side * 0.08
      ..strokeCap = StrokeCap.round;
    if (cross) {
      canvas.drawLine(Offset(side * 0.28, side * 0.28), Offset(side * 0.72, side * 0.72), paint);
      canvas.drawLine(Offset(side * 0.72, side * 0.28), Offset(side * 0.28, side * 0.72), paint);
    } else {
      _slash(canvas, side);
    }
  }

  void _speed(Canvas canvas, double side, String text, Color ring) {
    final center = Offset(side / 2, side / 2);
    final radius = side * 0.42;
    if (ring == _blue) {
      canvas.drawCircle(center, radius, Paint()..color = _blue);
      _label(canvas, center, text, side * 0.28, Colors.white);
      return;
    }
    canvas.drawCircle(center, radius, Paint()..color = ring);
    canvas.drawCircle(center, radius * 0.78, Paint()..color = Colors.white);
    _label(canvas, center, text, side * 0.28, Colors.black);
  }

  void _banSymbol(Canvas canvas, double side, void Function(Canvas, double) glyph) {
    final center = Offset(side / 2, side / 2);
    canvas.drawCircle(center, side * 0.42, Paint()..color = _red);
    canvas.drawCircle(center, side * 0.33, Paint()..color = Colors.white);
    glyph(canvas, side);
    _slash(canvas, side);
  }

  void _blueDisk(Canvas canvas, double side, void Function(Canvas, double) glyph) {
    canvas.drawCircle(Offset(side / 2, side / 2), side * 0.42, Paint()..color = _blue);
    glyph(canvas, side);
  }

  void _warning(Canvas canvas, double side, void Function(Canvas, Rect) glyph) {
    final path = Path()
      ..moveTo(side / 2, side * 0.08)
      ..lineTo(side * 0.92, side * 0.88)
      ..lineTo(side * 0.08, side * 0.88)
      ..close();
    canvas.drawPath(path, Paint()..color = _yellow);
    canvas.drawPath(
      path,
      Paint()
        ..color = Colors.black
        ..style = PaintingStyle.stroke
        ..strokeWidth = side * 0.055
        ..strokeJoin = StrokeJoin.round,
    );
    glyph(canvas, Rect.fromLTRB(side * 0.28, side * 0.36, side * 0.72, side * 0.82));
  }

  void _inverted(Canvas canvas, double side, String? text) {
    final outer = Path()
      ..moveTo(side * 0.08, side * 0.14)
      ..lineTo(side * 0.92, side * 0.14)
      ..lineTo(side / 2, side * 0.9)
      ..close();
    canvas.drawPath(outer, Paint()..color = _red);
    final inner = Path()
      ..moveTo(side * 0.2, side * 0.22)
      ..lineTo(side * 0.8, side * 0.22)
      ..lineTo(side / 2, side * 0.74)
      ..close();
    canvas.drawPath(inner, Paint()..color = Colors.white);
    if (text != null) {
      _label(canvas, Offset(side / 2, side * 0.38), text, side * 0.22, Colors.black);
    }
  }

  /// 停车让行是八角形红底白字，减速让行是倒三角——形状本身就是这两个标志的区别，
  /// 画成同一种形状等于把考点抹平了。
  void _octagon(Canvas canvas, double side) {
    final center = Offset(side / 2, side / 2);
    final radius = side * 0.46;
    final path = Path();
    for (var i = 0; i < 8; i++) {
      final angle = pi / 8 + i * pi / 4;
      final point = Offset(center.dx + radius * cos(angle), center.dy + radius * sin(angle));
      if (i == 0) {
        path.moveTo(point.dx, point.dy);
      } else {
        path.lineTo(point.dx, point.dy);
      }
    }
    path.close();
    canvas.drawPath(path, Paint()..color = _red);
    canvas.drawPath(
      path,
      Paint()
        ..color = Colors.white
        ..style = PaintingStyle.stroke
        ..strokeWidth = side * 0.05,
    );
    _label(canvas, center, "停", side * 0.4, Colors.white);
  }

  void _slash(Canvas canvas, double side) {
    canvas.drawLine(
      Offset(side * 0.24, side * 0.76),
      Offset(side * 0.76, side * 0.24),
      Paint()
        ..color = _red
        ..strokeWidth = side * 0.08
        ..strokeCap = StrokeCap.round,
    );
  }

  void _horn(Canvas canvas, double side) {
    final paint = Paint()..color = Colors.black;
    canvas.drawRect(Rect.fromLTWH(side * 0.32, side * 0.42, side * 0.16, side * 0.16), paint);
    final bell = Path()
      ..moveTo(side * 0.48, side * 0.4)
      ..lineTo(side * 0.68, side * 0.32)
      ..lineTo(side * 0.68, side * 0.68)
      ..lineTo(side * 0.48, side * 0.6)
      ..close();
    canvas.drawPath(bell, paint);
  }

  void _twoCars(Canvas canvas, double side) {
    _car(canvas, Offset(side * 0.38, side * 0.58), side * 0.28, Colors.black);
    _car(canvas, Offset(side * 0.62, side * 0.42), side * 0.28, const Color(0xFF424242));
  }

  void _uTurn(Canvas canvas, double side) {
    final paint = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.stroke
      ..strokeWidth = side * 0.07
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(Rect.fromCircle(center: Offset(side / 2, side * 0.5), radius: side * 0.16), pi, pi, false, paint);
    canvas.drawLine(Offset(side * 0.34, side * 0.5), Offset(side * 0.34, side * 0.68), paint);
    canvas.drawLine(Offset(side * 0.66, side * 0.5), Offset(side * 0.66, side * 0.38), paint);
    final head = Path()
      ..moveTo(side * 0.66, side * 0.28)
      ..lineTo(side * 0.74, side * 0.4)
      ..lineTo(side * 0.58, side * 0.4)
      ..close();
    canvas.drawPath(head, Paint()..color = Colors.black);
  }

  void _arrow(Canvas canvas, double side, double turns) {
    canvas.save();
    canvas.translate(side / 2, side / 2);
    canvas.rotate(turns);
    final path = Path()
      ..moveTo(0, -side * 0.28)
      ..lineTo(side * 0.16, -side * 0.04)
      ..lineTo(side * 0.06, -side * 0.04)
      ..lineTo(side * 0.06, side * 0.26)
      ..lineTo(-side * 0.06, side * 0.26)
      ..lineTo(-side * 0.06, -side * 0.04)
      ..lineTo(-side * 0.16, -side * 0.04)
      ..close();
    canvas.drawPath(path, Paint()..color = Colors.white);
    canvas.restore();
  }

  void _roundabout(Canvas canvas, double side) {
    final paint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.stroke
      ..strokeWidth = side * 0.07;
    canvas.drawCircle(Offset(side / 2, side / 2), side * 0.16, paint);
    for (var i = 0; i < 3; i++) {
      canvas.save();
      canvas.translate(side / 2, side / 2);
      canvas.rotate(i * 2 * pi / 3);
      canvas.drawPath(
        Path()
          ..moveTo(0, -side * 0.28)
          ..lineTo(side * 0.08, -side * 0.16)
          ..lineTo(-side * 0.08, -side * 0.16)
          ..close(),
        Paint()..color = Colors.white,
      );
      canvas.restore();
    }
  }

  void _children(Canvas canvas, Rect box) {
    _person(canvas, Offset(box.left + box.width * 0.32, box.bottom), box.height * 0.7, Colors.black);
    _person(canvas, Offset(box.left + box.width * 0.7, box.bottom - 2), box.height * 0.55, Colors.black);
  }

  void _crossroads(Canvas canvas, Rect box) {
    final paint = Paint()
      ..color = Colors.black
      ..strokeWidth = box.width * 0.18
      ..strokeCap = StrokeCap.square;
    canvas.drawLine(Offset(box.center.dx, box.top), Offset(box.center.dx, box.bottom), paint);
    canvas.drawLine(Offset(box.left, box.center.dy), Offset(box.right, box.center.dy), paint);
  }

  void _curve(Canvas canvas, Rect box) {
    final paint = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.stroke
      ..strokeWidth = box.width * 0.16
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(Rect.fromLTWH(box.left, box.top, box.width, box.height), pi * 0.9, pi * 0.9, false, paint);
  }

  void _slope(Canvas canvas, Rect box) {
    canvas.drawPath(
      Path()
        ..moveTo(box.left, box.bottom)
        ..lineTo(box.right, box.top + box.height * 0.25)
        ..lineTo(box.right, box.bottom)
        ..close(),
      Paint()..color = Colors.black,
    );
  }

  void _slip(Canvas canvas, Rect box) {
    _car(canvas, box.center, box.width * 0.9, Colors.black);
    canvas.drawLine(
      Offset(box.left, box.bottom),
      Offset(box.right, box.bottom - 4),
      Paint()
        ..color = Colors.black
        ..strokeWidth = 3,
    );
  }

  void _rail(Canvas canvas, Rect box) {
    final paint = Paint()
      ..color = Colors.black
      ..strokeWidth = 4;
    canvas.drawLine(Offset(box.left, box.center.dy), Offset(box.right, box.center.dy), paint);
    canvas.drawLine(
      Offset(box.left + 4, box.top + 6),
      Offset(box.right - 4, box.bottom - 6),
      paint,
    );
    canvas.drawLine(
      Offset(box.right - 4, box.top + 6),
      Offset(box.left + 4, box.bottom - 6),
      paint,
    );
  }

  void _house(Canvas canvas, Rect box) {
    canvas.drawPath(
      Path()
        ..moveTo(box.center.dx, box.top)
        ..lineTo(box.right, box.center.dy)
        ..lineTo(box.right - 4, box.bottom)
        ..lineTo(box.left + 4, box.bottom)
        ..lineTo(box.left, box.center.dy)
        ..close(),
      Paint()..color = Colors.black,
    );
  }

  void _person(Canvas canvas, Offset feet, double height, Color color) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = height * 0.16
      ..strokeCap = StrokeCap.round;
    final head = Offset(feet.dx, feet.dy - height * 0.82);
    canvas.drawCircle(head, height * 0.12, Paint()..color = color);
    canvas.drawLine(Offset(feet.dx, feet.dy - height * 0.68), Offset(feet.dx, feet.dy - height * 0.32), paint);
    canvas.drawLine(Offset(feet.dx - height * 0.22, feet.dy - height * 0.52), Offset(feet.dx + height * 0.22, feet.dy - height * 0.52), paint);
    canvas.drawLine(Offset(feet.dx, feet.dy - height * 0.32), Offset(feet.dx - height * 0.18, feet.dy), paint);
    canvas.drawLine(Offset(feet.dx, feet.dy - height * 0.32), Offset(feet.dx + height * 0.18, feet.dy), paint);
  }

  void _car(Canvas canvas, Offset center, double width, Color color) {
    final body = RRect.fromRectAndRadius(
      Rect.fromCenter(center: center, width: width, height: width * 0.45),
      const Radius.circular(3),
    );
    canvas.drawRRect(body, Paint()..color = color);
    canvas.drawCircle(Offset(center.dx - width * 0.28, center.dy + width * 0.22), width * 0.1, Paint()..color = color);
    canvas.drawCircle(Offset(center.dx + width * 0.28, center.dy + width * 0.22), width * 0.1, Paint()..color = color);
  }

  void _guide(Canvas canvas, double side) {
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(side * 0.08, side * 0.22, side * 0.84, side * 0.56),
        const Radius.circular(8),
      ),
      Paint()..color = _green,
    );
    _arrow(canvas, side, pi / 2);
  }

  void _diamond(Canvas canvas, double side) {
    final c = side / 2;
    final path = Path()
      ..moveTo(c, side * 0.08)
      ..lineTo(side * 0.92, c)
      ..lineTo(c, side * 0.92)
      ..lineTo(side * 0.08, c)
      ..close();
    canvas.drawPath(path, Paint()..color = Colors.white);
    canvas.drawPath(
      path,
      Paint()
        ..color = Colors.black
        ..style = PaintingStyle.stroke
        ..strokeWidth = side * 0.05
        ..strokeJoin = StrokeJoin.round,
    );
  }

  void _headlights(Canvas canvas, double side) {
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(side * 0.16, side * 0.3, side * 0.3, side * 0.4),
        const Radius.circular(6),
      ),
      Paint()..color = const Color(0xFF37474F),
    );
    final beam = Paint()
      ..color = const Color(0xFFFFF59D)
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;
    for (var i = 0; i < 3; i++) {
      final y = side * 0.38 + i * side * 0.1;
      canvas.drawLine(Offset(side * 0.5, y), Offset(side * 0.88, y - side * 0.04), beam);
    }
  }

  void _label(Canvas canvas, Offset center, String text, double fontSize, Color color) {
    final painter = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(color: color, fontSize: fontSize, fontWeight: FontWeight.w800, height: 1),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    painter.paint(canvas, center - Offset(painter.width / 2, painter.height / 2));
  }

  @override
  bool shouldRepaint(covariant _SignPainter oldDelegate) => oldDelegate.id != id;
}
