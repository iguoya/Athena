# ADR 0019：Linux 发行以 Ubuntu 26.04 为基线

- 日期：2026-08-29
- 状态：已接受

## 背景

Athena 的实际开发与目标运行环境是 Ubuntu 26.04。ADR 0018 初始把 Linux Release
Runner 固定为 Ubuntu 24.04，以扩大旧系统覆盖范围；但该 Runner 使用较早的 gtkmm/
glibmm，导致它无法编译项目在 Ubuntu 26.04 上完全有效的 `Glib::ustring` 与
`std::string` 测试比较。

为适配 24.04 而改写测试会把发布环境的历史限制带回项目源码，也无法代表实际目标系统。

## 决策

- Linux 的 GitHub Release 构建、测试和打包作业使用 `ubuntu-26.04` Runner。
- 撤销仅为旧版 glibmm 增加的字符串转换；测试继续直接表达 GTK 接口返回值与期望文本
  的比较。
- DEB 和 AppImage 的支持基线调整为 Ubuntu 26.04 及以上相近环境；不再声明 Ubuntu
  24.04 兼容性。
- 本决策取代 ADR 0018 中“Ubuntu 24.04 及以上”的 Release Runner 与 AppImage
  基线描述，DEB 为主、AppImage 非通用静态包的其余决策保持不变。

## 后果

- CI 的 GTK/WebKitGTK 依赖版本与开发环境一致，避免由旧系统 API 差异引入无意义的
  兼容性改写。
- `ubuntu-26.04` 目前是 GitHub Actions 的公开预览 Runner；其镜像变动或可用性应在
  Release 失败时优先检查。
- 若未来需要正式支持 Ubuntu 24.04，应单独建立该版本的测试/打包矩阵，并在其中修复
  真正的兼容性问题，而不是降低 26.04 基线的源码表达。
