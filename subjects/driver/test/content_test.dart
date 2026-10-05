import "dart:convert";
import "dart:io";
import "dart:math";

import "package:athena_driver/content.dart";
import "package:athena_driver/exam.dart";
import "package:athena_driver/models.dart";
import "package:athena_driver/recall_cards.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  test("课表与题库能从工作目录读出来，知识点对得上", () async {
    final bank = await ContentLoader.load();
    expect(bank.curriculum.subjects, hasLength(3));
    expect(bank.forSubject("subject1"), isNotEmpty);
    expect(bank.forSubject("subject4"), isNotEmpty);
    final topics = {
      for (final subject in bank.curriculum.subjects)
        for (final topic in subject.topics) topic.id,
    };
    for (final question in bank.questions) {
      // 速记题（ADR 0094）故意不在课表里：日常题、章节练习、模拟考、解锁判断都不会带上它。
      if (isRecallQuestionId(question.id)) {
        expect(question.topicId, startsWith(recallTopicPrefix));
        expect(topics.contains(question.topicId), isFalse);
      } else {
        expect(topics, contains(question.topicId));
      }
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
    expect(
      bank.questions.any((q) => q.topicId == "drive.s1.alcohol" && q.prompt.contains("20") && q.prompt.contains("毫克")),
      isTrue,
      reason: "考场高频：饮酒后驾驶血液酒精含量从 20 毫克/100 毫升起算",
    );
  });

  test("用真实题库组科目一模拟考：六个内容块和题型配比都抽得满", () async {
    final bank = await ContentLoader.load();
    final rules = bank.curriculum.subject("subject1").exam!;
    expect(rules.blocks.values.fold(0, (a, b) => a + b), rules.questionCount);
    final paper = Paper.draw(bank.forSubject("subject1"), rules, Random(7));
    expect(paper.questions, hasLength(rules.questionCount));
    for (final entry in rules.blocks.entries) {
      expect(paper.questions.where((q) => rules.blockOf(q) == entry.key).length, entry.value, reason: entry.key);
    }
    expect(paper.fullBank, isTrue);
    // 每道科目一题都要能归到一块，不然组卷时会漏在所有格子之外。
    for (final q in bank.forSubject("subject1")) {
      expect(rules.blockOf(q), isNotNull, reason: q.id);
    }
  });

  test("易混数字每组都找得到相关题，每行都有登记过的出处（ADR 0028）", () async {
    final bank = await ContentLoader.load();
    expect(bank.cheatsheet, isNotEmpty);
    final catalog = jsonDecode(File("content/sources/catalog.json").readAsStringSync()) as Map<String, dynamic>;
    final sources = {for (final s in catalog["sources"] as List<dynamic>) (s as Map<String, dynamic>)["id"] as String};
    for (final group in bank.cheatsheet) {
      expect(group.related(bank.forSubject("subject1")), isNotEmpty, reason: group.id);
      for (final row in group.rows) {
        expect(sources, contains(row.sourceId), reason: "${group.id} ${row.value}");
        expect(row.locator, isNotEmpty, reason: "${group.id} ${row.value}");
      }
    }
  });

  test("content 下每个 JSON 都登记进了 pubspec 的 assets——漏了开发时照常、打包副本读不到", () {
    final pubspec = File("pubspec.yaml").readAsStringSync();
    final listed = {
      for (final line in const LineSplitter().convert(pubspec))
        if (line.trim().startsWith("- content/")) line.trim().substring(2),
    };
    final files = Directory("content")
        .listSync(recursive: true)
        .whereType<File>()
        .map((f) => f.path.replaceAll("\\", "/"))
        .where((p) => p.endsWith(".json"));
    for (final path in files) {
      final covered = listed.contains(path) || listed.any((dir) => dir.endsWith("/") && path.startsWith(dir));
      expect(covered, isTrue, reason: "$path 没登记进 pubspec.yaml 的 assets");
    }
  });

  test("每道题的稳定编号都不重复，去掉了 drive. 前缀", () async {
    final bank = await ContentLoader.load();
    final serials = [for (final q in bank.questions) q.serial];
    expect(serials.toSet().length, serials.length);
    expect(serials.every((s) => !s.startsWith("drive.") && s.contains(".")), isTrue);
    expect(bank.byId("drive.s1.signals.207").serial, "s1.signals.207");
  });

  test("科目一、科目四的解释不能只剩条文号——答错会朗读解释，念一个条号没有教学价值（ADR 0055）", () async {
    final bank = await ContentLoader.load();
    // 把条文号、法规名、标准号、标点剥掉，剩下的才是「讲了什么」。
    final citation = RegExp(
      r"GA ?1026|GB ?\d+(\.\d+)?(—\d+)?|GA ?\d+|第?[0-9一二三四五六七八九十百]+(条|款|项|号令?)|"
      r"实施条例|条例|道路交通安全法|刑法|《[^》]*》|公安部令?|令|表\s?\d+|第|条|款|项|附录[A-Z]?|"
      r"[（）()、，,。.\s\-—:：和及的]",
    );
    final bare = [
      for (final q in bank.questions)
        if (q.id.startsWith("drive.s1.") || q.id.startsWith("drive.s4."))
          if (q.explain.replaceAll(citation, "").length < 6) q.id,
    ];
    expect(bare, isEmpty, reason: "解释只有条文号：$bare");
  });

  test("叫法统一：科目三是路考、科目四是安全文明驾驶常识，题面不用合称、解释不用缩写（ADR 0056）", () async {
    final bank = await ContentLoader.load();
    // 规章原文把两部分合称「科目三」，只允许出现在引用的条文里，题面和解释里不写。
    final merged = RegExp(
      r"科目三(?:（[^）]*）|道路驾驶技能)?[和、及与]?(?:道路驾驶技能[和、及与])?安全文明驾驶常识",
    );
    final slang = RegExp(r"科[二三四]");
    final bad = <String>[];
    for (final q in bank.questions) {
      if (!q.id.startsWith("drive.s1.") && !q.id.startsWith("drive.s4.")) continue;
      final stem = "${q.prompt}${q.choices.map((c) => c.label).join()}";
      if (merged.hasMatch(stem) || slang.hasMatch(q.explain)) bad.add(q.id);
    }
    expect(bad, isEmpty, reason: "出现了科目三合称或科二科三缩写：$bad");
  });
}
