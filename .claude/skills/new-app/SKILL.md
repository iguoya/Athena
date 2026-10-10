---
name: new-app
description: 在 Athena 仓库里新建一个独立应用（subjects/ 或 practice/ 下的新目录）时的完整流程——先定归类与名字、先落 ADR，再复制同栈应用的壳并逐项改名，建齐四件套，按类别补进度库与出处契约，最后在 REPOSITORY.md、根 README、根 AGENTS.md、CI 等处登记并跑结构卫生检查。使用者说「新建一个应用」「加一门课」「新开一个 subjects/xxx」「拆出一个子应用」「把素材坑转正」时使用；把一个应用拆成两个、或给考试应用新挂一个实践子课程时同样适用。
---

# 新增一个应用

加应用是这个仓库里最容易攒下混乱的操作：几乎每一类「文档与实际不符」都是加东西时漏了
别处。权威清单是 [docs/REPOSITORY.md](../../../docs/REPOSITORY.md) 末节「新增一个应用时动哪些地方」，
本 skill 不复述那份清单的理由，只把它落成可执行的步骤，并补上清单没写、但历次新增都踩过的细节。

## 0. 先定下来，再动手

下面几项任何一项没定，先用 `grill` skill 把它们问清楚，**不要边建边定**：

| 要定的 | 依据 |
|---|---|
| 归类：学习应用 / 图谱参考 / 素材坑 / `practice/` 项目应用 | REPOSITORY.md 三类判据——主问题是「要不要教会人什么、要不要证明学习者进步了」，按判据推，不查清单 |
| id 与目录名 | 完整英文单词，本领域知名缩写可以（`os`），不自造缩写、不用拼音（ADR 0097、0100、0104）；目录名与 id 一致 |
| 启动器位置：`group`（圈）与 `parent`（挂靠） | 看同圈现有应用的 `app.json`；考试应用与实践子课程的挂靠关系见 ADR 0103、0116、0118、0119 |
| 技术栈 | 判据是合不合适（ADR 0057）；跨平台优先、macOS ≈ Windows > Linux（ADR 0047、0051） |
| 学习应用另需：出处档位、方法原型、知识点前缀 | 档位：对应真实外部考试 → `exam`，否则 `open`（ADR 0043、0089）；原型：一主至多两辅（ADR 0113，初版画像见 docs/LEARNING-METHODS.md）；前缀短、全仓库唯一 |

**影响仓库结构的新决定先写 ADR 再动代码**——近期每个新应用都有一篇仓库级 ADR
（organization 0115、cs408 0116、competitions 0114）。ADR 怎么写、放哪、怎么编号，按
`grill` skill 的「落 ADR 的规矩」，ADR 单独一个提交。

## 1. 查清会冲突的号

动手前自己查，不问使用者：

```sh
# 下一个 dev 端口：取现有最大值加一（端口在 app.json、vite.config.ts、tauri.conf.json 三处出现）
grep -ho 'localhost:[0-9]*' subjects/*/app.json practice/*/app.json | sort -t: -k2 -n | tail -3
# 知识点前缀不能和别人撞：看 docs/REPOSITORY.md 名字表的第四列
# 仓库级 ADR 下一个编号
ls docs/decisions | tail -3
```

## 2. 复制最近的同栈应用做壳

不从零搭。选**技术栈相同、最近新建**的应用当壳（`app.json` 的 `dev.run` 与
`package.json` / `Cargo.toml` 一看便知）。只复制源码与配置，**不复制**
`node_modules/`、`src-tauri/target/`、`dist/`、`progress/`、`content/` 的具体内容、
对方的 `docs/decisions/` 条目。

改名必须逐项过，漏一处就是两个应用抢同一个端口或同一个数据目录：

- `app.json`：`id`、`title`、`group`、`parent`、`description`、`icon`（`letter`、`accent`、
  `symbol`）、`dev.ready.http` 端口、`dev.binary`（`athena-<id>`）、`dev.env` 里的
  `ATHENA_<ID>_ROOT`。
- `vite.config.ts` 端口；`src-tauri/tauri.conf.json` 的 `productName`、`identifier`、
  `devUrl`、窗口标题；`src-tauri/Cargo.toml` 的包名；Rust 代码里的环境变量名与发行版
  用户数据目录名（`Athena<Id>/`）。
- 本应用 `scripts/check.py` 里写死的 id、端口（如 `subjects/os` 的 `EXPECTED_ID` /
  `EXPECTED_PORT`；壳里没有就不用加）。
- 界面里的标题、文案。

改完**一定要全文搜一遍旧 id 和旧中文名**（排除 `node_modules`、`target`、`dist`、锁文件），
残留的旧名字比漏改配置更难发现——organization 复制 linux 的壳时，就顺手修掉了更早从
dsa 带过来的标题文案。锁文件（`package-lock.json`、`Cargo.lock`）重新生成，不手改。

