import "dart:convert";
import "dart:io";

import "package:athena_driver/progress.dart";
import "package:athena_driver/sync.dart";
import "package:flutter_test/flutter_test.dart";

/// 假的中心 API：按 nas_admin/driver_api 的契约实现内存版——去重键、游标、
/// 成就取更早、草稿按 saved_at 覆盖。同步器对这个假服务过一遍，等于把两端
/// 对契约的理解各核了一遍（ADR 0068 决策 4、ADR 0070）。
class FakeApi {
  HttpServer? _server;
  var _down = false;

  /// 模拟外网被 Cloudflare Access 拦住：所有请求 302 到登录页（ADR 0077）。
  var _blocked = false;

  /// 模拟旧版后台：没带设备令牌就 401。
  var _legacy = false;

  final Map<String, List<Map<String, Object?>>> _rows = {};
  final Map<String, String> _achievements = {};
  final Map<String, Map<String, Object?>> _drafts = {};

  /// 真实服务端的标志位存成 0/1 整数，拉回来也是整数；客户端上传时用布尔。假服务端照真实的来，
  /// 否则「拉回来是整数」这一类错误（`as bool` 强转崩）在测试里永远测不出来。
  static const _flags = {"correct", "hesitant", "passed", "read", "full_bank"};

  static Map<String, Object?> _serverShape(Map<String, Object?> row) => {
        for (final entry in row.entries)
          entry.key: _flags.contains(entry.key) && entry.value is bool ? ((entry.value! as bool) ? 1 : 0) : entry.value,
      };

  static final _dedupe = <String, int Function(Map<String, Object?>, String)>{
    "attempts": (m, u) => Object.hash(u, m["question_id"], m["at"]),
    "exams": (m, u) => Object.hash(u, m["subject_id"], m["at"]),
    "drill-runs": (m, u) => Object.hash(u, m["item_id"], m["at"]),
    "rehearsals": (m, u) => Object.hash(u, m["item_id"], m["at"]),
    "drill-notes": (m, u) => Object.hash(u, m["item_id"], m["at"]),
    "point-notes": (m, u) => Object.hash(u, m["item_id"], m["step"], m["at"]),
    "notices": (m, u) => Object.hash(u, m["kind"], m["title"], m["at"]),
    "explain-views": (m, u) => Object.hash(u, m["question_id"], m["attempt_at"]),
  };

  final _ids = <String, int>{};

  Future<void> start() async {
    _server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    _listen();
  }

  String get base => "http://127.0.0.1:${_server!.port}";

  void setDown(bool down) => _down = down;

  void setBlocked(bool blocked) => _blocked = blocked;

  void setLegacy(bool legacy) => _legacy = legacy;

  int rowCount(String resource) => _rows[resource]?.length ?? 0;

  Map<String, Object?>? draft(String user, String key) =>
      _drafts["$user${String.fromCharCode(0)}$key"];

  Future<void> _listen() async {
    await for (final request in _server!) {
      final response = request.response;
      try {
        if (_down) {
          await response.close();
          continue;
        }
        if (_legacy) {
          _json(response, 401, {"error": "unauthorized", "message": "缺少或无效的设备令牌"});
          continue;
        }
        if (_blocked) {
          response
            ..statusCode = 302
            ..headers.set("Location", "https://example.cloudflareaccess.com/cdn-cgi/access/login/x")
            ..headers.set("Www-Authenticate", "Cloudflare-Access resource_metadata=x");
          await response.close();
          continue;
        }
        final user = request.headers.value("X-Athena-User")?.trim() ?? "";
        if (user.isEmpty) {
          _json(response, 400, {"error": "invalid", "message": "user：不能为空"});
          continue;
        }
        await _handle(request, response, user);
      } catch (_) {
        _json(response, 500, {"error": "internal"});
      }
    }
  }

