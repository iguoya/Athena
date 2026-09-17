import "dart:convert";
import "dart:io";

import "package:athena_driver/progress.dart";
import "package:athena_driver/sync.dart";
import "package:flutter_test/flutter_test.dart";
import "package:http/http.dart" as http;
import "package:http/testing.dart";
import "package:path/path.dart" as p;

void main() {
  test("事件流导出后能原样并回来，重复的不会翻倍", () async {
    final store = await ProgressStore.open(path: ":memory:");
    await store.recordAttempt(
      questionId: "drive.s1.rules.001",
      topicId: "drive.s1.rules",
      subjectId: "subject1",
      correct: true,
      durationMs: 3200,
    );
    final events = await store.exportEvents();
    expect(events, hasLength(1));
    expect(events.first["kind"], "attempt");

    // 同一批事件再并一次，应当一条都不写入
    expect(await store.importEvents(events), 0);
    expect(await store.attemptTotal(), 1);

    // 另一台机器的记录并进来
    final fromOther = [
      {
        "kind": "attempt",
        "question_id": "drive.s1.rules.002",
        "topic_id": "drive.s1.rules",
        "subject_id": "subject1",
        "correct": 0,
        "duration_ms": 8000,
        "hesitant": 1,
        "at": "2026-09-17T09:00:00.000",
      },
    ];
    expect(await store.importEvents(fromOther), 1);
    expect(await store.attemptTotal(), 2);
    await store.close();
  });

  test("同步：拉回远端的记录并把合并结果推上去", () async {
    final store = await ProgressStore.open(path: ":memory:");
    await store.recordAttempt(
      questionId: "local.001",
      topicId: "drive.s1.rules",
      subjectId: "subject1",
      correct: true,
    );
    final remoteLine = jsonEncode({
      "kind": "attempt",
      "question_id": "remote.001",
      "topic_id": "drive.s1.rules",
      "subject_id": "subject1",
      "correct": 1,
      "duration_ms": 0,
      "hesitant": 0,
      "at": "2026-09-16T10:00:00.000",
    });
    String? pushed;
    final client = MockClient((request) async {
      if (request.method == "GET") {
        return http.Response(
          jsonEncode({"sha": "abc123", "content": base64Encode(utf8.encode(remoteLine))}),
          200,
        );
      }
      final body = jsonDecode(request.body) as Map<String, dynamic>;
      expect(body["sha"], "abc123", reason: "推送要带上刚读到的 sha，远端变了就该冲突重来");
      pushed = utf8.decode(base64Decode(body["content"] as String));
      return http.Response(jsonEncode({"content": {}}), 200);
    });

    const config = SyncConfig(owner: "me", repo: "progress", token: "t");
    final result = await GithubSync(config, client: client).run(store);

    expect(result.ok, isTrue);
    expect(result.pulled, 1, reason: "远端那条要并进本地");
    expect(await store.attemptTotal(), 2);
    expect(pushed, isNotNull);
    expect(const LineSplitter().convert(pushed!), hasLength(2), reason: "推上去的是两边的并集");
    await store.close();
  });

  _folderTests();

  test("令牌无效时给出能看懂的说明，而不是抛异常", () async {
    final store = await ProgressStore.open(path: ":memory:");
    final client = MockClient((request) async => http.Response("{}", 401));
    const config = SyncConfig(owner: "me", repo: "progress", token: "bad");
    final result = await GithubSync(config, client: client).run(store);
    expect(result.ok, isFalse);
    expect(result.message, contains("401"));
    await store.close();
  });
}

// ── 文件夹同步（iCloud Drive / OneDrive 这类云盘目录）──────────────────────
void _folderTests() {
  test("文件夹同步：并回别的机器那份，并把本机这份写出去", () async {
    final dir = await Directory.systemTemp.createTemp("athena-folder-sync");
    addTearDown(() => dir.deleteSync(recursive: true));
    File(p.join(dir.path, "driver-progress-other.jsonl")).writeAsStringSync(
      jsonEncode({
        "kind": "attempt",
        "question_id": "other.001",
        "topic_id": "drive.s1.rules",
        "subject_id": "subject1",
        "correct": 1,
        "duration_ms": 0,
        "hesitant": 0,
        "at": "2026-09-16T08:00:00.000",
      }),
    );

    final store = await ProgressStore.open(path: ":memory:");
    await store.recordAttempt(
      questionId: "mine.001",
      topicId: "drive.s1.rules",
      subjectId: "subject1",
      correct: true,
    );

    final config = SyncConfig(
      owner: "",
      repo: "",
      token: "",
      folder: dir.path,
      device: "mac",
    );
    final result = await FolderSync(config).run(store);

    expect(result.ok, isTrue);
    expect(result.pulled, 1, reason: "另一台的记录要并进来");
    expect(await store.attemptTotal(), 2);

    final mine = File(p.join(dir.path, "driver-progress-mac.jsonl"));
    expect(mine.existsSync(), isTrue, reason: "每台机器只写自己那份，云盘就不会有写冲突");
    expect(const LineSplitter().convert(mine.readAsStringSync()), hasLength(2));

    // 别的机器那份原样不动
    expect(
      const LineSplitter()
          .convert(File(p.join(dir.path, "driver-progress-other.jsonl")).readAsStringSync()),
      hasLength(1),
    );
    await store.close();
  });

  test("没选文件夹时给一句话，而不是抛异常", () async {
    final store = await ProgressStore.open(path: ":memory:");
    const config = SyncConfig(owner: "", repo: "", token: "");
    final result = await FolderSync(config).run(store);
    expect(result.ok, isFalse);
    expect(result.message, contains("同步文件夹"));
    await store.close();
  });
}
