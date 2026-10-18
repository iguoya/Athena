# Athena GTKMM · ADR 索引

本目录只记录 **`guide/gtkmm` 独立应用** 的架构与内容写作决策。仓库根
`docs/decisions/` 管跨应用规范；精神可对齐，编号与文件互不混用。

| 编号 | 决策 | 状态 |
|---|---|---|
| [0001](0001-tauri-shell-with-native-demo-track.md) | Tauri 文档壳 + 原生演示/实验双轨架构；清单与 JSON-RPC 协议是不变量，进程形态可演进 | 已接受 |
| [0002](0002-translation-baseline-and-source-layers.md) | 官方教程全量翻译为编排基准，GFDL 合规；语义基准与参考层三层认定 | 已接受 |
| [0003](0003-migration-chapters-return-to-mainline.md) | 官方第 4、5 章（版本迁移）回归教程主线，章节编号严格跟随官方 | 已接受 |
| [0004](0004-self-translation-layers.md) | 自译分层——应用内草稿存进度库，贡献产出走导出脚本人工对照 | 已接受 |
| [0005](0005-po-unit-as-translation-unit.md) | 翻译单元以官网 PO 翻译单元为准，词数聚合只作兜底 | 已接受 |
| [0006](0006-exercise-upstream-examples.md) | exercise/ 原样导入官方示例代码，壳内编译运行 | 已接受 |
| [0007](0007-snapshot-injects-example-code.md) | 正文快照复刻官方构建期的示例代码注入 | 已接受 |
| [0008](0008-examples-card-before-content.md) | 官方示例卡移到节页最上方——先演示，后读教程 | 已接受 |
| [0009](0009-example-workspace-copy.md) | 官方示例的工作区副本——VS Code 打开真实工程 | 已接受 |
| [0010](0010-translation-glossary.md) | 翻译术语约定：以社区 PO 多数为基线定主译法，glossary.json 为事实源，禁用写法由 check 阻断 | 已接受 |
| [0011](0011-quiz-standard.md) | 测验标准版：均衡答案位、等长选项、答后解析、读代码题；掌握度只认首次作答 | 已接受（试点） |
