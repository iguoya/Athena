# Athena

自用的学习软件平台。一个仓库里放**多个彼此平级的学习应用**，每个应用自带界面技术、
构建系统和内容体系，互不牵制；共用的是教学方法论，不是代码或配置格式。

## 应用

`course/` 是课程学科，`postgraduate/` 是考研应用（408 与考研公共课，ADR 0149），`practice/` 是项目应用（ADR 0060）。
分类判据见 [`AGENTS.md`](AGENTS.md)：要不要教会人什么、要不要证明学习者进步了。

| 目录 | 应用 | 技术 |
| --- | --- | --- |
| [`course/c-plus-plus`](course/c-plus-plus) | C++ 教程 | Tauri 2 + React |
| [`course/machine`](course/machine) | C 与机器（C 与汇编） | Qt Quick / QML、CMake |
| [`postgraduate/data-structures`](postgraduate/data-structures) | 数据结构（408，原 dsa 拆分 ADR 0108） | Tauri 2 + Vite |
| [`postgraduate/algorithms`](postgraduate/algorithms) | 算法设计（408，原 dsa 拆分 ADR 0108） | Tauri 2 + Vite |
| [`postgraduate/ascent`](postgraduate/ascent) | 拾阶（四六级 / 专四专八） | Tauri + Vite |
| [`postgraduate/mathematics`](postgraduate/mathematics) | 数学学习 | Tauri + Vite（Python sidecar） |
| [`tools/math-tools`](tools/math-tools) | 数学工具 | Tauri 2 + React |
| [`certification/driver`](certification/driver) | 驾考学习 | Flutter 桌面 |
| [`certification/software`](certification/software) | 软件设计师（软考中级备考） | Tauri 2 + React |
| [`certification/embedded`](certification/embedded) | 嵌入式系统设计师（软考中级备考，ADR 0090） | Tauri 2 + React |
| [`course/firmware`](course/firmware) | 嵌入式程序设计实验（电子信息圈，ADR 0103、0123） | Tauri 2 + React |
| [`course/microcontroller`](course/microcontroller) | 硬件实验台（电子信息圈，ADR 0103、0123） | Tauri 2 + React |
| [`course/rtos`](course/rtos) | 实时操作系统（电子信息圈，ADR 0106、0123） | Tauri 2 + React |
| [`course/database`](course/database) | 数据库 SQL 实验室（计算机基础圈，ADR 0103、0126、0148） | Tauri 2 + React |
| [`course/linux`](course/linux) | Linux 程序设计（程序设计圈，ADR 0109、0111） | Tauri 2 + Vite |
| [`guide/gtkmm`](guide/gtkmm) | gtkmm 官方教程精读（手册类，ADR 0143） | Tauri 2 + React |
| [`mentor/polaris`](mentor/polaris) | 北极星（技术体系图谱，ADR 0144） | Tauri 2 + React |
| [`postgraduate/organization`](postgraduate/organization) | 计算机组成原理（408，ADR 0115） | Tauri 2 + Vite |
| [`postgraduate/os`](postgraduate/os) | 操作系统实验（408，ADR 0103、0104） | Tauri 2 + React |
| [`postgraduate/network`](postgraduate/network) | 计算机网络（408，ADR 0103） | Tauri 2 + React |
| [`postgraduate/cs408`](postgraduate/cs408) | 408 计算机学科专业基础（考研考试主应用，ADR 0116） | Tauri 2 + Vite |
| [`course/python`](course/python) | Python 与 AI 工具链（「程序设计」圈，人工智能路线入口，ADR 0120、0148） | Tauri 2 + React |
| [`course/machine-learning`](course/machine-learning) | 机器学习基础（「人工智能」圈，ADR 0120、0122） | Tauri 2 + React |
| [`course/deep-learning`](course/deep-learning) | 深度学习与 PyTorch（「人工智能」圈，ADR 0120、0122） | Tauri 2 + React |
| [`course/llm-app`](course/llm-app) | 大模型应用开发（「人工智能」圈，ADR 0120、0122） | Tauri 2 + React |
| [`course/llm-finetune`](course/llm-finetune) | 大模型微调与部署（「人工智能」圈，ADR 0120、0122） | Tauri 2 + React |
| [`mentor/competitions`](mentor/competitions) | 赛历（竞赛清单与参赛资格，图谱/参考类，ADR 0114、0144） | Tauri 2 + Vite |
| [`course/design-patterns`](course/design-patterns) | 设计模式与程序组织（「程序设计」圈，ADR 0121） | Tauri 2 + Vite |
| [`practice/pocket_cube`](practice/pocket_cube) | 2 阶魔方 | GTK4 / gtkmm |
| [`practice/nas_admin`](practice/nas_admin) | 驾考中心服务后台 | Flask-AppBuilder |
| [`practice/c-gui-lab`](practice/c-gui-lab) | C 语言 GUI 框架对比实验室 | Electron + GTK/ImGui/LVGL |
| [`practice/earth`](practice/earth) | 地球（真实比例的地球分层 3D 可视化，ADR 0128） | Tauri 2 + React + Three.js |
| [`practice/cpp`](practice/cpp) | C++ 旧窗口（gtkmm，从 C++ 教程拆出，ADR 0141） | GTK4 / gtkmm |

每个应用怎么构建、怎么启动、怎么算就绪，都写在自己的 `app.json` 里；执行统一由
[`launcher/core`](launcher/core) 的编排器负责，没有一份应用自己的启动脚本（ADR 0046）。

C++ 教程曾经占据仓库根、是打开其他应用的必经之路；[ADR 0045](docs/decisions/0045-apps-are-peers.md)
之后它只是 `course/` 下的一个应用，没有任何特权。

## 打开应用

用 [`launcher/`](launcher) 的启动器，一张列表列出全部应用，点一下就打开，
已经在跑的只把窗口提到前面：

```sh
cargo build --release --manifest-path launcher/Cargo.toml   # 先备好编排器与界面
launcher/target/release/athena-launcher                     # 跨平台：托盘常驻 + 列表窗口
launcher/macos/scripts/install.sh                           # macOS：菜单栏常驻，⌃⌥A 唤出
```

终端里也能用同一个编排器：

```sh
launcher/target/release/launcher list        # 谁在跑、谁没跑
launcher/target/release/launcher open data-structures   # 打开；已在跑的只把窗口叫到前面
launcher/target/release/launcher stop data-structures
```

一律走这些热更新入口，不要启动打包副本——那会让人不知不觉对着旧版本工作。

## 验证

```sh
python3 scripts/check.py            # 跨应用内容出处检查 + 每个应用自己的检查
python3 scripts/check.py c-plus-plus       # 只跑某个应用，余下参数透传给它
python3 scripts/check.py data-structures --skip-rust   # Tauri 应用可以跳过较慢的 Rust 那段
```

CI 跑的是同一条命令（显式触发，ADR 0064）：每个应用各占矩阵位，另有跨应用检查；
打版本 tag 时全量跑。

## 文档

- [`AGENTS.md`](AGENTS.md)：仓库级协作规则（跨应用教学规范、应用之间的边界）。
- [`docs/decisions/`](docs/decisions)：跨应用的架构决策记录。
- `course/<id>/AGENTS.md` 与 `course/<id>/docs/`：各应用自己的规则与文档。

## 许可

见 [LICENSE](LICENSE)。
