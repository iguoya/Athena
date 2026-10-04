import "dart:math";

import "package:flutter/material.dart";
import "package:flutter_test/flutter_test.dart";
import "package:athena_driver/semantic.dart";
import "package:athena_driver/skin.dart";

double _contrast(Color a, Color b) {
  final la = a.computeLuminance();
  final lb = b.computeLuminance();
  return (max(la, lb) + 0.05) / (min(la, lb) + 0.05);
}

void main() {
  // 对比度由 Material 3 方案保证（ADR 0071）；这里守住「换种子色、换变体后仍然成立」。
  test("每个语义色的实心色与浅底都配得上自己的字，对比度不低于 4.5（AA）", () {
    final all = {
      "success": Sem.success,
      "warning": Sem.warning,
      "info": Sem.info,
      "danger": Sem.danger,
      "purple": Sem.purple,
      "teal": Sem.teal,
      "orange": Sem.orange,
      "pink": Sem.pink,
      "neutral": Sem.neutral,
    };
    for (final e in all.entries) {
      expect(_contrast(e.value.color, e.value.onColor), greaterThanOrEqualTo(4.5), reason: "${e.key} 实心色");
      expect(_contrast(e.value.container, e.value.onContainer), greaterThanOrEqualTo(4.5), reason: "${e.key} 浅底");
    }
  });

  test("每套皮肤的主色上能放白字，卡片在页面底上能分得出来", () {
    for (final skin in Skins.all) {
      expect(_contrast(skin.primary, skin.scheme.onPrimary), greaterThanOrEqualTo(4.5), reason: skin.id);
      expect(skin.card, isNot(skin.page), reason: "${skin.id} 卡片底与页面底同色");
    }
  });
}
