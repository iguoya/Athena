import "dart:convert";
import "dart:io";

import "package:path/path.dart" as p;

/// 一个学习者：编号是身份（服务端分配的 1～999 纯数字，永不变），名字只是称呼
/// （只能改自己的，ADR 0075）。编号用字符串存：本地库文件名、`X-Athena-User` 请求头、
/// 中心 `user` 列都是文本。
class UserProfile {
  const UserProfile({required this.id, required this.name, this.extra = const {}});

  final String id;
  final String name;

  /// 注册表文件里本版本不认识的字段，原样带回去（见 [UserRegistry] 的读写约定）。
  final Map<String, dynamic> extra;

  UserProfile withName(String newName) => UserProfile(id: id, name: newName, extra: extra);
}

/// 本机学习者缓存（ADR 0073、0074、0075）：这台机器上登录过哪些学习者、上次用的是谁。
///
/// **权威在中心目录**（后台库的 `athena_users`），这里只是缓存加本机的 `last`：
/// 缓存里有的名字离线也能直接进入，缓存没有的要联网问中心。无口令（信任模型与设备令牌
/// 一致）。文件放在**应用无关**的全局目录（ADR 0073），格式由主仓库
/// `docs/REPOSITORY.md` 定义，不由本应用单方面决定。
class UserRegistry {
  UserRegistry._(this.users, this.last, this._extra);

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
    return p.join(root, Platform.isMacOS || Platform.isWindows ? "Athena" : "athena");
  }

  /// 测试把注册表重定向到临时文件；生产为 null。
  static String? fileOverride;

  final List<UserProfile> users;

  /// 上次使用者的编号。
  String? last;

  /// 顶层的未知字段：将来别的应用或新版本加了字段，写回时不能抹掉。
  final Map<String, dynamic> _extra;

  static String get _path => fileOverride ?? p.join(globalDataDir(), "users.json");

  /// 读缓存。文件不存在、损坏都当「还没有学习者」；编号不是 1～999 数字串的条目（旧草稿
  /// 结构留下的）直接忽略，不崩。
  static UserRegistry load() {
    final file = File(_path);
    if (!file.existsSync()) return UserRegistry._([], null, {});
    try {
      final map = jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
      final users = <UserProfile>[];
      for (final entry in map["users"] as List<dynamic>? ?? const []) {
        if (entry is! Map) continue;
        final id = "${entry["id"]}";
        final name = entry["name"];
        if (name is! String || !_isValidId(id)) continue;
        users.add(UserProfile(
          id: id,
          name: name,
          extra: {
            for (final field in entry.entries)
              if (field.key != "id" && field.key != "name") "${field.key}": field.value,
          },
        ));
      }
      final last = map["last"] as String?;
      return UserRegistry._(
        users,
        last != null && users.any((profile) => profile.id == last) ? last : null,
        {
          for (final field in map.entries)
            if (field.key != "users" && field.key != "last") field.key: field.value,
        },
      );
    } on FormatException {
      return UserRegistry._([], null, {});
    } on TypeError {
      return UserRegistry._([], null, {});
    }
  }

  /// 先写临时文件再改名：写到一半断电不会留下半个 JSON。
  void _save() {
    final file = File(_path);
    file.parent.createSync(recursive: true);
    final temp = File("${file.path}.tmp");
    temp.writeAsStringSync(jsonEncode({
      ..._extra,
      "users": [
        for (final profile in users) {...profile.extra, "id": profile.id, "name": profile.name},
      ],
      "last": last,
    }));
    temp.renameSync(file.path);
  }

  /// 登录成功后记进缓存（已有就更新名字），并设为上次使用的人。
  UserProfile remember(UserProfile profile) {
    final index = users.indexWhere((entry) => entry.id == profile.id);
    final stored = index < 0
        ? profile
        : UserProfile(id: profile.id, name: profile.name, extra: users[index].extra);
    if (index < 0) {
      users.add(stored);
    } else {
      users[index] = stored;
    }
    last = stored.id;
    _save();
    return stored;
  }

  /// 服务端改名成功后同步缓存里的名字。
  void renamed(String id, String newName) {
    final index = users.indexWhere((entry) => entry.id == id);
    if (index < 0) return;
    users[index] = users[index].withName(newName);
    _save();
  }

  UserProfile? byId(String id) {
    for (final profile in users) {
      if (profile.id == id) return profile;
    }
    return null;
  }

  /// 缓存里叫这个名字的人（忽略大小写和首尾空白，与服务端同一口径）。
  List<UserProfile> matching(String name) {
    final key = nameKey(name);
    return [for (final profile in users) if (nameKey(profile.name) == key) profile];
  }

  void setLast(String id) {
    last = id;
    _save();
  }

  static String nameKey(String name) => name.trim().toLowerCase();

  static bool _isValidId(String id) {
    final number = int.tryParse(id);
    return number != null && number >= 1 && number <= 999 && id == "$number";
  }

  /// 用户输入的编号：1～999 的数字。
  static void validateId(String id) {
    if (!_isValidId(id.trim())) {
      throw const FormatException("学习者编号是 1～999 的数字");
    }
  }

  /// 显示名规范（与服务端一致）：非空、不超过 64 个字符、不含斜杠与空字符。
  static void validateName(String name) {
    final trimmed = name.trim();
    if (trimmed.isEmpty || trimmed.length > 64) {
      throw const FormatException("名字不能为空，且不超过 64 个字符");
    }
    if (trimmed.contains("\u0000") || trimmed.contains("/") || trimmed.contains(r"\")) {
      throw const FormatException("名字里不能有斜杠");
    }
  }
}
