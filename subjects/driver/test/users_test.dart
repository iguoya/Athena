import "dart:io";

import "package:athena_driver/users.dart";
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

  test("新建生成 u_ 前缀的随机 ID，注册表落在全局目录（ADR 0072、0073）", () {
    final registry = UserRegistry.load();
    expect(registry.users, isEmpty);
    final profile = registry.register("小张");
    expect(profile.id, matches(RegExp(r"^u_[0-9a-f]{16}$")));
    expect(profile.name, "小张");
    expect(registry.last, profile.id);

    final reopened = UserRegistry.load();
    expect(reopened.users.single.id, profile.id);
    expect(reopened.users.single.name, "小张");
    expect(reopened.last, profile.id);
  });

  test("改名只动显示名，ID 不变（ADR 0072）", () {
    final registry = UserRegistry.load();
    final profile = registry.register("tiger");
    registry.rename(profile.id, "老司机");
    final reopened = UserRegistry.load();
    expect(reopened.users.single.id, profile.id);
    expect(reopened.users.single.name, "老司机");
  });

  test("重名拒绝；续用（withId）用既有 ID、名字本机自己叫（ADR 0073）", () {
    final registry = UserRegistry.load();
    registry.register("tiger", withId: "u_d4d3f8fd73531202");
    expect(() => registry.register("tiger"), throwsFormatException);
    final adopted = registry.register("驾驶新手", withId: "u_abc");
    expect(adopted.id, "u_abc");
    expect(registry.byId("u_abc")!.name, "驾驶新手");
    // 同一 ID 不能登记两次。
    expect(() => registry.register("又一个人", withId: "u_abc"), throwsFormatException);
  });

  test("旧格式（名字数组）升级：名字直接当 ID——唯一存量 tiger 正好映射（ADR 0073）", () {
    File(UserRegistry.fileOverride!).writeAsStringSync('{"users": ["tiger"], "last": "tiger"}');
    final registry = UserRegistry.load();
    expect(registry.users.single.id, "tiger");
    expect(registry.users.single.name, "tiger");
  });
}
