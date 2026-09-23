import "package:athena_driver/speak.dart";
import "package:flutter_test/flutter_test.dart";

void main() {
  test("解析 say -v 的中文语音，增强音色排前面", () {
    const output = """
Tingting            zh_CN    # 你好，我叫婷婷。
Lilian (Premium)    zh_CN    # 你好！我叫黎潋。
Meijia              zh_TW    # 你好，我叫美佳。
Samantha            en_US    # Hello! My name is Samantha.
""";
    final voices = parseSayVoices(output);
    expect(voices.map((voice) => voice.name), ["Lilian (Premium)", "Tingting", "Meijia"]);
    expect(voices.first.better, isTrue);
  });

  test("Windows 音色按语言过滤", () {
    const output = """
Microsoft Huihui Desktop|zh-CN
Microsoft David Desktop|en-US
Microsoft Yaoyao Desktop|zh-CN
""";
    final voices = parseWindowsVoices(output);
    expect(voices.map((voice) => voice.name), [
      "Microsoft Huihui Desktop",
      "Microsoft Yaoyao Desktop",
    ]);
  });
}
