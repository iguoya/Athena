import "dart:convert";
import "dart:io";

import "package:athena_driver/core/progress.dart";
import "package:athena_driver/subject2/guide.dart";
import "package:athena_driver/subject2/points.dart";
import "package:athena_driver/subject2/review.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";
import "package:image/image.dart" as img;
import "package:path/path.dart" as p;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group("点位命中与照片标注", () {
    late Directory dir;
    late ProgressStore store;

    setUp(() async {
      dir = await Directory.systemTemp.createTemp("athena-driver-hit-");
      ProgressStore.pointsDirOverride = p.join(dir.path, "points");
      store = await ProgressStore.open(suite: "point_feedback_test");
    });

    tearDown(() async {
      ProgressStore.pointsDirOverride = null;
      await store.close();
      if (dir.existsSync()) await dir.delete(recursive: true);
    });

    test("命中写进练车记录，不进同步队列；拉回同一把不冲掉本地标注", () async {
      final at = DateTime.utc(2026, 10, 21, 1, 2, 3);
      await store.recordDrillRun("reverse", const ["stop"], at: at, pointHit: "early");
      await store.recordDrillRun("reverse", const [], at: at.add(const Duration(milliseconds: 1)));
      final runs = await store.drillRuns();
      expect(runs.first.pointHit, isNull);
      expect(runs[1].pointHit, "early");
      expect(pointHitLabel(runs[1].pointHit), "偏早");

      final queued = store.outboxBatch("drill-runs");
      expect(queued, hasLength(2));
      for (final entry in queued) {
        expect(entry.payload.containsKey("point_hit"), isFalse);
      }

      store.applyRemote("drill-runs", [
        {"item_id": "reverse", "mistakes": "stop", "at": at.toIso8601String()},
      ]);
      final again = await store.drillRuns();
      expect(again.last.pointHit, "early");
    });

    test("照片标注跟清单走，旧清单没有 marks 时读成空", () async {
      final manifest = File(p.join(ProgressStore.pointsDir, "photos.json"));
      manifest.parent.createSync(recursive: true);
      manifest.writeAsStringSync("""
[
  {
    "item_id": "parallel",
    "step": 1,
    "file": "parallel/old.jpg",
    "caption": "旧照片",
    "at": "2026-10-01T00:00:00.000"
  }
]
""");
      final loaded = await store.pointPhotos();
      expect(loaded.single.marks, isEmpty);

      await store.savePointPhotoMarks("parallel/old.jpg", const [
        PhotoMark(type: "point", label: "库角", x: 0.25, y: 0.5),
      ]);
      final saved = await store.pointPhotos();
      expect(saved.single.marks.single.label, "库角");
      expect(saved.single.marks.single.x, 0.25);
      expect(manifest.readAsStringSync(), contains("库角"));
      expect(store.outboxBatch("drill-runs"), isEmpty);
    });
  });

  testWidgets("复盘每一把一点即可标点位，点位卡显示最近三次", (tester) async {
    late ProgressStore store;
    late Subject2Guide guide;
    await tester.runAsync(() async {
      final raw = jsonDecode(await File("content/subject2.json").readAsString());
      guide = Subject2Guide.fromJson(raw as Map<String, dynamic>);
      store = await ProgressStore.open(suite: "point_feedback_review");
    });
    await tester.binding.setSurfaceSize(const Size(1400, 1600));
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => DayReview(guide: guide, store: store),
                  ),
                );
              },
              child: const Text("打开复盘"),
            ),
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.tap(find.text("打开复盘"));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    await tester.tap(find.widgetWithText(FilterChip, "倒车入库"));
    await tester.pump();
    await tester.tap(find.byKey(const ValueKey("review-hit-reverse-0-early")));
    await tester.pump();
    expect(find.widgetWithText(ChoiceChip, "偏早"), findsWidgets);

    await tester.tap(find.text("保存今天 3 把"));
    for (var i = 0; i < 100 && find.byType(DayReview).evaluate().isNotEmpty; i++) {
      await tester.pump(const Duration(milliseconds: 20));
    }
    late List<DrillRun> runs;
    await tester.runAsync(() async {
      runs = await store.drillRuns();
    });
    final mine = runs.where((r) => r.itemId == "reverse").toList().reversed.toList();
    expect(mine.first.pointHit, "early");
    expect(mine[1].pointHit, isNull);

    await tester.pumpWidget(
      MaterialApp(
        home: PointCards(
          item: guide.item("reverse")!,
          store: store,
          notes: const {},
          photos: const [],
          onChanged: () async {},
          recentHits: recentPointHits(runs, "reverse"),
        ),
      ),
    );
    await tester.pump();
    expect(find.text("最近点位：偏早"), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
    await tester.runAsync(store.close);
  });

  testWidgets("标注照优先于通用素材，宽窄两档都画得出标签", (tester) async {
    late Directory dir;
    late String relative;
    await tester.runAsync(() async {
      dir = await Directory.systemTemp.createTemp("athena-driver-mark-");
      ProgressStore.pointsDirOverride = p.join(dir.path, "points");
      final source = File(p.join(dir.path, "shot.jpg"));
      await source.writeAsBytes(img.encodeJpg(img.Image(width: 80, height: 60)));
      relative = await importPointPhoto(
        source.path,
        ProgressStore.pointsDir,
        "reverse",
        0,
        now: DateTime(2026, 10, 21, 9),
      );
    });
    final photo = PointPhoto(
      itemId: "reverse",
      step: 0,
      file: relative,
      caption: "我的车",
      at: DateTime(2026, 10, 21, 9),
      marks: const [PhotoMark(type: "point", label: "库角", x: 0.4, y: 0.6)],
    );
    final generic = StepShot(
      file: "missing.png",
      kind: "image",
      view: "车内",
      caption: "通用素材不该出现",
      note: "",
      marks: const [],
    );

    Future<void> pump(Size size) async {
      await tester.binding.setSurfaceSize(size);
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RepaintBoundary(
              key: const ValueKey("shot-photo"),
              child: StepVisual(media: [generic], annotated: [photo]),
            ),
          ),
        ),
      );
      await tester.pump();
    }

    await pump(const Size(1200, 700));
    expect(find.textContaining("我的参照物：库角"), findsOneWidget);
    expect(find.text("通用素材不该出现"), findsNothing);

    await pump(const Size(420, 800));
    expect(find.textContaining("我的参照物：库角"), findsOneWidget);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PointMarkEditor(
            photo: PointPhoto(
              itemId: photo.itemId,
              step: photo.step,
              file: photo.file,
              caption: photo.caption,
              at: photo.at,
            ),
            onSave: (marks) async {
              expect(marks, hasLength(1));
              expect(marks.single.label, "库角");
              expect(marks.single.x, closeTo(0.5, 0.15));
              expect(marks.single.y, closeTo(0.5, 0.15));
            },
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.enterText(find.byKey(const ValueKey("photo-mark-label")), "库角");
    await tester.tap(find.byKey(const ValueKey("photo-mark-surface")));
    await tester.pump();
    await tester.tap(find.byKey(const ValueKey("photo-mark-save")));
    await tester.pump();

    ProgressStore.pointsDirOverride = null;
    await tester.runAsync(() async {
      if (dir.existsSync()) await dir.delete(recursive: true);
    });
  });
}
