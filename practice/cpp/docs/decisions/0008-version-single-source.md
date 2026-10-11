# ADR 0008：版本号以 meson.build 为单一来源

- 日期：2026-08-15
- 状态：已接受
- 依据提交：`f9c6b3e`

## 背景

版本号同时存在于 `meson.build`、Git 标签和打包脚本的 `--version` 参数三处，
靠人工保持一致。Release 工作流已校验标签与 Meson 版本一致，但本地打包仍可
传入任意版本号，产出的 DMG 命名与实际构建版本可能不符。

## 决策

- `package_macos.py` 默认从 `meson.build` 的 `project()` 读取版本号。
- 显式传入 `--version` 时必须与 `meson.build` 一致，否则拒绝打包。
- `Info.plist` 版本由模板按该版本注入；Git 标签由 Release 工作流校验。
- 每次发版在 `CHANGELOG.md` 记录显著变化。

## 后果

- 发版流程固定为：改 `meson.build` 版本 → 补 `CHANGELOG.md` → 打
  `v*.*.*` 标签，三处不会再各自漂移。
- CI 的标签校验保留，作为标签与 `meson.build` 一致性的第二道防线。
