import "dart:math";

import "package:flutter/material.dart";

import "glyphs.dart";
import "look.dart";
import "models.dart";
import "progress.dart";

// 首页与诊断页用的统计图表：考试走势、每日活动、章节正确率、掌握度环、数字块、正确率环。
// 设计令牌与基础组件（Bs、BsCard、徽章等）在 look.dart。

/// 模拟考战绩：一次一根柱，90 分线横在上面，一眼看出在不在往上走。
/// 悬停高亮一根柱并在左上角给出完整取值（ADR 0061）。
class ExamTrend extends StatefulWidget {
  const ExamTrend({
    super.key,
    required this.records,
    this.passScore = 90,
    this.height = 132,
  });

  /// 时间正序：老的在左，新的在右。
  final List<ExamPoint> records;
  final int passScore;
  final double height;

  @override
  State<ExamTrend> createState() => _ExamTrendState();
}

/// 单场考试的展示信息：分数、日期、过没过。look.dart 不认识 [ExamRecord]，
/// 只收元组，业务类型留在调用方（ADR 0061 决策 2）。
typedef ExamPoint = (int score, DateTime at, bool passed);

class _ExamTrendState extends State<ExamTrend> {
  int? _hover;

  int? _slotAt(double dx, double width) {
    final n = widget.records.length;
    if (n == 0 || width <= 0) return null;
    return (dx / width * n).floor().clamp(0, n - 1);
  }

  @override
  Widget build(BuildContext context) {
    if (widget.records.isEmpty) {
      return Text(
        "还没有模拟考记录。四个阶段过关后就能开考，考完这里会画出每次的分数。",
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Bs.secondary),
      );
    }
    return SizedBox(
      height: widget.height,
      child: LayoutBuilder(
        builder: (context, constraints) => MouseRegion(
          onHover: (e) => setState(() => _hover = _slotAt(e.localPosition.dx, constraints.maxWidth)),
          onExit: (_) => setState(() => _hover = null),
          child: CustomPaint(
            painter: _TrendPainter(widget.records, widget.passScore, hover: _hover),
            child: const SizedBox.expand(),
          ),
        ),
      ),
    );
  }
}

class _TrendPainter extends CustomPainter {
  _TrendPainter(this.records, this.passScore, {this.hover});

  final List<ExamPoint> records;
  final int passScore;
  final int? hover;

  @override
  void paint(Canvas canvas, Size size) {
    const labelHeight = 20.0;
    final chart = Rect.fromLTWH(0, 0, size.width, size.height - labelHeight);
    final slot = chart.width / records.length;
    final barWidth = min(slot * 0.6, 34.0);
    double yOf(int score) => chart.bottom - chart.height * (score.clamp(0, 100) / 100);

    // 90 分线
    final line = yOf(passScore);
    final dash = Paint()
      ..color = Bs.secondary
      ..strokeWidth = 1;
    for (var x = 0.0; x < chart.width; x += 8) {
      canvas.drawLine(Offset(x, line), Offset(x + 4, line), dash);
    }
    _text(canvas, Offset(chart.width - 2, line - 16), "$passScore 分", Bs.secondary, align: TextAlign.right);

    for (var i = 0; i < records.length; i++) {
      final score = records[i].$1;
      final center = slot * i + slot / 2;
      final top = yOf(score);
      final rect = RRect.fromRectAndRadius(
        Rect.fromLTRB(center - barWidth / 2, top, center + barWidth / 2, chart.bottom),
        const Radius.circular(3),
      );
      canvas.drawRRect(rect, Paint()..color = score >= passScore ? Bs.success : Bs.danger);
      if (hover == i) {
        canvas.drawRRect(
          rect.inflate(2),
          Paint()
            ..color = Bs.dark
            ..style = PaintingStyle.stroke
            ..strokeWidth = 2,
        );
      }
      _text(canvas, Offset(center, chart.bottom + 2), "$score", Bs.dark, align: TextAlign.center);
    }
    if (hover != null && hover! < records.length) {
      final (score, at, passed) = records[hover!];
      _text(
        canvas,
        const Offset(0, 0),
        "${at.month}月${at.day}日 · $score 分 · ${passed ? "及格" : "未过"}",
        Bs.dark,
      );
    }
  }

