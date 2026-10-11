import "dart:async";
import "dart:io";
import "dart:math";
import "dart:ui" as ui;

import "package:flutter/material.dart";
import "package:flutter/services.dart";

import "glyphs.dart";
import "../core/content.dart";
import "semantic.dart";
import "skin.dart";
/// 语义色与皮肤令牌的门面。语义色（对错绿红、警示黄、题型青紫、频次档位）是
/// 全局常量，含义人人认得，不随皮肤变；氛围色（primary / nav / light / body /
/// border / paper）是 getter，指向当前皮肤（skin.dart，ADR 0058），换肤经
/// `MaterialApp` 整树重建后在这些 getter 上自然生效。图标用 Material 的系统
/// 符号。
class Bs {
  // —— 语义色：全局共享，含义不随皮肤变；色值由 Material 3 方案生成（semantic.dart，ADR 0071）——
  static Color get secondary => Sem.neutral.color;
  static Color get success => Sem.success.color;
  static Color get danger => Sem.danger.color;
  static Color get warning => Sem.warning.color;
  static Color get info => Sem.info.color;
  static Color get purple => Sem.purple.color;
  static Color get teal => Sem.teal.color;
  static Color get orange => Sem.orange.color;
  static Color get pink => Sem.pink.color;

  /// 深色文字与线条（图表字、次级文字、关闭图标）：名字沿用「墨色」，实际跟
  /// 主题的默认文字色（ADR 0081）——就是墨色。
  /// 给亮色块配深字用 [onColor]，它按底色亮度选固定的墨与白，不随皮肤。
  static Color get dark => Skins.current.scheme.onSurface;

  // —— 氛围色：跟随当前皮肤 ——
  static Color get primary => Skins.current.primary;

  /// 实心主色上的前景字（ADR 0081）：取自皮肤的 onPrimary，不写死白色。
  static Color get onPrimary => Skins.current.scheme.onPrimary;

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
  static Color get accent => purple;

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

  /// 底色亮就用固定的墨色深字，底色暗就用白字——黄底白字看不清是最常见的翻车点。
  /// 深字用 [Sem.ink] 而不是 [dark]：dark 跟主题文字色走，不是固定的墨色。
  static Color onColor(Color background) {
    return background.computeLuminance() > 0.5 ? Sem.ink : Colors.white;
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
    colorScheme: skin.scheme,
    useMaterial3: true,
    textTheme: Bs.textTheme(ThemeData(useMaterial3: true).textTheme),
    iconTheme: const IconThemeData(size: Bs.bodySize),
    visualDensity: VisualDensity.standard,
    splashFactory: NoSplash.splashFactory,
    scaffoldBackgroundColor: Colors.transparent,
    dividerColor: skin.border,
    hoverColor: skin.primary.withValues(alpha: 0.06),
    filledButtonTheme: FilledButtonThemeData(
      // 主按钮用主行动色，不再是一片深灰
      style: FilledButton.styleFrom(
        textStyle: const TextStyle(fontSize: Bs.bodySize, fontWeight: FontWeight.w600),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Bs.radius)),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        side: BorderSide(color: skin.border),
        textStyle: const TextStyle(fontSize: Bs.bodySize, fontWeight: FontWeight.w600),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Bs.radius)),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        textStyle: const TextStyle(fontSize: Bs.bodySize, fontWeight: FontWeight.w600),
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
    // 悬停提示（答题卡方格的题干摘要等）：反色面（inverseSurface）、控件级圆角。
    tooltipTheme: TooltipThemeData(
      decoration: BoxDecoration(
        color: skin.scheme.inverseSurface,
        borderRadius: BorderRadius.circular(Bs.radius),
      ),
      textStyle: TextStyle(color: skin.scheme.onInverseSurface, fontSize: 14, height: 1.4),
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
                  icon: Icon(Glyph.close, color: Bs.dark, size: 28),
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
        style: TextStyle(color: Bs.danger, fontWeight: FontWeight.w800),
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
  /// 默认是浅色调（tonal）徽章：底是 [color] 以低透明度铺在卡片底上，字与图标用 [color]
  /// 本身——Material 3 用状态层透明度做浅底的办法，色值随语义色走、对比度由实心色保证。
  final Color? color;

  /// 给了就是实心徽章：底是 [color]，字用这个色（放在深色底或需要强调的地方）。
  final Color? foreground;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final base = color ?? Bs.primary;
    final solid = foreground != null;
    final bg = solid ? base : Color.alphaBlend(base.withValues(alpha: 0.14), Bs.body);
    final fg = solid ? foreground! : base;
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
              Icon(Glyph.serial, size: 16, color: Bs.secondary),
              const SizedBox(width: 4),
              Text(serial, style: TextStyle(fontSize: 14, color: Bs.secondary, fontFamily: "monospace")),
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
    this.color,
    this.icon,
  });

  final Widget child;

  /// 缺省用信息色（默认参数必须是常量，语义色不再是常量，只能在这里回退）。
  final Color? color;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final color = this.color ?? Bs.info;
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

/// 整窗环境背景：页面色打底，再铺三团大半径柔色斑（ADR 0058 决策 4）。
/// 内容静态，RepaintBoundary 一次成层、之后每帧零成本，窗口尺寸变化才重画；
/// 不用系统窗口材质、不引原生插件——那是长期税（决策 4）。
class AmbientBackdrop extends StatelessWidget {
  const AmbientBackdrop({super.key, this.skin});

  /// 皮肤从 builder 传进来（main.dart 的 notifier 回调），不靠组件自己读全局
  /// 单例：const 实例在换肤时会被 Element 当 identical 跳过，色斑停在启动那套。
  final Skin? skin;

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: CustomPaint(
        painter: _AmbientPainter(skin ?? Skins.current),
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
              // 玻璃底取皮肤的 surfaceContainerLow（ADR 0081），不写死白色半透明。
              color: color ??
                  Skins.current.scheme.surfaceContainerLow.withValues(alpha: 0.62),
              border: Border.all(
                color: Skins.current.scheme.outlineVariant.withValues(alpha: 0.55),
              ),
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
