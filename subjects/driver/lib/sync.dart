import "dart:async";
import "dart:convert";
import "dart:io";

import "package:flutter/foundation.dart";
import "package:http/http.dart" as http;
import "package:path/path.dart" as p;

import "progress.dart";

/// 同步配置（主仓库 ADR 0077）：客户端**不持有任何令牌**。
///
/// - 内网端点直连路由器上的后台，家用网络内视为可信，不需要凭据；默认就是路由器的内网地址，
///   所以什么都不配也能同步。
/// - 外网端点过 Cloudflare，整个主机名由 Access 把守；程序调用带 Access 服务令牌头
///   （外网访问凭据，Cloudflare 的概念，全家共用一对，可选）。
///
/// 同步器按「上次用活的端点优先」的顺序尝试，切网自动换路。
class ApiConfig {
  const ApiConfig({
    this.lanBase = defaultLanBase,
    this.wanBase,
    this.cfClientId,
    this.cfClientSecret,
  });

  /// 路由器上后台的内网地址。
  static const defaultLanBase = "http://192.168.6.1:5000";

  final String lanBase;
  final String? wanBase;
  final String? cfClientId;
  final String? cfClientSecret;

  Map<String, Object?> toJson() => {
        "lan_base": lanBase,
        "wan_base": wanBase,
        "cf_client_id": cfClientId,
        "cf_client_secret": cfClientSecret,
      };

  /// 读取时忽略不认识的字段：旧版本留下的 `token` 就是这样被丢掉的。
  static ApiConfig fromJson(Map<String, dynamic> map) {
    final lan = (map["lan_base"] as String?)?.trim() ?? "";
    return ApiConfig(
      lanBase: lan.isEmpty ? defaultLanBase : lan,
      wanBase: map["wan_base"] as String?,
      cfClientId: map["cf_client_id"] as String?,
      cfClientSecret: map["cf_client_secret"] as String?,
    );
  }

  static String get _file => p.join(ProgressStore.userDataDir(), "api.json");

  /// 来源有两处：环境变量 `ATHENA_DRIVER_API`（JSON 串，CI 与脚本用）或用户数据目录的
  /// `api.json`（配置屏保存，POSIX 上 600）；都没有就是默认配置（内网地址、无外网）。
  /// 文件里的外网访问凭据不进仓库。
  static ApiConfig load() {
    final raw = Platform.environment["ATHENA_DRIVER_API"];
    if (raw != null && raw.isNotEmpty) {
      try {
        return ApiConfig.fromJson(jsonDecode(raw) as Map<String, dynamic>);
      } on FormatException {
        return const ApiConfig();
      } on TypeError {
        return const ApiConfig();
      }
    }
    final file = File(_file);
    if (!file.existsSync()) return const ApiConfig();
    try {
      return ApiConfig.fromJson(jsonDecode(file.readAsStringSync()) as Map<String, dynamic>);
    } on FormatException {
      return const ApiConfig();
    } on TypeError {
      return const ApiConfig();
    }
  }

  /// 配置屏「保存」用。写完在 POSIX 上收紧权限（里面可能有外网访问凭据）；Windows 没有
  /// chmod，用户数据目录本身的 ACL 已按用户隔离。
  void save() {
    final file = File(_file);
    file.parent.createSync(recursive: true);
    file.writeAsStringSync(jsonEncode(toJson()));
    if (!Platform.isWindows) {
      Process.runSync("chmod", ["600", _file]);
    }
  }
}

/// 请求被 Cloudflare Access 拦住的特征：重定向到登录页（3xx）、带 Cloudflare-Access 质询头，
/// 或 401/403 且正文不是应用自己的 JSON 错误（应用的错误都是 `{"error":…}`，见
/// nas_admin 的 API）。应用自己不回重定向，所以不会和业务错误混淆。
bool blockedByCloudflare(int status, Map<String, String> headers, String body) {
  if (status >= 300 && status < 400) return true;
  if ((headers["www-authenticate"] ?? "").contains("Cloudflare-Access")) return true;
  return (status == 401 || status == 403) && !body.trimLeft().startsWith("{");
}

