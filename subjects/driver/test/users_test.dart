import "dart:convert";
import "dart:io";

import "package:athena_driver/core/users.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  late Directory dir;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp("athena-driver-users-");
    UserRegistry.fileOverride = "${dir.path}${Platform.pathSeparator}users.json";
  });

  tearDown(() async {
    UserRegistry.fileOverride = null;
    await dir.delete(recursive: true);
  });

  File file() => File(UserRegistry.fileOverride!);

  test("登录过的人记进缓存并设为上次使用者，重开还在（ADR 0075 决策 7）", () {
    final registry = UserRegistry.load();
    expect(registry.users, isEmpty);
    registry.remember(const UserProfile(id: "3", name: "小张"));
    expect(registry.last, "3");

    final reopened = UserRegistry.load();
    expect(reopened.users.single.id, "3");
    expect(reopened.users.single.name, "小张");
    expect(reopened.last, "3");
  });

  test("再次登录同一个编号只更新名字，不重复登记", () {
    final registry = UserRegistry.load();
    registry.remember(const UserProfile(id: "3", name: "小张"));
    registry.remember(const UserProfile(id: "3", name: "老张"));
    expect(registry.users, hasLength(1));
    expect(registry.byId("3")!.name, "老张");
  });

  test("按名字找：忽略大小写和首尾空白，重名全部返回", () {
    final registry = UserRegistry.load();
    registry.remember(const UserProfile(id: "1", name: "Tiger"));
    registry.remember(const UserProfile(id: "2", name: "小王"));
    registry.remember(const UserProfile(id: "5", name: "小王"));
    expect(registry.matching("  tiger ").map((p) => p.id), ["1"]);
    expect(registry.matching("小王").map((p) => p.id), ["2", "5"]);
    expect(registry.matching("没人"), isEmpty);
  });

  test("改名只动名字，编号不变（ADR 0075）", () {
    final registry = UserRegistry.load();
    registry.remember(const UserProfile(id: "1", name: "tiger"));
    registry.renamed("1", "老司机");
    final reopened = UserRegistry.load();
    expect(reopened.users.single.id, "1");
    expect(reopened.users.single.name, "老司机");
  });

  test("读到不认识的字段，写回时原样保留（跨应用共用的文件，REPOSITORY.md 的读写约定）", () {
    file().writeAsStringSync(jsonEncode({
      "version": 2,
      "users": [
        {"id": "1", "name": "tiger", "avatar": "car"},
      ],
      "last": "1",
    }));
    final registry = UserRegistry.load();
    registry.remember(const UserProfile(id: "2", name: "小王"));
    registry.renamed("1", "老司机");

    final saved = jsonDecode(file().readAsStringSync()) as Map<String, dynamic>;
    expect(saved["version"], 2);
    final first = (saved["users"] as List).first as Map<String, dynamic>;
    expect(first["avatar"], "car");
    expect(first["name"], "老司机");
  });

  test("编号不是合法数字串的条目被忽略，不崩（0071~0073 的草稿结构从未发行）", () {
    file().writeAsStringSync(jsonEncode({
      "users": [
        "tiger",
        {"id": "u_d4d3f8fd73531202", "name": "旧草稿"},
        {"id": "0", "name": "零号"},
        {"id": "10000", "name": "越界"},
        {"id": "007", "name": "前导零"},
        {"id": 4, "name": "数字型编号也认"},
      ],
      "last": "u_d4d3f8fd73531202",
    }));
    final registry = UserRegistry.load();
    expect(registry.users.map((p) => p.id), ["4"]);
    expect(registry.last, isNull, reason: "last 指向被忽略的条目时作废");
  });

  test("本地学习者：编号从本机已有最大值加一、1000 起；isLocal 由编号段派生（ADR 0123）", () {
    final registry = UserRegistry.load();
    registry.remember(const UserProfile(id: "3", name: "小王"));
    expect(registry.nextLocalId(), 1000, reason: "服务器段的学习者不参与本地编号");
    registry.remember(const UserProfile(id: "1000", name: "本地一"));
    expect(registry.nextLocalId(), 1001);
    registry.remember(const UserProfile(id: "1005", name: "本地二"));
    expect(registry.nextLocalId(), 1006);

    expect(registry.byId("3")!.isLocal, isFalse);
    expect(registry.byId("1005")!.isLocal, isTrue);

    final reopened = UserRegistry.load();
    expect(reopened.users.map((p) => p.id), containsAll(["3", "1000", "1005"]));
    expect(reopened.byId("1000")!.name, "本地一", reason: "本地段编号照常在 users.json 里往返");
  });

  test("文件损坏当作还没有学习者", () {
    file().writeAsStringSync("{ not json");
    expect(UserRegistry.load().users, isEmpty);
    file().writeAsStringSync('{"users": "oops"}');
    expect(UserRegistry.load().users, isEmpty);
  });

  test("写盘走临时文件再改名，不留残片", () {
    final registry = UserRegistry.load();
    registry.remember(const UserProfile(id: "1", name: "tiger"));
    expect(File("${file().path}.tmp").existsSync(), isFalse);
  });

  test("名字与编号的输入校验", () {
    expect(() => UserRegistry.validateName(""), throwsFormatException);
    expect(() => UserRegistry.validateName("   "), throwsFormatException);
    expect(() => UserRegistry.validateName("a/b"), throwsFormatException);
    expect(() => UserRegistry.validateName(r"a\b"), throwsFormatException);
    expect(() => UserRegistry.validateName("x" * 65), throwsFormatException);
    UserRegistry.validateName("小王");

    for (final bad in ["", "0", "10000", "abc", "-1", "1.5", "u_1"]) {
      expect(() => UserRegistry.validateId(bad), throwsFormatException, reason: bad);
    }
    UserRegistry.validateId("1");
    UserRegistry.validateId(" 999 ");
    // 本地段编号也合法（ADR 0123）。
    UserRegistry.validateId("1000");
  });
}
