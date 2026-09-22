import "dart:async";
import "dart:io";
import "dart:math";
import "dart:ui" as ui;

import "package:flutter/material.dart";

import "content.dart";
import "progress.dart";

/// Bootstrap 5 色板与常用零件。图标用 Material 的系统符号，角色对齐 Bootstrap Icons。
class Bs {
  // 直接用 Bootstrap 5 的标准色板：蓝主行动、绿通过、红错误、黄注意、青信息，
  // 加上扩展色里的紫和青绿。明亮、通用、语义人人都认得。
  static const primary = Color(0xFF0D6EFD);
  static const secondary = Color(0xFF6C757D);
  static const success = Color(0xFF198754);
  static const danger = Color(0xFFDC3545);
  static const warning = Color(0xFFFFC107);
  static const info = Color(0xFF0DCAF0);
  static const purple = Color(0xFF6F42C1);
  static const teal = Color(0xFF20C997);
  static const orange = Color(0xFFFD7E14);
  static const pink = Color(0xFFD63384);
  static const light = Color(0xFFF8F9FA);
  static const dark = Color(0xFF212529);
  static const body = Color(0xFFFFFFFF);
  static const border = Color(0xFFDEE2E6);

  /// 侧栏：Bootstrap 里 navbar 配 bg-primary 的深一档，白字清晰。
  static const nav = Color(0xFF0A58CA);

  /// 品牌强调（题号、进度条、朗读条、选中态）——就是主色本身。
  static const paper = primary;

  /// 保留别名：老代码里的 accent 指紫色。
  static const accent = purple;

  static const radius = 4.0;
  static const bodySize = 20.0;

  /// 底色亮就用深字，底色暗就用白字——黄底白字看不清是最常见的翻车点。
  static Color onColor(Color background) {
    return background.computeLuminance() > 0.5 ? dark : Colors.white;
  }

  /// 题型各给一种颜色：判断青、单选蓝、多选紫，一眼分得出这题怎么答。
  static Color kindColor(String kind) {
    return switch (kind) {
      "judge" => teal,
      "multi" => purple,
      _ => primary,
    };
  }

  /// 高频红、常考黄、常规灰、偏难紫——按「要不要多练」排。
  static Color bandColor(String band) {
    return switch (band) {
      QuestionBandColors.hot => danger,
      QuestionBandColors.common => warning,
      QuestionBandColors.rare => purple,
      _ => secondary,
    };
  }

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
      "henan-road-safety" => "河南条例",
      "henan-expressway" => "河南高速条例",
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

/// 频次的取值——与 models 里的 QuestionBand 一致，放在这里是为了不让配色层依赖数据层。
class QuestionBandColors {
  static const hot = "hot";
  static const common = "common";
  static const regular = "regular";
  static const rare = "rare";
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

