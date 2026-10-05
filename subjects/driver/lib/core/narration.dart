import "dart:async";
import "dart:io";

import "speak.dart";
/// 动画讲解的朗读（ADR 0040）。播放器只认这个接口：真机走系统 TTS，测试换成可控的假实现。
abstract class Narrator {
  /// 准备好以后能不能念（没有中文语音就不能）。
  bool get available;

  Future<void> prepare();

  /// 开始念一段；上一段没念完就掐掉。
  Future<void> say(String text);

  /// 当前这段念完（或被掐掉）时完成；没在念就立刻完成。
  Future<void> done();

  Future<void> stop();
}

/// 系统 TTS：跟科目一念解释是同一个 [Speaker]。
class SpeakerNarrator implements Narrator {
  final _speaker = Speaker();

  @override
  bool get available => _speaker.available;

  @override
  Future<void> prepare() => _speaker.prepare();

  @override
  Future<void> say(String text) => _speaker.speak(text);

  @override
  Future<void> done() => _speaker.finished();

  @override
  Future<void> stop() => _speaker.stop();
}

/// 界面默认用的朗读器。跑 `flutter test` 时不起系统 TTS 进程——测试里的朗读由测试自己注入。
Narrator? defaultNarrator() => Platform.environment.containsKey("FLUTTER_TEST") ? null : SpeakerNarrator();
