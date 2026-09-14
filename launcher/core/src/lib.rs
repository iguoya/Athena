//! Athena 各学习应用的统一开发编排器。
//!
//! 每个应用在自己的 `app.json` 里**声明**怎么构建、怎么跑、怎么算就绪；
//! 构建、启动、状态探测、停止、窗口前置这些执行逻辑只在这里写一份
//! （ADR 0046）。这样新增一个应用不用再抄一份 dev 脚本，改一次行为
//! 也不用改五遍。
//!
//! 三个前端共用它：终端的 `athena-dev`、跨平台的 Slint 窗口、
//! macOS 的菜单栏常驻应用。

pub mod manifest;
pub mod paths;
pub mod runner;

pub use manifest::{discover, App};
pub use runner::{activate, launch, stop, ProcessSnapshot, RunState};
