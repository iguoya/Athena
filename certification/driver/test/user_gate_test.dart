import "dart:io";

import "package:athena_driver/app/user_gate_screen.dart";
import "package:athena_driver/core/sync.dart";
import "package:athena_driver/core/user_directory.dart";
import "package:athena_driver/core/users.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

/// 内存版目录：与 nas_admin/user_api 同一套语义。登录页的流程测试不碰网络。
class FakeDirectory implements UserDirectory {
  final List<UserProfile> rows = [];
  int calls = 0;

  /// 为真时所有调用都像网络不通。
  bool down = false;

  /// 不为空时，新建会被服务端拒绝（比如后台版本太旧）。
  String? registerRejection;

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
        if (row.name.toLowerCase() == key && (id == null || id.isEmpty || row.id == id)) row,
    ];
    if (hits.isEmpty) throw DirectoryNotFound();
    if (hits.length > 1) throw DirectoryAmbiguous(hits.length);
    return hits.single;
  }

  @override
  Future<UserProfile> register(String name) async {
    calls++;
    if (down) throw DirectoryUnavailable("网络不通");
    if (registerRejection != null) throw DirectoryRejected(registerRejection!);
    return add(name.trim());
  }

  @override
  Future<UserProfile> rename(String id, String name) async {
    calls++;
    if (down) throw DirectoryUnavailable("网络不通");
    final index = rows.indexWhere((row) => row.id == id);
    rows[index] = rows[index].withName(name.trim());
    return rows[index];
  }
}

