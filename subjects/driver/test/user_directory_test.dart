import "dart:convert";
import "dart:io";

import "package:athena_driver/sync.dart";
import "package:athena_driver/user_directory.dart";
import "package:flutter_test/flutter_test.dart";

/// 假的学习者目录服务：按 nas_admin/user_api 的契约实现内存版（登记、按名字登录、
/// 只能改自己）。客户端对它过一遍，等于把两端对契约的理解各核了一遍（ADR 0075）。
class FakeDirectoryServer {
  HttpServer? _server;
  final token = "dapi_dir_token";
  final List<({int id, String name})> rows = [];

  Future<void> start() async {
    _server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    _listen();
  }

  Future<void> stop() async => _server?.close(force: true);

  String get base => "http://127.0.0.1:${_server!.port}";

  static String _key(String name) => name.trim().toLowerCase();

  Future<void> _listen() async {
    await for (final request in _server!) {
      final response = request.response;
      try {
        if (request.headers.value("Authorization") != "Bearer $token") {
          _json(response, 401, {"error": "unauthorized"});
          continue;
        }
        final raw = await utf8.decoder.bind(request).join();
        final body = raw.isEmpty ? <String, dynamic>{} : jsonDecode(raw) as Map<String, dynamic>;
        _handle(request, response, body);
      } catch (_) {
        _json(response, 500, {"error": "internal"});
      }
    }
  }

  void _handle(HttpRequest request, HttpResponse response, Map<String, dynamic> body) {
    final path = request.uri.path.replaceFirst("/api/users/v1", "");
    final method = request.method;
    if (method == "POST" && path == "/users") {
      final id = rows.length + 1;
      final row = (id: id, name: (body["name"] as String).trim());
      rows.add(row);
      _json(response, 201, {"user": {"id": row.id, "name": row.name}});
    } else if (method == "POST" && path == "/login") {
      final wanted = body["id"] as int?;
      final hits = [
        for (final row in rows)
          if (_key(row.name) == _key(body["name"] as String) && (wanted == null || row.id == wanted)) row,
      ];
      if (hits.isEmpty) {
        _json(response, 404, {"error": "not_found", "message": "没有这个学习者"});
      } else if (hits.length > 1) {
        _json(response, 409, {"error": "ambiguous", "message": "有重名", "matches": hits.length});
      } else {
        _json(response, 200, {"user": {"id": hits.single.id, "name": hits.single.name}});
      }
    } else if (method == "PATCH" && path.startsWith("/users/")) {
      final id = int.parse(path.substring("/users/".length));
      if (request.headers.value("X-Athena-User") != "$id") {
        _json(response, 403, {"error": "forbidden", "message": "只能查看或修改当前登录的学习者自己"});
        return;
      }
      final index = rows.indexWhere((row) => row.id == id);
      rows[index] = (id: id, name: (body["name"] as String).trim());
      _json(response, 200, {"user": {"id": id, "name": rows[index].name}});
    } else {
      _json(response, 404, {"error": "not_found"});
    }
  }

  void _json(HttpResponse response, int status, Object body) {
    response
      ..statusCode = status
      ..headers.contentType = ContentType.json
      ..write(jsonEncode(body))
      ..close();
  }
}

void main() {
  late FakeDirectoryServer server;
  late HttpUserDirectory directory;

  setUp(() async {
    server = FakeDirectoryServer();
    await server.start();
    directory = HttpUserDirectory(ApiConfig(lanBase: server.base, token: server.token));
  });

  tearDown(() => server.stop());

  test("新建拿到服务端分配的编号，按名字登录能找回", () async {
    final created = await directory.register("  小王 ");
    expect((created.id, created.name), ("1", "小王"));
    final back = await directory.login("小王");
    expect(back.id, "1");
  });

  test("没有这个名字：DirectoryNotFound", () async {
    await expectLater(directory.login("没人"), throwsA(isA<DirectoryNotFound>()));
  });

  test("重名要再问编号：DirectoryAmbiguous 带个数，给了编号就能进（ADR 0075 决策 2）", () async {
    await directory.register("小王");
    final second = await directory.register("小王");
    await expectLater(
      directory.login("小王"),
      throwsA(isA<DirectoryAmbiguous>().having((e) => e.matches, "matches", 2)),
    );
    expect((await directory.login("小王", id: second.id)).id, second.id);
    await expectLater(directory.login("小王", id: "9"), throwsA(isA<DirectoryNotFound>()));
  });

  test("改自己的名字成功；改别人的被服务端拒绝（只能改自己）", () async {
    final me = await directory.register("tiger");
    final other = await directory.register("小王");
    expect((await directory.rename(me.id, "老司机")).name, "老司机");
    expect(server.rows.first.name, "老司机");

    // 客户端接口里「当前学习者」就是被改的编号，没有改别人的入口；
    // 这里直接伪造请求头，验证服务端那一道也在。
    final client = HttpClient();
    final request = await client.patchUrl(Uri.parse("${server.base}/api/users/v1/users/${other.id}"));
    request.headers
      ..set("Authorization", "Bearer ${server.token}")
      ..set("X-Athena-User", me.id)
      ..contentType = ContentType.json;
    request.write(jsonEncode({"name": "被改了"}));
    final response = await request.close();
    await response.drain<void>();
    client.close();
    expect(response.statusCode, 403);
    expect(server.rows.last.name, "小王");
  });

  test("令牌无效：DirectoryRejected，提示重新配置", () async {
    final bad = HttpUserDirectory(ApiConfig(lanBase: server.base, token: "dapi_wrong"));
    await expectLater(
      bad.login("tiger"),
      throwsA(isA<DirectoryRejected>().having((e) => e.message, "message", contains("令牌"))),
    );
  });

  test("内网端点不通自动换外网端点；全不通是 DirectoryUnavailable", () async {
    final dead = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    final deadBase = "http://127.0.0.1:${dead.port}";
    await dead.close(force: true);

    final fallback = HttpUserDirectory(ApiConfig(lanBase: deadBase, wanBase: server.base, token: server.token));
    expect((await fallback.register("tiger")).id, "1");

    final none = HttpUserDirectory(ApiConfig(lanBase: deadBase, token: server.token));
    await expectLater(none.login("tiger"), throwsA(isA<DirectoryUnavailable>()));
  });
}
