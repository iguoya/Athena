import "dart:convert";
import "dart:io";

import "package:flutter/services.dart";
import "package:path/path.dart" as p;

import "models.dart";

class ContentLoader {
  /// 读到内容的那个根目录；开发时是工作树，发行包里为空（走 assets）。
  static String? contentRoot;

  /// 题图要么在磁盘上（开发），要么打进 assets（发行）——两条路径都从这里给出。
  static String imagePath(String relative) {
    final root = contentRoot;
    return root == null ? "content/$relative" : p.join(root, "content", relative);
  }

  static bool get imagesOnDisk => contentRoot != null;

  static Future<Bank> load() async {
    final curriculum = Curriculum.fromJson(
      jsonDecode(await _read("curriculum.json")) as Map<String, dynamic>,
    );
    final signs = _signsOf(await _read("signs.json"));
    final seen = <String>{};
    final questions = <Question>[
      for (final question in [
        ..._questionsOf(await _read("questions/subject1.json")),
        ..._questionsOf(await _read("questions/subject4.json")),
      ])
        if (seen.add(question.id)) question,
    ];
    return Bank(curriculum: curriculum, questions: questions, signs: signs);
  }

  static List<RoadSign> _signsOf(String raw) {
    final data = jsonDecode(raw) as Map<String, dynamic>;
    return [
      for (final item in data["signs"] as List<dynamic>)
        RoadSign.fromJson(item as Map<String, dynamic>),
    ];
  }

  static List<Question> _questionsOf(String raw) {
    final data = jsonDecode(raw) as Map<String, dynamic>;
    return [
      for (final item in data["questions"] as List<dynamic>)
        Question.fromJson(item as Map<String, dynamic>),
    ];
  }

  static Future<String> _read(String relative) async {
    final env = Platform.environment["ATHENA_DRIVER_ROOT"];
    final candidates = <String>[
      if (env != null && env.isNotEmpty) p.join(env, "content", relative),
      p.join(Directory.current.path, "content", relative),
    ];
    for (final path in candidates) {
      try {
        final file = File(path);
        if (await file.exists()) {
          contentRoot = p.dirname(p.dirname(path));
          return await file.readAsString();
        }
      } on FileSystemException {
        // macOS 开着 App Sandbox 时文件看得到但读会被拒，改走下一候选或 assets。
        continue;
      }
    }
    return rootBundle.loadString("content/$relative");
  }
}