  /// 点开看细节：图里的红圈、远处的车灯，缩在栏里根本看不清。题库图片本身分辨率
  /// 普遍只有几百像素，跟内嵌显示的尺寸相差无几，只按原始像素放大等于没放大——
  /// 所以这里至少放大到 2 倍（屏幕装不下再等比缩小），不铺满整个窗口——铺满会把
  /// 长宽比不是屏幕比例的图硬撑出一圈黑边。
  void _open(BuildContext context) {
    showDialog<void>(
      context: context,
      // 不整屏遮暗——放大是看细节，不是切到另一个场景，身后的做题台应该
      // 还看得见。
      barrierColor: Colors.transparent,
      builder: (dialogContext) => Dialog(
        insetPadding: const EdgeInsets.all(32),
        backgroundColor: Colors.transparent,
        child: FutureBuilder<ui.Image>(
          future: _resolveImage(_provider),
          builder: (context, snapshot) {
            final natural = snapshot.data;
            final Widget picture;
            if (natural == null) {
              picture = const SizedBox(
                width: 240,
                height: 240,
                child: Center(child: CircularProgressIndicator(color: Colors.white)),
              );
            } else {
              final screen = MediaQuery.sizeOf(context);
              final scale = min(
                2.0,
                min(
                  (screen.width - 64) / natural.width,
                  (screen.height - 64) / natural.height,
                ),
              );
              picture = SizedBox(
                width: natural.width * scale,
                height: natural.height * scale,
                child: InteractiveViewer(
                  maxScale: 5,
                  child: Image(image: _provider, fit: BoxFit.contain),
                ),
              );
            }
            return Stack(
              alignment: Alignment.topRight,
              children: [
                picture,
                IconButton(
                  onPressed: () => Navigator.of(dialogContext).pop(),
                  icon: const Icon(Icons.close, color: Colors.white, size: 28),
                  tooltip: "关闭",
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Future<ui.Image> _resolveImage(ImageProvider provider) {
    final completer = Completer<ui.Image>();
    final stream = provider.resolve(const ImageConfiguration());
    late ImageStreamListener listener;
    listener = ImageStreamListener(
      (info, _) {
        completer.complete(info.image);
        stream.removeListener(listener);
      },
      onError: (error, stack) {
        completer.completeError(error, stack);
        stream.removeListener(listener);
      },
    );
    stream.addListener(listener);
    return completer.future;
  }
}

/// 题干里的否定词标红——"以下哪项是错误的""不得超车"这类反着问、反着答的
/// 题，漏看一个"不"字整题就反了，是最常见的翻车点。按长的词先匹配，
/// 免得「不可以」被短的「不可」抢先截半个词。
final _negationPattern = RegExp(
  "不正确|不属于|不包括|不允许|不可以|不需要|错误|不得|不能|不可|不用|不必|禁止|并非|没有|除外",
);

class PromptText extends StatelessWidget {
  const PromptText(this.text, {super.key, this.style, this.maxLines, this.overflow});

  final String text;
  final TextStyle? style;
  final int? maxLines;
  final TextOverflow? overflow;

  @override
  Widget build(BuildContext context) {
    final spans = <InlineSpan>[];
    var cursor = 0;
    for (final match in _negationPattern.allMatches(text)) {
      if (match.start > cursor) {
        spans.add(TextSpan(text: text.substring(cursor, match.start)));
      }
      spans.add(TextSpan(
        text: text.substring(match.start, match.end),
        style: const TextStyle(color: Bs.danger, fontWeight: FontWeight.w800),
      ));
      cursor = match.end;
    }
    if (cursor < text.length) {
      spans.add(TextSpan(text: text.substring(cursor)));
    }
    return Text.rich(
      TextSpan(style: style, children: spans),
      maxLines: maxLines,
      overflow: overflow ?? TextOverflow.clip,
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
    final fg = foreground ?? Bs.onColor(color);
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
          // 侧栏这类窄容器会把徽章压成 tight 约束——min 撑不开就得靠这个截断，
          // 不然内容一长（比如带阶段名）就在自己的 Row 里溢出。
          Flexible(
            child: Text(
              text,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(color: fg, fontSize: 16, fontWeight: FontWeight.w600),
            ),
          ),
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

/// 最近 N 天的练习量：柱子连不上就是断更了，颜色按当天正确率分（主仓库 ADR 0056）。
class DailyActivityChart extends StatelessWidget {
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
  Widget build(BuildContext context) {
    if (days.every((d) => d.attempts == 0)) {
      return Text(
        "最近还没有练习记录，练一组就会画出来。",
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Bs.secondary),
      );
    }
    return SizedBox(
      height: height,
      child: CustomPaint(
        painter: _DailyPainter(days),
        child: const SizedBox.expand(),
      ),
    );
  }
}

class _DailyPainter extends CustomPainter {
  _DailyPainter(this.days);

  final List<DailyCount> days;

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
      if (isToday || i == 0 || day.day.day == 1) {
        _text(canvas, Offset(center, chart.bottom + 2), "${day.day.month}/${day.day.day}", isToday ? Bs.dark : Bs.secondary, align: TextAlign.center);
      }
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
  bool shouldRepaint(covariant _DailyPainter oldDelegate) => true;
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
                      icon: const Icon(Icons.chevron_right, size: 20),
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
    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CustomPaint(
            size: Size(size, size),
            painter: _MasteryRingPainter(mastered: mastered, pending: pending, untouched: untouched),
          ),
          Text("$pct%", style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

class _MasteryRingPainter extends CustomPainter {
  _MasteryRingPainter({required this.mastered, required this.pending, required this.untouched});

  final int mastered;
  final int pending;
  final int untouched;

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
      final sweep = 2 * pi * count / total;
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
      oldDelegate.mastered != mastered || oldDelegate.pending != pending || oldDelegate.untouched != untouched;
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
        // 不写 min 的话 Row 会把统计块撑满整行，四个块各占一行，白占地方
        mainAxisSize: MainAxisSize.min,
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
