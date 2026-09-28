import "dart:math";

import "package:flutter/material.dart";
import "package:flutter/scheduler.dart";

/// 科目二四项的动画示意（ADR 0036）。
///
/// 车按后轴中心走「直线 + 满舵圆弧」，是自行车模型在转向瞬时到位时的轨迹——
/// 足够说明「什么时候打方向、车身怎么摆」，也能逐帧算出车身四角和四个车轮，
/// 由测试检查示意动作本身不出线、不压线。场地尺寸是示意，不按比例，以考场为准。
///
/// 坐标：米，屏幕方向（x 向右、y 向下）。朝向 heading 为弧度，前进方向
/// `(cos h, sin h)`；车的左手边是 `(sin h, -cos h)`。

/// 示意车：两厢小车的量级。
class CarSpec {
  const CarSpec({
    this.wheelbase = 2.6,
    this.frontOverhang = 0.9,
    this.rearOverhang = 0.9,
    this.width = 1.8,
    this.track = 1.5,
    this.minRadius = 5.0,
  });

  final double wheelbase;
  final double frontOverhang;
  final double rearOverhang;
  final double width;

  /// 左右车轮中心距。
  final double track;

  /// 满舵时后轴中心的转弯半径。
  final double minRadius;

  double get length => wheelbase + frontOverhang + rearOverhang;
}

const car = CarSpec();

class Pose {
  const Pose(this.x, this.y, this.heading);

  final double x;
  final double y;
  final double heading;

  Offset get position => Offset(x, y);
  Offset get forward => Offset(cos(heading), sin(heading));
  Offset get left => Offset(sin(heading), -cos(heading));

  /// 车身坐标（沿车头 a 米、向左 b 米）换成场地坐标。
  Offset local(double a, double b) => position + forward * a + left * b;

  /// 车身四角：左前、右前、右后、左后。
  List<Offset> corners([CarSpec spec = car]) {
    final front = spec.wheelbase + spec.frontOverhang;
    final back = -spec.rearOverhang;
    final half = spec.width / 2;
    return [local(front, half), local(front, -half), local(back, -half), local(back, half)];
  }

  /// 车身轮廓上均匀取点（每边 [perEdge] 段），用来判断「车身出线」。
  List<Offset> outline([CarSpec spec = car, int perEdge = 10]) {
    final c = corners(spec);
    return [
      for (var i = 0; i < 4; i++)
        for (var k = 0; k < perEdge; k++) Offset.lerp(c[i], c[(i + 1) % 4], k / perEdge)!,
    ];
  }

  /// 四个车轮的接地点：左前、右前、左后、右后；每个轮子取前后两点（轮胎接地有长度）。
  List<Offset> wheelPatches([CarSpec spec = car]) {
    final half = spec.track / 2;
    const tyre = 0.3;
    return [
      for (final a in [spec.wheelbase, 0.0])
        for (final b in [half, -half])
          for (final d in [-tyre, tyre]) local(a + d, b),
    ];
  }

  /// 两个前轮的接地点（判断「前轮越过控制线」）。
  List<Offset> frontWheels([CarSpec spec = car]) => [
        local(spec.wheelbase, spec.track / 2),
        local(spec.wheelbase, -spec.track / 2),
      ];
}

enum Gear { park, drive, reverse }

enum Signal { none, left, right }

/// 一段动作。
sealed class Move {
  const Move();

  /// 这一段走完需要的秒数。
  double seconds(double speed);

  Pose at(Pose start, double fraction);

  /// 前轮转角（弧度，向左为正），画车轮用。
  double get steer;

  Gear? get gear;
}

/// 直线：[distance] 正为前进，负为倒车。
class Straight extends Move {
  const Straight(this.distance);

  final double distance;

  @override
  double seconds(double speed) => distance.abs() / speed;

  @override
  Pose at(Pose start, double fraction) {
    final p = start.position + start.forward * (distance * fraction);
    return Pose(p.dx, p.dy, start.heading);
  }

