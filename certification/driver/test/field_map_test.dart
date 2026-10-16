import "dart:ui" as ui;

import "package:athena_driver/subject2/field_map.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  test("倒车入库草表是 7 步，右倒打满、入库回正、左倒方向相反", () {
    expect(reverseParkSketch, hasLength(7));
    expect(reverseParkSketch[0].steerDegrees, 0);
    expect(reverseParkSketch[1].steerDegrees, greaterThan(0));
    expect(reverseParkSketch[4].steerDegrees, 0);
    expect(reverseParkSketch[4].heading, closeTo(-pi / 2, 1e-9));
    expect(reverseParkSketch[6].steerDegrees, lessThan(0));
    expect(reverseParkSketch[2].marks, isNotEmpty);
  });

  test("七步都能画完", () {
    for (final step in reverseParkSketch) {
      final recorder = ui.PictureRecorder();
      FieldMapPainter(step).paint(Canvas(recorder), const Size(480, 320));
      recorder.endRecording().dispose();
    }
  });

  testWidgets("换步会换一幅图", (tester) async {
    Future<void> show(int index) {
      return tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SizedBox(
              width: 480,
              height: 320,
              child: FieldMap(steps: reverseParkSketch, index: index),
            ),
          ),
        ),
      );
    }

    await show(0);
    final first = _painter(tester);
    expect(first.step.x, reverseParkSketch[0].x);

    await show(4);
    final parked = _painter(tester);
    expect(parked.step.heading, reverseParkSketch[4].heading);
    expect(parked.shouldRepaint(first), isTrue);
    expect(tester.takeException(), isNull);
  });
}

const pi = 3.141592653589793;

FieldMapPainter _painter(WidgetTester tester) {
  final paint = find.descendant(
    of: find.byType(FieldMap),
    matching: find.byType(CustomPaint),
  );
  return tester.widget<CustomPaint>(paint).painter! as FieldMapPainter;
}
