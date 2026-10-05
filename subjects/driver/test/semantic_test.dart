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
  // 语义色的对比度由固定种子经 fromSeed 生成（ADR 0071 决策 4）；皮肤氛围色已改回
  // 手写色板（ADR 0081），对比度不再由方案保证，由这里的断言守。
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

  test("每套皮肤的主色配得上 onPrimary 的字，卡片在页面底上分得出来", () {
    for (final skin in Skins.all) {
      expect(_contrast(skin.primary, skin.scheme.onPrimary), greaterThanOrEqualTo(4.5), reason: skin.id);
      expect(skin.card, isNot(skin.page), reason: "${skin.id} 卡片底与页面底同色");
    }
  });

  // ADR 0081：四套皮肤里只有暮汐是深色（夜学），页面底必须是真正的深色，
  // 不然「深色皮肤」名不副实；其余三套是明色。
  test("明暗档位：只有暮汐是深色，且页面底是真正的深色", () {
    for (final skin in Skins.all) {
      if (skin.id == "violet") {
        expect(skin.scheme.brightness, Brightness.dark);
        expect(skin.page.computeLuminance(), lessThan(0.2), reason: "暮汐页面底不够深");
      } else {
        expect(skin.scheme.brightness, Brightness.light, reason: skin.id);
      }
    }
  });
}