  @override
  double get steer => 0;

  @override
  Gear get gear => distance >= 0 ? Gear.drive : Gear.reverse;
}

/// 满舵（或指定半径）圆弧：[degrees] 是车身转过的角度，[leftTurn] 是方向盘往左打，
/// [reverse] 为倒车。
class Arc extends Move {
  const Arc(this.degrees, {required this.leftTurn, this.reverse = false, this.radius = 0});

  final double degrees;
  final bool leftTurn;
  final bool reverse;

  /// 0 表示满舵（[CarSpec.minRadius]）。
  final double radius;

  double get _r => radius == 0 ? car.minRadius : radius;
  double get _length => _r * degrees * pi / 180;

  @override
  double seconds(double speed) => _length / speed;

  @override
  Pose at(Pose start, double fraction) {
    // 曲率 k 带符号（左正），走过 s 米后朝向变 -k·s，位置 P = P0 + (left(h0) - left(h)) / k。
    final k = (leftTurn ? 1 : -1) / _r;
    final s = (reverse ? -1 : 1) * _length * fraction;
    final heading = start.heading - k * s;
    final end = Pose(0, 0, heading);
    final p = start.position + (start.left - end.left) / k;
    return Pose(p.dx, p.dy, heading);
  }

  @override
  double get steer => (leftTurn ? 1 : -1) * atan(car.wheelbase / _r);

  @override
  Gear get gear => reverse ? Gear.reverse : Gear.drive;
}

/// 原地停一下：换挡、开灯、看清楚。
class Hold extends Move {
  const Hold(this.duration);

  final double duration;

  @override
  double seconds(double speed) => duration;

  @override
  Pose at(Pose start, double fraction) => start;

  @override
  double get steer => 0;

  @override
  Gear? get gear => null;
}

class DrillStep {
  const DrillStep(this.moves, {this.signal = Signal.none, this.gear, this.cue});

  final List<Move> moves;
  final Signal signal;

  /// 这一步开始时停着挂的挡（准备阶段是 P）；动起来以后按动作显示 D / R。
  final Gear? gear;

  /// 叠在画面上的一句要点。
  final String? cue;
}

enum LineKind { edge, bay, control, lane }

class SceneLine {
  const SceneLine(this.points, this.kind, {this.closed = false});

  final List<Offset> points;
  final LineKind kind;
  final bool closed;
}

/// 这一项按什么判出线：倒车入库、侧方停车看车身；曲线行驶、直角转弯看车轮。
enum Judged { body, wheels }

class DrillScene {
  const DrillScene({
    required this.id,
    required this.start,
    required this.steps,
    required this.lines,
    required this.inside,
    required this.judged,
    required this.bounds,
    this.labels = const [],
  });

  final String id;
  final Pose start;
  final List<DrillStep> steps;
  final List<SceneLine> lines;

  /// 允许的区域（道路 ∪ 库位）：判定点必须都在里面。
  final bool Function(Offset p) inside;
  final Judged judged;
  final Rect bounds;
  final List<(Offset, String)> labels;
}

/// 播放时某一刻的状态。
class Frame {
  const Frame({
    required this.pose,
    required this.step,
    required this.stepProgress,
    required this.gear,
    required this.signal,
    required this.steer,
    required this.trail,
  });

  final Pose pose;
  final int step;
  final double stepProgress;
  final Gear gear;
  final Signal signal;
  final double steer;

  /// 到这一刻为止后轴中心走过的点（画轨迹）。
  final List<Offset> trail;
}

/// 把一项的步骤摊成时间轴。
class Timeline {
  Timeline(this.scene, {this.speed = 1.3}) {
    var t = 0.0;
    var pose = scene.start;
    for (var i = 0; i < scene.steps.length; i++) {
      stepStarts.add(t);
      for (final move in scene.steps[i].moves) {
        final d = move.seconds(speed);
        _segments.add((i, move, t, d, pose));
        t += d;
        pose = move.at(pose, 1);
      }
    }
    total = t;
    end = pose;
  }

