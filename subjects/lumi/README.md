# Lumi 英语学习

给一位英语师范专业大一学生用的桌面英语学习软件：先夯实高中英语，再依次准备四级、专四、六级、专八。设计决策见 [adr/](adr/README.md)。

## 在 Windows 上运行

需要先装好：

1. [Node.js](https://nodejs.org/) 22 或更新，然后运行 `corepack enable` 启用 pnpm。
2. [Rust](https://www.rust-lang.org/tools/install)（rustup，默认的 MSVC 工具链）。
3. Microsoft C++ 生成工具，安装时勾选“使用 C++ 的桌面开发”。WebView2 在 Windows 10/11 上一般已经自带。

然后在仓库根目录运行：

```bash
pnpm install
pnpm tauri dev      # 开发模式，改代码会自动刷新
pnpm tauri build    # 打包安装程序，输出在 src-tauri/target/release/bundle/nsis/
```

平时开发可以直接双击根目录的“启动 Lumi（开发版）.cmd”：自动拉最新代码、装依赖、编译并运行。

只看界面也可以用 `pnpm dev`，在浏览器打开 http://localhost:1420 。

## 自动更新

推送到 master 后，GitHub Actions 会编译签名安装包并发布到 Releases；装好的软件每次启动会自动检查并更新。第一次使用前要设置签名密钥，步骤见 [ADR 0018](adr/0018-auto-update.md)。

## 常用命令

| 命令             | 作用                |
| ---------------- | ------------------- |
| `pnpm lint`      | ESLint 检查         |
| `pnpm format`    | Prettier 格式化     |
| `pnpm typecheck` | TypeScript 类型检查 |
| `pnpm test`      | Vitest 单元测试     |

## 目录

| 位置                   | 内容                                         |
| ---------------------- | -------------------------------------------- |
| `src/`                 | 界面：React + TypeScript + Tailwind + Motion |
| `src/styles/index.css` | 三套皮肤的设计变量（晨光、极光、手账）       |
| `src-tauri/`           | 桌面外壳和本地层（Rust）                     |
| `content/`             | 课程内容（JSON），来源和版权见 ADR 0019      |
| `scripts/content/`     | 开放资源导入脚本                             |
| `adr/`                 | 架构决策记录                                 |
| `archive/`             | 2020 年旧作文站，只作历史记录                |
