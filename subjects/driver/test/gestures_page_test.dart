import "dart:async";
import "dart:io";

import "package:athena_driver/core/content.dart";
import "package:athena_driver/speed/gesture_painter.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/core/models.dart";
import "package:athena_driver/core/progress.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

import "nav_helpers.dart";

void main() {
  // 内容契约（ADR 0073）：json 的每条 id 都要画得出来，含义文案不能缺；
  // 8 个法定动作 + 手势效力总则。
  test("gestures.json 的每条 id 都能画，每条都有含义文案", () async {
    final bank = await ContentLoader.load();
    expect(bank.gestureList.length, 9);
    expect(bank.gestureList.where((g) => g.kind == "action").length, 8);
    for (final gesture in bank.gestureList) {
      expect(paintableGestureIds, contains(gesture.id), reason: "${gesture.id} 没有对应的绘制");
      expect(gesture.meaning, isNotEmpty, reason: "${gesture.id} 缺「看到之后怎么开」的文案");
      expect(gesture.name, isNotEmpty);
    }
  });

  // 反向映射契约：29 道手势题全部挂上、无重复、id 真实存在。
  test("反向映射覆盖全部 29 道手势题", () async {
    final bank = await ContentLoader.load();
    final byId = {for (final q in bank.questions) q.id: q};
    final referenced = <String>[];
    for (final gesture in bank.gestureList) {
      expect(gesture.questions, isNotEmpty, reason: "${gesture.id} 一道相关题都没挂");
      for (final id in gesture.questions) {
        expect(byId, contains(id), reason: "${gesture.id} 映射的题 $id 不在题库里");
        referenced.add(id);
      }
    }
    expect(referenced.toSet().length, referenced.length, reason: "一道题被挂到两个手势下");
    expect(referenced.length, 29);
    expect(
      referenced.where((id) => byId[id]!.prompt.contains("手势")).length,
      29,
      reason: "映射进来的都必须是手势题",
    );
  });

  // 手势速记页：用真实内容渲染一遍，总则卡与动作网格都在。
  testWidgets("手势速记页用真实内容渲染不溢出", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-gestures-");
      store = await ProgressStore.open(suite: "gestures_page_test");
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
    expect(ready.isCompleted, isTrue, reason: "首页没在 20 秒内读完进度库");

    await showTopic(tester, "手势速记");
    await tester.tap(find.text("手势速记").first);
    await tester.pump();
    expect(find.text("手势速记"), findsWidgets);
    expect(find.text("手势的效力"), findsWidgets);
    expect(find.text("8 个法定动作"), findsOneWidget);
    expect(find.textContaining("练手势"), findsNothing, reason: "组里只有自测（ADR 0117）");
    expect(find.text("自测"), findsOneWidget);
    // 高频徽章与方向提醒都在
    expect(find.text("高频"), findsWidgets);
    expect(find.textContaining("他的左右和你看到的相反"), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });

}
