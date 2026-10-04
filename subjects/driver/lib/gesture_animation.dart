import "dart:math";

import "package:flutter/material.dart";

import "glyphs.dart";
import "look.dart";

/// 交通警察手势动画（ADR 0078）：静态图只能画出一个姿势，而手势是一段动作——先摆到什么位置、
/// 再怎么摆。这里把每个动作写成一串**关键姿势**，播放时在姿势之间插值，同时给出两个视角：
/// 正面（交警面向你）和俯视（看清「前平伸」「向右前方」这类前后方向）。
///
/// 坐标约定：交警面向观看者。x 轴朝观看者的右手边，也就是**交警自己的左边**；z 轴朝向观看者，
/// 也就是交警的正前方；y 轴朝上。手臂方向用「方位角 + 仰角」表示：方位角 0 = 正前方（朝向观看者），
/// 往交警自己的左边为正、往右边为负；仰角 0 = 水平，+90 = 笔直向上，−90 = 笔直向下。

/// 掌心朝向（交警自己的左右）。
enum Palm {
  forward(0, 0, 1),
  down(0, -1, 0),
  up(0, 1, 0),
  left(1, 0, 0),
  right(-1, 0, 0);

  const Palm(this.nx, this.ny, this.nz);
  final double nx, ny, nz;
}

/// 一条手臂的姿势：上臂（肩到肘）与前臂（肘到手）各一个方向。
class ArmPose {
  const ArmPose(this.upperAz, this.upperEl, this.foreAz, this.foreEl, this.palm);

  /// 整条手臂伸直指向同一个方向。
  const ArmPose.straight(double az, double el, Palm palm) : this(az, el, az, el, palm);

  /// 自然下垂。
  static const down = ArmPose.straight(0, -88, Palm.forward);

  final double upperAz, upperEl, foreAz, foreEl;
  final Palm palm;

  static ArmPose lerp(ArmPose a, ArmPose b, double t) {
    double mix(double x, double y) => x + (y - x) * t;
    return ArmPose(
      mix(a.upperAz, b.upperAz),
      mix(a.upperEl, b.upperEl),
      mix(a.foreAz, b.foreAz),
      mix(a.foreEl, b.foreEl),
      t < 0.5 ? a.palm : b.palm,
    );
  }

  /// 手臂指向的单位向量（x 朝交警左、y 朝上、z 朝交警正前方）。
  static (double, double, double) vector(double az, double el) {
    final a = az * pi / 180, e = el * pi / 180;
    return (sin(a) * cos(e), sin(e), cos(a) * cos(e));
  }

  /// 手所在的方向（前臂方向）。
  (double, double, double) get foreVector => vector(foreAz, foreEl);

  bool sameAs(ArmPose o) =>
      upperAz == o.upperAz &&
      upperEl == o.upperEl &&
      foreAz == o.foreAz &&
      foreEl == o.foreEl &&
      palm == o.palm;
}

class FigurePose {
  const FigurePose(this.left, this.right);

  /// 交警的左臂（观看者看到在右边）与右臂（观看者看到在左边）。
  final ArmPose left, right;

  static const rest = FigurePose(ArmPose.down, ArmPose.down);

  static FigurePose lerp(FigurePose a, FigurePose b, double t) =>
      FigurePose(ArmPose.lerp(a.left, b.left, t), ArmPose.lerp(a.right, b.right, t));

  bool sameAs(FigurePose o) => left.sameAs(o.left) && right.sameAs(o.right);
}

/// 一个关键姿势：用 [ms] 毫秒从上一个姿势过渡过来，再停留 [hold] 毫秒；[step] 是它对应的要领文字序号。
class GestureKey {
  const GestureKey(this.pose, {this.ms = 800, this.hold = 400, this.step = 0});

  final FigurePose pose;
  final int ms;
  final int hold;
  final int step;
}

/// 一个手势动作的动画：要领文字 + 关键姿势序列。首尾姿势相同（都回到自然下垂），循环播放时没有跳变。
class GestureClip {
  const GestureClip({required this.captions, required this.keys});

