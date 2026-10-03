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

  UserProfile add(String name) {
    final profile = UserProfile(id: "${rows.length + 1}", name: name);
    rows.add(profile);
    return profile;
  }

  @override
  Future<UserProfile> login(String name, {String? id}) async {
    calls++;
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
    return add(name.trim());
  }

  @override
  Future<UserProfile> rename(String id, String name) async {
    calls++;
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
  UserProfile? renamed;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp("athena-driver-gate-");
    UserRegistry.fileOverride = "${dir.path}${Platform.pathSeparator}users.json";
    registry = UserRegistry.load();
    directory = FakeDirectory();
    picked = adopted = renamed = null;
  });

  tearDown(() async {
    UserRegistry.fileOverride = null;
    await dir.delete(recursive: true);
  });

  Future<void> open(
    WidgetTester tester, {
    UserProfile? current,
    bool legacy = false,
    bool configured = true,
  }) async {
    tester.view.physicalSize = const Size(1200, 1600);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(
      home: UserGateScreen(
        registry: registry,
        directoryFactory: () => configured ? directory : null,
        currentUser: current,
        legacyPending: legacy,
        onPicked: (profile, adopt) {
          picked = profile;
          adopted = adopt;
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

  testWidgets("目录里没有这个名字：提示可以新建，不会自动新建", (tester) async {
    await open(tester);
    await typeName(tester, "新人");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked, isNull);
    expect(find.textContaining("点「新建学习者」"), findsOneWidget);
    expect(directory.rows, isEmpty);
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

  testWidgets("新建：分到编号后显著展示，点「知道了」才进入", (tester) async {
    await open(tester);
    await typeName(tester, "新人");
    await tester.tap(find.text("新建学习者"));
    await tester.pumpAndSettle();
    expect(find.text("你的学习者编号是 1"), findsOneWidget);
    expect(picked, isNull);

    await tester.tap(find.text("知道了"));
    await tester.pumpAndSettle();
    expect(picked?.id, "1");
    expect(registry.byId("1")?.name, "新人");
  });

  testWidgets("名字已有人用：新建前先确认，取消就不新建", (tester) async {
    directory.add("小王");
    await open(tester);
    await typeName(tester, "小王");
    await tester.tap(find.text("新建学习者"));
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
    await tester.tap(find.text("新建学习者"));
    await tester.pumpAndSettle();
    await tester.tap(find.text("仍要新建"));
    await tester.pumpAndSettle();
    expect(find.text("你的学习者编号是 2"), findsOneWidget);
    await tester.tap(find.text("知道了"));
    await tester.pumpAndSettle();
    expect(picked?.id, "2");
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

  testWidgets("没配设备令牌：给出配置入口；要联网的动作说明原因", (tester) async {
    await open(tester, configured: false);
    expect(find.text("配置同步"), findsOneWidget);
    await typeName(tester, "新人");
    await tester.tap(find.text("新建学习者"));
    await tester.pumpAndSettle();
    expect(find.textContaining("还没有配置同步设备令牌"), findsWidgets);
    expect(picked, isNull);
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