/// 同步状态的快照——侧栏常驻显示的「N 条待同步」与最近错误（ADR 0070 决策 4）。
class SyncStatus {
  const SyncStatus({
    this.running = false,
    this.pending = 0,
    this.dead = 0,
    this.lastSyncAt,
    this.lastError,
  });

  final bool running;
  final int pending;
  final int dead;
  final DateTime? lastSyncAt;
  final String? lastError;

  SyncStatus copyWith({bool? running, int? pending, int? dead, DateTime? lastSyncAt, String? lastError}) =>
      SyncStatus(
        running: running ?? this.running,
        pending: pending ?? this.pending,
        dead: dead ?? this.dead,
        lastSyncAt: lastSyncAt ?? this.lastSyncAt,
        lastError: lastError ?? this.lastError,
      );
}

/// 临时性失败（网络不通、5xx、限流）：本轮放弃，下一轮再来，不算错误事件。
class SyncTransient implements Exception {
  final String detail;
  SyncTransient(this.detail);
}

/// 外网被 Cloudflare 访问规则拦住（主仓库 ADR 0077）。继续重试没有意义，要人来处理
/// （检查同步设置里的外网访问凭据）。内网直连不会遇到这个。
class SyncAuthError implements Exception {}

/// 服务端把某条记录判为 invalid（400）：本地数据不合契约，属程序缺陷。
/// 该条标死、单独暴露，不让它卡住后面的记录（ADR 0070 决策 4）。
class SyncInvalid implements Exception {
  final String message;
  SyncInvalid(this.message);
}

/// 请求的资源不存在（404）：拉取草稿时表示服务端没有这份草稿。
class SyncNotFound implements Exception {}

/// 后台同步器（ADR 0068 决策 4、ADR 0070）：上传 outbox（幂等）、按游标拉取
/// 增量、维护状态。所有数据库操作都走 ProgressStore 的同步方法，与界面同
/// isolate 串行执行，不存在并发写。
class SyncEngine {
  SyncEngine({
    required ProgressStore store,
    required ApiConfig config,
    required this.user,
    required this.draftKeys,
  }) : _status = ValueNotifier(const SyncStatus()) {
    _store = store;
    _config = config;
    _store.onEnqueued = trigger;
  }

  static const _resources = [
    "attempts",
    "exams",
    "drill-runs",
    "rehearsals",
    "drill-notes",
    "point-notes",
    "notices",
    "explain-views",
  ];

  static const _batchSize = 500;
  static const _requestTimeout = Duration(seconds: 15);
  static const _interval = Duration(minutes: 5);

  late final ProgressStore _store;
  late final ApiConfig _config;

  /// 学习者名字（ADR 0071）：随每个请求发 `X-Athena-User`，服务端按它隔离读写。
  /// 是会话状态不是凭据——同一台设备换人不换令牌。
  final String user;

  /// 草稿 key 的封闭集合（每科目一份），同步时全部探一遍——别处新存的草稿
  /// 本地还没出现过，光靠本地 key 会漏。
  final List<String> draftKeys;

  late final ValueNotifier<SyncStatus> _status;
  Timer? _timer;
  Timer? _debounce;
  String? _activeBase;
  final _client = http.Client();
  bool _stopped = false;
  bool _running = false;

  ValueListenable<SyncStatus> get status => _status;

  /// 启动：先跑一轮，然后每 [_interval] 一轮。写入侧每次入队后 [trigger] 防抖触发。
  void start() {
    _stopped = false;
    _timer = Timer.periodic(_interval, (_) => syncNow());
    syncNow();
  }

  void stop() {
    _stopped = true;
    _timer?.cancel();
    _timer = null;
    _debounce?.cancel();
    _debounce = null;
    if (_store.onEnqueued == trigger) _store.onEnqueued = null;
  }

