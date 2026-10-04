import "dart:async";
import "dart:io";
import "dart:math";
import "dart:ui" as ui;

import "package:flutter/material.dart";
import "package:flutter/services.dart";

import "glyphs.dart";
import "content.dart";
import "progress.dart";
import "skin.dart";

/// 语义色与皮肤令牌的门面。语义色（对错绿红、警示黄、题型青紫、频次档位）是
/// 全局常量，含义人人认得，不随皮肤变；氛围色（primary / nav / light / body /
/// border / paper）是 getter，指向当前皮肤（skin.dart，ADR 0058），换肤经
/// `MaterialApp` 整树重建后在这些 getter 上自然生效。图标用 Material 的系统
/// 符号，角色对齐 Bootstrap Icons。
class Bs {
  // —— 语义色：全局共享的常量（Bootstrap 5 原板）——
  static const secondary = Color(0xFF6C757D);
  static const success = Color(0xFF198754);
  static const danger = Color(0xFFDC3545);
  static const warning = Color(0xFFFFC107);
  static const info = Color(0xFF0DCAF0);
  static const purple = Color(0xFF6F42C1);
  static const teal = Color(0xFF20C997);
  static const orange = Color(0xFFFD7E14);
  static const pink = Color(0xFFD63384);
  static const dark = Color(0xFF212529);

  // —— 氛围色：跟随当前皮肤 ——
  static Color get primary => Skins.current.primary;

  /// 品牌强调（题号、进度条、朗读条、选中态）——就是主色本身。
  static Color get paper => primary;

  /// 侧栏底色。
  static Color get nav => Skins.current.nav;

  /// 页面底色（旧 Bs.light 的语义）。
  static Color get light => Skins.current.page;

  /// 卡片底色（旧 Bs.body 的语义）。
  static Color get body => Skins.current.card;

  /// hairline 与分隔线。
  static Color get border => Skins.current.border;

  /// 保留别名：老代码里的 accent 指紫色。
  static const accent = purple;

  /// 圆角分级（ADR 0058 决策 5）：控件、卡片、徽章胶囊。
  static const radius = 10.0;
  static const radiusCard = 16.0;
  static const radiusPill = 999.0;

  /// 动效时长令牌（ADR 0058 决策 6）：常规反馈与入场。新代码用令牌，不自己调参。
  static const durFast = Duration(milliseconds: 200);
  static const durIn = Duration(milliseconds: 300);

