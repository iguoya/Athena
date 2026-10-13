import "dart:io";

import "package:athena_driver/core/binding.dart";
import "package:athena_driver/core/user_directory.dart";
import "package:athena_driver/core/users.dart";
import "package:flutter_test/flutter_test.dart";

/// 内存版目录：与 nas_admin/user_api 同一套语义。
class FakeDirectory implements UserDirectory {
  final List<UserProfile> rows = [];
  int calls = 0;
  bool down = false;
  String? rejection;

  UserProfile add(String name) {
    final profile = UserProfile(id: "${rows.length + 1}", name: name);
    rows.add(profile);
    return profile;
  }

  @override
  Future<UserProfile> login(String name, {String? id}) async {
    calls++;
    if (down) throw DirectoryUnavailable("网络不通");
    final key = name.trim().toLowerCase();
    final hits = [
      for (final row in rows)
        if (row.name.toLowerCase() == key) row,
    ];
    if (hits.isEmpty) throw DirectoryNotFound();
    if (hits.length > 1) throw DirectoryAmbiguous(hits.length);
    return hits.single;
  }

  @override
  Future<UserProfile> register(String name) async {
    calls++;
    if (down) throw DirectoryUnavailable("网络不通");
    if (rejection != null) throw DirectoryRejected(rejection!);
    return add(name.trim());
  }

  @override
  Future<UserProfile> rename(String id, String name) => throw UnimplementedError();
}

/// 学习者与中心目录的静默绑定（ADR 0127）：路由器在才发生，成败都不抛给调用方。
void main() {
  late Directory dir;
  late UserRegistry registry;
  late FakeDirectory directory;
  late LearnerBinder binder;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp("athena-driver-bind-");
    UserRegistry.fileOverride = "${dir.path}${Platform.pathSeparator}users.json";
    registry = UserRegistry.load();
    directory = FakeDirectory();
    binder = LearnerBinder(registry: registry, directoryFactory: () => directory);
  });

  tearDown(() async {
    UserRegistry.fileOverride = null;
    await dir.delete(recursive: true);
  });

  test("中心段编号的学习者本来就是中心编号：不问目录", () async {
    final tiger = registry.remember(const UserProfile(id: "1", name: "tiger"));
    expect(await binder.ensureBound(tiger), "1");
    expect(directory.calls, 0);
  });

  test("本机学习者按名字认领中心里唯一的同名者（同一个人换了台电脑）", () async {
    directory.add("tiger");
    final local = registry.remember(const UserProfile(id: "1000", name: "tiger"));
    expect(await binder.ensureBound(local), "1");
    expect(registry.byId("1000")?.serverId, "1", reason: "绑定记进本机缓存");
    expect(registry.byId("1000")?.id, "1000", reason: "本机编号不变，本地库文件名与记录归属都不动");
  });

  test("中心里没有这个名字：登记一个新的并绑定", () async {
    final local = registry.remember(const UserProfile(id: "1000", name: "新人"));
    expect(await binder.ensureBound(local), "1");
    expect(directory.rows.single.name, "新人");
    expect(registry.byId("1000")?.serverId, "1");
  });

  test("已经绑定过就不再问目录", () async {
    directory.add("tiger");
    final local = registry.remember(const UserProfile(id: "1000", name: "tiger"));
    await binder.ensureBound(local);
    final callsAfterFirst = directory.calls;
    expect(await binder.ensureBound(registry.byId("1000")!), "1");
    expect(directory.calls, callsAfterFirst);
  });

  test("路由器不在：返回 null、不抛错、不改缓存，下次再试", () async {
    directory.down = true;
    final local = registry.remember(const UserProfile(id: "1000", name: "tiger"));
    expect(await binder.ensureBound(local), isNull);
    expect(registry.byId("1000")?.serverId, isNull);

    directory.down = false;
    expect(await binder.ensureBound(local), "1");
  });

  test("中心里有不止一个同名者：不乱认，保持仅本机，也不登记新的", () async {
    directory.add("小王");
    directory.add("小王");
    final local = registry.remember(const UserProfile(id: "1000", name: "小王"));
    expect(await binder.ensureBound(local), isNull);
    expect(registry.byId("1000")?.serverId, isNull);
    expect(directory.rows, hasLength(2));
  });

  test("服务端拒绝：返回 null、不抛错", () async {
    directory.rejection = "编号已用完";
    final local = registry.remember(const UserProfile(id: "1000", name: "新人"));
    expect(await binder.ensureBound(local), isNull);
  });

  test("绑定记在 users.json 里，重新加载还在，且保留其它未知字段", () async {
    directory.add("tiger");
    final local = registry.remember(const UserProfile(id: "1000", name: "tiger", extra: {"future": 42}));
    await binder.ensureBound(local);
    final reloaded = UserRegistry.load().byId("1000");
    expect(reloaded?.serverId, "1");
    expect(reloaded?.extra["future"], 42);
  });
}