  final DrillScene scene;
  final double speed;
  final stepStarts = <double>[];
  final _segments = <(int, Move, double, double, Pose)>[];
  late final double total;
  late final Pose end;

  double stepEnd(int step) => step + 1 < stepStarts.length ? stepStarts[step + 1] : total;

  Frame frame(double t) {
    t = t.clamp(0, total);
    final trail = <Offset>[];
    Gear gear = scene.steps.first.gear ?? Gear.park;
    var result = scene.start;
    var step = 0;
    var steer = 0.0;
    for (final (index, move, begin, duration, from) in _segments) {
      if (begin > t) break;
      step = index;
      final stepGear = scene.steps[index].gear;
      if (stepGear != null && begin == stepStarts[index]) gear = stepGear;
      final fraction = duration == 0 ? 1.0 : ((t - begin) / duration).clamp(0.0, 1.0);
      final moving = move is! Hold;
      if (moving) {
        final samples = max(2, (duration * 8).ceil());
        final upto = (samples * fraction).ceil();
        for (var k = 0; k <= upto; k++) {
          trail.add(move.at(from, min(1.0, k / samples)).position);
        }
        gear = move.gear ?? gear;
      }
      result = move.at(from, fraction);
      steer = moving && fraction < 1 ? move.steer : 0;
    }
    final begin = stepStarts[step];
    final span = stepEnd(step) - begin;
    return Frame(
      pose: result,
      step: step,
      stepProgress: span == 0 ? 1 : ((t - begin) / span).clamp(0.0, 1.0),
      gear: gear,
      signal: scene.steps[step].signal,
      steer: steer,
      trail: trail,
    );
  }

  /// 逐帧取样（测试用）：[dt] 秒一帧。
  Iterable<Frame> sample([double dt = 0.02]) sync* {
    for (var t = 0.0; t <= total; t += dt) {
      yield frame(t);
    }
    yield frame(total);
  }
}

bool _inRect(Offset p, Rect r) => p.dx >= r.left && p.dx <= r.right && p.dy >= r.top && p.dy <= r.bottom;

List<Offset> _arcPoints(Offset c, double radius, double from, double to, [int n = 48]) => [
      for (var i = 0; i <= n; i++)
        c + Offset(cos(from + (to - from) * i / n), sin(from + (to - from) * i / n)) * radius,
    ];

// ---------------------------------------------------------------------------
// 倒车入库：道路在上，库在下方正中；两端各一条控制线。先从右端倒入，出库开到左端
// 控制线外，再倒入，最后回到右端起点（GA 1026—2022 5.2.2.2）。
// ---------------------------------------------------------------------------

const _reverseRoad = Rect.fromLTRB(-16, 0, 16, 7);
const _reverseBay = Rect.fromLTRB(-1.2, 7, 1.2, 12.1); // 宽 = 车宽 + 0.6，长 = 车长 + 0.7
const reverseControlX = 10.0;

