import "dart:async";
import "dart:convert";
import "dart:io";

import "package:flutter/foundation.dart";

/// 解释朗读：交互对齐英语应用（系统朗读 / 停止朗读），实现走本机 TTS。
/// Flutter 桌面没有 WebView，不能用英语那套 `speechSynthesis`。

const rateOptions = <(double, String)>[
  (0.7, "慢"),
  (0.86, "稍慢"),
  (1.0, "常速"),
  (1.15, "稍快"),
];

final _better = RegExp(
  r"premium|enhanced|neural|natural|超自然|增强|高级|高音质|优质",
  caseSensitive: false,
);

const _preferZh = [
  "Lilian",
  "Yue",
  "Tingting",
  "Ting-Ting",
  "Ting-ting",
  "Meijia",
  "Sinji",
  "Huihui",
  "Yaoyao",
  "Xiaoxiao",
  "Kangkang",
];

class NativeVoice {
  const NativeVoice({required this.name, required this.lang, this.better = false});

  final String name;
  final String lang;
  final bool better;

  String get label => better ? "$name · 增强" : name;
}

List<NativeVoice> parseSayVoices(String output) {
  final voices = <NativeVoice>[];
  final seen = <String>{};
  for (final line in output.split("\n")) {
    final head = line.split("#").first;
    final parts = [
      for (final part in head.split("  "))
        if (part.trim().isNotEmpty) part.trim(),
    ];
    if (parts.length < 2) continue;
    final name = parts[0];
    final lang = parts[1].replaceAll("_", "-");
    if (!lang.toLowerCase().startsWith("zh")) continue;
    final key = "$name|$lang";
    if (!seen.add(key)) continue;
    voices.add(NativeVoice(name: name, lang: lang, better: _better.hasMatch(name)));
  }
  return rankZhVoices(voices);
}

List<NativeVoice> parseWindowsVoices(String output) {
  final voices = <NativeVoice>[];
  final seen = <String>{};
  for (final line in output.split("\n")) {
    final parts = line.trim().split("|");
    if (parts.length < 2) continue;
    final name = parts[0].trim();
    final lang = parts[1].trim().replaceAll("_", "-");
    if (name.isEmpty || !lang.toLowerCase().startsWith("zh")) continue;
    final key = "$name|$lang";
    if (!seen.add(key)) continue;
    voices.add(NativeVoice(name: name, lang: lang, better: _better.hasMatch(name)));
  }
  return rankZhVoices(voices);
}

List<NativeVoice> rankZhVoices(List<NativeVoice> voices) {
  int rank(NativeVoice voice) {
    if (voice.better) return -100;
    final index = _preferZh.indexWhere(
      (name) => voice.name.toLowerCase().contains(name.toLowerCase()),
    );
    final langBoost = voice.lang.toLowerCase().startsWith("zh-cn") ? 0 : 50;
    return (index < 0 ? 500 : index) + langBoost;
  }

  final copy = [...voices];
  copy.sort((a, b) {
    final byRank = rank(a).compareTo(rank(b));
    if (byRank != 0) return byRank;
    return a.name.compareTo(b.name);
  });
  return copy;
}

class Speaker {
  /// 测试专用：置 true 后 [speak] 直接返回，不起系统朗读进程。否则测试里答错一题就真的调
  /// `say` 出声，还会在假时钟里留下一个没结束的计时器，让测试在收尾时报错。
  @visibleForTesting
  static var muted = false;

  Process? _proc;
  var voiceName = "";
  var rate = 0.86;
  var voices = const <NativeVoice>[];
  var available = false;

  /// 朗读状态：按钮态与「正在朗读…」由它驱动。进程念完（自然退出）也会落回 false，
  /// 不用 UI 层猜时长。
  final ValueNotifier<bool> speaking = ValueNotifier(false);

  Future<void> prepare() async {
    voices = await listVoices();
    available = voices.isNotEmpty || Platform.isMacOS;
    if (voiceName.isEmpty || !voices.any((voice) => voice.name == voiceName)) {
      voiceName = voices.firstOrNull?.name ?? "";
    }
  }

  Future<List<NativeVoice>> listVoices() async {
    if (Platform.isMacOS) {
      final result = await Process.run("say", ["-v", "?"]);
      return parseSayVoices("${result.stdout}");
    }
    if (Platform.isWindows) {
      const script = r"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.GetInstalledVoices() | ForEach-Object { '{0}|{1}' -f $_.VoiceInfo.Name, $_.VoiceInfo.Culture.Name }
""";
      final result = await Process.run("powershell", [
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        script,
      ]);
      return parseWindowsVoices("${result.stdout}");
    }
    return const [];
  }

  Future<void> speak(String text) async {
    if (muted) return;
    await stop();
    final trimmed = text.trim();
    if (trimmed.isEmpty) return;
    final file = File("${Directory.systemTemp.path}/athena-driver-speak.txt");
    await file.writeAsString(trimmed, encoding: utf8);
    try {
      final proc = await _spawn(file.path);
      _proc = proc;
      speaking.value = true;
      // 念完自动落回空闲；新一轮朗读换了进程时，别动它的状态。
      unawaited(proc.exitCode.then((_) {
        if (identical(_proc, proc)) speaking.value = false;
      }));
    } on ProcessException {
      available = false;
    }
  }

  /// 等当前这段念完（被 stop 掉也算完）；没在念就立刻返回。翻页要等它，免得把解释掐断（ADR 0025）。
  Future<void> finished() async {
    final proc = _proc;
    if (proc == null) return;
    try {
      await proc.exitCode;
    } catch (_) {}
  }

  Future<void> stop() async {
    final proc = _proc;
    _proc = null;
    if (proc == null) return;
    proc.kill();
    try {
      await proc.exitCode;
    } catch (_) {}
    speaking.value = false;
  }

  int get _wpm => (175 * rate).clamp(90, 500).round();

  int get _sapiRate => ((rate - 1) * 10).round().clamp(-10, 10);

  Future<Process> _spawn(String path) async {
    if (Platform.isMacOS) {
      final args = <String>["-r", "$_wpm", "-f", path];
      if (voiceName.isNotEmpty) {
        args.insertAll(0, ["-v", voiceName]);
      }
      return Process.start("say", args);
    }
    if (Platform.isWindows) {
      const script = r"""
param($Voice, $Path, $Rate)
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
if ($Voice) { try { $s.SelectVoice($Voice) } catch {} }
$s.Rate = [int]$Rate
$s.Speak([IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8))
""";
      final ps1 = File("${Directory.systemTemp.path}/athena-driver-speak.ps1");
      await ps1.writeAsString(script);
      return Process.start("powershell", [
        "-NoProfile",
        "-NonInteractive",
        // 默认执行策略 Restricted 会拦 .ps1 文件（只放行内联 -Command），
        // 不加这个参数在很多机器上会静默失败——进程正常退出、没有任何报错，
        // 但压根没念出声音。
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        ps1.path,
        "-Voice",
        voiceName,
        "-Path",
        path,
        "-Rate",
        "$_sapiRate",
      ]);
    }
    try {
      return await Process.start("espeak-ng", ["-v", "zh", "-s", "$_wpm", "-f", path]);
    } on ProcessException {
      return Process.start("espeak", ["-v", "zh", "-s", "$_wpm", "-f", path]);
    }
  }
}