  /// 写入后的防抖触发：连续答题时不要每题都起一轮 HTTP。
  void trigger() {
    if (_stopped || _running) return;
    _debounce?.cancel();
    _debounce = Timer(const Duration(seconds: 2), () => syncNow());
  }

  /// 状态发布。lastError 是三态（设置 / 保留 / 清除），copyWith 的「null = 保留」
  /// 表达不了清除，在这里显式处理。
  void _publish({bool clearError = false, String? error, DateTime? syncedAt}) {
    final current = _status.value;
    _status.value = SyncStatus(
      running: current.running,
      pending: _store.pendingCount(),
      dead: _store.deadCount(),
      lastSyncAt: syncedAt ?? current.lastSyncAt,
      lastError: error ?? (clearError ? null : current.lastError),
    );
  }

  /// 一轮完整同步：先上传（把本地新增推出去），再拉取（把别处的新增收进来）。
  /// 任何一步临时失败就整轮结束——上传与拉取的先后不影响收敛：两边都是幂等的。
  Future<void> syncNow() async {
    if (_running || _stopped) return;
    _running = true;
    _status.value = _status.value.copyWith(running: true);
    try {
      await _flush();
      await _pull();
      if (_store.deadCount() > 0) {
        // 本轮走完但仍有标死记录：错误不能被「同步完成」盖掉（ADR 0070 决策 4）。
        _publish(error: "有 ${_store.deadCount()} 条记录无法同步。");
      } else {
        _publish(clearError: true, syncedAt: DateTime.now());
      }
    } on SyncAuthError {
      _publish(error: "外网被 Cloudflare 访问规则拦住了：检查同步设置里的外网访问凭据（内网不受影响）。");
    } on SyncTransient catch (error) {
      // 网络不通是常态（不在内网、路由器重启）：如实记录，不惊动做题的人。
      _publish(error: "暂不同步：${error.detail}");
    } finally {
      _running = false;
      _status.value = _status.value.copyWith(running: false);
    }
  }

  // ---------------------------------------------------------------- 上传

  Future<void> _flush() async {
    var kinds = _store.pendingKinds();
    while (kinds.isNotEmpty) {
      for (final kind in kinds) {
        await _flushKind(kind);
      }
      // 可变数据在折叠中可能产生新 kind（如答题产生成就），直到清空为止。
      kinds = _store.pendingKinds();
      if (kinds.length > 8) break; // 防御：一轮别无限追新。
    }
  }

  Future<void> _flushKind(String kind) async {
    while (true) {
      final batch = _store.outboxBatch(kind, limit: _batchSize);
      if (batch.isEmpty) return;
      try {
        switch (kind) {
          case "achievement":
            for (final entry in batch) {
              await _send("PUT", "/achievements/${entry.key}", entry.payload);
            }
          case "exam-draft":
            for (final entry in batch) {
              await _send("PUT", "/exam-drafts/${entry.key}", entry.payload);
            }
          case "exam-draft-delete":
            for (final entry in batch) {
              await _send("DELETE", "/exam-drafts/${entry.key}", null);
            }
          case "read-all":
            await _send("POST", "/notices/read-all", {});
          default:
            await _send("POST", "/$kind", {
              "items": [for (final entry in batch) entry.payload],
            });
        }
        _store.outboxDelete([for (final entry in batch) entry.id]);
      } on SyncInvalid catch (error) {
        // 整批拒收时无法知道是哪一条（服务端 400 指向 items[i]）：追加型资源逐条
        // 复试一次，把坏的那条标死，其余继续。单条资源（成就、草稿、已读）直接标死。
        if (batch.length > 1 && _resources.contains(kind)) {
          for (final entry in batch) {
            try {
              await _send("POST", "/$kind", {"items": [entry.payload]});
              _store.outboxDelete([entry.id]);
            } on SyncInvalid {
              _store.outboxMarkDead(entry.id);
            }
          }
        } else {
          for (final entry in batch) {
            _store.outboxMarkDead(entry.id);
          }
        }
        _publish(error: "有 ${_store.deadCount()} 条记录无法同步（$kind：${error.message}）。");
        return;
      }
    }
  }

