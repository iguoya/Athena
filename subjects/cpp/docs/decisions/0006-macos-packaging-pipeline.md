# ADR 0006：macOS 发行统一由 package_macos.py 与标签 CI 承担

- 日期：2026-08-15（补记）
- 状态：已接受
- 依据提交：`a290179` 可携带应用与 DMG、`066e0bd` 双架构 Release 工作流、
  `585d48a` 发布 1.0.0

## 背景

直接复制可执行文件无法携带 GTK 运行时（动态库、图标主题、GSettings、
GdkPixbuf 加载器），换机即不可用；首批 0.1.0 包暴露了图标主题与 formula
前缀资源收集问题（`f6f7365`、`0bc7878`）。

## 决策

- macOS 可携带包唯一入口是 `scripts/package_macos.py`，不手工复制可执行文件
  作为 Release。
- `dist/` 是本地生成目录，不提交 `.app` 或 DMG；GitHub Release 只上传
  `v*.*.*` 标签构建产生的双架构 DMG 与校验和。
- 当前包为 ad-hoc 签名、未公证，对外描述必须如实；Developer ID 与
  notarization 属于后续阶段。

## 后果

- 修改打包器、macOS 模板或发行工作流后，必须本机生成并启动一次对应架构的
  `.app`，并验证 DMG 校验和与应用签名结构。
- 打包脚本本身暂无自动化测试，属于已知的验证盲区。