  /// 要领文字，一步一条；播放时高亮当前步。
  final List<String> captions;
  final List<GestureKey> keys;

  /// 第一个关键姿势是起点，没有「过渡进来」的时间。
  int _inMs(int i) => i == 0 ? 0 : keys[i].ms;

  int get totalMs {
    var t = 0;
    for (var i = 0; i < keys.length; i++) {
      t += _inMs(i) + keys[i].hold;
    }
    return t;
  }

  /// 第 [index] 个关键姿势刚到位的时刻。
  int reachedAt(int index) {
    var t = 0;
    for (var i = 0; i <= index; i++) {
      t += _inMs(i);
      if (i < index) t += keys[i].hold;
    }
    return t;
  }

  FigurePose poseAt(int ms) {
    var t = ms % totalMs;
    for (var i = 0; i < keys.length; i++) {
      final k = keys[i];
      if (i > 0 && t < k.ms) {
        final u = Curves.easeInOut.transform(t / k.ms);
        return FigurePose.lerp(keys[i - 1].pose, k.pose, u);
      }
      t -= i > 0 ? k.ms : 0;
      if (t < k.hold) return k.pose;
      t -= k.hold;
    }
    return keys.last.pose;
  }

  int stepAt(int ms) {
    var t = ms % totalMs;
    for (var i = 0; i < keys.length; i++) {
      final k = keys[i];
      final span = (i > 0 ? k.ms : 0) + k.hold;
      if (t < span) return k.step;
      t -= span;
    }
    return keys.last.step;
  }

  /// 画「残影」用的去重姿势：动作覆盖的范围一眼可见。
  List<FigurePose> get ghosts {
    final out = <FigurePose>[];
    for (final k in keys) {
      if (k.pose.sameAs(FigurePose.rest)) continue;
      if (out.any((p) => p.sameAs(k.pose))) continue;
      out.add(k.pose);
    }
    return out;
  }
}

// ---- 关键姿势：8 个法定动作 ----
//
// 依据：《道路交通安全法实施条例》（交通信号包括交通警察的指挥）与公安部《交通警察道路执勤执法工作规范》
// 附件的动作要领；姿势逐个用题库里 29 道手势题的题图核对过（每张题图是同一动作的两个姿势）。
// 「左」「右」都是交警自己的左右。

const _rest = FigurePose.rest;

/// 停止信号：左臂由前向上直伸，与身体成 135°角，掌心向前，面对来车；右臂自然下垂。
const _stopHold = FigurePose(ArmPose.straight(0, 45, Palm.forward), ArmPose.down);

/// 直行信号：两臂左右平伸，掌心向前；右臂水平摆向身前，掌心向左；左臂仍侧平。
const _straightOut = FigurePose(ArmPose.straight(90, 0, Palm.forward), ArmPose.straight(-90, 0, Palm.forward));
// 摆动的那条手臂在第二个姿势里是弯的：上臂仍在身侧，前臂横过身前（题图里都是这样画的）。
const _straightSwing = FigurePose(ArmPose.straight(90, 0, Palm.forward), ArmPose(-85, -15, 55, 0, Palm.left));

/// 左转弯信号：右臂向前平伸，掌心向前；左臂与手掌平直向右前方摆动，掌心向右。
const _leftTurnA = FigurePose(ArmPose(60, -45, 80, -10, Palm.right), ArmPose.straight(0, 0, Palm.forward));
const _leftTurnB = FigurePose(ArmPose(25, -55, -55, 8, Palm.right), ArmPose.straight(0, 0, Palm.forward));

/// 左转弯待转信号：左臂向左平伸，掌心向下，向下、向身前摆动。
const _waitA = FigurePose(ArmPose.straight(90, 0, Palm.down), ArmPose.down);
const _waitB = FigurePose(ArmPose(60, -50, -20, 12, Palm.down), ArmPose.down);

