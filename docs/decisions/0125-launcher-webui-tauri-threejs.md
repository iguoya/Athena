# ADR 0125：启动器 UI 层重选 Tauri 2 + Three.js，学习应用面板改「领域轨道环」3D 构图

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10：「目前的技术架构老是卡死 不适宜 看看有没有更绚丽
  开发维护效率更好的技术选型方案」「我想采用成熟的 3D 技术是否可行」「先考虑好 3D
  情况下的成熟布局方案」；方案比较后 tiger 选定 Tauri 2 + Three.js）
- 关系：收窄 [ADR 0044](0044-menubar-launcher.md)/[0046](0046-unified-dev-orchestrator.md)
  建立的 gui（Rust + Slint）前端的适用范围（冻结，不再投入，core 不动）；
  执行路径约定沿 0046 不变；布局纯函数约定（launcher AGENTS）延伸到 3D 布局；
  放弃本轮讨论过的「横向树干+领域叶丛」2D 构图（3D 愿景下改走轨道环）

## 背景

1. Slint 1.17 的自研渲染器在启动器上连环暴露问题：femtovg 在部分机器
   `glGenBuffers` 崩溃（gui 已默认退软件渲染）、Path 填充在局部重绘时按高不透明度
   画错并残留（同心环被迫预渲染成位图绕开）、Path 不支持虚线描边（core 被迫把
   贝塞尔切成段列）、大窗口下偶发取帧伪影。tiger 体感「老是卡死」。
2. tiger 提出两点诉求：技术栈要稳定、绚丽、开发维护效率高；启动器想上成熟的 3D。
   启动器的业务逻辑确实只有三件事：读清单、摆图标、启动程序——成本全在渲染层。
3. launcher-core（清单发现、布局纯函数、进程编排、图标管线）不依赖任何 UI 框架，
   是启动器最有价值的资产，换 UI 层不动它。
4. 仓库主栈是 Tauri 2 + React/TS + Vite（network、firmware、microcontroller、rtos、
   gtkmm 全是），模式成熟、可整段照抄。

## 决策

1. **UI 层换 Tauri 2 + React + Three.js（@react-three/fiber）**，新前端在
   `launcher/webui/`，进程形态照旧：托盘常驻 + 单例 + 自启动（Tauri 插件均有现成
   方案）。渲染交给 WebView2 的 WebGL——浏览器级稳定性，动画上限远高于 Slint。
2. **launcher-core 原样复用**：Tauri 后端直接依赖 core crate，`discover`、
   `mindmap` 布局、`runner`（启动/停止/状态）、`icons` 全部库内调用。执行路径约定
   （ADR 0046）不变：数据仍然只有 core 一处来源，CLI（`launcher list --json`）与
   库调用是同一实现的两种入口，前端依旧不读 `app.json`、不自判状态。
3. **学习应用面板改「领域轨道环」3D 构图**：虎头居中为恒星，每个领域圈是一条
   倾斜的 3D 轨道环，应用图标是环上的行星；拖拽旋转、滚轮缩放，悬停图标弹出
   关系线（虚线+高亮机制从 2D 版平移）。图标与中文文字用 DOM/CSS2D 叠加，保证
   清晰可点。
4. **保留 2D 平铺视图**（同一份数据层，一键切换）：日常快速启动用 2D，3D 供
   总览与演示；两种视图共享全部后端 command。
5. **3D 轨道布局是 core 的纯函数**（`launcher-core` 新布局模块，输入清单输出
   每条轨道的半径/倾角与每个节点的空间坐标，带单元测试），前端只渲染——沿用
   「布局不在界面里算」的既定约定。旧的同心椭圆布局与连线段列随 gui 冻结保留，
   不删除（ADR 0054 的宁增勿删精神：旧前端退场但代码留档）。
6. gui（Slint）**冻结**：不再修 bug、不新增功能，待 webui 功能对齐后整体退役；
   退役前它是可用的回退（`cargo run -p athena-launcher` 照常能跑）。

## 后果

- `launcher/` 下的前端从三个变四个（gui、macos、webui 与 CLI 本体），AGENTS 与
  README 的前端清单更新；webui 走 Tauri 的构建链（npm + vite + cargo），CI 的
  launcher 段要带上 `cargo build --manifest-path launcher/webui/src-tauri/Cargo.toml`。
- WebView2 在 Windows 10/11 系统自带，无分发负担；Linux 的 WebView 生态较弱，
  启动器本就按 ADR 0051 以 macOS ≈ Windows 优先，webui 首发只承诺 Windows。
- Slint 依赖从工作区可选化/移除推迟到 gui 退役时一并处理，期间两条构建链并存。
