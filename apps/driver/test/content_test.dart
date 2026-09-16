import "dart:io";

import "package:athena_driver/content.dart";
import "package:athena_driver/models.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  test("课表与题库能从工作目录读出来，知识点对得上", () async {
    final bank = await ContentLoader.load();
    expect(bank.curriculum.subjects, hasLength(2));
    expect(bank.forSubject("subject1"), isNotEmpty);
    expect(bank.forSubject("subject4"), isNotEmpty);
    final topics = {
      for (final subject in bank.curriculum.subjects)
        for (final topic in subject.topics) topic.id,
    };
    for (final question in bank.questions) {
      expect(topics, contains(question.topicId));
      expect(question.choices.where((c) => c.ok), isNotEmpty);
      expect(question.sourceRefs, isNotEmpty);
      for (final ref in question.sourceRefs) {
        expect(ref.url, isNotEmpty);
        expect(ref.sourceId, isNotEmpty);
        // 条号只有核对过才写（ADR 0008），所以 locator 可以空；
        // 但条文内容不能空，否则学习页的依据栏没东西可显示。
        expect(
          ref.locator.isNotEmpty || ref.note.isNotEmpty,
          isTrue,
          reason: "${question.id} 的出处既没有条号也没有条文",
        );
      }
    }
    // 题图要能在工作树里找到：contentRoot 记的是应用根，不是 content 目录，
    // 从文件路径倒推会算成 content/content/…
    final withImage = bank.questions.where((q) => q.image != null).toList();
    expect(withImage, isNotEmpty);
    for (final question in withImage) {
      expect(
        File(ContentLoader.imagePath(question.image!)).existsSync(),
        isTrue,
        reason: "${question.id} 的题图找不到：${ContentLoader.imagePath(question.image!)}",
      );
    }
    expect(bank.forSubject("subject1").length, greaterThanOrEqualTo(150));
    expect(bank.forSubject("subject4").length, greaterThanOrEqualTo(60));
    expect(bank.curriculum.subject("subject1").phases, hasLength(4));
    expect({for (final q in bank.forSubject("subject1")) q.phase}, equals({1, 2, 3, 4}));
    expect(unlockedThrough(bank.forSubject("subject1"), {}), 1);
    expect(allMastered(bank.forSubject("subject1"), {}), isFalse);
    expect(bank.byId("drive.s1.signals.020").phase, 3);
    expect(bank.byId("drive.s1.signals.020").isHot, isTrue);
    expect(bank.byId("drive.s1.license.008").isRare, isTrue);
    expect(bank.byId("drive.s1.highway.002").isRare, isTrue);
    expect(bank.byId("drive.s4.crash.007").isRare, isTrue);
    expect(dailyQuestions(bank.questions).any((q) => q.isRare), isFalse);
    expect(
      bank.questions.any((q) => q.prompt.contains("下图表示？") || q.prompt.contains("下图所示标志属于哪一类")),
      isFalse,
      reason: "不靠看图认名字、认类别凑题",
    );
    for (final question in bank.questions) {
      expect(QuestionBand.labels.containsKey(question.band), isTrue, reason: question.id);
    }
    final sample = bank.byId("drive.s1.license.001");
    expect(sample.speakText.startsWith(sample.explain), isTrue);
    expect(sample.speakText, contains("应当依法取得机动车驾驶证"));
    expect(sample.speakText.indexOf(sample.explain), lessThan(sample.speakText.indexOf("应当依法取得机动车驾驶证")));
  });
}
