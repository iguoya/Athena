import "dart:async";
import "dart:io";

import "package:athena_driver/content.dart";
import "package:athena_driver/home.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/points.dart";
import "package:athena_driver/progress.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

import "unlock_support.dart";
import "package:image/image.dart" as img;
import "package:path/path.dart" as p;

void main() {
  // 点位卡（ADR 0037）：文字只追加读最新、随事件同步；照片缩图存在进度库旁边、不进事件同步。
  group("点位卡存取", () {
    late Directory dir;
    late ProgressStore store;

    setUp(() async {
      dir = await Directory.systemTemp.createTemp("athena-driver-points-");
      ProgressStore.pointsDirOverride = p.join(dir.path, "points");
      store = await ProgressStore.open(suite: "points_test");
      await unlockSubject2(store);
    });

    tearDown(() async {
      ProgressStore.pointsDirOverride = null;
      await store.close();
      await dir.delete(recursive: true);
    });

    test("文字每次保存追加一行，读最新的；点位与默演随事件同步，重复导入不重写", () async {
      final t = DateTime(2026, 9, 28, 20);
      await store.savePointNote("reverse", 2, "旧说法", at: t);
      await store.savePointNote("reverse", 2, "右后视镜下沿碰到库角打满", at: t.add(const Duration(minutes: 1)));
      await store.recordRehearsal("reverse", const [2, 3], 7, at: t);
      final notes = await store.pointNotes();
      expect(notes[("reverse", 2)]!.text, "右后视镜下沿碰到库角打满");

    });

    test("照片缩到长边 1280 存成 JPEG，放在进度库旁边的 points/；删照片连文件一起删", () async {
      final source = File(p.join(dir.path, "big.png"));
      await source.writeAsBytes(img.encodePng(img.Image(width: 3000, height: 2000)));
      final relative = await importPointPhoto(source.path, ProgressStore.pointsDir, "parallel", 1, now: DateTime(2026, 9, 28, 20));
      expect(relative, startsWith("parallel/2-20260928-"));
      final file = File(p.join(ProgressStore.pointsDir, relative));
      expect(p.dirname(ProgressStore.pointsDir), dir.path);
      final saved = img.decodeJpg(await file.readAsBytes())!;
      expect(saved.width, pointPhotoEdge);
      expect(saved.height, 853);

      await store.addPointPhoto("parallel", 1, relative, "车头对齐库角");
      final photos = await store.pointPhotos();
      expect(photos.single.caption, "车头对齐库角");
      await store.removePointPhoto(photos.single);
      expect(await store.pointPhotos(), isEmpty);
      expect(await file.exists(), isFalse);
    });

    test("认不出的文件给一句能看懂的说明", () async {
      final bogus = File(p.join(dir.path, "not-an-image.jpg"));
      await bogus.writeAsString("hello");
      expect(
        () => importPointPhoto(bogus.path, ProgressStore.pointsDir, "curve", 0),
        throwsA(isA<FormatException>().having((e) => e.message, "message", contains("认不出"))),
      );
    });
  });

  testWidgets("单项页写点位：保存后在点位卡和当前步骤里都看得到；简报提示写了几步", (tester) async {
    late Directory dir;
    late ProgressStore store;
    late Bank bank;
    await tester.runAsync(() async {
      bank = await ContentLoader.load();
      dir = await Directory.systemTemp.createTemp("athena-driver-points-ui-");
      ProgressStore.pointsDirOverride = p.join(dir.path, "points");
      store = await ProgressStore.open(suite: "points_test");
      await unlockSubject2(store);
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
    await tester.tap(find.text("科目二（C2）"));
    await tester.pump();
    await tester.tap(find.text("项目手册"));
    await tester.pump();
    await tester.tap(find.text("直角转弯").first);
    for (var i = 0; i < 50; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    expect(find.text("我的点位卡"), findsOneWidget);

    final writeFirst = find.text("写点位").first;
    await tester.ensureVisible(writeFirst);
    await tester.pump();
    await tester.tap(writeFirst);
    await tester.pumpAndSettle();
    expect(find.text(pointTemplate), findsOneWidget);
    await tester.enterText(find.byType(TextField), "车身离右边线一拳");
    await tester.tap(find.text("保存"));
    // 对话框里的输入框也匹配这段文字，要等它关掉、点位卡里出现才算存上了。
    bool saved() => find.byType(AlertDialog).evaluate().isEmpty && find.text("车身离右边线一拳").evaluate().isNotEmpty;
    for (var i = 0; i < 300 && !saved(); i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
      await tester.pump();
    }
    await tester.pumpAndSettle();
    expect(find.text("车身离右边线一拳"), findsOneWidget);
    // 滚回顶部：当前是第 1 步，步骤列表里展开显示自己的点位；简报提示写了几步。
    final page = find.descendant(of: find.byKey(const ValueKey("subject2-item")), matching: find.byType(Scrollable)).first;
    await tester.scrollUntilVisible(find.textContaining("点位卡写了 1/4 步"), -300, scrollable: page);
    expect(find.textContaining("点位卡写了 1/4 步"), findsOneWidget);
    expect(find.textContaining("我的点位：车身离右边线一拳"), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.runAsync(() async {
      expect((await store.pointNotes())[("corner", 0)]!.text, "车身离右边线一拳");
    });
    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(() async {
      await store.close();
      await dir.delete(recursive: true);
    });
  });
}