final reverseScene = DrillScene(
  id: "reverse",
  start: const Pose(7.6, 3.2, 0),
  judged: Judged.body,
  bounds: const Rect.fromLTRB(-16, -1, 16, 13),
  inside: (p) => _inRect(p, _reverseRoad) || _inRect(p, _reverseBay),
  lines: [
    const SceneLine([Offset(-16, 0), Offset(16, 0)], LineKind.edge),
    const SceneLine([Offset(-16, 7), Offset(-1.2, 7), Offset(-1.2, 12.1), Offset(1.2, 12.1), Offset(1.2, 7), Offset(16, 7)], LineKind.bay),
    const SceneLine([Offset(-reverseControlX, 0), Offset(-reverseControlX, 7)], LineKind.control),
    const SceneLine([Offset(reverseControlX, 0), Offset(reverseControlX, 7)], LineKind.control),
  ],
  labels: const [
    (Offset(0, 9.6), "车库"),
    (Offset(-reverseControlX, -0.6), "控制线"),
    (Offset(reverseControlX, -0.6), "控制线"),
  ],
  steps: const [
    DrillStep([Hold(1.6)], gear: Gear.park, cue: "安全带、车门、P 挡启动"),
    DrillStep([Hold(0.6), Straight(-2.6)], cue: "R 挡，刹车控速慢慢倒"),
    DrillStep([Arc(90, leftTurn: false, reverse: true)], cue: "打满方向，看两侧后视镜"),
    DrillStep([Straight(-2.8), Hold(0.8)], cue: "车身摆正再回正，倒到位停"),
    DrillStep([Straight(2.8), Arc(90, leftTurn: true), Straight(2.6), Hold(0.8)], cue: "两个前轮都要越过控制线"),
    DrillStep([Straight(-2.6), Arc(90, leftTurn: true, reverse: true), Straight(-2.8), Hold(0.8)], cue: "第二次入库，方法相同"),
    DrillStep([Straight(2.8), Arc(90, leftTurn: false), Straight(2.6)], cue: "前进出库回起点"),
  ],
);

// ---------------------------------------------------------------------------
// 侧方停车：车头朝上（北）沿道路右侧行驶，库位在右侧；库左前方一次倒车入库，
// 开左转向灯向左前方出库，出库后关灯（GA 1026—2022 5.2.5.2）。
// ---------------------------------------------------------------------------

const _parallelRoad = Rect.fromLTRB(0, -16, 3.4, 16);
const _parallelBay = Rect.fromLTRB(3.4, 0, 6.0, 7.6); // 宽 = 车宽 + 0.8，长 = 1.5 倍车长 + 1
const _parallelLane = 2.2; // 车道里后轴中心离左边线的距离
const _parallelBayX = 4.7; // 入库后后轴中心（库位中线）
// 两段等角反向满舵弧把车横移 Δx：Δx = 2R(1 - cos α)。
final _parallelAngle = acos(1 - (_parallelBayX - _parallelLane) / (2 * car.minRadius)) * 180 / pi;
final _parallelStartY = 6.4 - 2 * car.minRadius * sin(_parallelAngle * pi / 180);

final parallelScene = DrillScene(
  id: "parallel",
  start: Pose(_parallelLane, _parallelStartY + 8, -pi / 2),
  judged: Judged.body,
  bounds: const Rect.fromLTRB(-2, -14, 8, 16),
  inside: (p) => _inRect(p, _parallelRoad) || _inRect(p, _parallelBay),
  lines: const [
    SceneLine([Offset(0, -16), Offset(0, 16)], LineKind.edge),
    SceneLine([Offset(3.4, -16), Offset(3.4, 0), Offset(6.0, 0), Offset(6.0, 7.6), Offset(3.4, 7.6), Offset(3.4, 16)], LineKind.bay),
  ],
  labels: const [(Offset(4.7, 3.8), "库位")],
  steps: [
    const DrillStep([Hold(1.2)], gear: Gear.park, cue: "靠右行驶，和右边线保持距离"),
    const DrillStep([Straight(8), Hold(0.8)], cue: "停在库的左前方，挂 R 挡"),
    DrillStep([Arc(_parallelAngle, leftTurn: false, reverse: true)], cue: "向右打满，车尾斜进库"),
    DrillStep([Arc(_parallelAngle, leftTurn: true, reverse: true), const Hold(0.8)], cue: "向左打满，车身摆正停车"),
    const DrillStep([Hold(1.4)], signal: Signal.left, cue: "先开左转向灯，再挂 D 挡"),
    DrillStep([Arc(_parallelAngle, leftTurn: true), Arc(_parallelAngle, leftTurn: false)], signal: Signal.left, cue: "向左前方出库，再回方向摆正"),
    const DrillStep([Straight(5)], cue: "出库后关闭转向灯"),
  ],
);

