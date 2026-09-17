import "dart:convert";
import "dart:io";

import "package:http/http.dart" as http;
import "package:path/path.dart" as p;

import "progress.dart";

/// 同步的落点：GitHub 上一个私有仓库里的一个 JSONL 文件。
///
/// 只走 REST Contents API，不需要本机装 git——另一台笔记本可能只拷了一个
/// `.app`（本应用 ADR 0010）。
class SyncConfig {
  const SyncConfig({
    required this.owner,
    required this.repo,
    required this.token,
    this.path = "driver-progress.jsonl",
    this.branch = "main",
    this.lastSyncedAt,
  });

  final String owner;
  final String repo;
  final String token;
  final String path;
  final String branch;

  /// 上次成功同步的时刻，只用来在界面上说一句「上次是什么时候」。
  final String? lastSyncedAt;

  bool get usable => owner.isNotEmpty && repo.isNotEmpty && token.isNotEmpty;

  static String get configPath => p.join(ProgressStore.userDataDir(), "sync.json");

  /// 读本机配置。令牌只存在这个文件里，不进版本库。
  static SyncConfig? load() {
    final file = File(configPath);
    if (!file.existsSync()) return null;
    try {
      final raw = jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
      return SyncConfig(
        owner: raw["owner"] as String? ?? "",
        repo: raw["repo"] as String? ?? "",
        token: raw["token"] as String? ?? "",
        path: raw["path"] as String? ?? "driver-progress.jsonl",
        branch: raw["branch"] as String? ?? "main",
        lastSyncedAt: raw["last_synced_at"] as String?,
      );
    } on FormatException {
      return null;
    }
  }

  void save() {
    final file = File(configPath);
    file.writeAsStringSync(
      const JsonEncoder.withIndent("  ").convert({
        "owner": owner,
        "repo": repo,
        "token": token,
        "path": path,
        "branch": branch,
        if (lastSyncedAt != null) "last_synced_at": lastSyncedAt,
      }),
    );
    // 令牌明文躺在磁盘上，至少别让同机其他用户读到。
    if (!Platform.isWindows) {
      Process.runSync("chmod", ["600", file.path]);
    }
  }

  SyncConfig withLastSynced(DateTime at) => SyncConfig(
    owner: owner,
    repo: repo,
    token: token,
    path: path,
    branch: branch,
    lastSyncedAt: at.toIso8601String(),
  );

  static void clear() {
    final file = File(configPath);
    if (file.existsSync()) file.deleteSync();
  }
}

class SyncResult {
  const SyncResult({
    required this.ok,
    this.pulled = 0,
    this.pushed = 0,
    this.total = 0,
    this.message = "",
  });

  final bool ok;

  /// 从远端并进本地的条数。
  final int pulled;

  /// 本地比远端多出、这次推上去的条数。
  final int pushed;

  /// 合并之后的事件总数。
  final int total;
  final String message;
}

class GithubSync {
  GithubSync(this.config, {http.Client? client}) : _client = client ?? http.Client();

  final SyncConfig config;
  final http.Client _client;

  Uri get _contentsUri => Uri.https(
    "api.github.com",
    "/repos/${config.owner}/${config.repo}/contents/${config.path}",
    {"ref": config.branch},
  );

  Map<String, String> _headers({String accept = "application/vnd.github+json"}) => {
    "Authorization": "Bearer ${config.token}",
    "Accept": accept,
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "athena-driver",
  };

  /// 拉远端 → 合并 → 推回去。远端在这中间被别的机器改过就重来一次。
  Future<SyncResult> run(ProgressStore store, {int attempt = 0}) async {
    if (!config.usable) {
      return const SyncResult(ok: false, message: "还没配置 GitHub 仓库和令牌");
    }
    try {
      final remote = await _fetch();
      final pulled = await store.importEvents(remote.events);
      final local = await store.exportEvents();
      final payload = local.map(jsonEncode).join("\n");
      final pushed = local.length - remote.events.length + pulled;
      if (remote.exists && payload == remote.text) {
        return SyncResult(
          ok: true,
          pulled: pulled,
          total: local.length,
          message: pulled > 0 ? "拉回 $pulled 条，两边已经一致" : "两边已经一致",
        );
      }
      final response = await _client.put(
        Uri.https(
          "api.github.com",
          "/repos/${config.owner}/${config.repo}/contents/${config.path}",
        ),
        headers: _headers(),
        body: jsonEncode({
          "message": "driver: 同步做题记录（${local.length} 条）",
          "content": base64Encode(utf8.encode(payload)),
          "branch": config.branch,
          if (remote.sha != null) "sha": remote.sha,
        }),
      );
      if (response.statusCode == 409 || response.statusCode == 422) {
        // 远端在我们读它之后被另一台改了：重新拉一遍再合并。
        if (attempt >= 2) {
          return const SyncResult(ok: false, message: "远端一直在变，稍后再试");
        }
        return await run(store, attempt: attempt + 1);
      }
      if (response.statusCode >= 300) {
        return SyncResult(ok: false, message: _explain(response));
      }
      return SyncResult(
        ok: true,
        pulled: pulled,
        pushed: pushed < 0 ? 0 : pushed,
        total: local.length,
        message: "已同步：拉回 $pulled 条，推上去 ${pushed < 0 ? 0 : pushed} 条",
      );
    } on SocketException {
      return const SyncResult(ok: false, message: "连不上 GitHub，检查网络");
    } on http.ClientException catch (error) {
      return SyncResult(ok: false, message: "请求失败：${error.message}");
    }
  }

  Future<_Remote> _fetch() async {
    final meta = await _client.get(_contentsUri, headers: _headers());
    if (meta.statusCode == 404) {
      return const _Remote(exists: false, sha: null, text: "", events: []);
    }
    if (meta.statusCode >= 300) {
      throw http.ClientException(_explain(meta));
    }
    final decoded = jsonDecode(meta.body) as Map<String, dynamic>;
    final sha = decoded["sha"] as String?;
    // 文件超过 1MB 时 content 字段是空的，得另外按 raw 取一次。
    final inline = (decoded["content"] as String? ?? "").replaceAll("\n", "");
    String text;
    if (inline.isNotEmpty) {
      text = utf8.decode(base64Decode(inline));
    } else {
      final raw = await _client.get(
        _contentsUri,
        headers: _headers(accept: "application/vnd.github.raw"),
      );
      if (raw.statusCode >= 300) throw http.ClientException(_explain(raw));
      text = utf8.decode(raw.bodyBytes);
    }
    return _Remote(exists: true, sha: sha, text: text, events: _parse(text));
  }

  static List<Map<String, Object?>> _parse(String text) {
    final events = <Map<String, Object?>>[];
    for (final line in const LineSplitter().convert(text)) {
      final trimmed = line.trim();
      if (trimmed.isEmpty) continue;
      try {
        final value = jsonDecode(trimmed);
        if (value is Map<String, dynamic>) events.add(value);
      } on FormatException {
        // 单行坏掉不该拖垮整份记录，跳过继续读——JSONL 选它就是图这个。
        continue;
      }
    }
    return events;
  }

  static String _explain(http.Response response) {
    return switch (response.statusCode) {
      401 => "令牌无效或已过期（401）",
      403 => "没有权限，或触到速率限制（403）",
      404 => "找不到仓库或分支，检查用户名、仓库名和分支（404）",
      _ => "GitHub 返回 ${response.statusCode}",
    };
  }
}

class _Remote {
  const _Remote({
    required this.exists,
    required this.sha,
    required this.text,
    required this.events,
  });

  final bool exists;
  final String? sha;
  final String text;
  final List<Map<String, Object?>> events;
}