  void _text(Canvas canvas, Offset at, String text, Color color, {TextAlign align = TextAlign.left}) {
    final painter = TextPainter(
      text: TextSpan(text: text, style: TextStyle(color: color, fontSize: 13, fontWeight: FontWeight.w600)),
      textDirection: TextDirection.ltr,
      textAlign: align,
    )..layout();
    final dx = switch (align) {
      TextAlign.center => at.dx - painter.width / 2,
      TextAlign.right => at.dx - painter.width,
      _ => at.dx,
    };
    painter.paint(canvas, Offset(dx, at.dy));
  }

  @override
  bool shouldRepaint(covariant _TrendPainter oldDelegate) =>
      !recordsEquals(oldDelegate.records, records) ||
      oldDelegate.passScore != passScore ||
      oldDelegate.hover != hover;
}

bool recordsEquals(List<ExamPoint> a, List<ExamPoint> b) {
  if (a.length != b.length) return false;
  for (var i = 0; i < a.length; i++) {
    if (a[i].$1 != b[i].$1 || !a[i].$2.isAtSameMomentAs(b[i].$2) || a[i].$3 != b[i].$3) return false;
  }
  return true;
}

/// 最近 N 天的练习量：柱子连不上就是断更了，颜色按当天正确率分（主仓库 ADR 0056）。
class DailyActivityChart extends StatefulWidget {
  const DailyActivityChart({super.key, required this.days, this.height = 96});

  /// 时间正序：老的在左，今天在右。
  final List<DailyCount> days;
  final double height;

  /// 从今天往前数，连续有练习的天数——跟连对题目是两回事，这个看的是有没有停更。
  static int dayStreak(List<DailyCount> days) {
    var n = 0;
    for (final day in days.reversed) {
      if (day.attempts == 0) break;
      n++;
    }
    return n;
  }

  @override
  State<DailyActivityChart> createState() => _DailyActivityChartState();
}

class _DailyActivityChartState extends State<DailyActivityChart> {
  int? _hover;

  int? _slotAt(double dx, double width) {
    final n = widget.days.length;
    if (n == 0 || width <= 0) return null;
    return (dx / width * n).floor().clamp(0, n - 1);
  }

  @override
  Widget build(BuildContext context) {
    if (widget.days.every((d) => d.attempts == 0)) {
      return Text(
        "最近还没有练习记录，练一组就会画出来。",
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Bs.secondary),
      );
    }
    return SizedBox(
      height: widget.height,
      child: LayoutBuilder(
        builder: (context, constraints) => MouseRegion(
          onHover: (e) => setState(() => _hover = _slotAt(e.localPosition.dx, constraints.maxWidth)),
          onExit: (_) => setState(() => _hover = null),
          child: CustomPaint(
            painter: _DailyPainter(widget.days, hover: _hover),
            child: const SizedBox.expand(),
          ),
        ),
      ),
    );
  }
}

class _DailyPainter extends CustomPainter {
  _DailyPainter(this.days, {this.hover});

  final List<DailyCount> days;
  final int? hover;

  @override
  void paint(Canvas canvas, Size size) {
    const labelHeight = 18.0;
    final chart = Rect.fromLTWH(0, 0, size.width, size.height - labelHeight);
    final slot = chart.width / days.length;
    final barWidth = min(slot * 0.6, 22.0);
    final maxAttempts = days.map((d) => d.attempts).fold(1, (a, b) => a > b ? a : b);
    double yOf(int n) => chart.bottom - chart.height * (n / maxAttempts);

    for (var i = 0; i < days.length; i++) {
      final day = days[i];
      final center = slot * i + slot / 2;
      final isToday = i == days.length - 1;
      final color = day.attempts == 0
          ? Bs.border
          : (day.rate >= 0.9 ? Bs.success : (day.rate >= 0.7 ? Bs.warning : Bs.danger));
      final top = day.attempts == 0 ? chart.bottom - 3 : yOf(day.attempts);
      final rect = RRect.fromRectAndRadius(
        Rect.fromLTRB(center - barWidth / 2, top, center + barWidth / 2, chart.bottom),
        const Radius.circular(3),
      );
      canvas.drawRRect(rect, Paint()..color = color);
      if (hover == i) {
        canvas.drawRRect(
          rect.inflate(2),
          Paint()
            ..color = Bs.dark
            ..style = PaintingStyle.stroke
            ..strokeWidth = 2,
        );
      }
      if (isToday || i == 0 || day.day.day == 1) {
        _text(canvas, Offset(center, chart.bottom + 2), "${day.day.month}/${day.day.day}", isToday ? Bs.dark : Bs.secondary, align: TextAlign.center);
      }
    }
    if (hover != null && hover! < days.length) {
      final day = days[hover!];
      final detail = day.attempts == 0
          ? "${day.day.month}/${day.day.day} · 没练"
          : "${day.day.month}/${day.day.day} · ${day.attempts} 题 · 正确 ${(day.rate * 100).round()}%";
      _text(canvas, const Offset(0, 0), detail, Bs.dark);
    }
  }

