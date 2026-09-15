# ADR 0002：桌面壳用 Flutter

- 日期：2026-09-15
- 状态：已接受
- 影响：`apps/driving` 的构建、启动方式与界面技术
- 对齐：主仓库 ADR 0047（跨平台优先）；英语应用 ADR 0002 曾排除 Flutter，那是
  因为长文划词和公众号 HTML 管线，本应用没有这两条

## 背景

仓库里已有 GTK、Qt Quick、Tauri、Slint。驾驶理论是题库、标志示意和限时考试，
适合自绘控件而不是 WebView 或 GTK 教案。Flutter 的 Skia/Impeller 在 Windows 与
macOS 是一等公民，Linux 为第二档，和本应用的平台优先级一致。

## 决策

1. 使用 **Flutter 桌面**（macOS / Windows / Linux），Dart 写界面。
2. 交通标志用 `CustomPaint` 按标准分类自绘示意，不嵌入浏览器，不复制标准图样。
3. 进度用 `sqflite_common_ffi` + 自带 sqlite，写入用户数据目录，Windows 不依赖
   系统 sqlite。
4. 启动声明写在 `app.json`：`scripts/run_dev.py` 按平台选 `flutter run -d`。
   就绪判据是进程在（没有 dev server 端口）。
5. 不引入 Electron、Tauri、Qt 或 GTK 来做同一份界面。

## 后果

- 本机和 CI 都需要 Flutter SDK（stable）。
- 改 `lib/` 热重载；改 `content/` 要热重启，因为开发模式从磁盘读 JSON。
- 仓库多一套构建工具，换来的是还没练过的自绘桌面族。
