import "package:athena_driving/content.dart";
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
    }
  });
}