// ---------------------------------------------------------------------------
// 曲线行驶：S 形弯，两段半圆首尾相接。车身走弯道外侧，给内侧后轮留内轮差。
// ---------------------------------------------------------------------------

const _curveCenter1 = Offset(-8, 0);
const _curveCenter2 = Offset(-24, 0);
const _curveRadius = 8.0;
const _curveHalfWidth = 1.8;
const _curveOuter1 = 8.3; // 左弯：后轴中心走外侧
const _curveOuter2 = 7.7; // 右弯：同一条后轴轨迹对第二个圆心而言在内侧 → 车身相对第二个弯走外侧

bool _curveInside(Offset p) {
  if (_inRect(p, const Rect.fromLTRB(-_curveHalfWidth, 0, _curveHalfWidth, 12))) return true;
  if (_inRect(p, const Rect.fromLTRB(-32 - _curveHalfWidth, -12, -32 + _curveHalfWidth, 0))) return true;
  final d1 = (p - _curveCenter1).distance;
  if (p.dy <= 0 && d1 >= _curveRadius - _curveHalfWidth && d1 <= _curveRadius + _curveHalfWidth) return true;
  final d2 = (p - _curveCenter2).distance;
  if (p.dy >= 0 && d2 >= _curveRadius - _curveHalfWidth && d2 <= _curveRadius + _curveHalfWidth) return true;
  return false;
}

final curveScene = DrillScene(
  id: "curve",
  start: const Pose(_curveOuter1 - 8, 11, -pi / 2),
  judged: Judged.wheels,
  bounds: const Rect.fromLTRB(-36, -12, 4, 12),
  inside: _curveInside,
  lines: [
    for (final dx in [-_curveHalfWidth, _curveHalfWidth]) SceneLine([Offset(dx, 12), Offset(dx, 0)], LineKind.edge),
    for (final r in [_curveRadius - _curveHalfWidth, _curveRadius + _curveHalfWidth])
      SceneLine(_arcPoints(_curveCenter1, r, 0, -pi), LineKind.edge),
    for (final r in [_curveRadius - _curveHalfWidth, _curveRadius + _curveHalfWidth])
      SceneLine(_arcPoints(_curveCenter2, r, 0, pi), LineKind.edge),
    for (final dx in [-32 - _curveHalfWidth, -32 + _curveHalfWidth]) SceneLine([Offset(dx, 0), Offset(dx, -12)], LineKind.edge),
    SceneLine(_arcPoints(_curveCenter1, _curveRadius, 0, -pi), LineKind.lane),
    SceneLine(_arcPoints(_curveCenter2, _curveRadius, 0, pi), LineKind.lane),
  ],
  labels: const [(Offset(-8, -4), "左弯"), (Offset(-24, 4), "右弯")],
  steps: const [
    DrillStep([Hold(0.8), Straight(11)], gear: Gear.park, cue: "D 挡怠速，匀速进入"),
    DrillStep([Arc(180, leftTurn: true, radius: _curveOuter1)], cue: "左弯走外侧，方向慢打慢回"),
    DrillStep([Arc(180, leftTurn: false, radius: _curveOuter2)], cue: "换向，右弯走外侧"),
    DrillStep([Straight(8)], cue: "驶出，全程不停车"),
  ],
);

// ---------------------------------------------------------------------------
// 直角转弯（左转）：车道宽 3.5 m。靠外侧（右侧）行驶，车身前部过了内角再打满方向。
// ---------------------------------------------------------------------------

const cornerLane = 3.5;
const _cornerX = 2.65; // 后轴中心：靠右，右侧车轮离外侧边线约 0.1 m
const _cornerTurnY = 3.2; // 在这里开始打满方向

bool _cornerInside(Offset p) =>
    _inRect(p, const Rect.fromLTRB(0, -cornerLane, cornerLane, 14)) ||
    _inRect(p, const Rect.fromLTRB(-14, -cornerLane, cornerLane, 0));

