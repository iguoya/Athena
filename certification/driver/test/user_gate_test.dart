import "dart:io";

import "package:athena_driver/app/user_gate_screen.dart";
import "package:athena_driver/core/users.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

/// 登录页（ADR 0075、0127）：学习者一律先在本机创建，页面不碰网络，也不出现「同步」概念。
void main() {
  late Directory dir;
  late UserRegistry registry;
  UserProfile? picked;
  bool? adopted;
  bool? createdFlag;
  UserProfile? renamed;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp("athena-driver-gate-");
    UserRegistry.fileOverride = "${dir.path}${Platform.pathSeparator}users.json";
    registry = UserRegistry.load();
    picked = adopted = createdFlag = renamed = null;
  });

  tearDown(() async {
    UserRegistry.fileOverride = null;
    await dir.delete(recursive: true);
  });

  Future<void> open(WidgetTester tester, {UserProfile? current, bool legacy = false}) async {
    tester.view.physicalSize = const Size(1200, 1600);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(
      home: UserGateScreen(
        registry: registry,
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

  testWidgets("名字在本机缓存里唯一命中：直接进", (tester) async {
    registry.remember(const UserProfile(id: "3", name: "小王"));
    await open(tester);
    await typeName(tester, "小王");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "3");
    expect(createdFlag, isFalse);
  });

  testWidgets("本机没有的名字：直接在本机新建（编号 1000 起），不弹任何确认", (tester) async {
    await open(tester);
    await typeName(tester, "新人");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "1000");
    expect(picked?.isLocal, isTrue);
    expect(createdFlag, isTrue);
    expect(find.byType(AlertDialog), findsNothing);
    expect(registry.byId("1000")?.name, "新人", reason: "记进本机缓存，下次直接进");
  });

  testWidgets("再新建一位：编号取已有最大值加一，不复用", (tester) async {
    registry.remember(const UserProfile(id: "1000", name: "老王"));
    await open(tester);
    await typeName(tester, "小李");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "1001");
  });

  testWidgets("新建过一次，下次再进是登录而不是再新建", (tester) async {
    await open(tester);
    await typeName(tester, "新人");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "1000");

    picked = null;
    await open(tester);
    await typeName(tester, "新人");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect((picked?.id, createdFlag), ("1000", false));
    expect(registry.users, hasLength(1));
  });

  testWidgets("显式新建：没有同名的人时直接新建", (tester) async {
    await open(tester);
    await typeName(tester, "新人");
    await tester.tap(find.text("我是另一个同名的人，新建"));
    await tester.pumpAndSettle();
    expect(find.byType(AlertDialog), findsNothing);
    expect((picked?.id, createdFlag), ("1000", true));
  });

  testWidgets("显式新建：本机已有同名，先确认；取消就不建", (tester) async {
    registry.remember(const UserProfile(id: "3", name: "小王"));
    await open(tester);
    await typeName(tester, "小王");
    await tester.tap(find.text("我是另一个同名的人，新建"));
    await tester.pumpAndSettle();
    expect(find.text("这台电脑上已有同名的学习者"), findsOneWidget);

    await tester.tap(find.text("取消"));
    await tester.pumpAndSettle();
    expect(picked, isNull);
    expect(registry.users, hasLength(1));
  });

  testWidgets("显式新建：本机已有同名，确认后新建，两个人靠编号区分", (tester) async {
    registry.remember(const UserProfile(id: "3", name: "小王"));
    await open(tester);
    await typeName(tester, "小王");
    await tester.tap(find.text("我是另一个同名的人，新建"));
    await tester.pumpAndSettle();
    await tester.tap(find.text("仍要新建"));
    await tester.pumpAndSettle();
    expect((picked?.id, createdFlag), ("1000", true));
    expect(registry.users, hasLength(2));
  });

  testWidgets("本机有重名的人：再问学习者编号，输对才进，输错不进", (tester) async {
    registry.remember(const UserProfile(id: "1000", name: "小王"));
    registry.remember(const UserProfile(id: "1001", name: "小王"));
    await open(tester);
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
    expect(registry.users, hasLength(2), reason: "对不上也不会顺手新建第三个");

    await tester.enterText(find.widgetWithText(TextField, "学习者编号"), "1001");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    expect(picked?.id, "1001");
  });

  testWidgets("没有当前学习者时没有改名入口", (tester) async {
    registry.remember(const UserProfile(id: "1", name: "tiger"));
    await open(tester);
    expect(find.text("改我的名字"), findsNothing);
  });

  testWidgets("改自己的名字：只写本机缓存并通知回调", (tester) async {
    const me = UserProfile(id: "1000", name: "本地人");
    registry.remember(me);
    await open(tester, current: me);
    expect(find.text("现在是：本地人（编号 1000）"), findsOneWidget);

    await tester.tap(find.text("改我的名字"));
    await tester.pumpAndSettle();
    await tester.enterText(find.descendant(of: find.byType(AlertDialog), matching: find.byType(TextField)), "老司机");
    await tester.tap(find.text("保存"));
    await tester.pumpAndSettle();

    expect(registry.byId("1000")?.name, "老司机");
    expect(renamed?.name, "老司机");
    expect(find.text("现在是：老司机（编号 1000）"), findsOneWidget);
  });

  testWidgets("改名不动已绑定的中心编号", (tester) async {
    registry.remember(const UserProfile(id: "1000", name: "本地人"));
    registry.bindServerId("1000", "7");
    final me = registry.byId("1000")!;
    await open(tester, current: me);

    await tester.tap(find.text("改我的名字"));
    await tester.pumpAndSettle();
    await tester.enterText(find.descendant(of: find.byType(AlertDialog), matching: find.byType(TextField)), "老司机");
    await tester.tap(find.text("保存"));
    await tester.pumpAndSettle();

    expect(registry.byId("1000")?.serverId, "7");
  });

  testWidgets("本机有单用户时代的旧记录：登录后问一句归不归他", (tester) async {
    registry.remember(const UserProfile(id: "1", name: "tiger"));
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
    registry.remember(const UserProfile(id: "1", name: "tiger"));
    await open(tester, legacy: true);
    await typeName(tester, "tiger");
    await tester.tap(find.text("进入"));
    await tester.pumpAndSettle();
    await tester.tap(find.text("不用"));
    await tester.pumpAndSettle();
    expect((picked?.id, adopted), ("1", false));
  });

  testWidgets("页面里没有同步、服务器、设置这类概念（ADR 0127）", (tester) async {
    registry.remember(const UserProfile(id: "1000", name: "老王"));
    await open(tester, current: registry.byId("1000"));
    expect(find.textContaining("同步"), findsNothing);
    expect(find.textContaining("服务器"), findsNothing);
    expect(find.textContaining("设置"), findsNothing);
    expect(find.textContaining("联网"), findsNothing);
  });
}
