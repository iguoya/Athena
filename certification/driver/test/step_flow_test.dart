import "package:athena_driver/subject2/guide.dart";
import "package:athena_driver/subject2/step_flow.dart";
import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";

GuideStep _fullStep() => const GuideStep(
  title: "找打方向时机",
  body: "一把匀速打满，中途不停顿不回补。",
  steer: "内角与门把手平齐，立刻向右打满。",
  reference: "右后视镜里内角与门把手的关系。",
  skill: "车慢方向快。",
  fix: [
    StepFix(sign: "打早了内后轮逼内角", action: "回半圈等车头甩过来再补"),
  ],
  caution: "眼看要压线就停，停车扣 10 分强过压线不合格。",
  cautionLocators: ["GA 1026—2022 6.2.3.1"],
  inside: StepInside(
    look: "右镜里线与车角",
    wrong: "别盯着车头盖",
    action: "向右打满",
  ),
  outside: StepOutside(focus: "内角与车身的相对位置", risk: "后轮碰库角"),
  done: "方向打满，车速压住。",
);

const GuideStep _bareStep = GuideStep(title: "回正出弯", body: "平行即回正。");

Widget _host(List<GuideStep> steps, int current, ValueChanged<int> onChanged) =>
    MaterialApp(
      home: Scaffold(
        body: SingleChildScrollView(
          child: StepFlow(
            steps: steps,
            current: current,
            onStepChanged: onChanged,
          ),
        ),
      ),
    );

void main() {
  testWidgets("当前步一屏讲完：双视角、方向盘与参照、警示区、注意条全部可见", (tester) async {
    await tester.pumpWidget(_host([_fullStep(), _bareStep], 0, (_) {}));
    for (final text in [
      "第 1 步 · 找打方向时机",
      "车外 · 盯哪",
      "内角与车身的相对位置",
      "要防：后轮碰库角",
      "车内 · 手脚",
      "盯：右镜里线与车角",
      "做：向右打满",
      "别按这个来：别盯着车头盖",
      "方向盘",
      "内角与门把手平齐，立刻向右打满。",
      "参照",
      "技巧：车慢方向快。",
      "偏了怎么修",
      "迹象：打早了内后轮逼内角 → 回半圈等车头甩过来再补",
      "做完：方向打满，车速压住。",
      "注意",
      "GA 1026—2022 6.2.3.1",
    ]) {
      expect(find.text(text), findsOneWidget, reason: "缺文本：$text");
    }
  });

  testWidgets("步骤条选步回调目标步下标", (tester) async {
    var selected = -1;
    await tester.pumpWidget(_host([_fullStep(), _bareStep], 0, (i) => selected = i));
    await tester.tap(find.text("2"));
    expect(selected, 1);
  });

  testWidgets("没写的字段不占版面", (tester) async {
    await tester.pumpWidget(_host([_bareStep], 0, (_) {}));
    expect(find.text("方向盘"), findsNothing);
    expect(find.text("参照"), findsNothing);
    expect(find.text("偏了怎么修"), findsNothing);
    expect(find.text("注意"), findsNothing);
    expect(find.text("车外 · 盯哪"), findsNothing);
    expect(find.text("车内 · 手脚"), findsNothing);
  });

  testWidgets("窄屏双视角纵向堆叠，两卡都完整可见", (tester) async {
    tester.view.physicalSize = const Size(400, 1600);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(_host([_fullStep()], 0, (_) {}));
    expect(find.text("车外 · 盯哪"), findsOneWidget);
    expect(find.text("车内 · 手脚"), findsOneWidget);
    final outside = tester.getTopLeft(find.text("车外 · 盯哪")).dy;
    final inside = tester.getTopLeft(find.text("车内 · 手脚")).dy;
    expect(inside, greaterThan(outside), reason: "窄屏应纵向堆叠");
  });
}
