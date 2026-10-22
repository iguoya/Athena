# 验证：伴随窗口读写 B 站外链播放器（claude-code，2026-10-22）

目的：验证「第二个 Tauri 窗口加载 B 站官方外链播放器页面 + 注入脚本」能否读播放时间、跳转、暂停、触发暂停点。
对象：`https://player.bilibili.com/player.html?bvid=BV1Ls411w7rx&p=2&autoplay=0`（翁恺 C 语言 B 站转载版第 2 集，478 秒）。
实现：Tauri 2（无 unstable 特性），`WebviewWindowBuilder` + `WebviewUrl::External` + `initialization_script`；
页面→Rust 用 `window.__TAURI_INTERNALS__.invoke('bridge_report')`，capability 的 `remote.urls` 只放行 `player.bilibili.com`，
权限只给 `allow-bridge-report` 一个命令；Rust→页面用 `window.eval`。代码在同目录 `spike-player-bridge/`。

## 结果（三次运行，Windows 11 / WebView2）
- 远程页面可以调用被放行的命令，时间/状态上报正常（tick 约每 100ms 采样，每秒上报）。
- seek、play（需先静音，否则可能被自动播放策略拦）、pause、事件（play/pause/seeked/waiting/ended）都可用。
- **暂停点触发可用**：自然播放跨过暂停点 → 脚本暂停并上报（155.01 s、155.09 s 两次均命中）；拖/跳越过不触发（seek 90 → 暂停点 95 的判定、seek 200 都符合设计）。
- 页面本身的 `<video>` 是标准元素，`window.player` 也在（含 getCurrentTime、on/emit），本验证只用了 `<video>`，不依赖私有 API。
- 页面里只有播放器，没有推荐/评论。页面文本里有「进入哔哩哔哩，观看更高清」——未登录的清晰度提示，登录由使用者在该窗口里处理。

## 未解释的现象（设计必须容忍）
- 第 1、2 次运行里播放器**自己暂停过一次**（视频时间约 93.2 s、94.65 s，无我方暂停调用；当时窗口有焦点）；第 3 次从 85 s 连播 25 s 越过该点，没有暂停。原因未查明。
- 设计含义：把「意外暂停」当成正常状态——脚本只在有暂停点时才算暂停点命中（已如此），意外暂停时主窗口显示「已暂停，点这里继续」，不当作错误；
  暂停点判定一律用「自然跨过」，不依赖暂停事件。
- 页面加载后会自动开始播放（`autoplay=0` 不生效），应用要在 ready 后先 `pause()`。
- 后台/最小化的窗口里定时器会被节流（约 1 秒一次），暂停点精度会下降：播放器窗口要保持可见（并排放置）。

## 没验证的
macOS（WKWebView）、Linux（WebKitGTK）；iframe 内嵌（同源限制，已知读不到）；中国大学 MOOC 播放器；B 站页面改版后的稳定性。

## 补充：视频窗格可以停靠在主窗口里（同日第四次运行）
用 Tauri 2 的多 webview（`Window::add_child`，需开 `unstable` 特性）把「应用界面」和「播放器页面」放进**同一个窗口**：
左 560px 是应用 UI（本地页面），右 840px 是 B 站外链播放器（外部 URL + 注入脚本）。同样的读时间、seek、play、暂停点命中（155.00 s）都正常，
capability 改成按 webview 标签（`webviews: ["player"]`）放行。结论：视频可以只是应用界面里的一个窗格，不必是单独窗口。
代价：`unstable` 特性意味着接口以后可能变，升级 Tauri 时要回归；退路是分开的伴随窗口（第一版验证，不需要 unstable）。