  /// 卡片双层软阴影：一层贴地定位置，一层大而淡铺氛围；hover 加深一档。
  static const cardShadow = [
    BoxShadow(color: Color(0x0F101828), blurRadius: 10, offset: Offset(0, 2)),
    BoxShadow(color: Color(0x0A101828), blurRadius: 24, offset: Offset(0, 8)),
  ];
  static const hoverShadow = [
    BoxShadow(color: Color(0x1A101828), blurRadius: 14, offset: Offset(0, 4)),
    BoxShadow(color: Color(0x12101828), blurRadius: 32, offset: Offset(0, 12)),
  ];

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
        // 等宽数字全局生效：统计大数、进度、计时刷新时宽度不抖（原来只有两处手写，
        // 大数与漏斗一直漏；在主题层一处生效全库）。
        fontFeatures: const [FontFeature.tabularFigures()],
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
      "criminal-law-full" => "刑法",
      "traffic-crime-interpretation" => "交通肇事司法解释",
      "spc-exam-cheating-cases-2024" => "最高法典型案例",
      "inspection-reform-2022" => "检验改革意见",
      "gb-4094" => "GB 4094 仪表符号",
      "gbt-39263" => "GB/T 39263 辅助驾驶",
      "gb-19522" => "GB 19522 酒精",
      "ga-1026" => "GA 1026",
      "exam-syllabus-2022" => "考试大纲",
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
      "judge" => Glyph.kindJudge,
      "multi" => Glyph.kindMulti,
      _ => Glyph.kindSingle,
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

/// 组装应用主题：皮肤只换氛围色，字号、密度、组件形状全局一致（ADR 0058）。
/// 页面自身全透明——环境背景由 `MaterialApp.builder` 里的 [AmbientBackdrop] 垫。
ThemeData buildTheme(Skin skin) {
  return ThemeData(
    colorScheme: ColorScheme.light(
      primary: skin.primary,
      secondary: skin.primary,
      error: Bs.danger,
      surface: skin.card,
    ),
    useMaterial3: true,
    textTheme: Bs.textTheme(ThemeData(useMaterial3: true).textTheme),
    iconTheme: IconThemeData(size: Bs.bodySize),
    visualDensity: VisualDensity.standard,
    splashFactory: NoSplash.splashFactory,
    scaffoldBackgroundColor: Colors.transparent,
    dividerColor: skin.border,
    hoverColor: skin.primary.withValues(alpha: 0.06),
    filledButtonTheme: FilledButtonThemeData(
      // 主按钮用主行动色，不再是一片深灰
      style: FilledButton.styleFrom(
        backgroundColor: skin.primary,
        foregroundColor: Colors.white,
        textStyle: TextStyle(fontSize: Bs.bodySize, fontWeight: FontWeight.w600),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Bs.radius)),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: skin.primary,
        side: BorderSide(color: skin.border),
        textStyle: TextStyle(fontSize: Bs.bodySize, fontWeight: FontWeight.w600),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Bs.radius)),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: skin.primary,
        textStyle: TextStyle(fontSize: Bs.bodySize, fontWeight: FontWeight.w600),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: skin.card,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Bs.radiusCard)),
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Bs.radius)),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(Bs.radius)),
    ),
    // 悬停提示（答题卡方格的题干摘要等）：深底白字、控件级圆角。
    tooltipTheme: TooltipThemeData(
      decoration: BoxDecoration(
        color: Bs.dark,
        borderRadius: BorderRadius.circular(Bs.radius),
      ),
      textStyle: const TextStyle(color: Colors.white, fontSize: 14, height: 1.4),
      waitDuration: const Duration(milliseconds: 350),
    ),
    // 桌面长列表的滚动条：圆角拇指、随皮肤走；桌面平台默认就会给 ScrollView 包
    // Scrollbar，这里只定样式（错题本、题库这类长列表之前没有任何滚动指示）。
    scrollbarTheme: ScrollbarThemeData(
      thumbColor: WidgetStatePropertyAll(skin.primary.withValues(alpha: 0.35)),
      thickness: const WidgetStatePropertyAll(6),
      radius: const Radius.circular(999),
      minThumbLength: 48,
      crossAxisMargin: 2,
      mainAxisMargin: 4,
    ),
  );
}

/// 频次的取值——与 models 里的 QuestionBand 一致，放在这里是为了不让配色层依赖数据层。
class QuestionBandColors {
  static const hot = "hot";
  static const common = "common";
  static const regular = "regular";
  static const rare = "rare";
}

/// 应用标志：跟启动器图块、任务栏同一份图（仓库 ADR 0065、本应用 ADR 0048），不另画。
class AppMark extends StatelessWidget {
  const AppMark({super.key, this.size = 30});

  final double size;

  @override
  Widget build(BuildContext context) {
    final path = ContentLoader.appIconPath;
    return Image(
      image: ContentLoader.imagesOnDisk ? FileImage(File(path)) : AssetImage(path),
      width: size,
      height: size,
      filterQuality: FilterQuality.medium,
      // 图标文件缺了也不该让侧栏报错，留出同样大小的空位。
      errorBuilder: (_, _, _) => SizedBox.square(dimension: size),
    );
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
                // 玻璃托盘：半透明白底 + 高光描边，题图带透明通道时底下不再是应用底色。
                GlassPanel(padding: const EdgeInsets.all(10), child: picture),
                IconButton(
                  onPressed: () => Navigator.of(dialogContext).pop(),
                  icon: const Icon(Glyph.close, color: Bs.dark, size: 28),
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
    this.color,
    this.foreground,
    this.icon,
  });

  final String text;

  /// 缺省用当前皮肤的主行动色（默认参数必须是常量，皮肤色只能在这里回退）。
  final Color? color;
  final Color? foreground;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final bg = color ?? Bs.primary;
    final fg = foreground ?? Bs.onColor(bg);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(Bs.radiusPill),
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

/// 题目的稳定编号（[Question.serial]）：点一下复制，反馈题目问题时报这个号。
class SerialBadge extends StatelessWidget {
  const SerialBadge(this.serial, {super.key});

