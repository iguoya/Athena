import "dart:convert";
import "dart:io";

import "package:flutter/material.dart";
import "package:path/path.dart" as p;

import "progress.dart";

/// 皮肤：与拾阶（ascent）、math-tools 的 skins 同构——一套组件，令牌换氛围
/// （本应用 ADR 0058）。每套皮肤手写一份完整的 [ColorScheme]：主色、surface 各档、
/// outline 系、inverse 面逐角色选定，三套之间的差异是整套色板的差异，不是一枚
/// 种子色被方案规律拉平后的零星点缀（ADR 0081 修订 0071 决策 1）。语义色（对错、
/// 警示、题型、频次）不在这里：那些含义人人认得，不随皮肤变。三套都是明色、各自
/// 带色温；深紫的「暮汐」因为太黑、文字看不清已去掉（ADR 0110）。
class Skin {
  Skin({
    required this.id,
    required this.name,
    required this.hint,
    required this.scheme,
    required this.ambient,
  });

  final String id;

  /// 皮肤名与一句话简述，切换器的气泡里显示。
  final String name;
  final String hint;

  /// 整套色彩方案：组件主题与下面的 getter 都读它。
  final ColorScheme scheme;

  /// 主行动色：按钮、选中态、题号、进度条。
  Color get primary => scheme.primary;

  /// 侧栏底色（Material 3 导航抽屉的 surfaceContainerLow）。渲染时叠一层透明度透出环境色斑。
  Color get nav => scheme.surfaceContainerLow;

  /// 侧栏文字与图标：默认 onSurfaceVariant，选中行用主色，禁用 38% 透明度
  /// （Material 3 的禁用态约定）。
  Color get navText => scheme.onSurfaceVariant;
  Color get navTextSelected => scheme.primary;
  Color get navTextMuted => scheme.onSurface.withValues(alpha: 0.38);

  /// 侧栏选中行的底（导航抽屉的 active indicator）：主色以低透明度铺在侧栏底上，
  /// 与徽章的浅色调同一做法；`secondaryContainer` 在手写色板里也压不住高饱和主色
  /// （曙途会像一条橙色药丸），维持 0071 阶段 3 的选择。
  Color get navSelected => Color.alphaBlend(scheme.primary.withValues(alpha: 0.14), nav);

  /// 页面底色（旧 Bs.light 的语义）。
  Color get page => scheme.surface;

  /// 卡片底色（旧 Bs.body 的语义）。
  Color get card => scheme.surfaceContainerLowest;

  /// hairline 与分隔线（旧 Bs.border 的语义）。
  Color get border => scheme.outlineVariant;

  /// 环境色斑：两三团大半径柔和色垫在整窗底下，玻璃感来自「面板半透明 +
  /// 背后有色可透」，不是来自系统模糊（ADR 0058：不引窗口材质）。逐套手选：
  /// 各套皮肤给各自色温的天光。
  final List<Color> ambient;
}

Skin _sky() => Skin(
  id: "sky",
  name: "晴空",
  hint: "冷蓝 · 继承旧观感",
  scheme: const ColorScheme.light(
    primary: Color(0xFF0D5CC0),
    onPrimary: Colors.white,
    primaryContainer: Color(0xFFD3E2FA),
    onPrimaryContainer: Color(0xFF0A3B8F),
    primaryFixedDim: Color(0xFF9DC1F0),
    secondary: Color(0xFF3D6489),
    onSecondary: Colors.white,
    secondaryContainer: Color(0xFFD9E7F9),
    onSecondaryContainer: Color(0xFF173A5E),
    tertiary: Color(0xFF4B5F9E),
    onTertiary: Colors.white,
    tertiaryContainer: Color(0xFFE0E6FF),
    onTertiaryContainer: Color(0xFF1B2D66),
    error: Color(0xFFB3261E),
    onError: Colors.white,
    errorContainer: Color(0xFFF9DEDC),
    onErrorContainer: Color(0xFF410E0B),
    surface: Color(0xFFF2F6FB),
    onSurface: Color(0xFF18242F),
    surfaceDim: Color(0xFFD8DFE8),
    surfaceBright: Color(0xFFF9FBFE),
    surfaceContainerLowest: Colors.white,
    surfaceContainerLow: Color(0xFFE8F0F9),
    surfaceContainer: Color(0xFFDFE9F4),
    surfaceContainerHigh: Color(0xFFD6E2EF),
    surfaceContainerHighest: Color(0xFFCDDAE9),
    surfaceTint: Color(0xFF0D5CC0),
    outline: Color(0xFF77879A),
    outlineVariant: Color(0xFFC8D6E6),
    inverseSurface: Color(0xFF2C3946),
    onInverseSurface: Color(0xFFEEF2F7),
    inversePrimary: Color(0xFFA6C8F8),
  ),
  ambient: const [Color(0xFFC2D8F2), Color(0xFF9CBCE8), Color(0xFFDCE8F8)],
);

