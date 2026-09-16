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
      "license-order-162" => "公安部令162号",
      "ga-1026" => "GA 1026",
      "gb5768-2" => "GB 5768",
      _ => sourceId,
    };
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

  @override
  Widget build(BuildContext context) {
    final resolved = ContentLoader.imagePath(path);
    final image = ContentLoader.imagesOnDisk
        ? Image.file(File(resolved), fit: BoxFit.contain)
        : Image.asset(resolved, fit: BoxFit.contain);
    return Align(
      alignment: Alignment.centerLeft,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(Bs.radius),
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: maxWidth),
          child: image,
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
