import "dart:io";

import "package:athena_driver/selftest_store.dart";
import "package:flutter_test/flutter_test.dart";

/// 自测的自评记录（ADR 0082、0083）：只管「这段时间还出不出」，不是掌握度，
/// 也不是「认得」的依据；自评认得的条目按 1 / 3 / 7 / 21 天的间隔回头考。
void main() {
  late Directory dir;
  setUp(() => dir = Directory.systemTemp.createTempSync("athena-selftest-"));
  tearDown(() => dir.deleteSync(recursive: true));

  test("第一次问就记住算自评认得，没记住清零，重现后才记住不算", () {
    final store = SelfTestStore();
    expect(store.isConfirmed("signs", "stop"), isFalse);
    expect(store.isLearning("signs", "stop"), isFalse, reason: "没考过不是「没记住过」");

    store.record("signs", "stop", remembered: false, firstTry: true);
    expect(store.isLearning("signs", "stop"), isTrue);
    // 没记住后重现、这次记住了：是被提醒出来的，不算认得。
    store.record("signs", "stop", remembered: true, firstTry: false);
    expect(store.isConfirmed("signs", "stop"), isFalse);
    expect(store.isLearning("signs", "stop"), isTrue);

    // 下一轮第一次问就记住：自评认得。
    store.record("signs", "stop", remembered: true, firstTry: true);
    expect(store.isConfirmed("signs", "stop"), isTrue);
    expect(store.isLearning("signs", "stop"), isFalse);

    // 页与页互不相干。
    expect(store.isConfirmed("markings", "stop"), isFalse);
  });

  test("间隔复现：1 天后到期重考，再次一次记住升级、间隔拉长到 3、7、21 天", () {
    var now = DateTime(2026, 10, 1, 9);
    final store = SelfTestStore(clock: () => now);
    store.record("signs", "stop", remembered: true, firstTry: true);
    expect(store.isConfirmed("signs", "stop"), isTrue);

    now = now.add(const Duration(hours: 23));
    expect(store.isConfirmed("signs", "stop"), isTrue, reason: "第 1 级间隔是 1 天，23 小时内还不用考");
    now = now.add(const Duration(hours: 2));
    expect(store.isConfirmed("signs", "stop"), isFalse);
    expect(store.isOverdue("signs", "stop"), isTrue, reason: "到期：该再考一次确认还记得");

    // 到期后再次一次就记住：升到第 2 级，间隔 3 天。
    store.record("signs", "stop", remembered: true, firstTry: true);
    now = now.add(const Duration(days: 2, hours: 23));
    expect(store.isConfirmed("signs", "stop"), isTrue);
    now = now.add(const Duration(hours: 2));
    expect(store.isOverdue("signs", "stop"), isTrue);

    // 到期后没记住：清零，成了「没记住过」，不再算到期。
    store.record("signs", "stop", remembered: false, firstTry: true);
    expect(store.isOverdue("signs", "stop"), isFalse);
    expect(store.isLearning("signs", "stop"), isTrue);

    expect([for (var s = 1; s <= 6; s++) SelfTestStore.daysForStage(s)], [1, 3, 7, 21, 21, 21], reason: "阶梯封顶");
  });

  test("按学习者落成文件，重开还在；换人是一份空白；重置只清本页", () {
    final tiger = SelfTestStore(user: "tiger", directory: dir.path);
    tiger.record("signs", "stop", remembered: true, firstTry: true);
    tiger.record("gauges", "abs", remembered: false, firstTry: true);

    final again = SelfTestStore(user: "tiger", directory: dir.path);
    expect(again.isConfirmed("signs", "stop"), isTrue);
    expect(again.isLearning("gauges", "abs"), isTrue);

    expect(SelfTestStore(user: "别人", directory: dir.path).isConfirmed("signs", "stop"), isFalse);

    again.reset("signs");
    final third = SelfTestStore(user: "tiger", directory: dir.path);
    expect(third.isConfirmed("signs", "stop"), isFalse);
    expect(third.isLearning("gauges", "abs"), isTrue, reason: "重置只清本页");
  });

  test("0082 版的老文件没有时间戳：认得过的条目当作很久以前，到期重考一次", () {
    File("${dir.path}/selftest-tiger.json").writeAsStringSync(
      '{"version":1,"pages":{"signs":{"stop":{"c":1,"m":0}}}}',
    );
    final store = SelfTestStore(user: "tiger", directory: dir.path);
    expect(store.isConfirmed("signs", "stop"), isFalse);
    expect(store.isOverdue("signs", "stop"), isTrue);
  });

  test("文件坏了当空白记录，不抛错；用户名里的非法字符不影响落盘", () {
    File("${dir.path}/selftest-tiger.json").writeAsStringSync("{ 不是 json");
    final store = SelfTestStore(user: "tiger", directory: dir.path);
    expect(store.isConfirmed("signs", "stop"), isFalse);
    store.record("signs", "stop", remembered: true, firstTry: true);
    expect(SelfTestStore(user: "tiger", directory: dir.path).isConfirmed("signs", "stop"), isTrue);

    final odd = SelfTestStore(user: r"a/b:c", directory: dir.path);
    odd.record("signs", "stop", remembered: true, firstTry: true);
    expect(SelfTestStore(user: r"a/b:c", directory: dir.path).isConfirmed("signs", "stop"), isTrue);
  });
}
