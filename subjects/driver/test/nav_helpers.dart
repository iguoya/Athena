import "package:athena_driver/speed_topics.dart";
import "package:flutter_test/flutter_test.dart";

/// 侧栏里的专题默认折叠在分组下（ADR 0109）：点专题之前先把它所在的分组展开。
/// 已经看得见（分组已展开）就什么也不做；只展开科目一的组（`.first`）。
Future<void> showTopic(WidgetTester tester, String title) async {
  Future<void> reveal() async {
    await tester.ensureVisible(find.text(title).first);
    await tester.pump(const Duration(milliseconds: 400));
  }

  if (find.text(title).evaluate().isNotEmpty) return reveal();
  for (final group in speedGroups) {
    final header = find.textContaining("${group.title} · ");
    if (header.evaluate().isEmpty) continue;
    await tester.ensureVisible(header.first);
    await tester.tap(header.first);
    await tester.pump(const Duration(milliseconds: 400)); // 科目分支是 AnimatedSize，等它长到位
    await tester.pump(const Duration(milliseconds: 400));
    if (find.text(title).evaluate().isNotEmpty) return reveal();
    // 没在这一组里：折回去，免得越展越长。
    await tester.tap(header.first);
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pump(const Duration(milliseconds: 400));
  }
}
