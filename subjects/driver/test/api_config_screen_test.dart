import "package:athena_driver/main.dart";
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
}
