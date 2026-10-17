import "dart:convert";
import "dart:io";

import "package:athena_driver/core/content.dart";
import "package:athena_driver/subject2/guide.dart";
import "package:athena_driver/subject2/step_media.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

const _png =
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";

void main() {
  test("标记打在 contain 之后的画面上，不打在留白上", () {
    final fitted = fittedImageRect(const Size(200, 100), const Size(100, 100));
    expect(fitted, const Rect.fromLTWH(50, 0, 100, 100));
    const mark = StepMark(type: "point", label: "库角", x: 0.5, y: 0.5);
    expect(mark.at(fitted), const Offset(100, 50));
    const line = StepMark(
      type: "line",
      label: "库口",
      x1: 0,
      y1: 1,
      x2: 1,
      y2: 0,
    );
    expect(line.from(fitted), const Offset(50, 100));
    expect(line.to(fitted), const Offset(150, 0));
  });

  test("素材按步骤号挂上，缺项和缺步都当没有", () async {
    final bank = await ContentLoader.load();
    final attached = bank.guide.withMedia({
      "reverse": {
        "3": [
          {
            "file": "images/subject2/reverse/03.jpg",
            "kind": "image",
            "view": "右后视镜",
            "caption": "库角刚到镜边",
            "note": "示例：点位以你自己的车为准",
            "marks": [
              {"type": "point", "x": 0.4, "y": 0.6, "label": "库角"},
            ],
          },
        ],
      },
    });
    expect(attached.item("reverse")!.steps[2].media, hasLength(1));
    expect(attached.item("reverse")!.steps[2].media.first.view, "右后视镜");
    expect(attached.item("reverse")!.steps[0].media, isEmpty);
    expect(attached.item("corner")!.steps.first.media, isEmpty);
  });

  testWidgets("静图叠标记，缺图降级，动图也能挂上", (tester) async {
    final dir = Directory.systemTemp.createTempSync("athena-driver-media-");
    final image = File("${dir.path}/content/images/fixture.png");
    image.parent.createSync(recursive: true);
    image.writeAsBytesSync(base64Decode(_png));
    final gif = File("${dir.path}/content/images/fixture.gif");
    gif.writeAsBytesSync(_gif);
    final previous = ContentLoader.contentRoot;
    ContentLoader.contentRoot = dir.path;
    addTearDown(() => ContentLoader.contentRoot = previous);

    const shot = StepShot(
      file: "images/fixture.png",
      kind: "image",
      view: "右后视镜",
      caption: "库角刚到镜边",
      note: "示例：点位以你自己的车为准",
      marks: [StepMark(type: "point", label: "库角", x: 0.5, y: 0.5)],
    );
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: StepMedia(shots: [shot])),
      ),
    );
    await tester.pump();
    expect(find.text("右后视镜 · 库角刚到镜边"), findsOneWidget);
    expect(find.text("示例：点位以你自己的车为准"), findsOneWidget);
    expect(find.text("这张图读不到"), findsNothing);

    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: StepMedia(
            shots: [
              StepShot(
                file: "images/missing.png",
                kind: "image",
                view: "左后视镜",
                caption: "没有这张",
                note: "",
                marks: [],
              ),
            ],
          ),
        ),
      ),
    );
    await tester.pump();
    expect(find.text("这张图读不到"), findsOneWidget);
    expect(find.text("左后视镜 · 没有这张"), findsOneWidget);

    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: StepMedia(
            shots: [
              StepShot(
                file: "images/fixture.gif",
                kind: "gif",
                view: "车头",
                caption: "动图",
                note: "",
                marks: [],
              ),
            ],
          ),
        ),
      ),
    );
    await tester.pump();
    expect(find.text("车头 · 动图"), findsOneWidget);
    expect(tester.takeException(), isNull);

    dir.deleteSync(recursive: true);
  });
}

/// 1×1 的最小 GIF，帧延时 100ms。
final _gif = [
  0x47,
  0x49,
  0x46,
  0x38,
  0x39,
  0x61,
  0x01,
  0x00,
  0x01,
  0x00,
  0x80,
  0x00,
  0x00,
  0xff,
  0xff,
  0xff,
  0x00,
  0x00,
  0x00,
  0x21,
  0xf9,
  0x04,
  0x00,
  0x0a,
  0x00,
  0x00,
  0x00,
  0x2c,
  0x00,
  0x00,
  0x00,
  0x00,
  0x01,
  0x00,
  0x01,
  0x00,
  0x00,
  0x02,
  0x02,
  0x44,
  0x01,
  0x00,
  0x3b,
];
