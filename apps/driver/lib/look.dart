import "dart:io";
import "dart:math";

import "package:flutter/material.dart";

import "content.dart";

/// Bootstrap 5 色板与常用零件。图标用 Material 的系统符号，角色对齐 Bootstrap Icons。
class Bs {
  static const primary = Color(0xFFB45309);
  static const success = Color(0xFF198754);
  static const danger = Color(0xFFDC3545);
  static const warning = Color(0xFFCA8A04);
  static const info = Color(0xFF57534E);
  static const paper = Color(0xFF8B5A2B);
  static const secondary = Color(0xFF6C757D);
  static const light = Color(0xFFF8F9FA);
  static const dark = Color(0xFF212529);
  static const body = Color(0xFFFFFFFF);
  static const border = Color(0xFFDEE2E6);
  static const nav = Color(0xFF2A2420);
  static const radius = 4.0;
  static const bodySize = 20.0;

  static TextTheme textTheme(TextTheme base) {
    TextStyle scaled(TextStyle? style, double size, {FontWeight? weight, double height = 1.4}) {
      return (style ?? const TextStyle()).copyWith(
        fontSize: size,
        height: height,
        fontWeight: weight ?? style?.fontWeight,
      );
    }

    return base.copyWith(
      displaySmall: scaled(base.displaySmall, 32, weight: FontWeight.w700, height: 1.2),
      headlineMedium: scaled(base.headlineMedium, 26, weight: FontWeight.w700, height: 1.25),
      headlineSmall: scaled(base.headlineSmall, 24, weight: FontWeight.w600, height: 1.35),
      titleLarge: scaled(base.titleLarge, 22, weight: FontWeight.w700, height: 1.35),
      titleMedium: scaled(base.titleMedium, bodySize, weight: FontWeight.w600),
      titleSmall: scaled(base.titleSmall, bodySize, weight: FontWeight.w600),
      bodyLarge: scaled(base.bodyLarge, bodySize),
      bodyMedium: scaled(base.bodyMedium, bodySize),
      bodySmall: scaled(base.bodySmall, 18),
      labelLarge: scaled(base.labelLarge, 18, weight: FontWeight.w600),
      labelMedium: scaled(base.labelMedium, 16, weight: FontWeight.w600),
      labelSmall: scaled(base.labelSmall, 16, weight: FontWeight.w600),
    );
  }

  static String sourceShort(String sourceId) {
    return switch (sourceId) {
      "road-safety-law" => "道交法",
      "road-safety-regulation" => "实施条例",
      "license-order-162" => "驾驶证规定",
      "penalty-order-163" => "记分办法",
      "registration-order-164" => "登记规定",
      "accident-order-146" => "事故处理规定",
      "criminal-law" => "刑法",
      "ga-1026" => "GA 1026",
      "gb5768-2" => "GB 5768 标志",
      "gb5768-3" => "GB 5768 标线",
      "public-bank-2022" => "公开题库",
      _ => sourceId,
    };
  }

  /// 说明「为什么选这条题」的来源不是法条，不进题干上方的徽章行。
  static bool isContentSource(String relation) {
    return relation != "selection_basis" && relation != "exam_alignment" && relation != "see_also";
  }

  static IconData kindIcon(String kind) {
    return switch (kind) {
      "judge" => Icons.rule,
      "multi" => Icons.library_add_check_outlined,
      _ => Icons.radio_button_checked,
    };
  }

  static String kindLabel(String kind) {
    return switch (kind) {
      "judge" => "判断",
      "multi" => "多选",
      _ => "单选",
    };
  }
}

/// 题图：开发时直接读工作树里的文件，发行包走打进去的 assets。
class QuestionImage extends StatelessWidget {
  const QuestionImage({super.key, required this.path, this.maxWidth = 560});

  final String path;
  final double maxWidth;

  ImageProvider get _provider {
    final resolved = ContentLoader.imagePath(path);
    return ContentLoader.imagesOnDisk ? FileImage(File(resolved)) : AssetImage(resolved);
  }

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Tooltip(
        message: "点开看大图",
        child: InkWell(
          onTap: () => _open(context),
          borderRadius: BorderRadius.circular(Bs.radius),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(Bs.radius),
            child: ConstrainedBox(
              constraints: BoxConstraints(maxWidth: maxWidth),
              child: Image(image: _provider, fit: BoxFit.contain),
            ),
          ),
        ),
      ),
    );
  }

  /// 点开铺满窗口看细节：图里的红圈、远处的车灯，缩在栏里根本看不清。
  void _open(BuildContext context) {
    showDialog<void>(
      context: context,
      barrierColor: Colors.black87,
      builder: (dialogContext) => Dialog(
        insetPadding: const EdgeInsets.all(32),
        backgroundColor: Colors.transparent,
        child: Stack(
          alignment: Alignment.topRight,
          children: [
            InteractiveViewer(
              maxScale: 5,
              child: Image(image: _provider, fit: BoxFit.contain),
            ),
            IconButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              icon: const Icon(Icons.close, color: Colors.white, size: 28),
              tooltip: "关闭",
            ),
          ],
        ),
      ),
    );
  }
}

