import "dart:convert";
import "dart:io";

import "package:flutter/material.dart";
import "package:path/path.dart" as p;

import "progress.dart";

/// 皮肤：与拾阶（ascent）、math-tools 的 skins 同构——一套组件，令牌换氛围
/// （本应用 ADR 0058）。语义色（对错、警示、题型、频次）不在这里：那些含义人人
/// 认得，不随皮肤变；皮肤只管氛围——主行动色、侧栏、页面底、卡片底、hairline
/// 和环境色斑。四套都是明色，不做暗色。
class Skin {
  const Skin({
    required this.id,
    required this.name,
    required this.hint,
    required this.primary,
    required this.nav,
    required this.page,
    required this.card,
    required this.border,
    required this.ambient,
  });

  final String id;

  /// 皮肤名与一句话简述，切换器的气泡里显示。
  final String name;
  final String hint;

  /// 主行动色：按钮、选中态、题号、进度条。
  final Color primary;

  /// 侧栏底色。渲染时叠一层透明度透出环境色斑。
  final Color nav;

  /// 页面底色（旧 Bs.light 的语义）。
  final Color page;

  /// 卡片底色（旧 Bs.body 的语义）。
  final Color card;

  /// hairline 与分隔线（旧 Bs.border 的语义）。
  final Color border;

  /// 环境色斑：两三团大半径柔和色垫在整窗底下，玻璃感来自「面板半透明 +
  /// 背后有色可透」，不是来自系统模糊（ADR 0058：不引窗口材质）。
  final List<Color> ambient;
}

const _skins = <Skin>[
  Skin(
    id: "sky",
    name: "晴空",
    hint: "蓝白 · 继承旧观感",
    primary: Color(0xFF0D6EFD),
    nav: Color(0xFF0A58CA),
    page: Color(0xFFF4F7FB),
    card: Color(0xFFFFFFFF),
    border: Color(0xFFE3E8EF),
    ambient: [Color(0xFF4D9FFF), Color(0xFF22C3D6), Color(0xFF8FB7FF)],
  ),
  Skin(
    id: "meadow",
    name: "青野",
    hint: "绿意 · 平和护眼",
    primary: Color(0xFF0C8F63),
    nav: Color(0xFF0B6B4A),
    page: Color(0xFFF4FAF6),
    card: Color(0xFFFFFFFF),
    border: Color(0xFFDDEBE2),
    ambient: [Color(0xFF34D399), Color(0xFFA3E635), Color(0xFF5EEAD4)],
  ),
  Skin(
    id: "sunrise",
    name: "曙途",
    hint: "暖橙 · 清晨上路",
    primary: Color(0xFFE8590C),
    nav: Color(0xFF9A3E0E),
    page: Color(0xFFFBF6F0),
    card: Color(0xFFFFFFFF),
    border: Color(0xFFF0E2D6),
    ambient: [Color(0xFFFFB454), Color(0xFFFF8787), Color(0xFFFFD3A5)],
  ),
  Skin(
    id: "violet",
    name: "暮汐",
    hint: "暮紫 · 安静夜学",
    primary: Color(0xFF7048E8),
    nav: Color(0xFF4C33B8),
    page: Color(0xFFF7F6FC),
    card: Color(0xFFFFFFFF),
    border: Color(0xFFE6E2F4),
    ambient: [Color(0xFFA78BFA), Color(0xFF7DD3FC), Color(0xFFC4B5FD)],
  ),
];

/// 皮肤清单与当前皮肤。切换经 [notifier] 通知 `MaterialApp` 换 theme 整树重建，
/// `Bs` 的 getter 读 [current] 拿到新值（ADR 0058）。
class Skins {
  Skins._();

  static const all = _skins;

  /// 清单第一套（晴空）：没存过口味、skin.json 坏了、或 id 不在清单里时用它。
  static Skin get fallback => all.first;

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