/// 右转弯信号：左臂向前平伸，掌心向前；右臂与手掌平直向左前方摆动，掌心向左。
const _rightTurnA = FigurePose(ArmPose.straight(0, 0, Palm.forward), ArmPose(-60, -45, -80, -10, Palm.left));
const _rightTurnB = FigurePose(ArmPose.straight(0, 0, Palm.forward), ArmPose(-25, -55, 55, 8, Palm.left));

/// 变道信号：右臂向前平伸，掌心向左；右臂向左水平摆动。
const _laneA = FigurePose(ArmPose.down, ArmPose.straight(0, 0, Palm.left));
const _laneB = FigurePose(ArmPose.down, ArmPose(-10, -35, 60, 5, Palm.left));

/// 减速慢行信号：右臂向右前方平伸，掌心向下，上下摆动。
const _slowUp = FigurePose(ArmPose.down, ArmPose.straight(-60, 5, Palm.down));
const _slowDown = FigurePose(ArmPose.down, ArmPose.straight(-60, -36, Palm.down));

/// 示意车辆靠边停车信号：左臂向前平伸，掌心向前；右臂由右向左摆动。
const _pullA = FigurePose(ArmPose.straight(0, 0, Palm.forward), ArmPose(-55, -35, -80, 0, Palm.left));
const _pullB = FigurePose(ArmPose.straight(0, 0, Palm.forward), ArmPose(-25, -50, 55, 8, Palm.left));

const gestureClips = <String, GestureClip>{
  "stop": GestureClip(
    captions: [
      "左臂由下向前上方举起，直伸到与身体成 135° 角",
      "掌心向前，面对来车方向；右臂自然下垂，保持不动",
    ],
    keys: [
      GestureKey(_rest, hold: 500),
      GestureKey(_stopHold, ms: 1000, hold: 400, step: 0),
      GestureKey(_stopHold, ms: 1, hold: 1600, step: 1),
      GestureKey(_rest, ms: 800, hold: 300, step: 1),
    ],
  ),
  "straight": GestureClip(
    captions: [
      "两臂左右平伸，掌心向前",
      "右臂水平摆向身前，掌心向左；左臂仍然侧平",
      "摆回，再来一遍",
    ],
    keys: [
      GestureKey(_rest, hold: 400),
      GestureKey(_straightOut, ms: 900, hold: 700, step: 0),
      GestureKey(_straightSwing, ms: 900, hold: 600, step: 1),
      GestureKey(_straightOut, ms: 900, hold: 500, step: 2),
      GestureKey(_straightSwing, ms: 900, hold: 600, step: 1),
      GestureKey(_rest, ms: 800, hold: 300, step: 2),
    ],
  ),
  "turn_left": GestureClip(
    captions: [
      "右臂向前平伸，掌心向前（你看到在左边的那只手）",
      "左臂与手掌平直，向右前方摆动，掌心向右",
      "左臂摆回，反复摆动",
    ],
    keys: [
      GestureKey(_rest, hold: 400),
      GestureKey(_leftTurnA, ms: 1000, hold: 600, step: 0),
      GestureKey(_leftTurnB, ms: 900, hold: 400, step: 1),
      GestureKey(_leftTurnA, ms: 900, hold: 300, step: 2),
      GestureKey(_leftTurnB, ms: 900, hold: 400, step: 1),
      GestureKey(_rest, ms: 900, hold: 300, step: 2),
    ],
  ),
  "turn_left_wait": GestureClip(
    captions: [
      "左臂向左平伸，掌心向下（右臂下垂）",
      "左臂向下、向身前摆动：示意左转车先进入路口的待转区，不是放行",
    ],
    keys: [
      GestureKey(_rest, hold: 400),
      GestureKey(_waitA, ms: 900, hold: 700, step: 0),
      GestureKey(_waitB, ms: 1000, hold: 600, step: 1),
      GestureKey(_waitA, ms: 1000, hold: 400, step: 0),
      GestureKey(_waitB, ms: 1000, hold: 600, step: 1),
      GestureKey(_rest, ms: 900, hold: 300, step: 0),
    ],
  ),
  "turn_right": GestureClip(
    captions: [
      "左臂向前平伸，掌心向前（你看到在右边的那只手）",
      "右臂与手掌平直，向左前方摆动，掌心向左",
      "右臂摆回，反复摆动",
    ],
    keys: [
      GestureKey(_rest, hold: 400),
      GestureKey(_rightTurnA, ms: 1000, hold: 600, step: 0),
      GestureKey(_rightTurnB, ms: 900, hold: 400, step: 1),
      GestureKey(_rightTurnA, ms: 900, hold: 300, step: 2),
      GestureKey(_rightTurnB, ms: 900, hold: 400, step: 1),
      GestureKey(_rest, ms: 900, hold: 300, step: 2),
    ],
  ),
  "change_lane": GestureClip(
    captions: [
      "右臂向前平伸，掌心向左（左臂下垂）",
      "右臂向左水平摆动：让该车道的车腾出车道，向指定车道变更",
    ],
    keys: [
      GestureKey(_rest, hold: 400),
      GestureKey(_laneA, ms: 900, hold: 700, step: 0),
      GestureKey(_laneB, ms: 1000, hold: 600, step: 1),
      GestureKey(_laneA, ms: 1000, hold: 400, step: 0),
      GestureKey(_laneB, ms: 1000, hold: 600, step: 1),
      GestureKey(_rest, ms: 900, hold: 300, step: 0),
    ],
  ),
  "slow_down": GestureClip(
    captions: [
      "右臂向右前方平伸，掌心向下（左臂下垂）",
      "手臂上下摆动，像把车速压下来",
    ],
    keys: [
      GestureKey(_rest, hold: 400),
      GestureKey(_slowUp, ms: 900, hold: 400, step: 0),
      GestureKey(_slowDown, ms: 700, hold: 200, step: 1),
      GestureKey(_slowUp, ms: 700, hold: 200, step: 1),
      GestureKey(_slowDown, ms: 700, hold: 200, step: 1),
      GestureKey(_slowUp, ms: 700, hold: 200, step: 1),
      GestureKey(_rest, ms: 900, hold: 300, step: 0),
    ],
  ),
  "pull_over": GestureClip(
    captions: [
      "左臂向前平伸，掌心向前",
      "右臂由右向左摆动：示意车辆靠边停车，接受检查",
    ],
    keys: [
      GestureKey(_rest, hold: 400),
      GestureKey(_pullA, ms: 1000, hold: 600, step: 0),
      GestureKey(_pullB, ms: 1000, hold: 500, step: 1),
      GestureKey(_pullA, ms: 1000, hold: 300, step: 1),
      GestureKey(_pullB, ms: 1000, hold: 500, step: 1),
      GestureKey(_rest, ms: 900, hold: 300, step: 0),
    ],
  ),
};