class BsBadge extends StatelessWidget {
  const BsBadge({
    super.key,
    required this.text,
    this.color = Bs.primary,
    this.foreground,
    this.icon,
  });

  final String text;
  final Color color;
  final Color? foreground;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final fg = foreground ?? (color == Bs.warning || color == Bs.light ? Bs.dark : Colors.white);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(Bs.radius),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 18, color: fg),
            const SizedBox(width: 6),
          ],
          Text(text, style: TextStyle(color: fg, fontSize: 16, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

class BsAlert extends StatelessWidget {
  const BsAlert({
    super.key,
    required this.child,
    this.color = Bs.info,
    this.icon,
  });

  final Widget child;
  final Color color;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        border: Border(left: BorderSide(color: color, width: 4)),
        borderRadius: BorderRadius.circular(Bs.radius),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 22, color: color),
            const SizedBox(width: 10),
          ],
          Expanded(child: child),
        ],
      ),
    );
  }
}

class BsProgress extends StatelessWidget {
  const BsProgress({super.key, required this.value, this.color = Bs.primary});

  final double value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(Bs.radius),
      child: LinearProgressIndicator(
        value: value.clamp(0, 1),
        minHeight: 10,
        color: color,
        backgroundColor: Bs.border,
      ),
    );
  }
}

/// 模拟考战绩：一次一根柱，90 分线横在上面，一眼看出在不在往上走。
class ExamTrend extends StatelessWidget {
  const ExamTrend({super.key, required this.scores, this.passScore = 90, this.height = 132});

  /// 时间正序：老的在左，新的在右。
  final List<int> scores;
  final int passScore;
  final double height;

  @override
  Widget build(BuildContext context) {
    if (scores.isEmpty) {
      return Text(
        "还没有模拟考记录。四个阶段过关后就能开考，考完这里会画出每次的分数。",
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Bs.secondary),
      );
    }
    return SizedBox(
      height: height,
      child: CustomPaint(
        painter: _TrendPainter(scores, passScore),
        child: const SizedBox.expand(),
      ),
    );
  }
}

class _TrendPainter extends CustomPainter {
  _TrendPainter(this.scores, this.passScore);

  final List<int> scores;
  final int passScore;

  @override
  void paint(Canvas canvas, Size size) {
    const labelHeight = 20.0;
    final chart = Rect.fromLTWH(0, 0, size.width, size.height - labelHeight);
    final slot = chart.width / scores.length;
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

    for (var i = 0; i < scores.length; i++) {
      final score = scores[i];
      final center = slot * i + slot / 2;
      final top = yOf(score);
      final rect = RRect.fromRectAndRadius(
        Rect.fromLTRB(center - barWidth / 2, top, center + barWidth / 2, chart.bottom),
        const Radius.circular(3),
      );
      canvas.drawRRect(rect, Paint()..color = score >= passScore ? Bs.success : Bs.danger);
      _text(canvas, Offset(center, chart.bottom + 2), "$score", Bs.dark, align: TextAlign.center);
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
      !listEquals(oldDelegate.scores, scores) || oldDelegate.passScore != passScore;
}

bool listEquals(List<int> a, List<int> b) {
  if (a.length != b.length) return false;
  for (var i = 0; i < a.length; i++) {
    if (a[i] != b[i]) return false;
  }
  return true;
}

class StatTile extends StatelessWidget {
  const StatTile({
    super.key,
    required this.icon,
    required this.label,
    required this.value,
    this.color = Bs.primary,
  });

  final IconData icon;
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 12, 16, 12),
      decoration: BoxDecoration(
        color: Bs.body,
        border: Border.all(color: Bs.border),
        borderRadius: BorderRadius.circular(Bs.radius),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 20,
            backgroundColor: color.withValues(alpha: 0.15),
            child: Icon(icon, size: 22, color: color),
          ),
          const SizedBox(width: 10),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(color: Bs.secondary, fontSize: 16)),
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
    this.color = Bs.primary,
    this.size = 56,
  });

  final double rate;
  final String caption;
  final Color color;
  final double size;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(
        painter: _RingPainter(rate.clamp(0, 1), color),
        child: Center(
          child: Text(
            caption,
            style: TextStyle(fontSize: size * 0.22, fontWeight: FontWeight.w700, color: color),
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
