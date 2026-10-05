import "package:flutter/material.dart";

/// 交通警察手势示意（ADR 0073）：简化人形（圆头 + 躯干 + 双臂线条），
/// 面向观看者——画面左右与交警本人的左右相反，页面顶部会提示这一点。
/// 动作按「伸直臂是交警哪只手 + 摆动臂与掌心朝向」区分。
class GestureView extends StatelessWidget {
  const GestureView({super.key, required this.id, this.size = 120});

  final String id;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: "交通警察手势示意 $id",
      child: CustomPaint(
        size: Size.square(size),
        painter: _GesturePainter(id),
      ),
    );
  }
}

/// `_GesturePainter` 画得出来的全部 id（ADR 0073）：加新手势时，这个清单与
/// 下面 switch 的 case 同步加。`content/gestures.json` 的每条 id 都必须落在
/// 这个集合里，test/gestures_page_test.dart 守住。
const paintableGestureIds = {
  "authority",
  "stop",
  "straight",
  "turn_left",
  "turn_left_wait",
  "turn_right",
  "change_lane",
  "slow_down",
  "pull_over",
};

class _GesturePainter extends CustomPainter {
  _GesturePainter(this.id);

  final String id;

  static const _bg = Color(0xFFEAF1F8);
  static const _uniform = Color(0xFF27425F);
  static const _skin = Color(0xFFE8B98A);
  static const _accent = Color(0xFFC62828);

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width, h = size.height;
    canvas.drawRRect(
      RRect.fromRectAndRadius(Offset.zero & size, Radius.circular(w * 0.12)),
      Paint()..color = _bg,
    );
    canvas.translate(w / 2, h / 2);
    switch (id) {
      case "authority":
        _whistle(canvas, w);
      case "stop":
        // 交警左臂（画面右）高举过肩，掌心向前。
        _body(canvas, w, h);
        _arm(canvas, w, Offset(w * 0.14, -h * 0.06), Offset(w * 0.30, -h * 0.40));
        _palm(canvas, Offset(w * 0.30, -h * 0.40));
        _arrow(canvas, Offset(0, h * 0.30), Offset(0, h * 0.12), w * 0.10);
      case "straight":
        // 双臂侧平：交警右臂（画面左）前伸，左臂（画面右）侧平。
        _body(canvas, w, h);
        _arm(canvas, w, Offset(-w * 0.10, -h * 0.05), Offset(-w * 0.38, -h * 0.05));
        _arm(canvas, w, Offset(w * 0.10, -h * 0.05), Offset(w * 0.38, -h * 0.05));
        _arrow(canvas, Offset(w * 0.12, h * 0.28), Offset(w * 0.36, h * 0.28), w * 0.10);
      case "turn_left":
        // 交警右臂（画面左）前平伸，左臂（画面右）向右前方摆动。
        _body(canvas, w, h);
        _arm(canvas, w, Offset(-w * 0.10, -h * 0.05), Offset(-w * 0.36, -h * 0.10));
        _arm(canvas, w, Offset(w * 0.10, -h * 0.02), Offset(w * 0.30, -h * 0.22), kink: Offset(w * 0.24, h * 0.02));
        _arrow(canvas, Offset(w * 0.30, h * 0.28), Offset(-w * 0.30, h * 0.28), w * 0.10);
      case "turn_left_wait":
        // 交警左臂（画面右）在侧下方，掌心朝下摆向正前方。
        _body(canvas, w, h);
        _arm(canvas, w, Offset(w * 0.10, h * 0.02), Offset(w * 0.34, h * 0.10));
        _palmDown(canvas, Offset(w * 0.34, h * 0.10));
        _arrow(canvas, Offset(w * 0.34, h * 0.26), Offset(w * 0.02, h * 0.26), w * 0.10);
      case "turn_right":
        // 交警左臂（画面右）前平伸，右臂（画面左）向左前方摆动。
        _body(canvas, w, h);
        _arm(canvas, w, Offset(w * 0.10, -h * 0.05), Offset(w * 0.36, -h * 0.10));
        _arm(canvas, w, Offset(-w * 0.10, -h * 0.02), Offset(-w * 0.30, -h * 0.22), kink: Offset(-w * 0.24, h * 0.02));
        _arrow(canvas, Offset(-w * 0.30, h * 0.28), Offset(w * 0.30, h * 0.28), w * 0.10);
      case "change_lane":
        // 交警右臂（画面左）前平伸掌心向左，前臂向左上方摆动。
        _body(canvas, w, h);
        _arm(canvas, w, Offset(-w * 0.10, -h * 0.05), Offset(-w * 0.34, -h * 0.08));
        _arm(canvas, w, Offset(-w * 0.10, -h * 0.05), Offset(-w * 0.26, -h * 0.26), kink: Offset(-w * 0.24, -h * 0.04));
        _arrow(canvas, Offset(-w * 0.08, h * 0.26), Offset(-w * 0.34, h * 0.26), w * 0.10);
      case "slow_down":
        // 交警右臂（画面左）向右前方伸出，掌心向下上下摆。
        _body(canvas, w, h);
        _arm(canvas, w, Offset(-w * 0.10, -h * 0.04), Offset(-w * 0.30, h * 0.06));
        _palmDown(canvas, Offset(-w * 0.30, h * 0.06));
        _arrow(canvas, Offset(-w * 0.30, -h * 0.16), Offset(-w * 0.30, h * 0.00), w * 0.09);
      case "pull_over":
        // 交警左臂（画面右）前平伸掌心向前，右臂（画面左）向左前摆动。
        _body(canvas, w, h);
        _arm(canvas, w, Offset(w * 0.10, -h * 0.05), Offset(w * 0.34, -h * 0.08));
        _palm(canvas, Offset(w * 0.34, -h * 0.08));
        _arm(canvas, w, Offset(-w * 0.10, -h * 0.02), Offset(-w * 0.28, -h * 0.20), kink: Offset(-w * 0.22, h * 0.00));
        _arrow(canvas, Offset(-w * 0.20, h * 0.28), Offset(-w * 0.36, h * 0.28), w * 0.09);
    }
  }

  Paint _stroke(Color color, double width) => Paint()
    ..color = color
    ..style = PaintingStyle.stroke
    ..strokeWidth = width
    ..strokeCap = StrokeCap.round;

  /// 躯干与头：帽檐 + 帽顶 + 圆头 + 制服上身 + 肩章。
  void _body(Canvas canvas, double w, double h) {
    final paint = Paint()..color = _uniform;
    canvas.drawRRect(
      RRect.fromRectAndRadius(Rect.fromLTWH(-w * 0.15, -h * 0.40, w * 0.30, h * 0.06), Radius.circular(w * 0.03)),
      paint,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(Rect.fromLTWH(-w * 0.10, -h * 0.48, w * 0.20, h * 0.08), Radius.circular(w * 0.04)),
      paint,
    );
    canvas.drawCircle(Offset(0, -h * 0.32), w * 0.075, Paint()..color = _skin);
    canvas.drawRRect(
      RRect.fromRectAndRadius(Rect.fromLTWH(-w * 0.14, -h * 0.24, w * 0.28, h * 0.40), Radius.circular(w * 0.07)),
      paint,
    );
    canvas.drawLine(Offset(-w * 0.13, -h * 0.20), Offset(-w * 0.05, -h * 0.20), _stroke(Colors.white, w * 0.02));
    canvas.drawLine(Offset(w * 0.05, -h * 0.20), Offset(w * 0.13, -h * 0.20), _stroke(Colors.white, w * 0.02));
  }

  /// 手臂：肩到肘到手，可带一个中间拐点（摆动相）。
  void _arm(Canvas canvas, double w, Offset shoulder, Offset hand, {Offset? kink}) {
    final paint = _stroke(_uniform, w * 0.075);
    if (kink == null) {
      canvas.drawLine(shoulder, hand, paint);
    } else {
      final path = Path()..moveTo(shoulder.dx, shoulder.dy)..lineTo(kink.dx, kink.dy)..lineTo(hand.dx, hand.dy);
      canvas.drawPath(path, paint);
    }
    canvas.drawCircle(hand, w * 0.035, Paint()..color = _skin);
  }

  /// 掌心向前的手：掌面小圆。
  void _palm(Canvas canvas, Offset center) {
    canvas.drawCircle(center, 5, Paint()..color = _skin);
  }

  /// 掌心朝下的手：一条短横线示意掌面。
  void _palmDown(Canvas canvas, Offset center) {
    canvas.drawLine(center.translate(-6, 0), center.translate(6, 0), _stroke(_skin, 4));
  }

  void _whistle(Canvas canvas, double w) {
    // 手势效力：指挥哨。
    canvas.drawCircle(Offset(-w * 0.06, 0), w * 0.16, _stroke(_uniform, w * 0.06));
    canvas.drawRRect(
      RRect.fromRectAndRadius(Rect.fromLTWH(w * 0.06, -w * 0.05, w * 0.22, w * 0.10), Radius.circular(w * 0.05)),
      Paint()..color = _accent,
    );
    canvas.drawCircle(Offset(-w * 0.06, 0), w * 0.06, Paint()..color = _accent);
  }

  void _arrow(Canvas canvas, Offset from, Offset to, double size) {
    final dir = to - from;
    final len = dir.distance;
    if (len == 0) return;
    final unit = dir / len;
    final normal = Offset(-unit.dy, unit.dx);
    final path = Path()
      ..moveTo(to.dx, to.dy)
      ..lineTo(to.dx - unit.dx * size + normal.dx * size * 0.45, to.dy - unit.dy * size + normal.dy * size * 0.45)
      ..lineTo(to.dx - unit.dx * size - normal.dx * size * 0.45, to.dy - unit.dy * size - normal.dy * size * 0.45)
      ..close();
    canvas.drawPath(path, Paint()..color = _accent);
    canvas.drawLine(from, to, _stroke(_accent, size * 0.22));
  }

  @override
  bool shouldRepaint(covariant _GesturePainter old) => old.id != id;
}