  final String serial;

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: "题目编号，点一下复制",
      child: InkWell(
        borderRadius: BorderRadius.circular(Bs.radius),
        onTap: () async {
          await Clipboard.setData(ClipboardData(text: serial));
          if (!context.mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("已复制题目编号 $serial"), duration: const Duration(seconds: 2)),
          );
        },
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            border: Border.all(color: Bs.border),
            borderRadius: BorderRadius.circular(Bs.radiusPill),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Glyph.serial, size: 16, color: Bs.secondary),
              const SizedBox(width: 4),
              Text(serial, style: const TextStyle(fontSize: 14, color: Bs.secondary, fontFamily: "monospace")),
            ],
          ),
        ),
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
  const BsProgress({super.key, required this.value, this.color});

  final double value;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(Bs.radius),
      child: BsTweenFraction(
        end: value,
        builder: (context, v) => LinearProgressIndicator(
          value: v,
          minHeight: 10,
          color: color ?? Bs.primary,
          backgroundColor: Bs.border,
        ),
      ),
    );
  }
}

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
              Text(label, style: const TextStyle(color: Bs.secondary, fontSize: 16)),
              Text(value, style: TextStyle(fontWeight: FontWeight.w700, fontSize: Bs.bodySize)),
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

/// 整窗环境背景：页面色打底，再铺三团大半径柔色斑（ADR 0058 决策 4）。
/// 内容静态，RepaintBoundary 一次成层、之后每帧零成本，窗口尺寸变化才重画；
/// 不用系统窗口材质、不引原生插件——那是长期税（决策 4）。
class AmbientBackdrop extends StatelessWidget {
  const AmbientBackdrop({super.key});

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: CustomPaint(
        painter: _AmbientPainter(Skins.current),
        child: const SizedBox.expand(),
      ),
    );
  }
}

class _AmbientPainter extends CustomPainter {
  _AmbientPainter(this.skin);

  final Skin skin;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawRect(Offset.zero & size, Paint()..color = skin.page);
    // 左上一大团、右中一团、左下沿一团：按比例摆放，什么窗口形状都铺得匀。
    final spots = [
      (Offset(size.width * 0.10, size.height * 0.02), size.width * 0.50, skin.ambient[0], 0.38),
      (Offset(size.width * 0.98, size.height * 0.36), size.width * 0.42, skin.ambient[1], 0.30),
      (Offset(size.width * 0.28, size.height * 1.05), size.width * 0.55, skin.ambient[2], 0.28),
    ];
    for (final (center, radius, color, alpha) in spots) {
      final paint = Paint()
        ..color = color.withValues(alpha: alpha)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 90);
      canvas.drawCircle(center, radius, paint);
    }
  }

  @override
  bool shouldRepaint(_AmbientPainter oldDelegate) => oldDelegate.skin.id != skin.id;
}

/// 阶 3 浮层的玻璃面板：背景模糊 + 半透明托底 + hairline 高光描边，阴影画在
/// clip 外层不被裁掉。只给小面积浮层用（大图预览这类），不给整窗（ADR 0058
/// 决策 4 的性能边界：BackdropFilter 是 saveLayer）。
class GlassPanel extends StatelessWidget {
  const GlassPanel({
    super.key,
    required this.child,
    this.radius = Bs.radiusCard,
    this.blur = 18,
    this.padding,
    this.color,
  });

  final Widget child;
  final double radius;
  final double blur;
  final EdgeInsetsGeometry? padding;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        boxShadow: Bs.cardShadow,
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(radius),
        child: BackdropFilter(
          filter: ui.ImageFilter.blur(sigmaX: blur, sigmaY: blur),
          child: Container(
            padding: padding,
            decoration: BoxDecoration(
              color: color ?? Colors.white.withValues(alpha: 0.62),
              border: Border.all(color: Colors.white.withValues(alpha: 0.55)),
            ),
            child: child,
          ),
        ),
      ),
    );
  }
}

