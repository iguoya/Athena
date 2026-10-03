import "dart:convert";
import "dart:io";
import "dart:math";

import "package:path/path.dart" as p;

/// 一个学习者：ID 是身份（永不变），名字只是称呼（随便改，ADR 0072）。
class UserProfile {
  const UserProfile({required this.id, required this.name});

  final String id;
  final String name;
}

/// 学习者目录（ADR 0071、0072、0073）：这台机器上有哪些学习者、上次用的是谁。
///
/// 无口令（信任模型与设备令牌一致）。ID 用于本地库文件名、照片清单名、
/// `X-Athena-User` 请求头与中心 `user` 列；显示名只存在本表，改名不触碰同步数据。
/// 跨设备续用靠 ID：另一台机器输入同一个 ID，同步的就是同一份历史。
///
/// 注册表放在**应用无关**的全局目录（ADR 0073）：学习者是「这个人」，不是驾考里的
/// 一个人——将来别的学习应用接入中心时，读的是同一份目录、认的是同一套 ID。
class UserRegistry {
  UserRegistry._(this.users, this.last);

  /// 全局数据目录（Athena/，与各应用自己的目录如 AthenaDriver/ 平级）。
  static String globalDataDir() {
    late final String root;
    if (Platform.isMacOS) {
      root = p.join(Platform.environment["HOME"]!, "Library", "Application Support");
    } else if (Platform.isWindows) {
      root = Platform.environment["APPDATA"] ?? Platform.environment["USERPROFILE"]!;
    } else {
      final home = Platform.environment["HOME"]!;
      root = Platform.environment["XDG_DATA_HOME"] ?? p.join(home, ".local", "share");
    }
    return p.join(root, "Athena");
  }

  /// 测试把注册表重定向到临时文件；生产为 null。
  static String? fileOverride;

  final List<UserProfile> users;

  /// 上次使用者的 ID。
  String? last;

  static String get _path =>
      fileOverride ?? p.join(globalDataDir(), "users.json");

  static UserRegistry load() {
    final file = File(_path);
    if (!file.existsSync()) return UserRegistry._(const [], null);
    try {
      final map = jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
      final raw = map["users"] as List<dynamic>? ?? const [];
      return UserRegistry._(
        [
          for (final entry in raw)
            if (entry is Map)
              UserProfile(id: entry["id"] as String, name: entry["name"] as String)
            else if (entry is String)
              // 0071 时代的旧结构（名字数组）：名字直接当 ID——唯一的存量
              // 是 tiger，正好 ADR 0072 把首用户 ID 定为字面量 tiger，无缝。
              UserProfile(id: entry, name: entry),
        ],
        map["last"] as String?,
      );
    } on FormatException {
      return UserRegistry._(const [], null);
    }
  }

  void _save() {
    final file = File(_path);
    file.parent.createSync(recursive: true);
    file.writeAsStringSync(jsonEncode({
      "users": [
        for (final profile in users) {"id": profile.id, "name": profile.name},
      ],
      "last": last,
    }));
  }

  /// 新建学习者：生成随机 ID（`u_` + 16 位十六进制）。[withId] 供收编与续用
  /// （首用户字面量 tiger、另一台机器输入的既有 ID）。
  UserProfile register(String name, {String? withId}) {
    final trimmed = name.trim();
    validateName(trimmed);
    final id = withId != null && withId.trim().isNotEmpty ? withId.trim() : _newId();
    if (users.any((profile) => profile.id == id)) {
      throw const FormatException("这个学习者 ID 已经在本机登记过了");
    }
    final profile = UserProfile(id: id, name: trimmed);
    users.add(profile);
    last = id;
    _save();
    return profile;
  }

  /// 改显示名：只动本表，ID 与一切同步数据不动（ADR 0072）。
  void rename(String id, String newName) {
    final trimmed = newName.trim();
    validateName(trimmed);
    if (users.any((profile) => profile.name == trimmed && profile.id != id)) {
      throw const FormatException("这个名字已经在用了");
    }
    final index = users.indexWhere((profile) => profile.id == id);
    if (index < 0) throw const FormatException("没有这个学习者");
    users[index] = UserProfile(id: id, name: trimmed);
    _save();
  }

  UserProfile? byId(String id) {
    for (final profile in users) {
      if (profile.id == id) return profile;
    }
    return null;
  }

  void setLast(String id) {
    last = id;
    _save();
  }

  static String _newId() {
    final random = Random.secure();
    return "u_${List.generate(16, (i) => "0123456789abcdef"[random.nextInt(16)]).join()}";
  }

  /// 显示名规范：非空、无空字符、长度有上限；不含路径分隔符（ID 会进本地库
  /// 文件名——随机 ID 天然满足，续用输入的 ID 走 [validateId]）。
  static void validateName(String name) {
    if (name.isEmpty || name.length > 64) {
      throw const FormatException("名字不能为空，且不超过 64 个字符");
    }
    if (name.contains("\u0000") || name.contains("/") || name.contains(r"\")) {
      throw const FormatException("名字里不能有斜杠");
    }
  }

  /// 续用输入的 ID 校验：非空、只含 ID 安全字符（字母数字、下划线、连字符）。
  static void validateId(String id) {
    if (!RegExp(r"^[A-Za-z0-9_-]{1,64}$").hasMatch(id)) {
      throw const FormatException("学习者 ID 只能是字母、数字、下划线或连字符");
    }
  }
}
