# ADR 0057：Windows 发行 MSI 与便携 zip

- 日期：2026-09-20
- 状态：已接受

## 背景

Athena 已在 Windows（MSYS2 UCRT64）上构建并跑过 CI，但标签 Release 只产
macOS DMG 和 Ubuntu DEB / AppImage。Windows 用户只能从源码编，和仓库级
「macOS ≈ Windows > Linux」（ADR 0051）以及「安装包允许 `.msi`」（仓库级
ADR 0047）对不上。

直接复制 `athena-cpp.exe` 带不走 GTK 运行时：动态库、GSettings schemas、
GdkPixbuf 加载器、图标主题、GtkSourceView 语言规格都在 MSYS2 prefix 里。
换一台没装 UCRT64 的机器即不可用。

## 决策

- `scripts/package_windows.py` 是 Windows 发行包的唯一入口：从一份
  `athena-cpp.exe` 生成 `Athena-VERSION-windows-x64.zip` 与
  `Athena-VERSION-windows-x64.msi`。
- 包维持 MSYS2 的 `bin` / `lib` / `share` 布局。glib 在 Windows 上按
  自身 DLL 所在目录的上一级当 prefix，这套布局换机即可运行，不要求再装
  MSYS2。
- zip 是便携下载；MSI 用 WiX 5 整树收进 `Program Files\Athena`，并放一条
  开始菜单快捷方式。两者内容相同。当前不做 Authenticode 签名。
- 标签 Release 增加一个 `windows-latest` + MSYS2 UCRT64 作业：构建、测试、
  打包、检查 zip/MSI 里有 `bin/athena-cpp.exe`，再交给发布作业汇总校验和。

## 后果

- 修改 Windows 打包器或发行工作流后，应在本机生成 zip，并至少启动一次
  `Athena.cmd`；MSI 由 GitHub Windows Runner 用固定版本的 WiX 打出。
- `meson.build` 版本、`CHANGELOG.md` 与 `v*.*.*` 标签仍须一致（ADR 0008）。
  标签写作 `v7.0.0` 这类三位版本，不能打成 `v7.0`。
