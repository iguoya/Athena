import "dart:math";

import "package:flutter/material.dart";

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
    final origin = Offset((size.width - side) / 2, (size.height - side) / 2);
    canvas.translate(origin.dx, origin.dy);
    switch (id) {
      case "no_entry":
        _noEntry(canvas, side);
      case "speed_40":
        _speed(canvas, side, "40");
      case "warning_pedestrian":
        _warning(canvas, side);
      case "pedestrian":
        _pedestrian(canvas, side);
      case "headlights":
        _headlights(canvas, side);
      default:
        _speed(canvas, side, "?");
    }
  }

  void _noEntry(Canvas canvas, double side) {
    final center = Offset(side / 2, side / 2);
    final radius = side * 0.42;
    canvas.drawCircle(center, radius, Paint()..color = const Color(0xFFC62828));
    canvas.drawCircle(center, radius * 0.82, Paint()..color = Colors.white);
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromCenter(center: center, width: radius * 1.35, height: radius * 0.28),
        const Radius.circular(4),
      ),
      Paint()..color = const Color(0xFFC62828),
    );
  }

  void _speed(Canvas canvas, double side, String text) {
    final center = Offset(side / 2, side / 2);
    final radius = side * 0.42;
    canvas.drawCircle(center, radius, Paint()..color = const Color(0xFFC62828));
    canvas.drawCircle(center, radius * 0.78, Paint()..color = Colors.white);
    final painter = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(
          color: Colors.black,
          fontSize: side * 0.28,
          fontWeight: FontWeight.w700,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    painter.paint(canvas, center - Offset(painter.width / 2, painter.height / 2));
  }

  void _warning(Canvas canvas, double side) {
    final path = Path()
      ..moveTo(side / 2, side * 0.08)
      ..lineTo(side * 0.92, side * 0.88)
      ..lineTo(side * 0.08, side * 0.88)
      ..close();
    canvas.drawPath(path, Paint()..color = const Color(0xFFF9A825));
    canvas.drawPath(
      path,
      Paint()
        ..color = Colors.black
        ..style = PaintingStyle.stroke
        ..strokeWidth = side * 0.06
        ..strokeJoin = StrokeJoin.round,
    );
    final painter = TextPainter(
      text: TextSpan(
        text: "!",
        style: TextStyle(
          color: Colors.black,
          fontSize: side * 0.36,
          fontWeight: FontWeight.w800,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    painter.paint(canvas, Offset(side / 2 - painter.width / 2, side * 0.38));
  }

  void _pedestrian(Canvas canvas, double side) {
    final paint = Paint()..color = Colors.white;
    canvas.drawCircle(Offset(side / 2, side / 2), side * 0.42, Paint()..color = const Color(0xFF1565C0));
    canvas.drawCircle(Offset(side / 2, side * 0.34), side * 0.08, paint);
    canvas.drawLine(
      Offset(side / 2, side * 0.44),
      Offset(side / 2, side * 0.62),
      paint
        ..strokeWidth = side * 0.07
        ..strokeCap = StrokeCap.round,
    );
    canvas.drawLine(Offset(side * 0.36, side * 0.5), Offset(side * 0.64, side * 0.5), paint);
    canvas.drawLine(Offset(side / 2, side * 0.62), Offset(side * 0.38, side * 0.78), paint);
    canvas.drawLine(Offset(side / 2, side * 0.62), Offset(side * 0.62, side * 0.78), paint);
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

  @override
  bool shouldRepaint(covariant _SignPainter oldDelegate) => oldDelegate.id != id;
}