Skin _meadow() => Skin(
  id: "meadow",
  name: "青野",
  hint: "米绿 · 纸感护眼",
  scheme: const ColorScheme.light(
    primary: Color(0xFF177A53),
    onPrimary: Colors.white,
    primaryContainer: Color(0xFFC8EBD5),
    onPrimaryContainer: Color(0xFF0A4A30),
    primaryFixedDim: Color(0xFF9ED4B2),
    secondary: Color(0xFF4F6A57),
    onSecondary: Colors.white,
    secondaryContainer: Color(0xFFD8EAD9),
    onSecondaryContainer: Color(0xFF1B3625),
    tertiary: Color(0xFF7A6430),
    onTertiary: Colors.white,
    tertiaryContainer: Color(0xFFF1E4C3),
    onTertiaryContainer: Color(0xFF3F3212),
    error: Color(0xFFB3261E),
    onError: Colors.white,
    errorContainer: Color(0xFFF9DEDC),
    onErrorContainer: Color(0xFF410E0B),
    surface: Color(0xFFF1F5EA),
    onSurface: Color(0xFF1E281C),
    surfaceDim: Color(0xFFD7DECB),
    surfaceBright: Color(0xFFF8FCF1),
    surfaceContainerLowest: Color(0xFFFDFEF8),
    surfaceContainerLow: Color(0xFFE3EDD8),
    surfaceContainer: Color(0xFFDAE6CC),
    surfaceContainerHigh: Color(0xFFD1DFC1),
    surfaceContainerHighest: Color(0xFFC9D7B7),
    surfaceTint: Color(0xFF177A53),
    outline: Color(0xFF78896E),
    outlineVariant: Color(0xFFC5D6B7),
    inverseSurface: Color(0xFF2C3629),
    onInverseSurface: Color(0xFFEDF3E7),
    inversePrimary: Color(0xFF93D2AE),
  ),
  ambient: const [Color(0xFFBEDCB4), Color(0xFFA3CCA5), Color(0xFFDCEBC4)],
);

Skin _sunrise() => Skin(
  id: "sunrise",
  name: "曙途",
  hint: "暖橙 · 清晨上路",
  scheme: const ColorScheme.light(
    primary: Color(0xFFB84A00),
    onPrimary: Colors.white,
    primaryContainer: Color(0xFFFFD9BE),
    onPrimaryContainer: Color(0xFF6B2A00),
    primaryFixedDim: Color(0xFFF3B285),
    secondary: Color(0xFF7A563C),
    onSecondary: Colors.white,
    secondaryContainer: Color(0xFFFBDEBB),
    onSecondaryContainer: Color(0xFF5F421F),
    tertiary: Color(0xFF856C2F),
    onTertiary: Colors.white,
    tertiaryContainer: Color(0xFFF7E3B0),
    onTertiaryContainer: Color(0xFF4A3A0E),
    error: Color(0xFFB3261E),
    onError: Colors.white,
    errorContainer: Color(0xFFF9DEDC),
    onErrorContainer: Color(0xFF410E0B),
    surface: Color(0xFFFAF2E7),
    onSurface: Color(0xFF2A2118),
    surfaceDim: Color(0xFFE2D8C8),
    surfaceBright: Color(0xFFFEF9F0),
    surfaceContainerLowest: Color(0xFFFFFEFA),
    surfaceContainerLow: Color(0xFFF4E8D6),
    surfaceContainer: Color(0xFFEFE1CC),
    surfaceContainerHigh: Color(0xFFE9D9C2),
    surfaceContainerHighest: Color(0xFFE3D2B8),
    surfaceTint: Color(0xFFB84A00),
    outline: Color(0xFF96846C),
    outlineVariant: Color(0xFFE0CFB6),
    inverseSurface: Color(0xFF362C21),
    onInverseSurface: Color(0xFFF6EFE5),
    inversePrimary: Color(0xFFFFB878),
  ),
  ambient: const [Color(0xFFF6D5A8), Color(0xFFEFB987), Color(0xFFFAE6CB)],
);

final _skins = <Skin>[_sky(), _meadow(), _sunrise()];

/// 皮肤清单与当前皮肤。切换经 [notifier] 通知 `MaterialApp` 换 theme 整树重建，
/// `Bs` 的 getter 读 [current] 拿到新值（ADR 0058）。
class Skins {
  Skins._();

  static final all = _skins;

  /// 默认皮肤（青野，ADR 0063 修订 0058 决策 1 的默认指定）：没存过口味、
  /// skin.json 坏了、或 id 不在清单里时用它。清单顺序不变，晴空仍是第一套。
  static Skin get fallback => byId("meadow");

  static Skin byId(String id) =>
      all.where((s) => s.id == id).firstOrNull ?? fallback;

  /// 当前皮肤。启动时 [load] 一次；切换走 [SkinStore.set]。
  static Skin get current => SkinStore.notifier.value;
}

/// 皮肤选择的持久化：机器级 `skin.json`（用户数据目录，模式同 `api.json`），
/// 不按学习者分——一台机器一个口味（ADR 0058 决策 7）。
class SkinStore {
  SkinStore._();

  static final ValueNotifier<Skin> notifier = ValueNotifier(_load());

  static String get _file => p.join(ProgressStore.userDataDir(), "skin.json");

  static Skin _load() {
    try {
      final map =
          jsonDecode(File(_file).readAsStringSync()) as Map<String, dynamic>;
      final id = map["id"];
      return id is String ? Skins.byId(id) : Skins.fallback;
    } catch (_) {
      // 没有 skin.json 或内容坏了：回到默认皮肤。清单里没有的旧 id 同样回退。
      return Skins.fallback;
    }
  }

  static void set(Skin skin) {
    notifier.value = skin;
    try {
      File(_file).writeAsStringSync(jsonEncode({"id": skin.id}));
    } catch (_) {
      // 写不进去只是记不住口味，不值得拦着换肤。
    }
  }
}
