import "dart:async";
import "dart:convert";

import "package:http/http.dart" as http;

import "sync.dart";
import "users.dart";

/// 中心学习者目录的客户端（主仓库 ADR 0074、0075；接口见 `practice/nas_admin/docs/user-api.md`）。
///
/// 目录是权威：新建要联网，异地首次登录要联网；已在本机缓存里的学习者不走这里
/// （离线照常进入）。认证复用同步用的设备令牌，端点顺序与同步器一致（内网优先，外网兜底）。
abstract class UserDirectory {
  /// 按名字登录；重名时需再给 [id]。
  /// 抛 [DirectoryNotFound]（没有这个人，或名字与编号对不上）、[DirectoryAmbiguous]
  /// （同名不止一个而没给编号）、[DirectoryUnavailable]（连不上）。
  Future<UserProfile> login(String name, {String? id});

  /// 新建学习者：名字 → 服务端分配编号。重名照样新建，是否确认由调用者先问。
  Future<UserProfile> register(String name);

  /// 改自己的名字。服务端校验当前学习者就是 [id]，改别人的被拒（只能改自己）。
  Future<UserProfile> rename(String id, String name);
}

/// 没有这个学习者；或给了编号却与名字对不上（服务端对两种情况给同一个答案）。
class DirectoryNotFound implements Exception {}

/// 有重名的学习者，需要再输入学习者编号；[matches] 是同名的个数。
class DirectoryAmbiguous implements Exception {
  DirectoryAmbiguous(this.matches);
  final int matches;
}

/// 连不上目录（网络不通、服务端故障、没配置设备令牌）。
class DirectoryUnavailable implements Exception {
  DirectoryUnavailable(this.detail);
  final String detail;

  @override
  String toString() => detail;
}

/// 服务端拒绝（校验不过、编号用完、令牌被撤销等），[message] 可直接给人看。
class DirectoryRejected implements Exception {
  DirectoryRejected(this.message);
  final String message;

  @override
  String toString() => message;
}

class HttpUserDirectory implements UserDirectory {
  HttpUserDirectory(this._config, {http.Client? client}) : _client = client ?? http.Client();

  final ApiConfig _config;
  final http.Client _client;
  String? _activeBase;

  static const _requestTimeout = Duration(seconds: 10);

  @override
  Future<UserProfile> login(String name, {String? id}) async {
    final body = <String, Object?>{"name": name.trim(), if (id != null && id.trim().isNotEmpty) "id": int.parse(id.trim())};
    return _profile(await _send("POST", "/login", body));
  }

  @override
  Future<UserProfile> register(String name) async =>
      _profile(await _send("POST", "/users", {"name": name.trim()}));

  @override
  Future<UserProfile> rename(String id, String name) async =>
      _profile(await _send("PATCH", "/users/$id", {"name": name.trim()}, acting: id));

  UserProfile _profile(Map<String, Object?> data) {
    final user = (data["user"] as Map).cast<String, Object?>();
    return UserProfile(id: "${user["id"]}", name: user["name"] as String);
  }

  Future<Map<String, Object?>> _send(String method, String path, Map<String, Object?> body, {String? acting}) async {
    final bases = [?_activeBase, _config.lanBase, ?_config.wanBase];
    final tried = <String>{};
    Object? lastNetworkError;
    for (final base in bases) {
      if (!tried.add(base)) continue;
      final request = http.Request(method, Uri.parse("$base/api/users/v1$path"))
        ..headers["Authorization"] = "Bearer ${_config.token}"
        ..headers["Cache-Control"] = "no-store"
        ..headers["Content-Type"] = "application/json; charset=utf-8"
        ..body = jsonEncode(body);
      if (acting != null) request.headers["X-Athena-User"] = acting;
      if (_config.cfClientId != null && _config.cfClientSecret != null) {
        request.headers["CF-Access-Client-Id"] = _config.cfClientId!;
        request.headers["CF-Access-Client-Secret"] = _config.cfClientSecret!;
      }
      try {
        final response = await _client.send(request).timeout(_requestTimeout);
        final text = await response.stream.bytesToString();
        _activeBase = base;
        final data = text.isEmpty ? <String, dynamic>{} : (jsonDecode(text) as Map).cast<String, dynamic>();
        final status = response.statusCode;
        if (status < 300) return data.cast<String, Object?>();
        final message = (data["message"] ?? "请求被拒绝").toString();
        if (status == 401) throw DirectoryRejected("设备令牌无效或已被撤销，请先在同步设置里重新配置。");
        if (status == 404) throw DirectoryNotFound();
        if (status == 409 && data["error"] == "ambiguous") {
          throw DirectoryAmbiguous((data["matches"] as num?)?.toInt() ?? 2);
        }
        if (status == 400 || status == 403 || status == 409) throw DirectoryRejected(message);
        throw DirectoryUnavailable("服务端返回 $status");
      } on DirectoryNotFound {
        rethrow;
      } on DirectoryAmbiguous {
        rethrow;
      } on DirectoryRejected {
        rethrow;
      } on DirectoryUnavailable {
        rethrow;
      } on TimeoutException {
        lastNetworkError = "$base 超时";
      } catch (error) {
        lastNetworkError = "$error";
      }
    }
    throw DirectoryUnavailable(lastNetworkError == null ? "没有可用端点" : "网络不通（$lastNetworkError）");
  }
}
