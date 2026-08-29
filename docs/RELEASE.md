# Athena 发行说明

## 当前范围

每个标签发行生成 macOS 双架构 DMG 和 Ubuntu x86_64 的两种安装包：

```text
Athena-VERSION-macos-x86_64.dmg
Athena-VERSION-macos-arm64.dmg
athena_VERSION_amd64.deb
Athena-VERSION-linux-x86_64.AppImage
```

当前发行包使用 ad-hoc 签名，尚未接入 Developer ID 和 Apple 公证。首次从网络下载
后，macOS Gatekeeper 可能要求用户在 Finder 中右键应用并选择“打开”。不要把当前
包描述为已签名或已公证版本。

## macOS 本机构建

除项目构建依赖外，打包还要求 Homebrew 安装 `librsvg`、
`adwaita-icon-theme` 和 `hicolor-icon-theme`，用于生成应用图标并收集 GTK
运行时主题资源。

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
  --output-dir dist
```

版本号以 `meson.build` 为单一来源，脚本默认直接读取；显式传入 `--version`
时必须与 `meson.build` 一致，否则拒绝打包。

打包器会：

- 创建标准 `Athena.app/Contents` 结构和 `Info.plist`。
- 从 `tiger.svg` 生成多尺寸 `Athena.icns`。
- 递归收集非系统动态库并改写为 `@executable_path` 相对引用。
- 打包 GTK 图标主题、GSettings 配置定义、Fontconfig 配置和 GdkPixbuf 加载器。
- 生成运行启动器，根据应用实际位置设置 GTK 运行环境。
- 对全部嵌套 Mach-O 文件和 `.app` 执行 ad-hoc 签名。
- 拒绝仍引用 `/usr/local` 或 `/opt/homebrew` 的不完整应用包。
- 生成带 Applications 快捷方式的压缩 DMG。

## 本机验证

```sh
dist/Athena.app/Contents/MacOS/Athena
codesign --verify --deep --strict dist/Athena.app
hdiutil verify dist/Athena-VERSION-macos-x86_64.dmg
```

正式发布前还应挂载 DMG，并从挂载卷中的 `.app` 启动一次。由于当前没有 Apple
公证，最好在没有 Athena 开发环境的另一台 Mac 上验证 Gatekeeper 提示和完整功能。

## Ubuntu 本机构建

Ubuntu 24.04 需要构建依赖之外的 `desktop-file-utils`、`squashfs-tools` 和 `curl`。
Linux 发行构建必须使用 `/usr` 前缀，保证 DEB 不会把文件装进 `/usr/local`：

```sh
meson setup build-linux-release --buildtype=release -Dstrip=true --prefix /usr
meson compile -C build-linux-release
xvfb-run -a meson test -C build-linux-release --print-errorlogs
```

下载固定版本的 linuxdeploy 与 AppImage runtime，并校验下载内容：

```sh
curl -fL -o linuxdeploy-x86_64.AppImage \
  https://github.com/linuxdeploy/linuxdeploy/releases/download/1-alpha-20251107-1/linuxdeploy-x86_64.AppImage
echo 'c20cd71e3a4e3b80c3483cef793cda3f4e990aca14014d23c544ca3ce1270b4d  linuxdeploy-x86_64.AppImage' | sha256sum --check
chmod +x linuxdeploy-x86_64.AppImage
curl -fL -o appimage-runtime-x86_64 \
  https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-x86_64
echo '1cc49bcf1e2ccd593c379adb17c9f85a36d619088296504de95b1d06215aebbf  appimage-runtime-x86_64' | sha256sum --check
```

再从同一份 Meson 安装树生成两种产物：

```sh
python3 scripts/package_linux.py \
  --project-root . \
  --build-dir build-linux-release \
  --output-dir dist \
  --linuxdeploy ./linuxdeploy-x86_64.AppImage \
  --appimage-runtime ./appimage-runtime-x86_64
```

DEB 是 Ubuntu 首选：`sudo apt install ./athena_VERSION_amd64.deb` 会解析依赖。AppImage
内置 Athena 和大多数库，但 WebKitGTK 的多进程辅助程序采用发行版固定路径；它定位为
Ubuntu 24.04 及以上相近环境的便携下载，不承诺任意 Linux 发行版的完全静态兼容。

## GitHub Release

`.github/workflows/release.yml` 由 `v*.*.*` 标签触发：Intel 与 Apple Silicon Runner
分别构建、测试和打包 DMG；Ubuntu 24.04 Runner 构建、测试并生成 DEB 与 AppImage。
三个构建任务完成后，发布任务汇总所有资产、生成 SHA-256 校验和，并创建 GitHub Release
和自动发行说明。

发布前要求：

1. `meson.build` 和目标标签使用同一个 `MAJOR.MINOR.PATCH` 版本；`Info.plist`
   版本由模板按 `meson.build` 生成，打包器与 Release 工作流都会拒绝不一致的版本。
2. 在 `CHANGELOG.md` 中记录该版本的显著变化。
3. `main` 已通过 CI，工作区没有未提交内容。
4. 标签必须指向准备发布的提交。

发布命令：

```sh
git tag -a v1.0.0 -m "Athena 1.0.0"
git push origin v1.0.0
```

工作流使用仓库自带的 `GITHUB_TOKEN` 创建 Release，不需要额外 GitHub Token。
Developer ID 证书、Apple 账号 Secret 和公证步骤属于后续正式签名阶段。
