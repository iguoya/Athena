import "dart:io";

import "package:athena_driver/api_config_screen.dart";
import "package:athena_driver/sync.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  // 外网访问凭据的 ID 不是邮箱（ADR 0077）：填了邮箱要当场拦住并说清楚，不能悄悄存下来。
  // 注意：只测「被拦住」的分支——它在保存之前就返回，不会写用户真实的 api.json。
  testWidgets("在外网访问凭据里填邮箱：保存和测试连接都被拦住，并说明邮箱不是这里要的东西", (tester) async {
    tester.view.physicalSize = const Size(1200, 1600);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(const ApiConfigScreen(allowSkip: true));

    await tester.enterText(find.widgetWithText(TextField, "外网访问凭据 · Client ID（可选）"), "someone@example.com");
    await tester.enterText(find.widgetWithText(TextField, "外网访问凭据 · Client Secret（可选）"), "secret");

    await tester.tap(find.text("保存并开始同步"));
    await tester.pump();
    expect(find.textContaining("这里填的不是邮箱"), findsOneWidget);
    expect(find.textContaining("服务令牌"), findsWidgets);

    // 测试连接同样先拦住（不会拿邮箱去请求）
    await tester.tap(find.text("测试连接"));
    await tester.pump();
    expect(find.textContaining("这里填的不是邮箱"), findsOneWidget);
    expect(find.textContaining("不是邮箱；是 Cloudflare"), findsOneWidget, reason: "输入框下面也有提示");
  });

  // 「测试连接」内网和外网各测各的、逐行显示；以前内网通了就停，「已连上」不能说明外网也通。
  // 外网访问凭据只发给外网端点。只点「测试连接」，不点保存，不会写用户真实的 api.json。
  testWidgets("测试连接：内网、外网逐行各自的结果；外网凭据只发给外网端点", (tester) async {
    // testWidgets 里 Flutter 会把所有 HTTP 请求换成假的（一律回 400）；这里要连本机真实的小服务，先关掉替换。
    HttpOverrides.global = null;
    late HttpServer lan;
    late HttpServer wan;
    final lanSeen = <String?>[];
    final wanSeen = <String?>[];
    await tester.runAsync(() async {
      lan = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      wan = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      lan.listen((r) {
        lanSeen.add(r.headers.value("CF-Access-Client-Id"));
        r.response
          ..statusCode = 200
          ..write('{"ok":true}')
          ..close();
      });
      wan.listen((r) {
        wanSeen.add(r.headers.value("CF-Access-Client-Id"));
        r.response
          ..statusCode = 302
          ..headers.set("Location", "https://x.cloudflareaccess.com/cdn-cgi/access/login/x")
          ..close();
      });
    });
    addTearDown(() async {
      await lan.close(force: true);
      await wan.close(force: true);
    });
    tester.view.physicalSize = const Size(1200, 1600);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(const ApiConfigScreen(allowSkip: true));

    final lanUrl = "http://127.0.0.1:${lan.port}";
    final wanUrl = "http://127.0.0.1:${wan.port}";
    await tester.enterText(find.widgetWithText(TextField, "内网端点（在家时用）"), lanUrl);
    await tester.enterText(find.widgetWithText(TextField, "外网端点（离开内网时用）"), wanUrl);
    await tester.enterText(find.widgetWithText(TextField, "外网访问凭据 · Client ID（可选）"), "abc.access");
    await tester.enterText(find.widgetWithText(TextField, "外网访问凭据 · Client Secret（可选）"), "s3cret");
    await tester.tap(find.text("测试连接"));
    for (var i = 0; i < 300 && find.textContaining("外网（").evaluate().isEmpty; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 20)));
      await tester.pump();
    }

    expect(find.textContaining("内网（$lanUrl）：已连上"), findsOneWidget);
    expect(find.textContaining("外网（$wanUrl）：被 Cloudflare 访问规则拦住了"), findsOneWidget);
    expect(lanSeen, [null], reason: "外网访问凭据不发给内网地址");
    expect(wanSeen, ["abc.access"]);
  });

  test("外网端点内置默认值：配置里没有、是空串、是 null 都回到默认（只有一个外网域名）", () {
    expect(const ApiConfig().wanBase, ApiConfig.defaultWanBase);
    expect(ApiConfig.fromJson(const {}).wanBase, ApiConfig.defaultWanBase);
    expect(ApiConfig.fromJson(const {"wan_base": null}).wanBase, ApiConfig.defaultWanBase);
    expect(ApiConfig.fromJson(const {"wan_base": "  "}).wanBase, ApiConfig.defaultWanBase);
    expect(ApiConfig.fromJson(const {"wan_base": "https://example.org"}).wanBase, "https://example.org");
    expect(ApiConfig.defaultWanBase, "https://www.yatiger.cn");
    expect(ApiConfig.fromJson(const {"cf_client_id": "a.access"}).cfClientId, "a.access");
  });

  testWidgets("设置页：外网端点框里直接就是内置的地址，不是灰色提示", (tester) async {
    tester.view.physicalSize = const Size(1200, 1600);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(const ApiConfigScreen(allowSkip: true));
    final field = tester.widget<TextField>(find.widgetWithText(TextField, "外网端点（离开内网时用）"));
    expect(field.controller!.text, isNotEmpty, reason: "要有真实的值，不是靠 hintText 假装填了");
  });
}
