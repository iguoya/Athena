# ADR 0106：RTOS 从嵌入式侧独立成子应用 rtos

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10：「嵌入式这边 RTOS 给独立出来吧」）
- 关系：沿 [ADR 0103](0103-practice-courses-as-attached-subapps.md) 的细分判据与
  挂靠机制（本条是其决策 2 表格的追加，不改原文）；命名按
  [ADR 0104](0104-os-rename.md) 口径（rtos 是嵌入式领域通行缩写）；与
  operating-system 的关系守 [ADR 0095](0095-one-exam-one-app.md) 决策 3
  （两考试公共课不共享不互引）

## 背景

1. 0103 把嵌入式第 4 章（系统软件 RTOS）划给了 microcontroller——当时按
   「真板实验归硬件台」的介质直觉归并。tiger 复核后认为 RTOS 自成一门课程，
   应独立。
2. 按 0103 三判据复核，RTOS 成立：以子课程为单元（实时操作系统：任务与调度、
   抢占与优先级反转、IPC、实时性）；实践性强（content-plan 评级 A ✓ 真板跑
   FreeRTOS 看抢占、B ✓ QEMU 或线程模拟调度真执行，两条路径都有）；有具体
   产出（真板/QEMU 里跑出的调度时序与任务观测记录）。
3. `rtos` 是嵌入式领域通行缩写（Real-Time Operating System），按 0104 口径
   可作 id；知识点前缀顺用 `rtos.`。

## 决策

1. **新增 `subjects/rtos`**：title「实时操作系统（RTOS）」，group「实时操作系统」，
   `parent: embedded`，端口 1496，Tauri 2 + Vue 3（嵌入家族，0103 决策 3），
   学习应用全套（进度库、AGENTS.md、CLAUDE.md、check.py、content-contract.json
   exam 档）。
2. **承接嵌入式第 4 章的实验路径**：真板 FreeRTOS 抢占观测（A）、QEMU +
   arm-none-eabi-gcc 交叉编译全流程（B，零硬件）、本机 gcc 线程级模拟
   （任务/信号量映射 pthread，调度直觉快速回路）；调度时序可视化（任务时间线）
   是本应用的核心教学界面。第 4 章的嵌入式文件系统/数据库理论部分留在
   embedded 应用，不进本应用。
3. **嵌入家族三分**（修订 0103 落地时 firmware AGENTS.md 里的两分表述）：
   - **firmware**＝嵌入式 C 编码（第 6、8、11 章，本机 gcc 真跑）；
   - **rtos**＝实时操作系统（第 4 章，FreeRTOS/QEMU/线程模拟）；
   - **microcontroller**＝板级基础实验（第 2、5 章，串口帧、点灯定时器、
     烧录与工具链）——承接清单由「第 2、4、5 章」收缩为「第 2、5 章」。
   三应用构建完全隔离（ADR 0032），QEMU/串口等能力各自实现，不共享代码。
4. **与 operating-system 的边界**：os 挂 software 承接软设第 4 章通用 OS 实验，
   rtos 挂 embedded 承接嵌入式第 4 章实时 OS 实验——两考试公共课各自维护
   （0095 决策 3），不共享、不互引；实时性语义（调度确定性、优先级协议）是
   rtos 独有的教学重心。0103 决策 6 中「嵌入式第 4 章通用 OS 部分的实验由
   operating-system 承接」一句由本条取代。

## 后果

- 应用 +1（共 7 个实践子应用），领域圈 +1；embedded 底下挂三个子应用。
- microcontroller 的 app.json description、AGENTS.md、firmware 的 AGENTS.md
  分工段、content-plan 嵌入式归属、根登记同步。
- 真板路径仍有 0103 决策 7 的购置前置（入门开发板 + ST-Link + USB-TTL）；
  QEMU 与线程模拟路径零硬件可先行。
