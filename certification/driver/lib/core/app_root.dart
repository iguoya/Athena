import "dart:io";

import "package:path/path.dart" as p;

/// 工作树里的应用根（有 `app.json` 的那一级）；拿不到工作树的发行副本返回 null。
///
/// 依次看 `ATHENA_DRIVER_ROOT`、当前目录、可执行文件往上的各级目录。最后一条不能省：
/// 从程序坞、访达或资源管理器直接点开 `build/` 下的调试包时，既没有环境变量，
/// 当前目录也是 `/`——只认前两条的话，这个窗口会悄悄换用用户数据目录那份进度库
/// 和打包时的旧题库，答过的题在另一个窗口里就成了没答过（ADR 0030）。
String? workingTreeRoot() {
  final env = Platform.environment["ATHENA_DRIVER_ROOT"];
  final candidates = <String>[
    if (env != null && env.isNotEmpty) env,
    Directory.current.path,
  ];
  var dir = p.dirname(Platform.resolvedExecutable);
  while (true) {
    candidates.add(dir);
    final parent = p.dirname(dir);
    if (parent == dir) break;
    dir = parent;
  }
  for (final base in candidates) {
    if (File(p.join(base, "app.json")).existsSync() && Directory(p.join(base, "content")).existsSync()) {
      return base;
    }
  }
  return null;
}
