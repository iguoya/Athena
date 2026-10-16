/// 科目二静态分步俯视图（T-008）。只吃几何数据，不写步骤说明。
///
/// 坐标：x 向右，y 向下（路在上、库在下），和倒库动画的场地朝向一致。
/// 车身位姿的原点在后轴中心，heading 0 朝 +x，顺时针为正。
library;

import "dart:async";
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

/// 这一步「别这样」的红色示意（T-010）：打早了后轮扫过的轮迹、要压上的线。
/// 注意事项的空间含义直接画在图上，文字只留短句。只画不写字。
class FieldRisk {
  const FieldRisk(this.points);

  final List<Offset> points;
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
    this.risks = const [],
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

  /// 「别这样」的红色示意线。
  final List<FieldRisk> risks;
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
    // 打晚了车尾直着怼库口，右后轮压上库口右角。
    risks: [
      FieldRisk([Offset(4.6, 4.6), Offset(3.0, 6.4), Offset(1.6, 7.1)]),
    ],
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
    // 看到车身过早平行还继续倒，右后轮扫库口右角。
    risks: [
      FieldRisk([Offset(0.9, 7.6), Offset(1.05, 7.2), Offset(1.2, 7.05)]),
    ],
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

    for (final risk in step.risks) {
      if (risk.points.length < 2) continue;
      final pts = [for (final p in risk.points) map(p)];
      final paint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.5
        ..color = const Color(0xFFFF6E6E);
      for (var i = 0; i < pts.length - 1; i++) {
        _dash(canvas, pts[i], pts[i + 1], paint);
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
        old.marks.length != step.marks.length ||
        old.risks.length != step.risks.length;
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

/// 两步位姿的插值：车身沿步骤序列平滑走位（T-010）。场地线/标记/风险直接取
/// 目标步（同一场地只有车在动）；heading 走最短角差，不从 -π 绕整圈到 +π。
FieldMapStep lerpFieldStep(FieldMapStep a, FieldMapStep b, double t) {
  double angleDelta = (b.heading - a.heading) % (2 * math.pi);
  if (angleDelta > math.pi) angleDelta -= 2 * math.pi;
  if (angleDelta < -math.pi) angleDelta += 2 * math.pi;
  return FieldMapStep(
    x: a.x + (b.x - a.x) * t,
    y: a.y + (b.y - a.y) * t,
    heading: a.heading + angleDelta * t,
    steerDegrees: a.steerDegrees + (b.steerDegrees - a.steerDegrees) * t,
    lines: b.lines,
    marks: b.marks,
    risks: b.risks,
    bounds: b.bounds,
  );
}

/// 俯视图动起来（T-010，ADR 0036「应用内动画示意」的回归）。
///
/// 外部 [index] 变化时，车身从当前位置平滑走到目标步（受控过渡）；
/// [autoPlay] 时进场先自动演示一轮（逐步走到最后一步），随后回到受控模式，
/// 用户点步骤条即从当前位置平滑过去。位姿插值，文字与联动不变。
class FieldMapAnimated extends StatefulWidget {
  const FieldMapAnimated({
    super.key,
    required this.steps,
    required this.index,
    this.autoPlay = false,
  });

  final List<FieldMapStep> steps;
  final int index;
  final bool autoPlay;

  @override
  State<FieldMapAnimated> createState() => _FieldMapAnimatedState();
}

class _FieldMapAnimatedState extends State<FieldMapAnimated>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 650),
  );
  late FieldMapStep _from = widget.steps.first;
  late int _target = widget.index;
  bool _demo = false;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    if (widget.autoPlay && widget.steps.length > 1) {
      _demo = true;
      _timer = Timer(const Duration(milliseconds: 900), _advanceDemo);
    }
  }

  @override
  void didUpdateWidget(FieldMapAnimated old) {
    super.didUpdateWidget(old);
    if (!_demo && widget.index != old.index) _goTo(widget.index);
  }

  void _advanceDemo() {
    if (!mounted) return;
    if (_target + 1 < widget.steps.length) {
      _goTo(_target + 1);
      _timer = Timer(const Duration(milliseconds: 1500), _advanceDemo);
    } else {
      setState(() => _demo = false); // 演示一轮结束，回到受控模式
    }
  }

  void _goTo(int i) {
    setState(() {
      _from = _shown;
      _target = i;
    });
    _controller.forward(from: 0);
  }

  FieldMapStep get _shown =>
      lerpFieldStep(_from, widget.steps[_target], _controller.value);

  @override
  void dispose() {
    _timer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) => CustomPaint(
        painter: FieldMapPainter(_shown),
        child: const SizedBox.expand(),
      ),
    );
  }
}