  void _text(Canvas canvas, Offset at, String text, Color color, {TextAlign align = TextAlign.left}) {
    final painter = TextPainter(
      text: TextSpan(text: text, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w600)),
      textDirection: TextDirection.ltr,
      textAlign: align,
    )..layout();
    final dx = switch (align) {
      TextAlign.center => at.dx - painter.width / 2,
      TextAlign.right => at.dx - painter.width,
      _ => at.dx,
    };
    painter.paint(canvas, Offset(dx, at.dy));
  }

  @override
  bool shouldRepaint(covariant _DailyPainter oldDelegate) =>
      true; // 悬停状态画在图里，hover 变化就重画；图本身小，不值得做差量比较
}

/// 各章节正确率横向对比：条越短、越红的越该优先补（主仓库 ADR 0056）。
class TopicAccuracyChart extends StatelessWidget {
  const TopicAccuracyChart({super.key, required this.items, this.onTap});

  /// (章节标题, 这一章的作答统计)，调用方按想要的顺序传（通常是正确率从低到高）。
  final List<(String, TopicStats)> items;

  /// 点一行跳到哪——下标对应 `items` 里的顺序。不传就是纯展示，不能点。
  final void Function(int index)? onTap;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return Text(
        "还没有分章节的作答记录。",
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Bs.secondary),
      );
    }
    final style = Theme.of(context).textTheme.bodyMedium;
    // 标题列按最长的那个章节名量出宽度：最长的单行放得下，其余的自然也放得下，
    // 所有行的标题列同宽，条形图的起点和长度才能对齐、统一。
    var titleWidth = 0.0;
    for (final (title, _) in items) {
      final painter = TextPainter(
        text: TextSpan(text: title, style: style),
        textDirection: Directionality.of(context),
        maxLines: 1,
      )..layout();
      if (painter.width > titleWidth) titleWidth = painter.width;
    }
    return Column(
      children: [
        for (var i = 0; i < items.length; i++)
          () {
            final (title, stats) = items[i];
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  SizedBox(width: titleWidth, child: Text(title, maxLines: 1, style: style)),
                  const SizedBox(width: 20),
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(Bs.radius),
                      child: LinearProgressIndicator(
                        value: stats.attempts == 0 ? 0 : stats.rate,
                        minHeight: 14,
                        backgroundColor: Bs.border,
                        color: stats.attempts == 0
                            ? Bs.border
                            : (stats.rate >= 0.9 ? Bs.success : (stats.rate >= 0.7 ? Bs.warning : Bs.danger)),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  SizedBox(
                    width: 80,
                    child: Text(
                      stats.attempts == 0 ? "未练" : "${stats.correct}/${stats.attempts}",
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Bs.secondary),
                    ),
                  ),
                  // 跳转只挂在这个图标上——条形图、标题、数字都不能点，
                  // 免得使用者划过图表时误触跳转。
                  if (onTap != null) ...[
                    const SizedBox(width: 4),
                    IconButton(
                      tooltip: "去练这一章",
                      onPressed: () => onTap!(i),
                      icon: const Icon(Glyph.goTo, size: 20),
                    ),
                  ],
                ],
              ),
            );
          }(),
      ],
    );
  }
}

/// 掌握度环：已掌握、待练、还没见过三色分段，中间写百分比（主仓库 ADR 0056）。
class MasteryRing extends StatelessWidget {
  const MasteryRing({
    super.key,
    required this.mastered,
    required this.pending,
    required this.untouched,
    this.size = 96,
  });

  final int mastered;
  final int pending;
  final int untouched;
  final double size;

  int get _total => mastered + pending + untouched;

