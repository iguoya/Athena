# Athena

自用的学习软件平台。一个仓库里放**多个彼此平级的学习应用**，每个应用自带界面技术、
构建系统和内容体系，互不牵制；共用的是教学方法论，不是代码或配置格式。

## 应用

`subjects/` 是课程学科（学习应用 + 图谱/参考类），`practice/` 是项目应用（ADR 0060）。
分类判据见 [`AGENTS.md`](AGENTS.md)：要不要教会人什么、要不要证明学习者进步了。

| 目录 | 应用 | 技术 |
| --- | --- | --- |
| [`subjects/c-plus-plus`](subjects/c-plus-plus) | C++ 教程 | GTK4 / gtkmm、Meson |
| [`subjects/machine`](subjects/machine) | C 与机器（C 与汇编） | Qt Quick / QML、CMake |
| [`subjects/data-structures`](subjects/data-structures) | 数据结构（408，原 dsa 拆分 ADR 0108） | Tauri 2 + Vite |
| [`subjects/algorithms`](subjects/algorithms) | 算法设计（408，原 dsa 拆分 ADR 0108） | Tauri 2 + Vite |
| [`subjects/ascent`](subjects/ascent) | 拾阶（四六级 / 专四专八） | Tauri + Vite |
| [`subjects/mathematics`](subjects/mathematics) | 数学学习 | Tauri + Vite（Python sidecar） |
| [`subjects/math-tools`](subjects/math-tools) | 数学工具（图谱/参考类） | Tauri + Vue 3 |
| [`subjects/driver`](subjects/driver) | 驾考学习 | Flutter 桌面 |
| [`subjects/software`](subjects/software) | 软件设计师（软考中级备考） | Tauri 2 + React |
| [`subjects/embedded`](subjects/embedded) | 嵌入式系统设计师（软考中级备考，ADR 0090） | Tauri 2 + Vue 3 |
| [`subjects/firmware`](subjects/firmware) | 嵌入式程序设计实验（电子信息圈，ADR 0103、0123） | Tauri 2 + Vue 3 |
| [`subjects/microcontroller`](subjects/microcontroller) | 硬件实验台（电子信息圈，ADR 0103、0123） | Tauri 2 + Vue 3 |
| [`subjects/rtos`](subjects/rtos) | 实时操作系统（电子信息圈，ADR 0106、0123） | Tauri 2 + Vue 3 |
| [`subjects/database`](subjects/database) | 数据库 SQL 实验室（计算机圈，ADR 0103、0126） | Tauri 2 + React |
| [`subjects/linux`](subjects/linux) | Linux 程序设计（程序设计圈，ADR 0109、0111） | Tauri 2 + Vite |
| [`subjects/gtkmm`](subjects/gtkmm) | gtkmm 官方教程精读 | Tauri 2 + React |
| [`subjects/polaris`](subjects/polaris) | 北极星（技术体系图谱） | Tauri 2 + React |
| [`subjects/organization`](subjects/organization) | 计算机组成原理（408，ADR 0115） | Tauri 2 + Vite |
| [`subjects/os`](subjects/os) | 操作系统实验（408，ADR 0103、0104） | Tauri 2 + React |
| [`subjects/network`](subjects/network) | 计算机网络（408，ADR 0103） | Tauri 2 + React |
| [`subjects/cs408`](subjects/cs408) | 408 计算机学科专业基础（考研考试主应用，ADR 0116） | Tauri 2 + Vite |
| [`subjects/python`](subjects/python) | Python 与 AI 工具链（「人工智能」圈首门课，ADR 0120） | Tauri 2 + React |
| [`subjects/machine-learning`](subjects/machine-learning) | 机器学习基础（「人工智能」圈，ADR 0120、0122） | Tauri 2 + React |
| [`subjects/deep-learning`](subjects/deep-learning) | 深度学习与 PyTorch（「人工智能」圈，ADR 0120、0122） | Tauri 2 + React |
| [`subjects/llm-app`](subjects/llm-app) | 大模型应用开发（「人工智能」圈，ADR 0120、0122） | Tauri 2 + React |
| [`subjects/llm-finetune`](subjects/llm-finetune) | 大模型微调与部署（「人工智能」圈，ADR 0120、0122） | Tauri 2 + React |
| [`subjects/competitions`](subjects/competitions) | 赛历（竞赛清单与参赛资格，图谱/参考类，ADR 0114） | Tauri 2 + Vite |
| [`subjects/design-patterns`](subjects/design-patterns) | 设计模式与程序组织（「程序设计」圈，ADR 0121） | Tauri 2 + Vite |
| [`practice/pocket_cube`](practice/pocket_cube) | 2 阶魔方 | GTK4 / gtkmm |
| [`practice/nas_admin`](practice/nas_admin) | 驾考中心服务后台 | Flask-AppBuilder |
| [`practice/c-gui-lab`](practice/c-gui-lab) | C 语言 GUI 框架对比实验室 | Electron + GTK/ImGui/LVGL |

每个应用怎么构建、怎么启动、怎么算就绪，都写在自己的 `app.json` 里；执行统一由
[`launcher/core`](launcher/core) 的编排器负责，没有一份应用自己的启动脚本（ADR 0046）。

C++ 教程曾经占据仓库根、是打开其他应用的必经之路；[ADR 0045](docs/decisions/0045-apps-are-peers.md)
之后它只是 `subjects/` 下的一个应用，没有任何特权。

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
- `subjects/<id>/AGENTS.md` 与 `subjects/<id>/docs/`：各应用自己的规则与文档。

## 许可

见 [LICENSE](LICENSE)。
