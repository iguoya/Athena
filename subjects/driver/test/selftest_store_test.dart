import "dart:io";

import "package:athena_driver/selftest_store.dart";
import "package:flutter_test/flutter_test.dart";

/// 自测的作答记录（ADR 0082、0083，ADR 0085 起记录的是选择题对错）：把每张卡区分成没考过 / 答错过 /
/// 答对过，只管「还出不出」，不是掌握度，也不是「认得」的依据；答对过的以后不再出现（ADR 0090）。
void main() {
  late Directory dir;
  setUp(() => dir = Directory.systemTemp.createTempSync("athena-selftest-"));
  tearDown(() => dir.deleteSync(recursive: true));

  test("第一次问就答对算一次，没答对清零，重现后才答对不算", () {
    final store = SelfTestStore();
    expect(store.isConfirmed("signs", "stop"), isFalse);
    expect(store.isLearning("signs", "stop"), isFalse, reason: "没考过不是「没答对过」");

    store.record("signs", "stop", remembered: false, firstTry: true);
    expect(store.isLearning("signs", "stop"), isTrue);
    // 没答对后重现、这次答对了：是被提醒出来的，不算认得。
    store.record("signs", "stop", remembered: true, firstTry: false);
    expect(store.isConfirmed("signs", "stop"), isFalse);
    expect(store.isLearning("signs", "stop"), isTrue);

    // 下一轮第一次问就答对：这次不再出。
    store.record("signs", "stop", remembered: true, firstTry: true);
    expect(store.isConfirmed("signs", "stop"), isTrue);
    expect(store.isLearning("signs", "stop"), isFalse);

    // 页与页互不相干。
    expect(store.isConfirmed("markings", "stop"), isFalse);
  });

  test("答对的不再出现：隔多久都不回头，只有重置才清掉；答错过的下次再考，第二次答对才算过（ADR 0090）", () {
    var now = DateTime(2026, 10, 1, 9);
    final store = SelfTestStore(clock: () => now);
    store.record("signs", "stop", remembered: true, firstTry: true);
    expect(store.isConfirmed("signs", "stop"), isTrue);

    // 隔一天、一个月、一年，答对过的还是认得，不会按间隔回头出现。
    for (final later in [const Duration(days: 1), const Duration(days: 30), const Duration(days: 400)]) {
      now = now.add(later);
      expect(store.isConfirmed("signs", "stop"), isTrue, reason: "答对的不用在后续测试中出现");
    }

    // 区分三种记录：没考过 / 答错过（下次再考） / 答对过（不再出）。
    expect(store.isLearning("signs", "stop"), isFalse);
    store.record("gauges", "abs", remembered: false, firstTry: true);
    expect(store.isLearning("gauges", "abs"), isTrue, reason: "答错过：下次自测再考");
    expect(store.isConfirmed("gauges", "abs"), isFalse);
    // 下次自测第一次问就答对：从「答错过」变成「答对过」，以后不再出。
    store.record("gauges", "abs", remembered: true, firstTry: true);
    expect(store.isLearning("gauges", "abs"), isFalse);
    expect(store.isConfirmed("gauges", "abs"), isTrue);

    store.reset("signs");
    expect(store.isConfirmed("signs", "stop"), isFalse, reason: "重新自测清掉本页记录");
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

  test("0082 版的老文件没有时间戳：答对过的照样认得，不再出现", () {
    File("${dir.path}/selftest-tiger.json").writeAsStringSync(
      '{"version":1,"pages":{"signs":{"stop":{"c":1,"m":0}}}}',
    );
    final store = SelfTestStore(user: "tiger", directory: dir.path);
    expect(store.isConfirmed("signs", "stop"), isTrue);
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