// ---- 绘制 ----

const _bg = Color(0xFFEAF1F8);
const _uniform = Color(0xFF27425F);
const _sleeve = Color(0xFF3F689A);
const _skin = Color(0xFFE8B98A);
const _skinBack = Color(0xFFC99A6C);
const _accent = Color(0xFFC62828);

Paint _stroke(Color color, double width) => Paint()
  ..color = color
  ..style = PaintingStyle.stroke
  ..strokeWidth = width
  ..strokeCap = StrokeCap.round
  ..strokeJoin = StrokeJoin.round;

/// 正面视角：交警面向观看者。朝向观看者的前伸臂向体内、向下偏一点（透视），手画大一点（近大远小）。
class GestureFrontPainter extends CustomPainter {
  GestureFrontPainter(this.pose, this.ghosts);

  final FigurePose pose;
  final List<FigurePose> ghosts;

  static const _upper = 0.165;
  static const _fore = 0.165;

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width, h = size.height;
    canvas.drawRRect(
      RRect.fromRectAndRadius(Offset.zero & size, Radius.circular(w * 0.08)),
      Paint()..color = _bg,
    );
    canvas.translate(w / 2, h / 2);
    _body(canvas, w, h);
    for (final g in ghosts) {
      _arms(canvas, w, h, g, ghost: true);
    }
    _arms(canvas, w, h, pose, ghost: false);
  }

  void _arms(Canvas canvas, double w, double h, FigurePose p, {required bool ghost}) {
    _arm(canvas, w, h, Offset(w * 0.13, -h * 0.07), 1, p.left, ghost);
    _arm(canvas, w, h, Offset(-w * 0.13, -h * 0.07), -1, p.right, ghost);
  }

  /// [side]：肩在画面右边为 1、左边为 −1，前伸时往体内收。
  void _arm(Canvas canvas, double w, double h, Offset shoulder, int side, ArmPose arm, bool ghost) {
    Offset step(Offset from, double az, double el, double len) {
      final (dx, dy, dz) = ArmPose.vector(az, el);
      return from + Offset((dx - side * 0.34 * dz) * len * w, (-dy + 0.34 * dz) * len * w);
    }

    final elbow = step(shoulder, arm.upperAz, arm.upperEl, _upper);
    final hand = step(elbow, arm.foreAz, arm.foreEl, _fore);
    final path = Path()
      ..moveTo(shoulder.dx, shoulder.dy)
      ..lineTo(elbow.dx, elbow.dy)
      ..lineTo(hand.dx, hand.dy);
    if (ghost) {
      canvas.drawPath(path, _stroke(_uniform.withValues(alpha: 0.13), w * 0.06));
      return;
    }
    // 袖子比躯干浅一档，外面描一圈白边：手臂前伸、叠在躯干上时仍然看得清。
    canvas.drawPath(path, _stroke(Colors.white.withValues(alpha: 0.9), w * 0.062 + 4));
    canvas.drawPath(path, _stroke(_sleeve, w * 0.062));
    final (_, _, dz) = arm.foreVector;
    _hand(canvas, hand, arm.palm, w * 0.050 * (1 + 0.3 * dz));
  }

  /// 手：圆片，掌心朝向决定扁度（正对观看者是圆，侧向是窄椭圆）。
  void _hand(Canvas canvas, Offset center, Palm palm, double r) {
    final facing = palm.nz;
    final minor = r * max(0.28, facing.abs());
    canvas.save();
    canvas.translate(center.dx, center.dy);
    // 椭圆的短轴沿掌心法线在画面上的投影方向。
    final angle = (palm.nx == 0 && palm.ny == 0) ? 0.0 : atan2(-palm.ny, palm.nx);
    canvas.rotate(angle);
    final rect = Rect.fromCenter(center: Offset.zero, width: minor * 2, height: r * 2);
    canvas.drawOval(rect, Paint()..color = facing >= 0 ? _skin : _skinBack);
    canvas.drawOval(rect, _stroke(const Color(0x55000000), 1));
    canvas.restore();
  }

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
      RRect.fromRectAndRadius(Rect.fromLTWH(-w * 0.14, -h * 0.24, w * 0.28, h * 0.46), Radius.circular(w * 0.07)),
      paint,
    );
    canvas.drawLine(Offset(-w * 0.13, -h * 0.20), Offset(-w * 0.05, -h * 0.20), _stroke(Colors.white, w * 0.02));
    canvas.drawLine(Offset(w * 0.05, -h * 0.20), Offset(w * 0.13, -h * 0.20), _stroke(Colors.white, w * 0.02));
  }

  @override
  bool shouldRepaint(covariant GestureFrontPainter old) => true;
}

