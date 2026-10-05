import "dart:async";

import "package:athena_driver/subject2/drill.dart";
import "package:athena_driver/core/narration.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

/// 可控的朗读器：念什么记下来，什么时候念完由测试说了算。
class FakeNarrator implements Narrator {
  final said = <String>[];
  var stops = 0;
  Completer<void>? _current;

  @override
  bool get available => true;

  @override
  Future<void> prepare() async {}

  @override
  Future<void> say(String text) async {
    finish();
    said.add(text);
    _current = Completer<void>();
  }

  @override
  Future<void> done() => _current?.future ?? Future.value();

  @override
  Future<void> stop() async {
    stops++;
    if (!(_current?.isCompleted ?? true)) _current!.complete();
  }

  void finish() {
    if (!(_current?.isCompleted ?? true)) _current!.complete();
  }
}

void main() {
  // 语音讲解（ADR 0040）：动画播到一步末尾时讲解没念完，就停在末尾等，念完才进下一步。
  testWidgets("讲解没念完动画停在这一步末尾；念完进下一步并开始念下一段；暂停就停念", (tester) async {
    final narrator = FakeNarrator();
    final key = GlobalKey<DrillPlayerState>();
    final lines = [for (var i = 0; i < cornerScene.steps.length; i++) "第${i + 1}步讲解"];
    await tester.binding.setSurfaceSize(const Size(1400, 1000));
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: DrillPlayer(
            key: key,
            scene: cornerScene,
            stepTitles: [for (var i = 0; i < cornerScene.steps.length; i++) "步骤$i"],
            narration: lines,
            cautions: [for (var i = 0; i < cornerScene.steps.length; i++) "注意$i"],
            narrator: narrator,
          ),
        ),
      ),
    );
    await tester.tap(find.byTooltip("播放"));
    await tester.pump();
    expect(narrator.said, ["第1步讲解"]);

    // 第 1 步动画只要 3.9 秒；讲解没念完，播 10 秒也还停在第 1 步。
    for (var i = 0; i < 100; i++) {
      await tester.pump(const Duration(milliseconds: 100));
    }
    final state = key.currentState!;
    expect(Timeline(cornerScene).frame(state.time).step, 0);
    expect(state.playing, isTrue);

    narrator.finish();
    await tester.pump();
    for (var i = 0; i < 5; i++) {
      await tester.pump(const Duration(milliseconds: 100));
    }
    expect(Timeline(cornerScene).frame(state.time).step, 1);
    expect(narrator.said, ["第1步讲解", "第2步讲解"]);

    await tester.tap(find.byTooltip("暂停"));
    await tester.pump();
    expect(narrator.stops, greaterThan(0));
    expect(state.playing, isFalse);

    // 关掉讲解：不再念，动画照常往下走。
    await tester.tap(find.byTooltip("关掉语音讲解"));
    await tester.pump();
    final said = narrator.said.length;
    await tester.tap(find.byTooltip("播放"));
    for (var i = 0; i < 100; i++) {
      await tester.pump(const Duration(milliseconds: 100));
    }
    expect(narrator.said.length, said);
    expect(Timeline(cornerScene).frame(state.time).step, greaterThan(1));
    await tester.pumpWidget(const SizedBox());
  });
}
