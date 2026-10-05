import "dart:convert";
import "dart:io";

import "package:path/path.dart" as p;

import "progress.dart";

/// 自测的**作答**记录（ADR 0082、0083、0085、0090）：自测里每张卡判一次对错，这里记下结果，
/// 把每张卡区分成三种状态——没考过、答错过、答对过。答对过的以后不再出现；答错过的下次
/// 再考（第二次只考它们）；没考过的先考。它补作答记录管不到的地方：没有相关题的条目
/// （胎压灯这类）的兜底，以及本页「还出不出」的过滤。0085 前记录的是自评，字段与格式原样沿用。
///
/// **它不是掌握度，也不是「认得」的依据。** 速记卡有相关题的，「认得」只看作答记录
/// （答对并掌握才算，见 `classifyEntry`）；自测答得再对也只能得到「自测答对，待做题确认」。
/// 这份记录不进作答、不进统计与激励、不参与过关，也不同步——换一台机器就是重新自测一遍，
/// 代价很小，换来的是不必为它改中心库的表结构。
///
/// 每位学习者一份文件 `selftest-<学习者>.json`（用户数据目录）；[user] 为空就只存内存
/// （测试与没登录的场景），关掉即消失。条目键由页面给出（页面键 + 条目键）。
class SelfTestStore {
  SelfTestStore({String? user, String? directory, DateTime Function()? clock})
    : _clock = clock ?? DateTime.now,
      _file = user == null
          ? null
          : p.join(directory ?? ProgressStore.userDataDir(), "selftest-${_safe(user)}.json") {
    _load();
  }

  final DateTime Function() _clock;
  final String? _file;

  DateTime now() => _clock();

  /// 页面键 → 条目键 → 记录 `{c: 一次就答对的次数, m: 答错的次数, t: 最近一次作答的毫秒时间}`。
  final Map<String, Map<String, Map<String, int>>> _pages = {};

  static String _safe(String user) => user.replaceAll(RegExp(r'[/\\:*?"<>|]'), "_");

  Map<String, int>? _entry(String page, String id) => _pages[page]?[id];

  /// 答对过（第一次问就答对）：以后不再出现，除非「重新自测」清掉记录（ADR 0090，
  /// 取代 0083 的间隔复现——答对的不用在后续测试中出现）。
  bool isConfirmed(String page, String id) => (_entry(page, id)?["c"] ?? 0) >= 1;

  /// 答错过、还没答对过：下次自测优先再考。
  bool isLearning(String page, String id) {
    final e = _entry(page, id);
    return e != null && (e["c"] ?? 0) == 0 && (e["m"] ?? 0) > 0;
  }

  /// 记一次作答。[firstTry]：这一次自测里第一次问到它（没经过「答错 → 重现」）。
  /// - 第一次问就答对：记为答对过，以后不再出现；
  /// - 答错：答对次数清零、答错次数 +1，下次自测再考；
  /// - 答错后重现才答对：不算答对过（提醒出来的不算自己想起来的），记录原样保留，下次再考一次。
  void record(String page, String id, {required bool remembered, required bool firstTry}) {
    final e = _pages.putIfAbsent(page, () => {}).putIfAbsent(id, () => {"c": 0, "m": 0, "t": 0});
    final stamp = now().millisecondsSinceEpoch;
    if (!remembered) {
      e["c"] = 0;
      e["m"] = (e["m"] ?? 0) + 1;
      e["t"] = stamp;
    } else if (firstTry) {
      e["c"] = (e["c"] ?? 0) + 1;
      e["t"] = stamp;
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
              "t": (mark["t"] as num?)?.toInt() ?? 0,
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
      File(path).writeAsStringSync(jsonEncode({"version": 2, "pages": _pages}));
    } catch (_) {
      // 写不进去只是记不住这次结果，不拦着继续自测。
    }
  }
}
