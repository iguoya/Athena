# ADR 0176：把六个散乱的 GitHub 旧仓库并入对应教学应用的「历史归档」章节

- 日期：2026-10-21
- 状态：已接受（使用者 2026-10-21：「Practice、Linux、algorithm、DesignPatterns、Qt5、DesignPattern 太杂乱了，整体目标是归档这些仓库，把精华合并到 Athena 中；按内容分类，统一集成在对应程序里被集中调用；设计模式在现有 Tauri 程序里单独设历史归档章节，数据结构和算法同理；尽可能保持原有代码，并在最新程序里批注指出写法和组织上的不足；Linux、Qt5 没有现成教学程序的就新建，作为归档性质；各自独立设历史归档章节，省得干扰原本的软件设计规范」；追加：GTK（C）归 c-gui-lab，gtkmm 归**新建**的 gtkmm 项目、不与现有 gtkmm 文档应用重合，汇编归 machine）
- 关系：不改嫁规则见根 `AGENTS.md`（ADR 0129）；公域数据规则见 ADR 0159；多代理协作走 ADR 0165 的舱；新应用走 `new-app` 流程；共用壳见 ADR 0161

## 背景

1. 六个旧仓库（`Practice`、`Linux`、`algorithm`、`DesignPatterns`、`DesignPattern`、`Qt5`）是 2018–2023 年的练习堆，共约 7000 个被跟踪文件。调用方式各异（Qt Creator 工程、Makefile、CodeLite、手敲 g++），没有统一入口。
2. 它们之间大量重复：对 `.cpp/.h/.c/.md/.qml/.ui/.py` 做内容哈希，1217 份不同内容里有 588 份出现在两个以上仓库；设计模式那批代码在 5 处各存一份。`Linux` 里还混着第三方库（`Algorithm/qdarkstyle` 481 个文件）、`GTK/` 的 1635 个文件和 Qt 书籍样例（`Sample/chap*`）。
3. Athena 里已有对口的教学应用，但现有壳的实验引擎只能编译**单个** `main.cpp`（`packages/athena-course-shell` 的 `compile_command`、`case_path`），装不下旧代码的多文件工程。

## 决策

1. **目标应用对照**（按内容分，不按来源仓库分）：

   | 内容 | 目标 | 说明 |
   |---|---|---|
   | 设计模式（5 处重复 + `algorithm/design-patterns` 笔记） | `programming/design-patterns` | 现有 |
   | 数据结构 | `postgraduate/data-structures` | 现有 |
   | 算法（含递归、分治、回溯） | `postgraduate/algorithms` | 现有 |
   | C++ 语言基础（类、多态、容器、线程） | `programming/c-plus-plus` | 现有 |
   | Linux 进程、线程、驱动、C 编程、单元测试 | `programming/linux` | 现有 |
   | 汇编 | `programming/machine` | 现有 |
   | GTK（C 语言） | `practice/c-gui-lab` | 现有项目应用，不建进度库 |
   | gtkmm（C++） | **新建** `programming/gtkmm-lab` | 与 `guide/gtkmm`（官方手册精读）互不引用、互不干扰 |
   | Qt Widgets / QML / PyQt / Qt 书籍样例 | **新建** `programming/qt` | 归档为主，学习应用 |
   | CGI、Vue、XNode、杂项 | 逐项评估 | 无教学价值的显式删除（记入清单，原仓库可取回） |

2. **每个目标应用只新增一个章节「历史归档」**，放在课程最后，`layer: "archive"`（与 `topic`、`extension` 同级，界面标签「归档 ·」）。**不插入、不改动现有章节与知识点**，原有的设计规范不受干扰；使用者日后人工审视后决定留、并入主线还是删。
3. **一个归档条目 = 一个历史练习单元**（一个模式、一个数据结构、一个小工程）。条目含：
   - 出处行：来源仓库、路径、首次提交日期（从 git 取，不凭印象）；
   - **原代码原样保留**：放 `content/cases/arc_<slug>/`，保持原文件名与目录，只在必要时加最小修改使其可编译，修改处用 `// [ARCHIVE]` 标注；
   - **批注**（新写）：指出原代码在写法和程序组织上的不足（命名、职责、资源管理、耦合、可测试性、与本课现行规范的差距），能指向本应用现行章节的就指过去，不泛泛说教；
   - 能运行的配实验入口（跑原样代码，不要求补骨架——它是历史产物，ADR 0059 的骨架要求对归档条目不适用，但必须原样能跑）。
4. **去重**：同一内容多处出现，只留一份**规范版**（取最新、最完整的），其余在条目出处行注明「重复于 X」，不重复入库。第三方库（qdarkstyle、GTK 官方样例、他人书籍样例的整套拷贝）不入库，在清单里记「第三方，不收」与原始来源。书籍样例若是使用者自己跟练并改过的，按原创处理。
5. **能不能运行分级**，写进条目元数据 `run`：
   - `cli`：本机编译器即可（设计模式、数据结构、算法、C++ 基础）——必须能一键跑；
   - `toolchain`：需要 Qt、GTK、SDL 等库（`qt`、`gtkmm-lab`、`c-gui-lab` 的条目）——检测不到工具链时给安装指引，不假装能跑；
   - `linux-only`：依赖 Linux 内核或 POSIX（进程、驱动）——Windows 上走 WSL 或如实降级；
   - `read-only`：只看代码与批注。
6. **多文件运行支持是共用壳的新能力**：`athena-course-shell` 增加可选的多文件案例（`sources` 列表或整目录编译），旧的单 `entrypoint` 案例行为不变。该改动由 leader 在 `release-next` 舱对壳的改动落地后实施；各应用的前端渲染 `archive` 层各自实现（应用之间不共享前端代码，ADR 0132）。
7. **执行方式**：先产出清单、后搬内容。第一步由 ZCode、Cursor 各按领域**只读**生成清单（单元划分、去重、第三方判定、运行分级、目标应用），leader 审定后才批量搬运和写批注。搬运前先提交一版原样（根 `AGENTS.md` 的要求），删除要显式、提交信息写清删了什么和取回方式。舱名 `legacy-archive`，领导者 claude-code。
8. **新应用 `qt`、`gtkmm-lab`** 各按 `new-app` 流程建立（壳复制自同栈应用、四件套、进度库声明、登记）。因为内容是归档性质，首批交付物就是「历史归档」章节里经批注的条目；不为凑结构硬写空章节（ADR 0129）。Qt 工具链现状：本机为 Qt 6.8.1（MSVC），旧代码是 Qt5，条目若需小改才能编译，用 `// [ARCHIVE]` 标出。
9. **原仓库的处置**：全部条目验收后，使用者确认再在 GitHub 上把六个仓库设为 archived（可逆，历史完整保留）。在此之前不动远程。

## 后果

- 各目标应用的 `content/curriculum.json` 各增一个 `archive` 层章节；`scripts/check.py` 对该层放宽「骨架」「出处档位」检查，但仍校验：条目有出处行、原代码目录存在、`run` 分级合法。
- 仓库体积增加（去重后预计数十 MB 量级）；大二进制（图片、`.bmp`、编译产物）不收，除非条目必需。
- 新增两个应用意味着启动器里多两个入口，发版清单暂不加入（ADR 0168 标准，等内容稳定）。
- 本 ADR 只定归并的规则与去向；每个应用里的具体条目清单由清单任务产出，放在 `comms/legacy-archive/artifacts/`。
