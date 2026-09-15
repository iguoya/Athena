# Athena

自用的学习软件平台。一个仓库里放**多个彼此平级的学习应用**，每个应用自带界面技术、
构建系统和内容体系，互不牵制；共用的是教学方法论，不是代码或配置格式。

## 应用

| 目录 | 应用 | 技术 |
| --- | --- | --- |
| [`apps/cpp`](apps/cpp) | C++ 教程 | GTK4 / gtkmm、Meson |
| [`apps/c`](apps/c) | C 语言编程 | Qt Quick / QML、CMake |
| [`apps/dsa`](apps/dsa) | 数据结构与算法 | Tauri + Vite |
| [`apps/english`](apps/english) | 英语学习 | Tauri + Vite |
| [`apps/mathematics`](apps/mathematics) | 数学学习 | Tauri + Vite |

每个应用怎么构建、怎么启动、怎么算就绪，都写在自己的 `app.json` 里；执行统一由
[`launcher/core`](launcher/core) 的编排器负责，没有一份应用自己的启动脚本（ADR 0046）。

C++ 教程曾经占据仓库根、是打开其他应用的必经之路；[ADR 0045](docs/decisions/0045-apps-are-peers.md)
之后它只是 `apps/` 下的一个应用，没有任何特权。

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
launcher/target/release/athena-dev list        # 谁在跑、谁没跑
launcher/target/release/athena-dev open dsa    # 打开；已在跑的只把窗口叫到前面
launcher/target/release/athena-dev stop dsa
```

一律走这些热更新入口，不要启动打包副本——那会让人不知不觉对着旧版本工作。

## 验证

```sh
python3 scripts/check.py            # 跨应用内容出处检查 + 每个应用自己的检查
python3 scripts/check.py cpp        # 只跑某个应用，余下参数透传给它
python3 scripts/check.py dsa --skip-rust   # Tauri 应用可以跳过较慢的 Rust 那段
```

CI 跑的是同一条命令，五个应用各一个 job。

## 文档

- [`AGENTS.md`](AGENTS.md)：仓库级协作规则（跨应用教学规范、应用之间的边界）。
- [`docs/decisions/`](docs/decisions)：跨应用的架构决策记录。
- `apps/<id>/AGENTS.md` 与 `apps/<id>/docs/`：各应用自己的规则与文档。

## 许可

见 [LICENSE](LICENSE)。