  @override
  Widget build(BuildContext context) {
    final pct = _total == 0 ? 0 : (mastered / _total * 100).round();
    return BsTweenFraction(
      end: 1,
      builder: (context, v) {
        final shown = (pct * v).round();
        return SizedBox(
          width: size,
          height: size,
          child: Stack(
            alignment: Alignment.center,
            children: [
              CustomPaint(
                size: Size(size, size),
                painter: _MasteryRingPainter(
                  mastered: mastered,
                  pending: pending,
                  untouched: untouched,
                  progress: v,
                ),
              ),
              Text("$shown%", style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
            ],
          ),
        );
      },
    );
  }
}

class _MasteryRingPainter extends CustomPainter {
  _MasteryRingPainter({
    required this.mastered,
    required this.pending,
    required this.untouched,
    this.progress = 1,
  });

  final int mastered;
  final int pending;
  final int untouched;

  /// 滑入因子（ADR 0060）：各段弧长乘它，进页面时环从 0 长出来。
  final double progress;

  @override
  void paint(Canvas canvas, Size size) {
    const strokeWidth = 10.0;
    final rect = Rect.fromLTWH(strokeWidth / 2, strokeWidth / 2, size.width - strokeWidth, size.height - strokeWidth);
    canvas.drawArc(
      rect,
      0,
      2 * pi,
      false,
      Paint()
        ..color = Bs.border
        ..style = PaintingStyle.stroke
        ..strokeWidth = strokeWidth,
    );
    final total = mastered + pending + untouched;
    if (total == 0) return;
    var start = -pi / 2;
    for (final segment in [(mastered, Bs.success), (pending, Bs.paper), (untouched, Bs.warning)]) {
      final count = segment.$1;
      if (count == 0) continue;
      final sweep = 2 * pi * progress * count / total;
      canvas.drawArc(
        rect,
        start,
        sweep,
        false,
        Paint()
          ..color = segment.$2
          ..style = PaintingStyle.stroke
          ..strokeWidth = strokeWidth,
      );
      start += sweep;
    }
  }

  @override
  bool shouldRepaint(covariant _MasteryRingPainter oldDelegate) =>
      oldDelegate.mastered != mastered ||
      oldDelegate.pending != pending ||
      oldDelegate.untouched != untouched ||
      oldDelegate.progress != progress;
}

class StatTile extends StatelessWidget {
  const StatTile({
    super.key,
    required this.icon,
    required this.label,
    required this.value,
    this.color,
  });

  final IconData icon;
  final String label;
  final String value;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final tone = color ?? Bs.primary;
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 12, 16, 12),
      decoration: BoxDecoration(
        color: Bs.body,
        borderRadius: BorderRadius.circular(Bs.radiusCard),
        boxShadow: Bs.cardShadow,
      ),
      child: Row(
        // 不写 min 的话 Row 会把统计块撑满整行，四个块各占一行，白占地方
        mainAxisSize: MainAxisSize.min,
        children: [
          CircleAvatar(
            radius: 20,
            backgroundColor: tone.withValues(alpha: 0.15),
            child: Icon(icon, size: 22, color: tone),
          ),
          const SizedBox(width: 10),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: TextStyle(color: Bs.secondary, fontSize: 16)),
              Text(value, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: Bs.bodySize)),
            ],
          ),
        ],
      ),
    );
  }
}

class RateRing extends StatelessWidget {
  const RateRing({
    super.key,
    required this.rate,
    required this.caption,
    this.color,
    this.size = 56,
  });

  final double rate;
  final String caption;
  final Color? color;
  final double size;

  @override
  Widget build(BuildContext context) {
    final tone = color ?? Bs.primary;
    return SizedBox(
      width: size,
      height: size,
      child: BsTweenFraction(
        end: rate,
        builder: (context, v) => CustomPaint(
          painter: _RingPainter(v, tone),
          child: Center(
            child: Text(
              caption,
              style: TextStyle(fontSize: size * 0.22, fontWeight: FontWeight.w700, color: tone),
            ),
          ),
        ),
      ),
    );
  }
}

class _RingPainter extends CustomPainter {
  _RingPainter(this.rate, this.color);

  final double rate;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = min(size.width, size.height) / 2 - 4;
    final track = Paint()
      ..color = Bs.border
      ..style = PaintingStyle.stroke
      ..strokeWidth = 5;
    final fill = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 5
      ..strokeCap = StrokeCap.round;
    canvas.drawCircle(center, radius, track);
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -pi / 2,
      2 * pi * rate,
      false,
      fill,
    );
  }

  @override
  bool shouldRepaint(covariant _RingPainter oldDelegate) =>
      oldDelegate.rate != rate || oldDelegate.color != color;
}
