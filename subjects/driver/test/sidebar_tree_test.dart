import "dart:async";
import "dart:io";

import "package:athena_driver/core/content.dart";
import "package:athena_driver/ui/glyphs.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

/// 侧栏按科目分目录（ADR 0050）：章节挂在所属科目底下，箭头只展开 / 收起，锁着的科目没有子项；
/// 跨科目入口钉在底部（ADR 0051）。
void main() {
  testWidgets("科目一的章节挂在科目一和科目二之间，收起后不见，锁着的科目没有箭头，错题本和考前复习钉在底部", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-tree-");
      store = await ProgressStore.open(suite: "sidebar_tree_test");
    });
    await tester.binding.setSurfaceSize(const Size(1600, 2600));
    final ready = Completer<void>();
    await tester.pumpWidget(
      MaterialApp(home: HomePage(bank: bank, store: store, onReady: ready.complete)),
    );
    for (var i = 0; i < 2000 && !ready.isCompleted; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(ready.isCompleted, isTrue);

    // 主区的科目一概览也列章节，只在侧栏里找。
    Finder inSidebar(Finder f) => find.descendant(of: find.byType(ListView).first, matching: f);
    final firstTopic = bank.curriculum.subject("subject1").topics.first.title;
    final topic = inSidebar(find.textContaining(firstTopic));

    expect(topic, findsOneWidget, reason: "科目一默认展开");
    final y = tester.getCenter(topic).dy;
    expect(y, greaterThan(tester.getCenter(inSidebar(find.text("科目一"))).dy));
    expect(y, lessThan(tester.getCenter(inSidebar(find.text("科目二（未解锁）"))).dy));
    expect(inSidebar(find.text("模拟考试")), findsOneWidget);

    // 新库里科目二、科目四都锁着：整个侧栏只有科目一一个箭头。
    expect(find.byIcon(Glyph.collapse), findsOneWidget);
    expect(find.byIcon(Glyph.expand), findsNothing);

    await tester.tap(find.byIcon(Glyph.collapse));
    await tester.pump();
    expect(topic, findsNothing);
    expect(inSidebar(find.text("模拟考试")), findsNothing);
    expect(find.byIcon(Glyph.expand), findsOneWidget);

    await tester.tap(find.byIcon(Glyph.expand));
    await tester.pump();
    expect(topic, findsOneWidget);

    // 矮窗口里科目一的章节放不下，错题本、考前复习仍钉在底部看得见、点得到（ADR 0051）。
    await tester.binding.setSurfaceSize(const Size(1600, 600));
    await tester.pump();
    for (final entry in ["错题本", "考前复习"]) {
      final f = find.textContaining(entry);
      expect(f, findsOneWidget);
      expect(tester.getBottomLeft(f).dy, lessThanOrEqualTo(600));
    }
    await tester.tap(find.textContaining("考前复习"));
    await tester.pump();
    // 新库没有累计答错的题，这一页显示空状态；断言「页面确实打开了」，不依赖作答数据。
    expect(find.textContaining("还没有累计答错"), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
