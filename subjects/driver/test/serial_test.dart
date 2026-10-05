import "package:athena_driver/ui/look.dart";
import "package:flutter/material.dart";
import "package:flutter/services.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  testWidgets("题目编号点一下复制到剪贴板，并提示已复制", (tester) async {
    String? copied;
    tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, (call) async {
      if (call.method == "Clipboard.setData") copied = (call.arguments as Map)["text"] as String;
      return null;
    });
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: Center(child: SerialBadge("s1.signals.207")))));
    expect(find.text("s1.signals.207"), findsOneWidget);
    await tester.tap(find.text("s1.signals.207"));
    await tester.pump();
    expect(copied, "s1.signals.207");
    expect(find.text("已复制题目编号 s1.signals.207"), findsOneWidget);
  });
}
