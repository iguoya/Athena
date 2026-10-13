# 在线演示

纯前端、不依赖本机后端的应用，构建成网页放在这里，浏览器里直接用（ADR 0154）。
应用本体仍是 Tauri 桌面程序，这里只是同一份前端的网页版。

| 演示 | 说明 |
| --- | --- |
| [地球](https://iguoya.github.io/Athena/demo/earth/) | 真实比例的地球分层 3D 可视化，源码在 [`practice/earth`](https://github.com/iguoya/Athena/tree/main/practice/earth)（ADR 0128）。首次打开要加载约 15 MB 的地球贴图，稍等几秒 |

课程类应用（算法设计、数据结构等）的课程内容、进度存储和代码编译都走 Rust 后端，
没有后端的浏览器里跑不起来，所以没有网页版。
