import "dart:io";

import "package:athena_driver/main.dart";
import "package:athena_driver/user_directory.dart";
import "package:athena_driver/users.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

/// 内存版目录：与 nas_admin/user_api 同一套语义。登录页的流程测试不碰网络。
class FakeDirectory implements UserDirectory {
  final List<UserProfile> rows = [];
  int calls = 0;

  /// 为真时所有调用都像网络不通。
  bool down = false;

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

  Future<void> open(
    WidgetTester tester, {
    UserProfile? current,
    bool legacy = false,
  }) async {
    tester.view.physicalSize = const Size(1200, 1600);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(
      home: UserGateScreen(
        registry: registry,
        directoryFactory: () => directory,
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

  testWidgets("本机没有这个名字：问中心目录，找到一个就进并记进缓存", (tester) async {
    directory.add("tiger");
    await open(tester);
    await typeName(tester, "Tiger");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "1");
    expect(registry.byId("1")?.name, "tiger");
  });

  testWidgets("名字没人用过：点「进入」就直接新建并进入，不弹窗、不用另找按钮（ADR 0078）", (tester) async {
    await open(tester);
    await typeName(tester, "新人");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "1");
    expect(createdFlag, isTrue, reason: "告诉启动门这是新建的，进入后用提示条说编号");
    expect(directory.rows.single.name, "新人");
    expect(registry.byId("1")?.name, "新人");
    expect(find.byType(AlertDialog), findsNothing, reason: "编号不再弹窗拦人");
  });

  testWidgets("已有的人点「进入」不会被当成新建", (tester) async {
    directory.add("小王");
    await open(tester);
    await typeName(tester, "小王");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(createdFlag, isFalse);
    expect(directory.rows, hasLength(1));
  });

  testWidgets("名字和编号对不上不会自动新建（只有「没有这个名字」才新建）", (tester) async {
    directory.add("小王");
    directory.add("小王");
    await open(tester);
    await typeName(tester, "小王");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    await tester.enterText(find.widgetWithText(TextField, "学习者编号（1～999）"), "9");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked, isNull);
    expect(directory.rows, hasLength(2), reason: "没有因为对不上就新建第三个");
  });

  testWidgets("重名：再问学习者编号，输对才进，输错不进（ADR 0075 决策 2）", (tester) async {
    directory.add("小王");
    directory.add("小王");
    await open(tester);
    await typeName(tester, "小王");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked, isNull);
    expect(find.text("学习者编号（1～999）"), findsOneWidget);

    await tester.enterText(find.widgetWithText(TextField, "学习者编号（1～999）"), "9");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked, isNull);
    expect(find.textContaining("名字和编号对不上"), findsOneWidget);

    await tester.enterText(find.widgetWithText(TextField, "学习者编号（1～999）"), "2");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "2");
  });

  testWidgets("显式新建（同名的另一个人）：名字没人用时直接新建进入，没有编号弹窗", (tester) async {
    await open(tester);
    await typeName(tester, "新人");
    await tester.tap(find.text("我是另一个同名的人，新建"));
    await tester.pumpAndSettle();
    expect(find.byType(AlertDialog), findsNothing);
    expect((picked?.id, createdFlag), ("1", true));
  });

  testWidgets("名字已有人用：新建前先确认，取消就不新建", (tester) async {
    directory.add("小王");
    await open(tester);
    await typeName(tester, "小王");
    await tester.tap(find.text("我是另一个同名的人，新建"));
    await tester.pumpAndSettle();
    expect(find.text("已有同名的学习者"), findsOneWidget);

    await tester.tap(find.text("取消"));
    await tester.pumpAndSettle();
    expect(directory.rows, hasLength(1));
    expect(picked, isNull);
  });

  testWidgets("名字已有人用：确认后仍可新建，重名靠编号区分", (tester) async {
    directory.add("小王");
    await open(tester);
    await typeName(tester, "小王");
    await tester.tap(find.text("我是另一个同名的人，新建"));
    await tester.pumpAndSettle();
    await tester.tap(find.text("仍要新建"));
    await tester.pumpAndSettle();
    expect((picked?.id, createdFlag), ("2", true));
    expect(directory.rows, hasLength(2));
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

  testWidgets("连不上目录：新建说明原因，页面有同步设置入口；本机用过的人仍能直接进", (tester) async {
    registry.remember(const UserProfile(id: "3", name: "小王"));
    directory.down = true;
    await open(tester);
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

  testWidgets("本机有单用户时代的旧记录：登录后问一句归不归他", (tester) async {
    directory.add("tiger");
    await open(tester, legacy: true);
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
    await open(tester, legacy: true);
    await typeName(tester, "tiger");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    await tester.tap(find.text("不用"));
    await tester.pumpAndSettle();
    expect((picked?.id, adopted), ("1", false));
  });
}