void main() {
  late Directory dir;
  late UserRegistry registry;
  late FakeDirectory directory;
  UserProfile? picked;
  bool? adopted;
  bool? createdFlag;
  UserProfile? renamed;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp("athena-driver-gate-");
    UserRegistry.fileOverride = "${dir.path}${Platform.pathSeparator}users.json";
    registry = UserRegistry.load();
    directory = FakeDirectory();
    picked = adopted = createdFlag = renamed = null;
  });

  tearDown(() async {
    UserRegistry.fileOverride = null;
    await dir.delete(recursive: true);
  });

  /// [remote] 模拟「同步设置里明确填了外网访问凭据」（ADR 0124）：只有这时登录页才会
  /// 碰中心目录；默认不配——新建一律落到本机。
  Future<void> open(
    WidgetTester tester, {
    UserProfile? current,
    bool legacy = false,
    bool remote = false,
  }) async {
    tester.view.physicalSize = const Size(1200, 1600);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(
      home: UserGateScreen(
        registry: registry,
        directoryFactory: () => directory,
        configLoader: () => remote
            ? const ApiConfig(wanBase: "https://wan.example", cfClientId: "id.access", cfClientSecret: "secret")
            : const ApiConfig(wanBase: null),
        currentUser: current,
        legacyPending: legacy,
        onPicked: (profile, adopt, created) {
          picked = profile;
          adopted = adopt;
          createdFlag = created;
        },
        onRenamed: (profile) => renamed = profile,
      ),
    ));
  }

  Future<void> typeName(WidgetTester tester, String name) async {
    await tester.enterText(find.widgetWithText(TextField, "你的名字"), name);
  }

  testWidgets("名字在本机缓存里唯一命中：直接进，不联网（离线可用）", (tester) async {
    registry.remember(const UserProfile(id: "3", name: "小王"));
    await open(tester);
    await typeName(tester, "小王");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "3");
    expect(directory.calls, 0);
  });

  testWidgets("配了凭据：本机没有的名字问中心目录，找到一个就进并记进缓存（异地登录）", (tester) async {
    directory.add("tiger");
    await open(tester, remote: true);
    await typeName(tester, "Tiger");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "1");
    expect(registry.byId("1")?.name, "tiger");
  });

  testWidgets("没配凭据：本机没有的名字直接在本地新建（编号 1000 起），不碰目录（ADR 0124）", (tester) async {
    await open(tester);
    await typeName(tester, "新人");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "1000", reason: "默认只存这台电脑，编号用本地段");
    expect(picked?.isLocal, isTrue);
    expect(createdFlag, isTrue);
    expect(directory.calls, 0, reason: "没配凭据就完全本机，登录页不发任何请求");
    expect(find.byType(AlertDialog), findsNothing);
  });

  testWidgets("配了凭据、目录里没有：点「进入」默认本地新建，不自动注册到服务器（ADR 0124）", (tester) async {
    directory.add("tiger");
    await open(tester, remote: true);
    await typeName(tester, "没人用过");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "1000");
    expect(picked?.isLocal, isTrue);
    expect(directory.rows, hasLength(1), reason: "只有原有的 tiger；没有把新人注册到服务器");
  });

  testWidgets("配了凭据：目录里有的人点「进入」是登录，不会被当成新建", (tester) async {
    directory.add("小王");
    await open(tester, remote: true);
    await typeName(tester, "小王");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(createdFlag, isFalse);
    expect(directory.rows, hasLength(1));
  });

  testWidgets("配了凭据：名字和编号对不上不会自动新建（只有「没有这个名字」才本地新建）", (tester) async {
    directory.add("小王");
    directory.add("小王");
    await open(tester, remote: true);
    await typeName(tester, "小王");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    await tester.enterText(find.widgetWithText(TextField, "学习者编号"), "9");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked, isNull);
    expect(directory.rows, hasLength(2), reason: "没有因为对不上就新建第三个");
  });

  testWidgets("配了凭据：重名再问学习者编号，输对才进，输错不进（ADR 0075 决策 2）", (tester) async {
    directory.add("小王");
    directory.add("小王");
    await open(tester, remote: true);
    await typeName(tester, "小王");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked, isNull);
    expect(find.text("学习者编号"), findsOneWidget);

    await tester.enterText(find.widgetWithText(TextField, "学习者编号"), "9");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked, isNull);
    expect(find.textContaining("名字和编号对不上"), findsOneWidget);

    await tester.enterText(find.widgetWithText(TextField, "学习者编号"), "2");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "2");
  });

  testWidgets("配了凭据：显式新建建到服务器，跨机器可同步（ADR 0124）", (tester) async {
    await open(tester, remote: true);
    await typeName(tester, "新人");
    await tester.tap(find.text("我是另一个同名的人，新建"));
    await tester.pumpAndSettle();
    expect(find.byType(AlertDialog), findsNothing);
    expect((picked?.id, createdFlag), ("1", true));
    expect(picked?.isLocal, isFalse);
  });

  testWidgets("没配凭据：显式新建建到本地（编号 1000 起），不碰目录（ADR 0124）", (tester) async {
    await open(tester);
    await typeName(tester, "新人");
    await tester.tap(find.text("我是另一个同名的人，新建"));
    await tester.pumpAndSettle();
    expect(find.byType(AlertDialog), findsNothing);
    expect((picked?.id, createdFlag), ("1000", true));
    expect(picked?.isLocal, isTrue);
    expect(directory.calls, 0);
  });

  testWidgets("配了凭据：名字已有人用，显式新建前先确认，取消就不建", (tester) async {
    directory.add("小王");
    await open(tester, remote: true);
    await typeName(tester, "小王");
    await tester.tap(find.text("我是另一个同名的人，新建"));
    await tester.pumpAndSettle();
    expect(find.text("已有同名的学习者"), findsOneWidget);

    await tester.tap(find.text("取消"));
    await tester.pumpAndSettle();
    expect(directory.rows, hasLength(1));
    expect(picked, isNull);
  });

  testWidgets("配了凭据：名字已有人用，确认后仍可在服务器新建，重名靠编号区分", (tester) async {
    directory.add("小王");
    await open(tester, remote: true);
    await typeName(tester, "小王");
    await tester.tap(find.text("我是另一个同名的人，新建"));
    await tester.pumpAndSettle();
    await tester.tap(find.text("仍要新建"));
    await tester.pumpAndSettle();
    expect((picked?.id, createdFlag), ("2", true));
    expect(directory.rows, hasLength(2));
  });

  testWidgets("没配凭据：本机已有同名，显式新建前先确认，确认后建到本地（ADR 0124）", (tester) async {
    registry.remember(const UserProfile(id: "3", name: "小王"));
    await open(tester);
    await typeName(tester, "小王");
    await tester.tap(find.text("我是另一个同名的人，新建"));
    await tester.pumpAndSettle();
    expect(find.text("这台电脑上已有同名的学习者"), findsOneWidget);

    await tester.tap(find.text("仍要新建"));
    await tester.pumpAndSettle();
    expect((picked?.id, createdFlag), ("1000", true));
    expect(directory.calls, 0);
  });

  testWidgets("只能改当前登录的这位：没有当前学习者时没有改名入口", (tester) async {
    registry.remember(const UserProfile(id: "1", name: "tiger"));
    await open(tester);
    expect(find.text("改我的名字"), findsNothing);
  });

  testWidgets("改自己的名字：服务端改成功后缓存与回调同步更新", (tester) async {
    final me = directory.add("tiger");
    registry.remember(me);
    await open(tester, current: me);
    expect(find.text("现在是：tiger（编号 1）"), findsOneWidget);

    await tester.tap(find.text("改我的名字"));
    await tester.pumpAndSettle();
    await tester.enterText(find.descendant(of: find.byType(AlertDialog), matching: find.byType(TextField)), "老司机");
    await tester.tap(find.text("保存"));
    await tester.pumpAndSettle();

    expect(directory.rows.single.name, "老司机");
    expect(registry.byId("1")?.name, "老司机");
    expect(renamed?.name, "老司机");
    expect(find.text("现在是：老司机（编号 1）"), findsOneWidget);
  });

  testWidgets("配了凭据：名字没人用、自动本地新建不经过服务端；服务端拒绝只发生在显式注册", (tester) async {
    directory.registerRejection = legacyServerMessage;
    await open(tester, remote: true);
    await typeName(tester, "tiger");
    await tester.tap(find.text("我是另一个同名的人，新建"));
    await tester.pumpAndSettle();
    expect(picked, isNull);
    expect(find.textContaining("旧版本"), findsOneWidget);
    expect(directory.rows, isEmpty);
  });

  testWidgets("配了凭据但连不上目录：新建说明原因，页面有同步设置入口；本机用过的人仍能直接进", (tester) async {
    registry.remember(const UserProfile(id: "3", name: "小王"));
    directory.down = true;
    await open(tester, remote: true);
    expect(find.text("同步设置"), findsOneWidget);

    await typeName(tester, "新人");
    await tester.tap(find.text("我是另一个同名的人，新建"));
    await tester.pumpAndSettle();
    expect(find.textContaining("连不上学习者目录"), findsOneWidget);
    expect(picked, isNull);

    // 本机缓存里的人离线照常进，不受影响。
    await typeName(tester, "小王");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "3");
  });

  testWidgets("配了凭据但连不上目录：出现「在这台电脑上新建（不同步）」，建出的本地学习者编号 1000 起（ADR 0123）", (tester) async {
    directory.down = true;
    await open(tester, remote: true);
    await typeName(tester, "本地新人");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(find.text("在这台电脑上新建（不同步）"), findsOneWidget);

    final callsAfterFailedEnter = directory.calls;
    await tester.tap(find.text("在这台电脑上新建（不同步）"));
    await tester.pumpAndSettle();
    expect(picked?.id, "1000", reason: "本地段从 1000 起，不与中心目录的 1～999 重叠");
    expect(picked?.isLocal, isTrue);
    expect(createdFlag, isTrue);
    expect(directory.calls, callsAfterFailedEnter, reason: "本地新建本身不再碰目录");
    expect(registry.byId("1000")?.name, "本地新人", reason: "记进本机缓存，下次离线也能进");
  });

  testWidgets("配了凭据但连不上目录：本地新建遇到本机同名的本地学习者，先确认，取消就不建（ADR 0123）", (tester) async {
    registry.remember(const UserProfile(id: "1000", name: "老王"));
    directory.down = true;
    await open(tester, remote: true);
    await typeName(tester, "老王");
    // 显式新建在目录不可达时失败（本机已有同名先确认一次，确认后 register 碰壁），
    // 失败后出现本地新建的出路。
    await tester.tap(find.text("我是另一个同名的人，新建"));
    await tester.pumpAndSettle();
    await tester.tap(find.text("仍要新建"));
    await tester.pumpAndSettle();
    expect(find.textContaining("连不上学习者目录"), findsOneWidget);

    await tester.tap(find.text("在这台电脑上新建（不同步）"));
    await tester.pumpAndSettle();
    expect(find.text("这台电脑上已有同名的本地学习者"), findsOneWidget);
    await tester.tap(find.text("取消"));
    await tester.pumpAndSettle();
    expect(picked, isNull);
    expect(registry.users, hasLength(1), reason: "取消就没有新建");

    await tester.tap(find.text("在这台电脑上新建（不同步）"));
    await tester.pumpAndSettle();
    await tester.tap(find.text("仍要新建"));
    await tester.pumpAndSettle();
    expect(picked?.id, "1001", reason: "编号不复用，取已有最大值加一");
    expect(picked?.isLocal, isTrue);
  });

  testWidgets("没配凭据：本地新建过一次，缓存里的人下次直接进，全程不碰目录（ADR 0124）", (tester) async {
    await open(tester);
    await typeName(tester, "本地新人");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "1000");

    // 重开登录页：缓存命中，直接进。
    picked = null;
    await open(tester);
    await typeName(tester, "本地新人");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "1000");
    expect(directory.calls, 0, reason: "没配凭据，两次进入都没碰目录");
  });

  testWidgets("本地学习者改自己的名字：只写本机缓存，不碰目录（ADR 0123）", (tester) async {
    final me = const UserProfile(id: "1000", name: "本地人");
    registry.remember(me);
    await open(tester, current: me);
    expect(find.text("现在是：本地人（编号 1000）"), findsOneWidget);

    await tester.tap(find.text("改我的名字"));
    await tester.pumpAndSettle();
    await tester.enterText(find.descendant(of: find.byType(AlertDialog), matching: find.byType(TextField)), "离线老司机");
    await tester.tap(find.text("保存"));
    await tester.pumpAndSettle();

    expect(directory.calls, 0, reason: "本地学习者改名不问中心目录");
    expect(registry.byId("1000")?.name, "离线老司机");
    expect(renamed?.name, "离线老司机");
    expect(find.text("现在是：离线老司机（编号 1000）"), findsOneWidget);
  });

  testWidgets("本机有单用户时代的旧记录：登录后问一句归不归他", (tester) async {
    directory.add("tiger");
    await open(tester, legacy: true, remote: true);
    await typeName(tester, "tiger");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(find.text("这台电脑上有一份旧的本地记录"), findsOneWidget);
    expect(picked, isNull);

    await tester.tap(find.text("归到我名下"));
    await tester.pumpAndSettle();
    expect((picked?.id, adopted), ("1", true));
  });

  testWidgets("旧记录选「不用」：照样进入，不认领", (tester) async {
    directory.add("tiger");
    await open(tester, legacy: true, remote: true);
    await typeName(tester, "tiger");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    await tester.tap(find.text("不用"));
    await tester.pumpAndSettle();
    expect((picked?.id, adopted), ("1", false));
  });
}