## 3. 四件套与按类别的附加物

四件套缺一个，`check.py --sources-only` 的结构卫生检查就会报：

- **`AGENTS.md`**：本应用规则。参照 `subjects/cs408/AGENTS.md` 的骨架：
  - 定位：属于哪一类、按什么判据；挂靠关系；学习应用写**出处档位**与**方法原型**
    （主原型决定首页入口与单元块顺序）。
  - 技术栈：壳来自哪个应用要写，但写成「最初复制自 X，此后独立演进」——**不写**「沿用 X 的
    做法」「对齐 X 的 ADR」（ADR 0062：约束不继承，本应用也成立的做法自己写下理由）。
  - 端口、进程名、知识点前缀、进度库位置。
  - 开发与验证命令。
- **`CLAUDE.md`**：只写 `@AGENTS.md`（ADR 0061）。
- **`README.md`**：一段定位与入口。
- **`scripts/check.py`**：本应用验证入口（ADR 0007）。没有它，根入口会静默跳过这个应用。

按类别再加：

- **学习应用**：进度库 `progress/learning.db` 由应用首次运行时建，建出来后进版本库
  （ADR 0037、0053）；`content-contract.json`
  按档位声明 `tier`（`exam` 阻断、`open` 只报告，字段格式照抄现有契约）；
  `docs/decisions/README.md` 建应用级 ADR 索引。
- **图谱/参考类**：不建进度库、不建出处契约，教学规范不生效。
- **`practice/`**：不建进度库，教学规范不生效；打开命令要加 `--root practice`。
- **图标**（ADR 0065）：画 `icon.svg`，在 `app.json` 的 `icon.renders` 声明要出的位图，
  然后用启动器渲染：

  ```sh
  launcher/target/release/launcher icons          # 写入位图
  launcher/target/release/launcher icons --check  # 只核对
  ```

  注意：本机 PATH 上的 `launcher` 可能是别的程序（PyCharm 也带一个），用仓库里的二进制。

## 4. 登记

启动器靠目录自动发现，不改代码（ADR 0046）。但文档与工作流必须登记，漏登不会报错，
等发现时文档里早已是幽灵行或缺口：

| 位置 | 改什么 | 检查拦不拦 |
|---|---|---|
| `docs/REPOSITORY.md` 结构树 | 加一行 | 拦（与实际目录对账） |
| `docs/REPOSITORY.md` 名字表 | 加一行：目录/id、界面、进程、前缀 | 拦（只对 `subjects/`） |
| 根 `README.md` 应用表 | 加一行 | 拦 |
| 根 `AGENTS.md`「仓库结构」代码块 | 学科清单里加上 id | **不拦**，靠自觉 |
| 根 `AGENTS.md` 与 `docs/TEACHING.md` 的考试档清单 | `exam` 档才加 | **不拦** |
| `docs/LEARNING-METHODS.md` 各课程方法画像表 | 学习应用加一行主/辅原型 | **不拦** |
| `.github/workflows/ci.yml` | 对应技术栈的 job/矩阵、job 级 `if` 过滤、`workflow_dispatch` 的 `options` | 只拦幽灵项，**漏登不拦** |
| `.github/workflows/release.yml` | 要发布才加，`publish` 的校验和清单与资产通配都要覆盖（ADR 0081） | 拦（发布必须先有 CI） |

改 `AGENTS.md`、`docs/` 这类共享文件前，先 `git status` 看有没有别的代理的未提交改动——有就
先停下告诉使用者（根 AGENTS.md「多个代理并行」）。改规则性文字时先改 `docs/` 原文，
再同步 AGENTS.md 里对应那一行（ADR 0061）。

## 5. 验证与提交

```sh
python3 scripts/check.py --sources-only   # 结构卫生、skill 两处一致、出处、工作流
python3 scripts/check.py <id>             # 本应用自己的检查
cargo test --manifest-path launcher/Cargo.toml -p launcher-core mindmap   # 新圈/新挂靠时跑，看布局
launcher/target/release/launcher open <id>    # 真的打开一次（practice 加 --root practice）
```

拆成几个提交：**ADR** → **应用目录本身** → **登记**（文档与工作流）。提交只加自己的文件。
整个新目录都是你建的时，按文件逐个加，不用目录参数（项目 hook 会拦 `git add <目录>`）：

```sh
git ls-files --others --exclude-standard -z subjects/<id> | xargs -0 git add --
```

加之前用 `git status --short subjects/<id>` 确认里面只有你的文件，并且构建产物都已被忽略
（结构卫生检查也会核对 `target`、`node_modules` 是否被 `.gitignore` 覆盖）。
