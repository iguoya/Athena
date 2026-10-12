# ADR 0006：多目标运行环境与平台矩阵

- 日期：2026-10-03
- 状态：已接受
- 依赖：ADR 0005（三类章、三个目标）；仓库 ADR 0057（基线是开发机）、0049（跨平台是成本收益判断）、
  0051（平台优先级）、0059（实验给骨架）、0064（CI 显式触发）

## 背景

汇编线要求「真能运行」，模拟器也可以。三个目标：

| 目标 | 指令集 | ABI | 典型环境 |
|---|---|---|---|
| `win-x64` | x86-64 | Microsoft x64 | Windows |
| `sysv-x64` | x86-64 | System V | Linux、macOS |
| `aarch64-linux` | ARM64 | AAPCS64（Linux） | Linux、手机、云上 ARM 服务器 |

一台 Windows 开发机原生只能跑第一个。后两个需要 Linux 环境：`sysv-x64` 在 WSL2 里原生跑，
`aarch64-linux` 在 WSL2 里用 `qemu-user` 模拟跑。**观察汇编不需要运行**，clang 的
`--target` 可以为任意目标生成汇编。

## 决策

**1. 观察层与运行层分开。**
- 观察层：教案里展示的汇编，由 `scripts/` 里的脚本从课程里的 C 源码用 clang 的 `--target`
  生成，作为内容文件入库，文件头记录 clang 版本。三个平台看到的内容一致，不依赖使用者装了什么。
- 运行层：实验台调用本机工具链真正编译并运行。

**2. 运行所需工具（Windows 开发机，首要验证平台）。**
- `win-x64`：LLVM 的 clang。
- `sysv-x64`、`aarch64-linux`：WSL2 的 Ubuntu，其中 `gcc`、`gdb`、`gcc-aarch64-linux-gnu`、
  `qemu-user`、`gdb-multiarch`。

**3. 平台矩阵（真跑 / 只观察）。**

| 开发机 | `win-x64` | `sysv-x64` | `aarch64-linux` |
|---|---|---|---|
| Windows | 真跑 | 经 WSL 真跑 | 经 WSL + qemu 真跑 |
| macOS | 只观察 | 只观察（Linux 版）；Rosetta 可跑 macOS 版变体 | 只观察（Linux 版）；Apple Silicon 可跑 macOS 版变体 |
| Linux | 只观察 | 原生真跑 | 经 qemu 真跑 |

macOS 上两个变体的差异（符号名前缀下划线等）首次在 macOS 上实现时，以修订本 ADR 的方式补充；
在此之前 macOS 不声称支持运行层。**CI 里不留假装支持的探测位**（ADR 0049、0064）。

**4. 检测与指引（ADR 0057）。** 打开实验台时检测所需工具；缺什么，给出装什么、哪条命令
（如 `wsl --install Ubuntu`、`sudo apt install gcc-aarch64-linux-gnu qemu-user`），只写查起来
费事的部分。需要使用者动手的，用对话框，不写兜底降级。

**5. 实验的形态（ADR 0059）。** 固定一份 `main.c` 作驱动，负责调用汇编函数并打印结果；每个目标
一份 `.s` 骨架，默认可编译运行。学习者改动一处再运行，三个目标的输出应当一致。汇编函数是纯计算，
不使用系统调用。

**6. 检查脚本。** 校验三个目标的骨架都能用 `clang --target=…` 编译到汇编（不要求能运行，这样
没有 WSL 的机器也能过检查）；不逐字比对预生成的汇编，避免编译器升级造成噪声。

**7. 前置要求写进应用 README**：Windows 需要 WSL2 和 Ubuntu 发行版，给出安装命令。

## 后果

- Windows 上的完整体验依赖 WSL2；它出问题时，`sysv-x64` 与 `aarch64-linux` 的运行层不可用，
  观察层与 `win-x64` 不受影响。
- macOS 暂不声称支持运行层，是一个明确的欠账，实现时回来修订本 ADR。
- 单步调试（`gdb`、`gdb-multiarch` 连 `qemu -g`）是后续增强，不在首批实验台里。
