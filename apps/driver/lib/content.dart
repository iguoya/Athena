import "dart:convert";
import "dart:io";

import "package:flutter/services.dart";
import "package:path/path.dart" as p;

import "models.dart";

class ContentLoader {
  static Future<Bank> load() async {
    final curriculum = Curriculum.fromJson(
      jsonDecode(await _read("curriculum.json")) as Map<String, dynamic>,
    );
    final questions = <Question>[
      ..._questionsOf(await _read("questions/subject1.json")),
      ..._questionsOf(await _read("questions/subject4.json")),
    ];
    return Bank(curriculum: curriculum, questions: questions);
  }

  static List<Question> _questionsOf(String raw) {
    final data = jsonDecode(raw) as Map<String, dynamic>;
    return [
      for (final item in data["questions"] as List<dynamic>)
        Question.fromJson(item as Map<String, dynamic>),
    ];
  }

  static Future<String> _read(String relative) async {
    final env = Platform.environment["ATHENA_DRIVING_ROOT"];
    final candidates = <String>[
      if (env != null && env.isNotEmpty) p.join(env, "content", relative),
      p.join(Directory.current.path, "content", relative),
    ];
    for (final path in candidates) {
      final file = File(path);
      if (file.existsSync()) return file.readAsString();
    }
    return rootBundle.loadString("content/$relative");
  }
}
