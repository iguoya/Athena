# ADR 0109：新增「Linux 程序设计」子应用 linux 挂靠 software；os 与 linux 的图标归属

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10：「我打算新开一个 Linux 程序设计的课程节点 挂在
  软件设计师下面吧」；os 图标改用 Unix 专有图标，Tux 让给 linux）
- 关系：沿 [ADR 0103](0103-practice-courses-as-attached-subapps.md) 的细分判据与
  挂靠机制（同 [0106](0106-rtos-subapp.md) 的追加模式）；命名按
  [0100](0100-single-word-app-ids.md)（linux 是领域通行单词）；与 operating-system
  的分工守 [0095](0095-one-exam-one-app.md) 决策 3 公共课隔离

## 背景

1. tiger 提出新开「Linux 程序设计」课程节点。按 0103 三判据成立：以子课程为
   单元（shell 与命令行、文件 IO、进程与线程、IPC 与信号、socket 网络编程是
   一门独立课程）；实践性强（B 路径真编码——本机 gcc/make/bash 真跑，开发机
   基线 ADR 0057 自带）；有具体产出（可编译运行的程序与脚本）。
2. 软考侧承接：软件设计师上午题连年考 Linux 命令（第 4 章操作系统的 Linux 部分）。
3. os 的启动器图标此前用 Tux（Linux 标志），与「操作系统」的通用语义不符且与
   新课程撞车：Tux 归 linux，os 改用 Unix 专有图标。

## 决策

1. **新增 `subjects/linux`**：title「Linux 程序设计」，group「Linux」，`parent:
   software`，端口 1499，进程/二进制 `athena-linux`，知识点前缀 `linux.`；壳沿
   data-structures 架构（Tauri 2 + 本机编译实验，ADR 0108），均为技术学习类
   学习应用（出处 open 档）。
2. **承接与分工**：承接软设第 4 章的 Linux 命令实验与「Linux 程序设计」学科
   本身（shell、文件 IO、进程线程、IPC、socket）；operating-system 继续承接
   第 4 章的通用 OS 概念实验（调度/页置换模拟、pthread 信号量）——Linux 专属
   的命令与系统调用实践归 linux，通用 OS 语义归 os，两应用不共享代码。
3. **内容先立骨架**：course 骨架五章（shell 与常用命令、文件 IO、进程与线程、
   进程间通信、socket 网络编程），topics 与实验后续按 content-plan 排期填充
   （0103「先不考虑内容填充」同规）。
4. **图标归属**：linux 用 Tux 企鹅（devicon「linux-original」矢量版）；os 改用
   devicon「unix-original」（Unix 专有图标）。出处与商标声明照例写在各
   icon.svg 头部。

## 后果

- 应用 +1（挂 software 的实践子应用达 8 个）；领域圈 +1「Linux」。
- 根 `AGENTS.md` subjects 清单同步；启动器零改动，`仓库里的真实清单排得干净`
  测试守住新布局。
- os 与 linux 的课程树互放「去对方做实验」的文字指引（0095 决策 3 同规）。