final cornerScene = DrillScene(
  id: "corner",
  start: const Pose(_cornerX, 13, -pi / 2),
  judged: Judged.wheels,
  bounds: const Rect.fromLTRB(-14, -6, 6, 15),
  inside: _cornerInside,
  lines: const [
    SceneLine([Offset(0, 14), Offset(0, 0), Offset(-14, 0)], LineKind.edge),
    SceneLine([Offset(cornerLane, 14), Offset(cornerLane, -cornerLane), Offset(-14, -cornerLane)], LineKind.edge),
  ],
  labels: const [(Offset(-0.9, 0.9), "内角")],
  steps: const [
    DrillStep([Hold(0.8), Straight(4)], gear: Gear.park, cue: "靠外侧（右侧）行驶"),
    DrillStep([Straight(13 - 4 - _cornerTurnY)], signal: Signal.left, cue: "转弯前开左转向灯"),
    DrillStep([Arc(90, leftTurn: true)], signal: Signal.left, cue: "车头过了内角再打满方向"),
    DrillStep([Straight(7)], cue: "回正驶出，关闭转向灯"),
  ],
);

final drillScenes = {for (final s in [reverseScene, parallelScene, curveScene, cornerScene]) s.id: s};

// ---------------------------------------------------------------------------
// 播放器
// ---------------------------------------------------------------------------

class DrillPlayer extends StatefulWidget {
  const DrillPlayer({super.key, required this.scene, required this.stepTitles, this.onStep});

  final DrillScene scene;

  /// 步骤标题（来自 content/subject2.json，条数与场景步骤一致）。
  final List<String> stepTitles;
  final ValueChanged<int>? onStep;

  @override
  State<DrillPlayer> createState() => DrillPlayerState();
}

class DrillPlayerState extends State<DrillPlayer> with SingleTickerProviderStateMixin {
  late Timeline _timeline = Timeline(widget.scene);
  late final Ticker _ticker = createTicker(_tick);
  Duration _last = Duration.zero;
  double _t = 0;
  double _rate = 1;
  bool _playing = false;
  int _step = 0;

  double get time => _t;
  bool get playing => _playing;

