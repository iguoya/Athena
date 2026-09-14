# Athena 启动器

常驻 macOS 菜单栏的启动器：一张列表，列出 C++ 教程（主程序）和 `apps/` 下的
各个独立学习应用，点一下就打开——已经在跑的直接把窗口提到前面，没跑的才拉起来。
背景与取舍见 [ADR 0044](../docs/decisions/0044-menubar-launcher.md)。

技术栈是 Swift + AppKit/SwiftUI，只用系统自带框架，没有第三方依赖。

## 安装（日常用这个）

```sh
launcher/macos/scripts/install.sh
```

release 编译后装到 `~/Applications/Athena Launcher.app` 并立刻启动。仓库路径在
这一步写进 `Info.plist`，所以仓库搬家后要重新装一次。

装好后在菜单里点「登录时自动启动启动器」，以后开机就在。

## 用法

- **点菜单栏的学士帽图标**，或按 **⌃⌥A**（Control + Option + A）打开列表。
- **点一项** = 打开它。已经在运行就只是把窗口叫到前面，不会起第二份。
- **每行右侧的 ⋯**（悬停出现）：重新启动、停止、开机预热、查看启动日志、
  在访达中显示。
- **开机预热**：勾上的应用会在登录后被悄悄拉起来，窗口一出现就藏起来；
  等你真去点它时，`cargo` / `vite` 那几十秒已经付过了。Tauri 那三个值得勾。
- 状态点的含义：灰=未运行，橙=启动中（正在构建），蓝=已预热（窗口藏着），
  绿=运行中。

启动日志在 `~/Library/Logs/AthenaLauncher/<id>.log`，构建失败时先看它。

## 终端入口

```sh
launcher/macos/.build/debug/AthenaLauncher --list        # 列出各应用和当前状态
launcher/macos/.build/debug/AthenaLauncher --open dsa    # 等于在菜单里点一下「数据结构与算法」
```

`--open` 可以挂到 Raycast、Alfred 或任何快捷键工具上。

## 开发

```sh
launcher/macos/scripts/dev.sh
```

增量编译并直接跑源码产物（会先清掉正在运行的那一份）。这种方式没有 bundle，
「登录时自动启动」在它上面用不了——那个要用 `install.sh` 装出来的 `.app`。

离屏渲染一张菜单的样子，用来检查界面而不必真的点开：

```sh
launcher/macos/.build/debug/AthenaLauncher --snapshot /tmp/menu.png
```

## 清单从哪来

启动器不维护自己的应用列表，它读的是各应用已有的 `app.json`：

- 仓库根 `app.json` —— 主程序（C++ 教程），`match` 指明进程落在 `builddir/`；
- `apps/<id>/app.json` —— 每个独立学习应用，主程序图谱读的是同一份。

新增一个学习应用，只要照样放一份 `app.json`，启动器和主程序都不用改代码。
其中 `icon.symbol` 是菜单栏用的 SF Symbol 名，主程序忽略它。
