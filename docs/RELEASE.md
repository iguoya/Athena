# Athena macOS 发行说明

## 当前范围

Athena 0.1.0 支持生成两个独立的 macOS 安装包：

```text
Athena-0.1.0-macos-x86_64.dmg
Athena-0.1.0-macos-arm64.dmg
```

当前发行包使用 ad-hoc 签名，尚未接入 Developer ID 和 Apple 公证。首次从网络下载
后，macOS Gatekeeper 可能要求用户在 Finder 中右键应用并选择“打开”。不要把当前
包描述为已签名或已公证版本。

## 本机构建

先构建经过优化和剥离符号的发行版：

```sh
meson setup build-release --buildtype=release -Dstrip=true
meson compile -C build-release
meson test -C build-release --print-errorlogs
```

然后生成 `.app` 和与当前机器架构对应的 DMG：

```sh
python3 scripts/package_macos.py \
  --project-root . \
  --binary build-release/Athena \
  --output-dir dist \
  --version 0.1.0
```

打包器会：

- 创建标准 `Athena.app/Contents` 结构和 `Info.plist`。
- 从 `tiger.svg` 生成多尺寸 `Athena.icns`。
- 递归收集非系统动态库并改写为 `@executable_path` 相对引用。
- 打包 GTK 图标主题、GSettings Schema、Fontconfig 配置和 GdkPixbuf 加载器。
- 生成运行启动器，根据应用实际位置设置 GTK 运行环境。
- 对全部嵌套 Mach-O 文件和 `.app` 执行 ad-hoc 签名。
- 拒绝仍引用 `/usr/local` 或 `/opt/homebrew` 的不完整应用包。
- 生成带 Applications 快捷方式的压缩 DMG。

## 本机验证

```sh
dist/Athena.app/Contents/MacOS/Athena
codesign --verify --deep --strict dist/Athena.app
hdiutil verify dist/Athena-0.1.0-macos-x86_64.dmg
```

正式发布前还应挂载 DMG，并从挂载卷中的 `.app` 启动一次。由于当前没有 Apple
公证，最好在没有 Athena 开发环境的另一台 Mac 上验证 Gatekeeper 提示和完整功能。

## GitHub Release

`.github/workflows/release.yml` 由 `v*.*.*` 标签触发，在 Intel 和 Apple Silicon
Runner 上分别构建、测试和打包。两个架构任务完成后，发布任务汇总 DMG，并使用
标签创建 GitHub Release 和自动发行说明。

发布前要求：

1. `meson.build`、`Info.plist` 和目标标签使用同一个 `MAJOR.MINOR.PATCH` 版本。
2. `main` 已通过 CI，工作区没有未提交内容。
3. 标签必须指向准备发布的提交。

发布命令：

```sh
git tag -a v0.1.0 -m "Athena 0.1.0"
git push origin v0.1.0
```

工作流使用仓库自带的 `GITHUB_TOKEN` 创建 Release，不需要额外 GitHub Token。
Developer ID 证书、Apple 账号 Secret 和公证步骤属于后续正式签名阶段。
