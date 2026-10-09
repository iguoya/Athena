# 实时操作系统（RTOS） 应用协作规则

仓库级规则见根 `AGENTS.md`，本文只写本应用自己的约定。本应用目录 id `rtos`，
知识点前缀 `rtos.`（与目录 id 一致）。本应用是**学习应用**（三类判据见
`docs/REPOSITORY.md`）：要教会人软考中级·嵌入式系统设计师「第 4 章」对应的实践课程，并用
可观察的证据（实验校验通过）证明掌握度在进步。跨应用教学规范
（`docs/TEACHING.md`）全部生效。

## 应用定位

- **本应用是软考中级·嵌入式系统设计师「第 4 章」的实践课程**，按仓库 ADR 0106 从考试应用
  独立成挂靠子应用：`parent: embedded`，单父一层挂靠（ADR 0092、0099），启动器
  画在嵌入式系统设计师外一圈，也可单独使用。
- 细分判据（ADR 0103 决策 1，三条同时满足）：以子课程为单元；实践性强
  （content-plan 评级 A ✓ 真板跑 FreeRTOS 看抢占、B ✓ QEMU/线程模拟调度真
  执行）；有具体产出——真板/QEMU 里跑出的调度时序与任务观测记录。
- **分工**：承接章的理论侧讲解、viz 演示与纸笔考核留在 嵌入式系统设计师；本应用
  承接全部实验路径。第 4 章的嵌入式文件系统/数据库理论部分留在 嵌入式系统设计师，
  不进本应用。
- **嵌入家族三分**（ADR 0106 决策 3）：firmware＝嵌入式 C 编码（第 6、8、11
  章）；本应用＝实时操作系统（第 4 章）；microcontroller＝板级基础实验（第 2、
  5 章）。三应用构建完全隔离（ADR 0032），QEMU/串口等能力各自实现。
- **与 operating-system 的边界**：os 挂 software 承接软设第 4 章通用 OS 实验；
  两考试公共课各自维护（ADR 0095 决策 3），不共享、不互引；调度确定性、优先级
  协议等实时性语义是本应用独有的教学重心。

## 技术栈与选型理由

- 壳 **Tauri 2**（Rust + 系统 WebView）。
- 前端：Vue 3 + TypeScript + Vite + Tailwind CSS 4（与 embedded 同体系，
  ADR 0103 决策 3）；代码编辑器统一用 CodeMirror 6。
- **实验引擎（本应用的核心差异化架构，ADR 0106 决策 2）**：真板跑 FreeRTOS 看抢占（串口输出观测，需开发板，ADR 0091 决策 5 前置）；QEMU + arm-none-eabi-gcc 交叉编译全流程（零硬件真跑）；本机 gcc 线程级模拟（任务/信号量映射 pthread，调度直觉快速回路）。调度时序可视化（任务时间线甘特图）是核心教学界面。命令一律白名单 spawn。
- **安全边界**（沿 ADR 0091 决策 3）：应用只执行白名单内的预设命令与实验断言，
  参数模板化；不提供任意 shell。
- dev 端口 **1496**（strictPort）；进程/二进制 `athena-rtos`；窗口标题
  「实时操作系统（RTOS）」；应用内文案用中文。

## 内容组织

```
content/
├── sources.json            来源登记(出处检查的 catalog)
├── course.json             课程骨架:承接章映射 + 实验节列表
└── experiments/*.json      实验卡:步骤、骨架、校验断言(带出处)
```

- 实验卡三要素（ADR 0059 骨架可运行）：**骨架**（不改一行也能编译运行）、
  **校验断言**（输出比对/结果比对/观测记录）、**出处**。
- **判分条目是实验的 `assertions`**（content-contract.json 的 `itemMarkers`）：
  断言引用教材例题或真题时必须标 `verbatim` / `adapted` 出处（年份与题号严禁
  凭记忆编造）；骨架代码本身标 `authored`，不是出处门禁对象。
- 出处档位 **exam**（ADR 0089）：本应用判分内容直接对应真实考试，档位从严。
  骨架阶段无判分条目，契约 `blocking: false`；内容入库后改 `true`。

## 掌握度与进度库

- **掌握度只由作答写入**（ADR 0052）：一个实验节的校验断言全部通过 =
  该节的一次作答，写入 `attempts`；不设「实验币」等旁路激励；激励只展示
  由记录派生的量。
- `progress/learning.db` 随仓库走（ADR 0037、0053），Rust 侧自建自迁移：
  仓库工作树内（以 `app.json` 存在为准）写 `progress/learning.db`，发行包写
  系统数据目录。骨架阶段库由首次运行生成；schema 变更直接改建表语句并保证
  旧库可迁移，不引迁移框架。

## 验证与构建

```sh
python3 scripts/check.py            # 结构校验（骨架阶段默认）
python3 scripts/check.py --full     # + 前端构建 + Rust 检查
python3 scripts/check.py --full --skip-rust   # 只改内容或前端时用
```

- 骨架阶段（ADR 0106：先不考虑内容填充）默认只做结构校验：app.json 一致性
  （id/parent/端口三方对齐）、内容 JSON 语法、course.json 节前缀、出处契约、
  图标齐备。**内容开始填充后把默认翻转成完整构建检查**（改 `check.py` 的
  `DEFAULT_FULL`）。
- 跨应用出处检查由根 `scripts/check-app-sources.mjs` 按
  `content-contract.json` 接入。

## 约定

- 影响本应用架构边界的新决定，在 `docs/decisions/` 增补 ADR 后再动代码。
- 与其他应用构建完全隔离（ADR 0032、0062）：不引用任何应用的路径、配置或
  代码；与 嵌入式系统设计师 的关系是课程归属声明，不是运行时依赖。