  Future<void> _handle(HttpRequest request, HttpResponse response, String user) async {
    final path = request.uri.path.replaceFirst(RegExp(r"^/api/driver/v1"), "");
    final method = request.method;

    if (method == "GET" && path == "/ping") {
      _json(response, 200, {"ok": true, "device": "测试设备"});
      return;
    }

    for (final resource in _dedupe.keys) {
      if (path != "/$resource") continue;
      if (method == "GET") {
        final after = int.parse(request.uri.queryParameters["after_id"] ?? "0");
        final limit = int.parse(request.uri.queryParameters["limit"] ?? "500");
        final all = _rows[resource] ?? const [];
        final page = [
          for (final row in all)
            // 按用户过滤，返回行剥掉 user（与真实服务端同一口径，ADR 0071）。
            if (row["user"] == user && (row["id"] as int) > after)
              {for (final entry in row.entries) if (entry.key != "user") entry.key: entry.value},
        ].take(limit).toList();
        _json(response, 200, {
          "items": page,
          "has_more": page.length == limit,
          "next_after_id": page.isEmpty ? after : page.last["id"],
        });
        return;
      }
      if (method == "POST") {
        final body = await _body(request);
        final items = (body["items"] as List).cast<Map<String, Object?>>();
        // 模拟真实服务端的校验：at 不是合法 ISO-8601 就整批 400。
        for (final item in items) {
          final at = item["at"];
          if (at is! String || DateTime.tryParse(at) == null) {
            _json(response, 400, {"error": "invalid", "message": "items[0].at：不是合法 ISO-8601 时间"});
            return;
          }
        }
        var inserted = 0;
        var skipped = 0;
        final known = <int>{};
        for (final row in _rows[resource] ?? const <Map<String, Object?>>[]) {
          known.add(_dedupe[resource]!(row, row["user"] as String));
        }
        final list = _rows.putIfAbsent(resource, () => []);
        for (final item in items) {
          final key = _dedupe[resource]!(item, user);
          if (known.contains(key)) {
            skipped++;
            continue;
          }
          known.add(key);
          _ids[resource] = (_ids[resource] ?? 0) + 1;
          list.add({..._serverShape(item), "user": user, "id": _ids[resource]});
          inserted++;
        }
        _json(response, 200, {"inserted": inserted, "skipped": skipped});
        return;
      }
    }

    if (method == "POST" && path == "/notices/read-all") {
      for (final row in _rows["notices"] ?? const <Map<String, Object?>>[]) {
        if (row["user"] == user) row["read"] = 1;
      }
      _json(response, 200, {"updated": 0});
      return;
    }

    if (path.startsWith("/achievements")) {
      final nul = String.fromCharCode(0);
      if (method == "GET" && path == "/achievements") {
        _json(response, 200, {
          "items": [
            for (final entry in _achievements.entries)
              if (entry.key.startsWith("$user$nul"))
                {"key": entry.key.split(nul)[1], "at": entry.value},
          ],
        });
        return;
      }
      if (method == "PUT") {
        final key = path.split("/").last;
        final at = (await _body(request))["at"] as String;
        final full = "$user$nul$key"; // 键表按 (user, key) 幂等（ADR 0071）
        final existing = _achievements[full];
        if (existing == null || at.compareTo(existing) < 0) _achievements[full] = at;
        _json(response, 200, {"key": key, "at": _achievements[full]});
        return;
      }
    }

    if (path.startsWith("/exam-drafts/")) {
      final key = path.split("/").last;
      final full = "$user${String.fromCharCode(0)}$key"; // 键表按 (user, key)（ADR 0071）
      if (method == "GET") {
        final draft = _drafts[full];
        if (draft == null) {
          _json(response, 404, {"error": "not_found"});
        } else {
          // 真实服务端把草稿字段直接放在响应顶层，不再包一层 draft。
          _json(response, 200, draft);
        }
        return;
      }
      if (method == "PUT") {
        final body = await _body(request);
        final existing = _drafts[full];
        final incoming = (body["saved_at"] as String?) ?? "";
        if (existing == null || incoming.compareTo((existing["saved_at"] as String?) ?? "") > 0) {
          _drafts[full] = _serverShape(body);
          _json(response, 200, {"applied": true});
        } else {
          _json(response, 200, {"applied": false});
        }
        return;
      }
      if (method == "DELETE") {
        _drafts.remove(full);
        response.statusCode = 204;
        await response.close();
        return;
      }
    }

    _json(response, 404, {"error": "not_found"});
  }

  Future<Map<String, Object?>> _body(HttpRequest request) async {
    final text = await utf8.decoder.bind(request).join();
    return (jsonDecode(text) as Map).cast<String, Object?>();
  }

  static void _json(HttpResponse response, int status, Map<String, Object?> body) {
    response.statusCode = status;
    response.headers.contentType = ContentType.json;
    response.write(jsonEncode(body));
    response.close();
  }
}