  // ---------------------------------------------------------------- 拉取

  Future<void> _pull() async {
    for (final resource in _resources) {
      while (true) {
        final cursor = _store.cursor(resource);
        final data = await _send("GET", "/$resource?after_id=$cursor&limit=$_batchSize", null);
        final items = (data["items"] as List<dynamic>? ?? const []).cast<Map<String, dynamic>>();
        _store.applyRemote(resource, items);
        _store.setCursor(resource, (data["next_after_id"] as num).toInt());
        if (data["has_more"] != true) break;
      }
    }

    final achievements = await _send("GET", "/achievements", null);
    for (final item in (achievements["items"] as List<dynamic>? ?? const [])) {
      final map = item as Map<String, dynamic>;
      _store.applyRemoteAchievement(map["key"] as String, map["at"] as String);
    }

    final keys = {...draftKeys, ..._store.localDraftKeys()};
    for (final key in keys) {
      try {
        final data = await _send("GET", "/exam-drafts/$key", null);
        // 真实服务端把草稿字段直接放在响应顶层；早先的假服务端多包了一层 draft。两种都认。
        final raw = (data["draft"] is Map ? data["draft"] as Map : data).cast<String, Object?>();
        _store.applyRemoteDraft(key, ExamDraft.fromApi(raw));
      } on SyncNotFound {
        // 404：服务端没有这份草稿（别处交卷后删了）。
        _store.applyRemoteDraft(key, null);
      }
    }
  }

  // ---------------------------------------------------------------- HTTP

  /// 发一个请求。端点顺序：上次用活的优先，失败换下一个；网络层全失败是
  /// [SyncTransient]，HTTP 401 是 [SyncAuthError]，400 是 [SyncInvalid]，
  /// 其余状态码按临时失败处理。
  Future<Map<String, Object?>> _send(String method, String path, Map<String, Object?>? body) async {
    final bases = [
      ?_activeBase,
      _config.lanBase,
      ?_config.wanBase,
    ];
    final tried = <String>{};
    Object? lastNetworkError;
    for (final base in bases) {
      if (!tried.add(base)) continue;
      final uri = Uri.parse("$base/api/driver/v1$path");
      final request = http.Request(method, uri)
        ..followRedirects = false // 被 Access 拦住会 302 到登录页，要看见它而不是跟过去
        ..headers["X-Athena-User"] = user
        ..headers["Cache-Control"] = "no-store";
      if (_config.cfClientId != null && _config.cfClientSecret != null) {
        request.headers["CF-Access-Client-Id"] = _config.cfClientId!;
        request.headers["CF-Access-Client-Secret"] = _config.cfClientSecret!;
      }
      if (body != null) {
        request.headers["Content-Type"] = "application/json; charset=utf-8";
        request.body = jsonEncode(body);
      }
      try {
        final response = await _client.send(request).timeout(_requestTimeout);
        final text = await response.stream.bytesToString();
        _activeBase = base;
        if (blockedByCloudflare(response.statusCode, response.headers, text)) throw SyncAuthError();
        if (response.statusCode == 404) throw SyncNotFound();
        if (response.statusCode == 400) {
          throw SyncInvalid(((jsonDecode(text.isEmpty ? "{}" : text) as Map)["message"] ?? "校验失败").toString());
        }
        if (response.statusCode >= 400) {
          throw SyncTransient("服务端返回 ${response.statusCode}");
        }
        if (text.isEmpty) return const {};
        return (jsonDecode(text) as Map).cast<String, Object?>();
      } on SyncAuthError {
        rethrow;
      } on SyncInvalid {
        rethrow;
      } on SyncNotFound {
        rethrow;
      } on TimeoutException {
        lastNetworkError = "$uri 超时";
      } catch (error) {
        lastNetworkError = "$error";
      }
    }
    throw SyncTransient(lastNetworkError == null ? "没有可用端点" : "网络不通（$lastNetworkError）");
  }
}