/// 俯视视角：从头顶往下看，交警面朝画面下方（观看者所在的一侧）。看清手臂是朝前、朝侧还是朝后；
/// 手点的颜色表示高度：红 = 举过肩，灰 = 垂在腰下，深色 = 平举。
class GestureTopPainter extends CustomPainter {
  GestureTopPainter(this.pose, this.ghosts);

  final FigurePose pose;
  final List<FigurePose> ghosts;

  static const _u = 0.20;

  @override
  void paint(Canvas canvas, Size size) {
    final s = size.width;
    canvas.drawRRect(
      RRect.fromRectAndRadius(Offset.zero & size, Radius.circular(s * 0.08)),
      Paint()..color = _bg,
    );
    canvas.translate(s / 2, s * 0.42);
    // 地面参考线：交警脚下的十字，说明前后左右。
    final guide = _stroke(const Color(0x14000000), 1);
    canvas.drawLine(Offset(-s * 0.46, 0), Offset(s * 0.46, 0), guide);
    canvas.drawLine(Offset(0, -s * 0.40), Offset(0, s * 0.50), guide);
    // 躯干与头。
    canvas.drawOval(Rect.fromCenter(center: Offset.zero, width: s * 0.30, height: s * 0.13), Paint()..color = _uniform);
    canvas.drawCircle(Offset.zero, s * 0.05, Paint()..color = _skin);
    // 胸口朝向：画面下方，也就是观看者这一侧。
    final chest = Path()
      ..moveTo(0, s * 0.13)
      ..lineTo(-s * 0.035, s * 0.07)
      ..lineTo(s * 0.035, s * 0.07)
      ..close();
    canvas.drawPath(chest, Paint()..color = _accent);
    for (final g in ghosts) {
      _arms(canvas, s, g, ghost: true);
    }
    _arms(canvas, s, pose, ghost: false);
    _label(canvas, "交警的前方（你在这一侧）", Offset(0, s * 0.56), s * 0.056);
    _label(canvas, "后", Offset(0, -s * 0.34), s * 0.056);
    _label(canvas, "他的左", Offset(s * 0.40, -s * 0.03), s * 0.05);
    _label(canvas, "他的右", Offset(-s * 0.40, -s * 0.03), s * 0.05);
  }

