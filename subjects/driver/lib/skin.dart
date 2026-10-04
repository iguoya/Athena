import "dart:convert";
import "dart:io";

import "package:flutter/material.dart";
import "package:path/path.dart" as p;

import "progress.dart";

/// 皮肤：与拾阶（ascent）、math-tools 的 skins 同构——一套组件，令牌换氛围
/// （本应用 ADR 0058）。每套皮肤只存一个种子色，全部色彩角色由 Material 3 的
/// [ColorScheme.fromSeed] 生成（ADR 0071），不手写十六进制补色。语义色（对错、
/// 警示、题型、频次）不在这里：那些含义人人认得，不随皮肤变。四套都是明色，
/// 不做暗色。
class Skin {
  Skin({
    required this.id,
    required this.name,
    required this.hint,
    required this.seed,
  }) : scheme = ColorScheme.fromSeed(
          seedColor: seed,
          // fidelity：色板贴着种子色走，primaryContainer 就是种子色本身，四套皮肤
          // 才认得出（默认的 tonalSpot 会把蓝压成灰蓝、橙压成棕）。
          dynamicSchemeVariant: DynamicSchemeVariant.fidelity,
        );

  final String id;

  /// 皮肤名与一句话简述，切换器的气泡里显示。
  final String name;
  final String hint;

  /// 种子色：整套 [scheme] 由它生成。
  final Color seed;

  /// Material 3 色彩方案（明色）。组件主题与下面的 getter 都读它。
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
  /// 与徽章的浅色调同一做法；`secondaryContainer` 在 fidelity 方案里偏艳（曙途像一条橙色药丸）。
  Color get navSelected => Color.alphaBlend(scheme.primary.withValues(alpha: 0.14), nav);

  /// 页面底色（旧 Bs.light 的语义）。
  Color get page => scheme.surface;

  /// 卡片底色（旧 Bs.body 的语义）。
  Color get card => scheme.surfaceContainerLowest;

  /// hairline 与分隔线（旧 Bs.border 的语义）。
  Color get border => scheme.outlineVariant;

  /// 环境色斑：两三团大半径柔和色垫在整窗底下，玻璃感来自「面板半透明 +
  /// 背后有色可透」，不是来自系统模糊（ADR 0058：不引窗口材质）。
  List<Color> get ambient => [scheme.primaryContainer, scheme.primaryFixedDim, scheme.secondaryContainer];
}

final _skins = <Skin>[
  Skin(id: "sky", name: "晴空", hint: "蓝白 · 继承旧观感", seed: const Color(0xFF0D6EFD)),
  Skin(id: "meadow", name: "青野", hint: "绿意 · 平和护眼", seed: const Color(0xFF0C8F63)),
  Skin(id: "sunrise", name: "曙途", hint: "暖橙 · 清晨上路", seed: const Color(0xFFE8590C)),
  Skin(id: "violet", name: "暮汐", hint: "暮紫 · 安静夜学", seed: const Color(0xFF7048E8)),
];

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