  @override
  void didUpdateWidget(DrillPlayer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.scene != widget.scene) {
      _timeline = Timeline(widget.scene);
      _seek(0);
    }
  }

  @override
  void dispose() {
    _ticker.dispose();
    super.dispose();
  }

  void _tick(Duration elapsed) {
    final dt = (elapsed - _last).inMicroseconds / 1e6;
    _last = elapsed;
    _seek(_t + dt * _rate);
    final stopAt = _stopAt;
    if (stopAt != null && _t >= stopAt) {
      _seek(stopAt);
      _stopAt = null;
      pause();
    } else if (_t >= _timeline.total) {
      pause();
    }
  }

  void _seek(double t) {
    setState(() => _t = t.clamp(0, _timeline.total));
    final step = _timeline.frame(_t).step;
    if (step != _step) {
      _step = step;
      widget.onStep?.call(step);
    }
  }

  void play() {
    if (_t >= _timeline.total) _seek(0);
    _last = Duration.zero;
    _ticker.start();
    setState(() => _playing = true);
  }

  void pause() {
    _ticker.stop();
    setState(() => _playing = false);
  }

  /// 跳到某一步开头并暂停，方便对着画面读这一步。
  void jumpTo(int step) {
    pause();
    _seek(_timeline.stepStarts[step.clamp(0, _timeline.stepStarts.length - 1)]);
  }

  /// 单步：播完这一步就停。
  void playStep(int step) {
    jumpTo(step);
    _stopAt = _timeline.stepEnd(step.clamp(0, _timeline.stepStarts.length - 1));
    play();
  }

  double? _stopAt;

  @override
  Widget build(BuildContext context) {
    final frame = _timeline.frame(_t);
    final steps = widget.scene.steps;
    final title = frame.step < widget.stepTitles.length ? widget.stepTitles[frame.step] : "";
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AspectRatio(
          aspectRatio: 16 / 10,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: CustomPaint(
              painter: DrillPainter(
                scene: widget.scene,
                frame: frame,
                caption: "第 ${frame.step + 1} 步 · $title",
                cue: steps[frame.step].cue,
                blinkOn: (_t * 2.5).floor().isEven,
              ),
            ),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            IconButton(
              tooltip: "上一步",
              onPressed: () => jumpTo(frame.step - (frame.stepProgress < 0.05 ? 1 : 0)),
              icon: const Icon(Icons.skip_previous),
            ),
            IconButton.filled(
              tooltip: _playing ? "暂停" : "播放",
              onPressed: () {
                _stopAt = null;
                _playing ? pause() : play();
              },
              icon: Icon(_playing ? Icons.pause : Icons.play_arrow),
            ),
            IconButton(
              tooltip: "只播这一步",
              onPressed: () => playStep(frame.step),
              icon: const Icon(Icons.play_circle_outline),
            ),
            IconButton(
              tooltip: "下一步",
              onPressed: frame.step + 1 < steps.length ? () => jumpTo(frame.step + 1) : null,
              icon: const Icon(Icons.skip_next),
            ),
            IconButton(tooltip: "从头", onPressed: () => jumpTo(0), icon: const Icon(Icons.replay)),
            const SizedBox(width: 8),
            Expanded(
              child: Slider(
                value: _t,
                max: _timeline.total,
                onChanged: (v) {
                  pause();
                  _seek(v);
                },
              ),
            ),
            SegmentedButton<double>(
              showSelectedIcon: false,
              segments: const [
                ButtonSegment(value: 0.5, label: Text("慢")),
                ButtonSegment(value: 1, label: Text("常速")),
                ButtonSegment(value: 2, label: Text("快")),
              ],
              selected: {_rate},
              onSelectionChanged: (v) => setState(() => _rate = v.first),
            ),
          ],
        ),
      ],
    );
  }
}

class DrillPainter extends CustomPainter {
  DrillPainter({
    required this.scene,
    required this.frame,
    required this.caption,
    required this.cue,
    required this.blinkOn,
  });

  final DrillScene scene;
  final Frame frame;
  final String caption;
  final String? cue;
  final bool blinkOn;

  static const _ground = Color(0xFF3F454D);
  static const _lineWhite = Color(0xFFF2F2F2);
  static const _lineYellow = Color(0xFFF2C94C);
  static const _body = Color(0xFF2F80ED);
  static const _amber = Color(0xFFFFB020);

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawRect(Offset.zero & size, Paint()..color = _ground);
    final b = scene.bounds;
    final scale = min(size.width / b.width, size.height / b.height) * 0.94;
    final origin = Offset(
      (size.width - b.width * scale) / 2 - b.left * scale,
      (size.height - b.height * scale) / 2 - b.top * scale,
    );
    Offset map(Offset p) => origin + p * scale;

    // 场地线
    for (final line in scene.lines) {
      final paint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = line.kind == LineKind.lane ? 1 : 2.5
        ..color = switch (line.kind) {
          LineKind.bay => _lineYellow,
          LineKind.lane => _lineWhite.withValues(alpha: 0.25),
          _ => _lineWhite,
        };
      final pts = [for (final p in line.points) map(p)];
      if (line.kind == LineKind.control) {
        _dashed(canvas, pts.first, pts.last, paint);
      } else {
        canvas.drawPath(Path()..addPolygon(pts, line.closed), paint);
      }
    }
    for (final (at, text) in scene.labels) {
      _text(canvas, text, map(at), 13, _lineWhite.withValues(alpha: 0.75), center: true);
    }

    // 已走过的轨迹（后轴中心）
    if (frame.trail.length > 1) {
      canvas.drawPath(
        Path()..addPolygon([for (final p in frame.trail) map(p)], false),
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2
          ..color = _amber.withValues(alpha: 0.7),
      );
    }

