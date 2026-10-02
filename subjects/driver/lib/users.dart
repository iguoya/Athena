import "dart:convert";
import "dart:io";

import "package:path/path.dart" as p;

import "progress.dart";

/// 用户注册表（ADR 0071）：这台机器上有哪些学习者、上次用的是谁。
///
/// 用户就是一个名字（无口令，信任模型与设备令牌一致）；名字即稳定标识——本地库
/// 文件名、中心 `user` 列存的都是它，重名拒绝、不做改名（要换名字就是从头开始）。
/// 注册表只在本机：两台机器起同一个名字，共享的就是同一份历史——这是特性。
class UserRegistry {
  UserRegistry._(this.users, this.last);

  static String get _file => p.join(ProgressStore.userDataDir(), "users.json");

  final List<String> users;
  String? last;

  static UserRegistry load() {
    final file = File(_file);
    if (!file.existsSync()) return UserRegistry._(const [], null);
    try {
      final map = jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
      return UserRegistry._(
        [for (final name in map["users"] as List<dynamic>) name as String],
        map["last"] as String?,
      );
    } on FormatException {
      return UserRegistry._(const [], null);
    }
  }

  void _save() {
    final file = File(_file);
    file.parent.createSync(recursive: true);
    file.writeAsStringSync(jsonEncode({"users": users, "last": last}));
  }

  /// 注册一个新名字。重名拒绝（名字即标识，两个同名会共享历史——共享靠有意起
  /// 同名达成，不靠注册表制造意外）。
  void register(String name) {
    final trimmed = name.trim();
    validate(trimmed);
    if (users.contains(trimmed)) {
      throw const FormatException("这个名字已经在用了");
    }
    users.add(trimmed);
    last = trimmed;
    _save();
  }

  void setLast(String name) {
    last = name;
    _save();
  }

  /// 名字规范与服务端同一口径（X-Athena-User 过 string() 校验）：非空、无空字符、
  /// 长度有上限；再加一条本地的：不含路径分隔符（名字要进本地库文件名）。
  /// 输入界面也用它做即时校验。
  static void validate(String name) {
    if (name.isEmpty || name.length > 64) {
      throw const FormatException("名字不能为空，且不超过 64 个字符");
    }
    if (name.contains("\u0000") || name.contains("/") || name.contains(r"\")) {
      throw const FormatException("名字里不能有斜杠");
    }
  }
}
