# ADR 0018：Ubuntu 同时发行 DEB 与 AppImage

- 日期：2026-08-29
- 状态：已接受

## 背景

Athena 已在 Ubuntu 使用 GTK4、GtkSourceView 5 和 WebKitGTK 6.0 运行，但标签发布
流程只生成 macOS DMG。Ubuntu 用户缺少可直接安装的发行产物。

## 决策

- `scripts/package_linux.py` 是 Linux 发行包的唯一入口：从 Meson 的 `/usr` 安装树
  同时生成 `athena_VERSION_amd64.deb` 与 `Athena-VERSION-linux-x86_64.AppImage`。
- DEB 是 Ubuntu 的主安装包，明确依赖 GTK、GtkSourceView、WebKitGTK、MD4C HTML 和
  SQLite 运行时；用户通过 APT 安装时由系统解析其传递依赖。
- AppImage 由固定版本并校验 SHA-256 的 linuxdeploy 生成，作为 Ubuntu 24.04 及以上
  相近环境的便携下载选项。WebKitGTK 采用多进程辅助程序并使用发行版固定安装路径，
  因此不承诺该 AppImage 在没有对应 WebKitGTK 运行时的任意 Linux 发行版上运行。
- 标签 Release 在 macOS 双架构 DMG 之外，新增一个 Ubuntu x86_64 作业构建、测试、
  打包、结构验证并上传两种 Linux 资产；发布作业统一生成校验和与 GitHub Release。

## 后果

- Linux 发布构建目录必须用 `--prefix /usr` 配置，避免 DEB 把文件放进 `/usr/local`。
- 修改 Linux 打包器或工作流后，至少要本地生成并检查 DEB 元数据和 AppImage 结构，
  并由 GitHub Ubuntu Runner 重复完成这组验证。
- 未来若需跨发行版、无系统 WebKitGTK 依赖的强隔离发布，应新增 Flatpak 方案或改用
  可重定位的 WebKit 运行时，而不是把当前 AppImage 描述成通用静态包。