    // 车
    final pose = frame.pose;
    final bodyPath = Path()..addPolygon([for (final c in pose.corners()) map(c)], true);
    canvas.drawPath(bodyPath, Paint()..color = _body);
    canvas.drawPath(
      bodyPath,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5
        ..color = Colors.white,
    );
    // 前挡风玻璃：一眼看出车头朝哪边
    final glass = [
      pose.local(car.wheelbase + 0.1, car.width / 2 - 0.2),
      pose.local(car.wheelbase + 0.1, -car.width / 2 + 0.2),
      pose.local(car.wheelbase - 0.5, -car.width / 2 + 0.25),
      pose.local(car.wheelbase - 0.5, car.width / 2 - 0.25),
    ];
    canvas.drawPath(Path()..addPolygon([for (final g in glass) map(g)], true), Paint()..color = const Color(0xFFBFD7F5));
    // 车轮：前轮随转向转动
    for (final (a, front) in [(car.wheelbase, true), (0.0, false)]) {
      for (final side in [1.0, -1.0]) {
        final center = pose.local(a, side * car.track / 2);
        final h = pose.heading - (front ? frame.steer : 0);
        final dir = Offset(cos(h), sin(h));
        final across = Offset(sin(h), -cos(h));
        const len = 0.35, wid = 0.12;
        final pts = [
          center + dir * len + across * wid,
          center + dir * len - across * wid,
          center - dir * len - across * wid,
          center - dir * len + across * wid,
        ];
        canvas.drawPath(Path()..addPolygon([for (final p in pts) map(p)], true), Paint()..color = const Color(0xFF111111));
      }
    }
    // 转向灯
    if (frame.signal != Signal.none && blinkOn) {
      final side = frame.signal == Signal.left ? 1.0 : -1.0;
      final lampPaint = Paint()..color = _amber;
      for (final a in [car.wheelbase + car.frontOverhang - 0.1, -car.rearOverhang + 0.1]) {
        canvas.drawCircle(map(pose.local(a, side * (car.width / 2 - 0.1))), max(3, 0.22 * scale), lampPaint);
      }
    }
    // 挡位
    final gear = switch (frame.gear) {
      Gear.park => "P",
      Gear.drive => "D",
      Gear.reverse => "R",
    };
    _badge(canvas, gear, map(pose.local(car.wheelbase / 2, 0)), frame.gear == Gear.reverse ? const Color(0xFFEB5757) : const Color(0xFF27AE60));

    // 说明条
    _text(canvas, caption, const Offset(14, 12), 16, Colors.white, bold: true);
    if (cue != null) _text(canvas, cue!, const Offset(14, 38), 14, _amber);
    _text(canvas, "示意图，不按比例；尺寸以考场为准", Offset(14, size.height - 24), 11, _lineWhite.withValues(alpha: 0.6));
  }

  void _dashed(Canvas canvas, Offset a, Offset b, Paint paint) {
    final total = (b - a).distance;
    const dash = 8.0, gap = 6.0;
    final dir = (b - a) / total;
    for (var d = 0.0; d < total; d += dash + gap) {
      canvas.drawLine(a + dir * d, a + dir * min(total, d + dash), paint);
    }
  }

  void _badge(Canvas canvas, String text, Offset at, Color color) {
    canvas.drawCircle(at, 11, Paint()..color = color);
    _text(canvas, text, at, 13, Colors.white, center: true, bold: true);
  }

  void _text(Canvas canvas, String text, Offset at, double size, Color color, {bool center = false, bool bold = false}) {
    final painter = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(
          fontSize: size,
          color: color,
          fontWeight: bold ? FontWeight.w700 : FontWeight.w400,
          shadows: const [Shadow(blurRadius: 3, color: Colors.black54)],
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    painter.paint(canvas, center ? at - Offset(painter.width / 2, painter.height / 2) : at);
  }

  @override
  bool shouldRepaint(DrillPainter old) => old.frame != frame || old.blinkOn != blinkOn || old.caption != caption;
}
