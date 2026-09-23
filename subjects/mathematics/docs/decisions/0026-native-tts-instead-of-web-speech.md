# ADR 0026：朗读改走系统 TTS，不用 WebView 的 Web Speech API

- 日期：2026-09-14
- 状态：已接受
- 修正：ADR 0018（语音与脚本动画）的实现手段，教学用途不变
- 依赖：ADR 0025（Rust 侧管一个不做业务的进程，同一套做法）

## 背景

使用者反复说「语音改了没生效」。查下来，前两轮的修复方向全是错的，而且错得
很彻底。

### 1. 实测：桌面应用只看得见两个中文语音

让应用把自己看到的语音表打进 `tauri dev` 的日志（`report_env` 命令）：

```
[env] 语音 2 个，高音质 0 个；当前「Tingting」；全部：Meijia[zh-TW] / Tingting[zh-CN]
```

同一台机器，同一时刻：

| 环境 | 中文语音数 | 高音质 |
|---|---|---|
| Chromium（开发时用来核对的） | **20** | 2（黎潋、月） |
| **WKWebView（应用真正跑的地方）** | **2** | **0** |
| `say -v '?'`（系统本身） | 21 | 2（Lilian (Premium)、Yue (Premium)） |

**WKWebView 只暴露 Meijia 和 Tingting 两个老语音**——使用者下载的 Premium
拿不到，连 Shelley、Sandy、Flo、Eddy 这些系统自带的新语音也拿不到。

### 2. 因此前两轮修复是空转

- ADR 0018 时期那次「认出中文系统上的高音质语音」，把正则补上「高音质/优质/
  neural」——**在应用里毫无作用**，因为那两个语音根本不在列表里。当时的「实测
  枚举」是在浏览器里做的，不是在 WKWebView 里。
- 这次又改了两轮（语音表迟到时重画侧边栏、先认 voice 再定 lang），同样没碰到
  真正的原因。

**教训写在这里**：开发时手边的浏览器和应用真正跑的 WebView 是两个环境，涉及
系统能力（语音、媒体、剪贴板、文件）时，**不能拿浏览器的结果替应用下结论**。
`report_env` 这个命令保留下来，就是为了下次不用再猜。

### 3. 绕不过去

这不是配置问题。WKWebView 的 Web Speech 实现只挂着一小撮内置语音，Tauri 没有
开关能让它多看见几个。要用上系统里那些语音，只能不走 Web Speech。

## 决策

### 1. 朗读改由 Rust 侧调用 macOS 的 `say`

已实测：`say -v Lilian`、`say -v Yue` 都能正常合成（各约 54 KB 音频），
`-r` 能调语速。

- Rust 提供 `speak_native(text, voice, rate)` 与 `stop_native()`。
- **同一时刻只允许一个朗读进程**：新的一句先杀掉上一句，对应 Web Speech 的
  `cancel()`。
- 进程退出即朗读结束，前端据此串起「念完一段再念下一段」。
- 语音列表也改由 Rust 从 `say -v '?'` 解析后给前端，不再用
  `speechSynthesis.getVoices()`。

这与 ADR 0025 是同一套做法：**Rust 侧管一个不做业务的进程**。区别是符号引擎要
常驻（`import sympy` 太贵），而 `say` 启动很轻，每句一个进程即可。

### 2. Web Speech 留作非 macOS 的回退

Linux 上没有 `say`。前端先问 Rust 要原生语音列表，拿不到就退回
`speechSynthesis`。两条路的接口保持一致，页面代码不关心走的是哪条。

> **2026-09-15 复核：这个「回退」在 Windows 上恐怕不够，本节的判断需要扩展。**
>
> 本 ADR 的全部论据是「WKWebView 只看得见 2 个中文语音」——那是 macOS 特有的
> 限制，所以当时把其余平台一律归为「退回 Web Speech 即可」。但 Windows 上
> Tauri 用的是 WebView2，它有一个**性质相同的已知问题**：
> `speechSynthesis.getVoices()` 拿不到微软的 Natural voices，尽管同一台机器上
> 的 Edge 浏览器拿得到（WebView2Feedback #2660）。
>
> 也就是说 macOS 与 Windows 撞的是同一类墙——**宿主 WebView 只暴露一部分系统
> 语音**——只是成因不同。按 ADR 0051 的平台优先级（macOS ≈ Windows > Linux），
> Windows 也该有原生实现，而不是停在回退上。
>
> 代码层面目前是安全的：`tts_voices` 在没有 `say` 的平台上返回空，
> `useNative` 置 false，页面照常走 Web Speech，不崩也不报错
> （`mathematics（windows-latest）` 的 cargo check 一直是绿的）。所以这不是
> bug，是**功能在优先平台上的缺口**。
>
> 真要补，Windows 侧的选择不止一个，且各有代价：PowerShell 的
> `System.Speech.Synthesis` 最简单，但它走 SAPI5，同样拿不到 Natural voices；
> 要拿到好语音得用 WinRT 的 `Windows.Media.SpeechSynthesis`，那是另一套依赖。
> **先别动手**——按本 ADR 自己的方法论，应当先在一台真实 Windows 上把语音列表
> 打出来（`report_env` 已经有这个能力），确认实际看得见几个中文语音、够不够用，
> 再决定值不值得引入原生实现。当年 macOS 这条结论就是这么得出来的。

### 3. 语速换算需要实听校准

Web Speech 的 `rate` 是倍数（0.9–1.45），`say -r` 是每分钟词数（默认约 175）。
先按线性映射 `-r = 175 × rate`，**这个系数是估的**，中文按字计与英文按词计不同，
要实际听过再调。校准前不要把它当成准确值写进文档。

### 4. 「下载增强语音」那条提示要重写

现有提示说「装好后回到这里就能选到」。在 WKWebView 里这句话是**错的**——装了也
看不到。改走原生之后它才成立；在回退到 Web Speech 的平台上，这条提示不该出现。

## 后果

- `src/speak.ts` 的 `listVoices()`、`speak()` 改为经 Rust；前端缓存一次语音表，
  保持 `listVoices()` 同步可用，不必把调用方全改成异步。
- 多一个 Rust 模块管朗读进程，职责与 `engine.rs` 并列。
- macOS 与 Linux 走不同路径，**Linux 上的朗读质量仍受限于浏览器引擎**，这是已知
  差距，不在本 ADR 解决。
- `report_env` 保留为长期的环境自检入口——这次的 bug 绕了三轮才定位，就是因为
  没有这样一个东西。