/// 白卡片：card 底、卡片级圆角、双层软阴影替代 1px 描边的「表格感」；桌面鼠标
/// 悬停轻微上浮。首页概览先行收编，其余页的描边卡片后续顺手换（ADR 0058 决策 5）。
class BsCard extends StatefulWidget {
  const BsCard({
    super.key,
    required this.child,
    this.margin,
    this.padding = const EdgeInsets.fromLTRB(16, 14, 16, 12),
    this.onTap,
  });

  final Widget child;
  final EdgeInsetsGeometry? margin;
  final EdgeInsetsGeometry padding;
  final VoidCallback? onTap;

  @override
  State<BsCard> createState() => _BsCardState();
}

class _BsCardState extends State<BsCard> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      cursor: widget.onTap != null ? SystemMouseCursors.click : MouseCursor.defer,
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: AnimatedContainer(
        duration: Bs.durFast,
        curve: Curves.easeOut,
        margin: widget.margin,
        transform: Matrix4.translationValues(0, _hover ? -2 : 0, 0),
        padding: widget.padding,
        decoration: BoxDecoration(
          color: Bs.body,
          borderRadius: BorderRadius.circular(Bs.radiusCard),
          boxShadow: _hover ? Bs.hoverShadow : Bs.cardShadow,
        ),
        child: widget.child,
      ),
    );
  }
}

/// 概览卡片入场：按序延迟 45ms 淡入加轻微上滑，一列卡片「拾阶而上」。
/// 延迟用可取消的 Timer：页面在延迟到期前被销毁（测试树拆掉、快速切换）时
/// 取消掉，不给 flutter_test 留 pending timer。
class StaggerIn extends StatefulWidget {
  const StaggerIn({super.key, required this.index, required this.child});

  final int index;
  final Widget child;

  @override
  State<StaggerIn> createState() => _StaggerInState();
}

class _StaggerInState extends State<StaggerIn> with SingleTickerProviderStateMixin {
  late final AnimationController _controller =
      AnimationController(vsync: this, duration: Bs.durIn);
  late final Animation<double> _anim =
      CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic);
  Timer? _delay;

  @override
  void initState() {
    super.initState();
    _delay = Timer(Duration(milliseconds: 45 * widget.index), () {
      if (mounted) _controller.forward();
    });
  }

  @override
  void dispose() {
    _delay?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _anim,
      child: SlideTransition(
        position: Tween(begin: const Offset(0, 0.04), end: Offset.zero).animate(_anim),
        child: widget.child,
      ),
    );
  }
}

/// 换页淡入（ADR 0060）：[pageKey] 变化时新内容从 0 淡到 1。只淡入、不交叉溶解——
/// 页面底是同一层环境色斑，淡入即够；交叉溶解会让新旧两棵页面树并存一个时长，
/// 测试的唯一性断言和内存都跟着变贵。旧页立即卸载，测试照常查唯一性。
class PageFadeIn extends StatefulWidget {
  const PageFadeIn({super.key, required this.pageKey, required this.child});

  final Object pageKey;
  final Widget child;

  @override
  State<PageFadeIn> createState() => _PageFadeInState();
}

class _PageFadeInState extends State<PageFadeIn> with SingleTickerProviderStateMixin {
  late final AnimationController _controller =
      AnimationController(vsync: this, duration: Bs.durIn)..forward();
  late Object _key = widget.pageKey;

  @override
  void didUpdateWidget(PageFadeIn oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.pageKey != widget.pageKey) {
      _key = widget.pageKey;
      _controller.forward(from: 0);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: CurvedAnimation(parent: _controller, curve: Curves.easeOut),
      child: KeyedSubtree(key: ValueKey(_key), child: widget.child),
    );
  }
}

/// 数值滑入（ADR 0060）：占比从 0 长到目标值（进页面一次），目标值变化时从旧值
/// 滑到新值。进度条、环、漏斗这类占比图形共用；数字本身不跳、不循环。
class BsTweenFraction extends StatelessWidget {
  const BsTweenFraction({super.key, required this.end, required this.builder});

  final double end;
  final Widget Function(BuildContext context, double value) builder;

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: end.clamp(0, 1)),
      duration: Bs.durIn,
      curve: Curves.easeOutCubic,
      builder: (context, v, _) => builder(context, v),
    );
  }
}
