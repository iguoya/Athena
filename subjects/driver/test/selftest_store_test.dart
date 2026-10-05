import "dart:io";

import "package:athena_driver/selftest_store.dart";
import "package:flutter_test/flutter_test.dart";

/// 自测的「认得了没有」记录（ADR 0082）：只决定一张卡还出不出，不是掌握度。
void main() {
  late Directory dir;
  setUp(() => dir = Directory.systemTemp.createTempSync("athena-selftest-"));
  tearDown(() => dir.deleteSync(recursive: true));

  test("第一次问就记住算认得，没记住清零，重现后才记住不算认得", () {
    final store = SelfTestStore();
    expect(store.isKnown("signs", "stop"), isFalse);
    expect(store.isLearning("signs", "stop"), isFalse, reason: "没考过不是「没记住过」");

    store.record("signs", "stop", remembered: false, firstTry: true);
    expect(store.isLearning("signs", "stop"), isTrue);
    // 没记住后重现、这次记住了：是被提醒出来的，不算认得。
    store.record("signs", "stop", remembered: true, firstTry: false);
    expect(store.isKnown("signs", "stop"), isFalse);
    expect(store.isLearning("signs", "stop"), isTrue);

    // 下一轮第一次问就记住：认得。
    store.record("signs", "stop", remembered: true, firstTry: true);
    expect(store.isKnown("signs", "stop"), isTrue);
    expect(store.isLearning("signs", "stop"), isFalse);

    // 页与页互不相干。
    expect(store.isKnown("markings", "stop"), isFalse);
    expect(store.knownCount("signs", ["stop", "yield"]), 1);
  });

  test("按学习者落成文件，重开还在；换人是一份空白；重置只清本页", () {
    final tiger = SelfTestStore(user: "tiger", directory: dir.path);
    tiger.record("signs", "stop", remembered: true, firstTry: true);
    tiger.record("gauges", "abs", remembered: false, firstTry: true);

    final again = SelfTestStore(user: "tiger", directory: dir.path);
    expect(again.isKnown("signs", "stop"), isTrue);
    expect(again.isLearning("gauges", "abs"), isTrue);

    expect(SelfTestStore(user: "别人", directory: dir.path).isKnown("signs", "stop"), isFalse);

    again.reset("signs");
    final third = SelfTestStore(user: "tiger", directory: dir.path);
    expect(third.isKnown("signs", "stop"), isFalse);
    expect(third.isLearning("gauges", "abs"), isTrue, reason: "重置只清本页");
  });

  test("文件坏了当空白记录，不抛错；用户名里的非法字符不影响落盘", () {
    File("${dir.path}/selftest-tiger.json").writeAsStringSync("{ 不是 json");
    final store = SelfTestStore(user: "tiger", directory: dir.path);
    expect(store.isKnown("signs", "stop"), isFalse);
    store.record("signs", "stop", remembered: true, firstTry: true);
    expect(SelfTestStore(user: "tiger", directory: dir.path).isKnown("signs", "stop"), isTrue);

    final odd = SelfTestStore(user: r"a/b:c", directory: dir.path);
    odd.record("signs", "stop", remembered: true, firstTry: true);
    expect(SelfTestStore(user: r"a/b:c", directory: dir.path).isKnown("signs", "stop"), isTrue);
  });
}