  void _arms(Canvas canvas, double s, FigurePose p, {required bool ghost}) {
    _arm(canvas, s, Offset(s * 0.10, 0), p.left, ghost);
    _arm(canvas, s, Offset(-s * 0.10, 0), p.right, ghost);
  }

  void _arm(Canvas canvas, double s, Offset shoulder, ArmPose arm, bool ghost) {
    Offset step(Offset from, double az, double el) {
      final (dx, _, dz) = ArmPose.vector(az, el);
      return from + Offset(dx * _u * s, dz * _u * s);
    }

    final elbow = step(shoulder, arm.upperAz, arm.upperEl);
    final hand = step(elbow, arm.foreAz, arm.foreEl);
    final path = Path()
      ..moveTo(shoulder.dx, shoulder.dy)
      ..lineTo(elbow.dx, elbow.dy)
      ..lineTo(hand.dx, hand.dy);
    if (ghost) {
      canvas.drawPath(path, _stroke(_uniform.withValues(alpha: 0.13), s * 0.045));
      return;
    }
    canvas.drawPath(path, _stroke(_uniform, s * 0.045));
    final el = arm.foreEl;
    final dot = el > 20 ? _accent : (el < -50 ? const Color(0xFF8A94A3) : _uniform);
    canvas.drawCircle(hand, s * 0.04, Paint()..color = dot);
    canvas.drawCircle(hand, s * 0.04, _stroke(Colors.white, 1.5));
  }

  void _label(Canvas canvas, String text, Offset center, double size) {
    final painter = TextPainter(
      text: TextSpan(text: text, style: TextStyle(fontSize: size, color: const Color(0xFF5B6B7D))),
      textDirection: TextDirection.ltr,
    )..layout();
    painter.paint(canvas, center - Offset(painter.width / 2, painter.height / 2));
  }

  @override
  bool shouldRepaint(covariant GestureTopPainter old) => true;
}

/// 一个手势的动画：循环播放；[interactive] 时带播放 / 暂停、上一步 / 下一步、进度条与要领文字，
/// 并并排给出俯视视角。格子里的小图只循环播放，没有控件。
class GestureAnimation extends StatefulWidget {
  const GestureAnimation({super.key, required this.id, this.size = 120, this.interactive = false});

  final String id;
  final double size;
  final bool interactive;

  @override
  State<GestureAnimation> createState() => _GestureAnimationState();
}

