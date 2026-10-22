# Whisper 转写可行性实测（zcode，2026-10-22）

对象：翁恺《C 语言》B 站转载版（BV1Ls411w7rx）P2，478 秒，本机 Windows 11 / Python 3.14 / CPU。
结论：**可行**。全链路（B 站拉音频 → 本机转写）一次跑通，small 模型约 3 倍实时速，中文讲课
文本近乎全对，常见英文术语识别正常，生僻英文词会错；132 集全量转写约 6–7 小时机时，可分批做。

## 环境与命令

```sh
pip install faster-whisper yt-dlp "av<15"   # av<15 装不上，见坑 1，可不装
yt-dlp -f "ba/b" -o "weng-p2.%(ext)s" --no-playlist "https://www.bilibili.com/video/BV1Ls411w7rx?p=2"
ffmpeg -i weng-p2.m4a -ar 16000 -ac 1 weng-p2-16k.wav    # ffmpeg 用的 Octave 自带的
python - <<'PY'    # 核心：喂 numpy 数组，绕开 PyAV 解码
import wave, numpy as np
w = wave.open('weng-p2-16k.wav','rb')
audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)/32768.0
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
segs, info = model.transcribe(audio, language='zh', vad_filter=True)
PY
```

- 音频拉流：未登录成功，格式 30280（音频流），7.3 MiB / 478 s。
- 模型：`small`（int8 量化），首次下载 31 s（HuggingFace，网络快）。
- **转写耗时 156.5 s / 477 s 音频 ≈ 0.33×（约 3 倍实时）**，纯 CPU。243 段，2310 字。
- 推算全量：132 集约 1163 分钟音频 → small 约 6.5 小时机时；medium 约 4 倍于此。建议
  small 起步全量转，重点集（暂停点密集的）用 medium 复核。

## 踩坑记录（正式管线要规避）

1. **av 19.0.2 与 faster-whisper 1.2.1 不兼容**：`decode_audio` 用了 `av.open(...,
   metadata_errors=...)`，该参数在 PyAV 15+ 已移除；而 Python 3.14 只有 av 19 有预编译
   wheel，`pip install "av<15"` 会触发源码编译 FFmpeg 绑定然后失败。**解法如上命令**：
   ffmpeg 先转 16 kHz wav，numpy 数组直接喂 `transcribe()`，完全绕开 PyAV。若以后换
   Python ≤3.12 的环境，可直接钉 `av==14.*` 省掉转码一步。
2. B 站页面会自动开播（SPIKE 里也发现了），yt-dlp 拉流不受影响。

## 质量样例

B 站转载版**无字幕可对照**（claude 先前已核对），以下 10 行是转写原样输出，可疑处随行标注：

```
[   4.2] 计算机是我们的生活必需品
[  11.2] 你都有意无意的在使用计算机或者在使用计算机给你提供的服务
[  18.2] ATM是一台计算机
[  37.2] 我们想的是去哪找一个APP                      ← APP 识别正确
[ 100.2] 那我可能会跟这个Whiter说                     ← 应为 waiter（餐厅点菜比喻），错
[ 111.2] 当然他Whiter就知道说                         ← 同上
[ 190.2] What to do
[ 198.2] How to do
[ 260.2] 你 double click                              ← double click 识别正确
[ 325.2] 具体一开始CFFA                               ← 生僻缩写，不可靠
```

- **中文讲课文本**：通顺、标点合理、近零错误（抽读全篇 243 段未见中文错词）。
- **英文**：高频词（APP、ATM、double click、What to do）全对；低频词会拼错（waiter→
  Whiter）。对 C 课的代码念白（printf、scanf、include 是高频重复词）预期能识别，但 P2
  是导论课没有代码念白——**这项要在有代码的集（如 P10 以后）里补一次验证再下结论**。
- VAD 过滤有效：片头片尾静音没有产生碎段。

## 对设计的含义（接 DESIGN-v2 第 6 节）

1. 转写文本可入库：一集约 2300 字、132 集合计约 30 万字，体积无压力；按 ADR 0159 公域
   数据直接进仓库，文件头标注生成方式（模型、命令、日期、来源视频 URL）。
2. 转写是**参考层**：可搜、点句跳时间，但不作教学正文、不作出处（出处仍是课件页码）。
3. 节拍草案可以用它自动推：转写段落边界 + 课件页边界 → 节拍草案（REVIEW-DESIGN-v2 第 3
   节的建议），「边看边标」只做校正。
4. 本机 audio 文件不入库（体积），转写脚本入库、产物按需再生成。
