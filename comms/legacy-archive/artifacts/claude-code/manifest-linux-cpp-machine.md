# T-901 清单：Linux / C++ / 汇编及杂项

生成器 [build_manifest.py](build_manifest.py)，结果 [manifest-linux-cpp-machine.json](manifest-linux-cpp-machine.json)，
校验 [verify-linux-cpp-machine.txt](verify-linux-cpp-machine.txt)。范围内 507 个被跟踪文件**全部**被某个单元覆盖（零遗漏）。

## 统计
- 119 个单元：keep 109、并入工程 4、重复 2、第三方 1、垃圾 3。
- keep 去向：c-plus-plus 82、linux 16、machine 5、c-gui-lab 5（SDL）、qt 1（Practice/XNode）。
- 本机 g++ 15.2 / gcc 实测 86 个单元，73 个编译通过；13 个失败的原因：缺 boost（2）、缺 cgicc、缺 Linux 头文件（内核模块、sys/wait.h 等，预期）、`/usr/include` 老路径、多文件 extern 示例需联编、`limits` 与 `variable_limit` 的整数溢出常量在 C++20 下报错等。逐条失败原因在 json 的 `build` 字段。

## 要点
1. `Practice/CPP`（38 个独立小程序）与 `Linux/CPlusPlus/*`（按章节的目录）**内容几乎不重合**（仅 1 个文件相同），都保留，前者按文件拆单元。
2. `Practice/CGI` 与 `Linux/CPlusPlus/33-cgi` 内容相同；`Practice/Assembly` 与 `Linux/CPlusPlus/0-assembly` 重叠，已标 drop-duplicate，规范版见 json 的 `duplicates`。
3. `Linux/UnitTest/App` 是 googletest 官方 samples 原样拷贝（第三方，不收）；其余四个 gtest 工程是 Qt Creator 模板级的，价值低，建议最多合成一条。
4. `Linux/SDL/3-line` 是 Anjuta 自动生成的 autotools 样板，只剩一个 main.c，已 drop。
5. `Practice/XNode`（Qt 网络节点工程，44 个源码文件）按内容归 `qt` 应用，已通知 cursor 并入 T-101 清单，避免两边都列。
6. `Practice/Vue` 是 3 个文件的空壳，drop。
7. `Linux/CPlusPlus/FrameWork` 的工厂/单例已并入 C++ 综合工程，是否与设计模式清单里的 Factory/Singleton 重复，由 T-001 清单核对后我合并。

## 待裁决（leader 自决，已决）
- C 语言基础（栈溢出、指针、glade 界面）归 `machine`（它是“C 与机器”），不是 `linux`。
- Linux 的 pthread / fork / 内核模块条目 `run` 标 `linux-only`：Windows 上经 WSL 运行，本机 WSL 现状见记忆，不作为验收阻断。