class _GestureAnimationState extends State<GestureAnimation> with SingleTickerProviderStateMixin {
  late final GestureClip _clip = gestureClips[widget.id]!;
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: Duration(milliseconds: _clip.totalMs),
  );
  late final List<FigurePose> _ghosts = _clip.ghosts;
  bool _playing = true;

  @override
  void initState() {
    super.initState();
    _controller.repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  int get _ms => (_controller.value * _clip.totalMs).round();

  void _toggle() {
    setState(() {
      _playing = !_playing;
      if (_playing) {
        _controller.repeat(min: 0, max: 1, period: Duration(milliseconds: _clip.totalMs));
      } else {
        _controller.stop();
      }
    });
  }

  /// 跳到第 [index] 个关键姿势刚到位的时刻并暂停。
  void _jump(int index) {
    final i = (index % _clip.keys.length + _clip.keys.length) % _clip.keys.length;
    setState(() {
      _playing = false;
      _controller.stop();
      _controller.value = _clip.reachedAt(i) / _clip.totalMs;
    });
  }

  /// 当前时刻所在的关键姿势序号：已经到位的最后一个。
  int get _currentKey {
    final now = _ms;
    var current = 0;
    for (var i = 0; i < _clip.keys.length; i++) {
      if (_clip.reachedAt(i) <= now) current = i;
    }
    return current;
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.interactive) {
      return Semantics(
        label: "交通警察手势动画 ${widget.id}",
        child: AnimatedBuilder(
          animation: _controller,
          builder: (context, _) => CustomPaint(
            size: Size.square(widget.size),
            painter: GestureFrontPainter(_clip.poseAt(_ms), _ghosts),
          ),
        ),
      );
    }
    final theme = Theme.of(context);
    final muted = theme.colorScheme.onSurfaceVariant;
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final pose = _clip.poseAt(_ms);
        final step = _clip.stepAt(_ms);
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Column(
                  children: [
                    CustomPaint(size: Size.square(widget.size), painter: GestureFrontPainter(pose, _ghosts)),
                    const SizedBox(height: 4),
                    Text("正面（交警面向你）", style: TextStyle(fontSize: 13, color: muted)),
                  ],
                ),
                const SizedBox(width: 14),
                Column(
                  children: [
                    CustomPaint(size: Size.square(widget.size * 0.78), painter: GestureTopPainter(pose, _ghosts)),
                    const SizedBox(height: 4),
                    Text("俯视（看前后方向）", style: TextStyle(fontSize: 13, color: muted)),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 12),
            ConstrainedBox(
              constraints: BoxConstraints(maxWidth: widget.size * 2 + 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  for (var i = 0; i < _clip.captions.length; i++)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            width: 22,
                            height: 22,
                            alignment: Alignment.center,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: i == step ? Bs.primary : Colors.transparent,
                              border: Border.all(color: i == step ? Bs.primary : muted.withValues(alpha: 0.5)),
                            ),
                            child: Text(
                              "${i + 1}",
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                                color: i == step ? Colors.white : muted,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _clip.captions[i],
                              style: TextStyle(
                                fontSize: 15,
                                height: 1.4,
                                fontWeight: i == step ? FontWeight.w600 : FontWeight.w400,
                                color: i == step ? theme.colorScheme.onSurface : muted,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 6),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  tooltip: "上一个姿势",
                  onPressed: () => _jump(_currentKey - 1),
                  icon: const Icon(Glyph.stepBack),
                ),
                IconButton.filled(
                  tooltip: _playing ? "暂停" : "播放",
                  onPressed: _toggle,
                  icon: Icon(_playing ? Glyph.pause : Glyph.play),
                ),
                IconButton(
                  tooltip: "下一个姿势",
                  onPressed: () => _jump(_currentKey + 1),
                  icon: const Icon(Glyph.stepNext),
                ),
                SizedBox(
                  width: widget.size * 1.2,
                  child: Slider(
                    value: _controller.value.clamp(0.0, 1.0),
                    onChanged: (v) => setState(() {
                      _playing = false;
                      _controller.stop();
                      _controller.value = v;
                    }),
                  ),
                ),
              ],
            ),
          ],
        );
      },
    );
  }
}