void main() {
  late FakeApi api;
  late ProgressStore store;
  late SyncEngine engine;

  setUp(() async {
    api = FakeApi();
    await api.start();
    store = await ProgressStore.open(suite: "sync_test");
    engine = SyncEngine(
      store: store,
      config: ApiConfig(lanBase: api.base, wanBase: null),
      user: "tiger",
      draftKeys: const ["subject1.exam"],
    );
  });

  tearDown(() async {
    engine.stop();
    await store.close();
    await api._server!.close(force: true);
  });

  test("离线做题排进队列，联网一轮补发成功且队列清空", () async {
    api.setDown(true);
    await store.recordAttempt(questionId: "q1", topicId: "t", subjectId: "s", correct: true);
    await store.recordExam(subjectId: "subject1", score: 96, passed: true);
    expect(store.pendingCount(), greaterThan(0));

    api.setDown(false);
    await engine.syncNow();
    expect(store.pendingCount(), 0);
    expect(api.rowCount("attempts"), 1);
    expect(api.rowCount("exams"), 1);
    // 交卷及格还会产生通知与成就，一并上传（成就键带用户前缀，FakeApi 内部口径）。
    expect(api.rowCount("notices"), greaterThanOrEqualTo(1));
    expect(api._achievements.keys, contains("tiger${String.fromCharCode(0)}exam.pass.subject1"));
  });

  test("上传幂等：同一条重复上传被服务端跳过，本地不会重复", () async {
    await store.recordAttempt(questionId: "q1", topicId: "t", subjectId: "s", correct: true);
    await engine.syncNow();
    // 再直接把同一批重发一次（模拟补发重叠），服务端应跳过。
    final batch = store.outboxBatch("attempts");
    expect(batch, isEmpty);
    expect(api.rowCount("attempts"), 1);
  });

  test("游标拉取：别处新增的记录并进本地，重复拉不重复插", () async {
    api._rows.putIfAbsent("attempts", () => []).add({
      "id": 1,
      "user": "tiger",
      "question_id": "remote.1",
      "topic_id": "t",
      "subject_id": "s",
      "correct": true,
      "duration_ms": 0,
      "hesitant": false,
      "at": "2026-09-01T10:00:00.000",
    });
    await engine.syncNow();
    expect(await store.attemptTotal(), 1);
    expect(store.cursor("attempts"), 1);
    // 第二轮：没有新数据，不增。
    await engine.syncNow();
    expect(await store.attemptTotal(), 1);
  });

  test("成就取更早：远端早于本地时，两端都收敛到更早的时间", () async {
    final nul = String.fromCharCode(0);
    api._achievements["tiger${nul}streak.5"] = "2026-01-01T00:00:00.000";
    // 本地连对 5 题解锁（at 是现在，晚于远端）。
    for (var i = 0; i < 5; i++) {
      await store.recordAttempt(questionId: "q$i", topicId: "t", subjectId: "s", correct: true);
    }
    expect(store.achievements().keys, contains("streak.5"));
    await engine.syncNow();
    // 上传（服务端保留更早）再拉取（本地也取更早）：两端一致为远端那个时间。
    expect(api._achievements["tiger${nul}streak.5"], "2026-01-01T00:00:00.000");
    expect(store.achievements()["streak.5"], "2026-01-01T00:00:00.000");
  });

  test("草稿按 saved_at 覆盖：远端更新才覆盖本地，远端删除且本地无待传时本地也删", () async {
    final draft = ExamDraft(
      subjectId: "subject1",
      title: "模拟考",
      questionIds: const ["q1"],
      questionCount: 100,
      minutes: 45,
      passScore: 90,
      pointsPerQuestion: 1,
      mix: const {},
      fullBank: true,
      picked: const {0: {"T"}},
      startedAt: DateTime.parse("2026-10-01T10:00:00"),
      savedAt: DateTime.parse("2026-10-01T10:05:00"),
    );
    await store.saveExamDraft(draft, draftKey: "subject1.exam");
    await engine.syncNow();
    expect(api.draft("tiger", "subject1.exam"), isNotNull);

    // 远端被别处更新（saved_at 更新），拉取后覆盖本地。
    api._drafts["tiger${String.fromCharCode(0)}subject1.exam"] = {
      ...draft.toApi(),
      "saved_at": "2026-10-01T10:09:00.000",
      "picked": "{\"1\": [\"T\"]}",
    };
    await engine.syncNow();
    final pulled = await store.loadExamDraft("subject1.exam");
    expect(pulled!.picked.keys, {1});

    // 远端删除（交卷了），本地也没有待传的保存 → 本地草稿跟着删。
    api._drafts.remove("tiger${String.fromCharCode(0)}subject1.exam");
    await engine.syncNow();
    expect(await store.loadExamDraft("subject1.exam"), isNull);
  });

  test("invalid 标死：整批被拒后逐条复试，坏的一条标死、好的照常上传", () async {
    // 正常写入路径不会产生坏记录；这里直接往 outbox 塞一条 at 非法的，
    // 模拟程序缺陷（ADR 0070 决策 4：标死并显式暴露，不无限重试）。
    await store.recordAttempt(questionId: "good", topicId: "t", subjectId: "s", correct: true);
    // 直接在底层补一条坏记录（at 不是时间）。
    store.debugEnqueue("attempts", {
      "question_id": "bad",
      "topic_id": "t",
      "subject_id": "s",
      "correct": true,
      "duration_ms": 0,
      "hesitant": false,
      "at": "not-a-time",
    });
    expect(store.pendingCount(), 2);

    await engine.syncNow();
    expect(store.deadCount(), 1);
    expect(store.pendingCount(), 0);
    expect(api.rowCount("attempts"), 1); // 只有 good 上去了
    expect(engine.status.value.lastError, contains("无法同步"));
  });

  test("多用户：两份本地库同步到同一中心，互不可见也不互吞（ADR 0071）", () async {
    // 第二位学习者：独立的本地库文件就是独立的空白历史。
    final storeB = await ProgressStore.open(suite: "sync_test_user_b");
    addTearDown(() => storeB.close());
    final engineB = SyncEngine(
      store: storeB,
      config: ApiConfig(lanBase: api.base, wanBase: null),
      user: "second",
      draftKeys: const ["subject1.exam"],
    );
    addTearDown(engineB.stop);

    // tiger 答对一题；second 离线答同一题、同一时刻。
    await store.recordAttempt(questionId: "q1", topicId: "t", subjectId: "s", correct: true, at: DateTime.parse("2026-10-02T10:00:00"));
    await storeB.recordAttempt(questionId: "q1", topicId: "t", subjectId: "s", correct: false, at: DateTime.parse("2026-10-02T10:00:00"));
    await engine.syncNow();
    await engineB.syncNow();

    // 中心各存一条（去重键含 user），两边各自只拉到自己的。
    expect(api.rowCount("attempts"), 2);
    expect(await store.wrongQuestionIds(), isEmpty);
    expect(await storeB.wrongQuestionIds(), ["q1"]);
    expect(store.cursor("attempts"), 1);
    // 游标在该用户的行流上前进，不因别人的行跳号而漏拉。
    expect(storeB.cursor("attempts"), 2);
  });

  test("路由器上还是旧版后台（401）：说清楚是版本旧，队列保留，升级后补发", () async {
    api.setLegacy(true);
    final engine = SyncEngine(store: store, config: ApiConfig(lanBase: api.base, wanBase: null), user: "tiger", draftKeys: const []);
    await store.recordAttempt(questionId: "q1", topicId: "t", subjectId: "s", correct: true);
    await engine.syncNow();
    expect(store.pendingCount(), greaterThan(0));
    expect(engine.status.value.lastError, contains("旧版本"));
    api.setLegacy(false);
    await engine.syncNow();
    expect(store.pendingCount(), 0);
    engine.stop();
  });

  test("外网被 Cloudflare 访问规则拦住（302 到登录页）：报清楚原因，队列保留，放行后补发", () async {
    // 连得上 Cloudflare、但没带对外网访问凭据：所有请求 302 到登录页。
    // 客户端不跟随重定向，直接说明是访问规则拦住了，不当成网络不通（ADR 0077）。
    api.setBlocked(true);
    final blocked = SyncEngine(
      store: store,
      config: ApiConfig(lanBase: api.base, wanBase: null),
      user: "tiger",
      draftKeys: const [],
    );
    await store.recordAttempt(questionId: "q1", topicId: "t", subjectId: "s", correct: true);
    await blocked.syncNow();
    expect(store.pendingCount(), greaterThan(0));
    expect(blocked.status.value.lastError, contains("Cloudflare"));
    api.setBlocked(false);
    await blocked.syncNow();
    expect(store.pendingCount(), 0, reason: "放行后队列自然补发");
    blocked.stop();
  });
}
