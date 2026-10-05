import "dart:convert";
import "dart:io";

import "package:path/path.dart" as p;

import "progress.dart";

/// 自测的「认得了没有」记录（ADR 0082）：让自测只考没认得的，不反复考已经会的。
///
/// **它不是掌握度。** 掌握度只由作答对错写入（ADR 0020、主仓库 0052），这里的记录只
/// 决定一张速记卡「还出不出」：不进作答记录、不进统计与激励、不参与过关判断，也不同步——
/// 换一台机器就是重新自测一遍，代价很小，换来的是不必为它改中心库的表结构。
///
/// 每位学习者一份文件 `selftest-<学习者>.json`（用户数据目录）；[user] 为空就只存内存
/// （测试与没登录的场景），关掉即消失。条目键由页面给出（页面键 + 条目键）。
class SelfTestStore {
  SelfTestStore({String? user, String? directory})
    : _file = user == null
          ? null
          : p.join(directory ?? ProgressStore.userDataDir(), "selftest-${_safe(user)}.json") {
    _load();
  }

  /// 一轮里「第一次问就记住」达到几次算认得。1：使用者要的是「认知正确的不再测试」；
  /// 没记住后重现才记住的不算（那是被提醒出来的，不是自己想起来的）。
  static const knownAfterClean = 1;

  final String? _file;

  /// 页面键 → 条目键 → 记录 `{c: 连续一次就记住的次数, m: 没记住的次数}`。
  final Map<String, Map<String, Map<String, int>>> _pages = {};

  static String _safe(String user) => user.replaceAll(RegExp(r'[/\\:*?"<>|]'), "_");

  Map<String, int>? _entry(String page, String id) => _pages[page]?[id];

  /// 这条已经认得，自测不再出。
  bool isKnown(String page, String id) => (_entry(page, id)?["c"] ?? 0) >= knownAfterClean;

  /// 这条考过且没记住过（还没认得）：自测优先再考。
  bool isLearning(String page, String id) {
    final e = _entry(page, id);
    return e != null && !isKnown(page, id) && (e["m"] ?? 0) > 0;
  }

  /// [ids] 里已经认得的条数。
  int knownCount(String page, Iterable<String> ids) => ids.where((id) => isKnown(page, id)).length;

  /// 记一次自评。[firstTry]：这一轮里第一次问到它（没经过「没记住 → 重现」）。
  /// - 第一次问就记住：认得次数 +1；
  /// - 没记住：认得次数清零、没记住次数 +1；
  /// - 重现后才记住：不加认得次数（提醒出来的不算自己想起来的），记录原样保留。
  void record(String page, String id, {required bool remembered, required bool firstTry}) {
    final e = _pages.putIfAbsent(page, () => {}).putIfAbsent(id, () => {"c": 0, "m": 0});
    if (!remembered) {
      e["c"] = 0;
      e["m"] = (e["m"] ?? 0) + 1;
    } else if (firstTry) {
      e["c"] = (e["c"] ?? 0) + 1;
    }
    _save();
  }

  /// 清空一个页面的记录（「重新自测」）。
  void reset(String page) {
    if (_pages.remove(page) != null) _save();
  }

  void _load() {
    final path = _file;
    if (path == null) return;
    try {
      final raw = jsonDecode(File(path).readAsStringSync()) as Map<String, dynamic>;
      for (final MapEntry(key: page, value: entries) in (raw["pages"] as Map<String, dynamic>).entries) {
        _pages[page] = {
          for (final MapEntry(key: id, value: mark) in (entries as Map<String, dynamic>).entries)
            id: {
              "c": ((mark as Map<String, dynamic>)["c"] as num?)?.toInt() ?? 0,
              "m": (mark["m"] as num?)?.toInt() ?? 0,
            },
        };
      }
    } catch (_) {
      // 没有文件或内容坏了：当作一份空白记录，等于重新自测一遍，不值得报错。
      _pages.clear();
    }
  }

  void _save() {
    final path = _file;
    if (path == null) return;
    try {
      Directory(p.dirname(path)).createSync(recursive: true);
      File(path).writeAsStringSync(jsonEncode({"version": 1, "pages": _pages}));
    } catch (_) {
      // 写不进去只是记不住这次结果，不拦着继续自测。
    }
  }
}
