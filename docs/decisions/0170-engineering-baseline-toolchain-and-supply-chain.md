# ADR 0170：工程基线补强——工具链钉版本、Rust 格式、供应链与密钥扫描、推送前钩子

- 日期：2026-10-18
- 状态：已接受（使用者：从软件开发规范化、成熟化角度补齐，先易后难）
- 关系：补充 [ADR 0007](0007-unified-check-entry.md)（统一验证入口）；不改 [ADR 0064](0064-ci-explicit-trigger.md)（CI 显式触发）；出处与合规边界按 [ADR 0159](0159-jiuzhou-academic-layer-in-repo.md)，不查许可证。

## 背景

对照「规范化、成熟化」盘点，Athena 的统一入口、ADR、CHANGELOG、发版脚本、工作流校验都已经到位。缺的是几处**让既有流程不被环境悄悄改变**的东西：

- 编译器和 Node 都跟「最新」走：发版工作流用 `dtolnay/rust-toolchain@stable`，Node 在八处写死 `22`。哪天 stable 升一版，已经全绿的构建可能变红，本地和 CI 也可能用着不同的编译器。
- Rust 代码从没跑过 rustfmt：140 个 `.rs` 里 32 个不符合默认风格，diff 里混着排版噪音，也没有检查守着。
- 没有任何密钥或依赖漏洞扫描。Dependabot 只管版本落后；`driver` 连着中心 PostgreSQL，密钥进历史就删不干净。
- 日常提交不触发 CI（ADR 0064），推送前没有任何自动拦截。

## 决策

1. **工具链钉在一处。** Rust 钉在仓库根的 `rust-toolchain.toml`（具体版本号，带 rustfmt、clippy），两个 Cargo 工作区（仓库根与 `launcher/`）同时受它约束；Node 钉在 `.node-version`，工作流一律用 `node-version-file` 读它。发版工作流的 `dtolnay/rust-toolchain` 版本号必须与 `rust-toolchain.toml` 相同。升级时三处一起改，由 `scripts/hygiene.py` 的「工具链一致」检查对账，不靠记忆。
2. **Rust 格式用 rustfmt 默认风格，不写 `rustfmt.toml`。** 默认风格是社区共识，少一份要维护的配置。一次性全仓库格式化作为独立提交（只有排版，无逻辑改动），此后「Rust 格式」检查守住两个工作区。
3. **安全扫描单独成 `check.py --security`，在 CI 的跨应用任务里跑。**
   - gitleaks 扫全部提交历史与工作区，**阻断**；已核实的误报登记在 `.gitleaks.toml`，不放宽规则本身。首次全历史扫描（253 个提交）的 20 条命中全部是误报（牛津词表 CSV 里的音频文件名；驾考测试里的业务概念 `draftKey`）。
   - cargo-deny 只查漏洞公告（`deny.toml`），**只报告**；不查许可证与重复版本（自用软件，ADR 0159；重复版本由 Tauri 间接依赖决定）。
   - `pnpm audit --prod` **只报告**。
   - 后两项不阻断的理由：Tauri 的 Linux 依赖里有 gtk3 绑定停止维护这类我们治不了的公告，阻断只会让 CI 常年红。看清现状、处理掉能处理的之后，再升级为阻断。
   - 工具用固定版本的发布二进制（gitleaks 8.30.0、cargo-deny 0.18.9），不走 `cargo install`。
4. **推送前钩子。** `scripts/hooks/pre-push` 只转调 `check.py --sources-only`（便宜、不含平台构建），用 `python3 scripts/install_hooks.py` 启用（设置本仓库的 `core.hooksPath`）。这是 ADR 0064 之外唯一的自动拦截，不改变 CI 的显式触发；临时绕过用 `git push --no-verify`。
5. **`.editorconfig`、`CODEOWNERS` 补齐。** `.editorconfig` 只写全仓库成立的规则（UTF-8、LF、末尾换行、去行尾空白），缩进只给已有惯例的语言（Python、Rust 四格，前端与 Dart 两格），不替没有共识的类型拍板。`CODEOWNERS` 单人维护，全部归仓库所有者，让「谁该审」有显式答案。

## 没有做的，以及为什么

- **GitHub Actions 钉提交 SHA**：需要读取各 action 仓库的标签对应的提交，云会话读不了那些仓库；`dependabot.yml` 已有 `github-actions` 生态，钉 SHA 后它也能继续维护。登记进 `docs/HANDOFF.md`，由本地代理用 `pinact` 一类工具一次做完。
- **主分支保护**：是 GitHub 仓库设置，不在代码里，也不是云会话能改的。登记进 `docs/HANDOFF.md`。
- **cargo-deny 公告库的首跑**：云里连不上 RustSec 公告库，只验证了配置能被解析（`cargo deny check bans` 通过）。首次真实结果以 CI 为准。

## 后果

- `check.py` 默认入口与 `--sources-only` 多两项：工具链一致、Rust 格式；新增 `--security`。检查逻辑在 `scripts/hygiene.py`，不再往 `check.py` 里堆。
- 本机多需要 `gitleaks`、`cargo-deny` 才能跑 `--security`；缺工具时报错并给安装命令（与 actionlint 同口径）。不跑 `--security` 的日常检查不受影响。
- 仓库根新增 `.editorconfig`、`.node-version`、`rust-toolchain.toml`、`.gitleaks.toml`、`deny.toml`，已登记进结构卫生的根目录白名单。
- 首次扫描就发现两条真实依赖公告，见下，未随本 ADR 处理：
  - `maplibre-gl`（`mentor/jiuzhou`）：当前 5.24.0，公告要求升到 6.4.1 以上，是跨大版本升级，需要在真机上验证地图渲染。
  - `katex`（`certification/embedded`）：当前 0.16.47，低危，公告要求 0.18.2 以上。
  两处在自用本地应用里都不是可利用路径（地图与公式内容都是自己的），按风险排期，不借本 ADR 盲升。
