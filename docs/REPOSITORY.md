# 仓库结构与独立应用

> 本文是根 [`AGENTS.md`](../AGENTS.md) 中「仓库结构」「独立应用」两节的**完整原文**，2026-09-26 按
> [ADR 0061](decisions/0061-agent-instructions-single-source.md) 从 AGENTS.md 移出，未删减。
> AGENTS.md 只留规则要点，要点是本文的摘要，不得与本文冲突；改规则时先改本文，
> 再同步 AGENTS.md 里对应的那一行。

## 仓库结构

```
subjects/<id>/ 课程学科学习：一个目录一个独立应用，彼此完全平级
  cpp/         C++ 教程（GTK4 / gtkmm，原来的"主程序"）
  machine/     C 与机器（Qt Quick / QML，原 c/，ADR 0005）
  dsa/         数据结构与算法（Tauri）——软设第 3、8 章实践课程，挂靠 software
               （ADR 0092、0099；原 algorithm，复名见 ADR 0105）
  english/     磨砚（考研英语二，Tauri）
  ascent/      拾阶（英语师范生四六级、专四专八，Tauri）
  mathematics/ 数学学习（Tauri）
  math-tools/  数学工具（Tauri）——数学学习的配套工具，图谱/参考类，不是学习应用（ADR 0084）
  driver/      驾考学习（Flutter 桌面，科目一 / 科目四）
  software/    软考中级·软件设计师备考（Tauri 2 + React）——以考试为学科，与 driver 同构；
               各为一级大类「计算机」（ADR 0102）
  embedded/    嵌入式系统设计师备考（Tauri 2 + Vue 3）——从 software（原 softcert）拆出，
               一级大类「电子信息」（ADR 0090、0102；定名见 ADR 0097、0100）
  database/         数据库 SQL 实验室（Tauri 2 + React）——软设第 9 章实践课程，挂靠 software（ADR 0103）
  design-patterns/  设计模式编码实验（Tauri 2 + React）——软设第 7 章实践课程，挂靠 software；
                    原素材坑转正（ADR 0103）
  os/               操作系统实验（Tauri 2 + React）——软设第 4 章实践课程，挂靠 software
                    （ADR 0103；原 operating-system，改名见 ADR 0104）
  network/          网络与信息安全实验（Tauri 2 + React）——软设第 10 章实践课程，挂靠 software（ADR 0103）
  firmware/         嵌入式程序设计实验（Tauri 2 + Vue 3）——嵌入第 6/8/11 章实践课程，挂靠 embedded（ADR 0103）
  microcontroller/  硬件实验台（Tauri 2 + Vue 3）——嵌入第 2/5 章实践课程，挂靠 embedded（ADR 0103）
  rtos/             实时操作系统（Tauri 2 + Vue 3）——嵌入第 4 章实践课程，挂靠 embedded（ADR 0106）
  gtkmm/       gtkmm 官方教程精读（Tauri 2 + React）
  polaris/       技术体系图谱（Tauri 2 + React，原 Qt 壳已退役，ADR 0015）——不是学习应用，见下文
  organization/  计算机组成原理（Tauri 2 + Vite）——408 组成原理，挂靠 cs408、引用挂到 software（ADR 0115、0116）
  cs408/         408 计算机学科专业基础（Tauri 2 + Vite）——考研考试主应用，「考研」圈；数据结构、算法设计、
                 操作系统、计算机网络以引用挂在它下面（ADR 0116）
  competitions/  赛历（Tauri 2 + Vite）——「大赛」圈的竞赛清单，图谱/参考类，不是学习应用（ADR 0114）
practice/<id>/ 项目应用：动手做的独立小项目，不接掌握度体系（ADR 0060）
  pocket_cube/ 2 阶魔方（GTK4 / gtkmm）
  nas_admin/   驾考中心服务后台（Flask-AppBuilder，部署在软路由）
  c-gui-lab/   C 语言 GUI 框架对比实验室（Electron 母体收编各框架官方 demo）
launcher/      启动器：macos/（Swift 菜单栏常驻）、core/、gui/
docs/decisions/  跨应用的架构决策记录（ADR）
scripts/       仓库级脚本：统一验证入口 check.py、跨应用内容出处检查
archive/       历史归档，不参与构建
```

**C++ 教程没有特权**（ADR 0045）：它和别的学科一样住在 `subjects/` 下，仓库根不再有它的
源码、构建文件、脚本和文档。任何"以主程序为中心"的假设都是过时的。

**归档**。不参与构建与检查的历史按「离它最近的归档位」放：仓库级的前身与旧数据进根
`archive/`（如前身 computer 仓库、driver 迁中心 PG 前的最后一个本地进度库），应用
自己的历史档进应用目录内的 `archive/`（如 `subjects/ascent/archive/` 的 vuepress 旧站）。

**名字**。仓库叫 Athena。打开应用的终端命令是 `launcher open <id>`（二进制在
`launcher/target/`，名字是 `launcher`；旧文档里的 `athena-dev` 是同一个编排器）。
进程名用 `athena-<id>`，连字符。目录、界面标题、知识点前缀不必是同一个词；
已经写进进度库的前缀不改。目录名允许下划线的历史遗留（`practice/nas_admin`、
`practice/pocket_cube`），但 id 与进程名一律连字符；新目录起名跟 id 一致。
**id 与目录名取英文词或其通行缩写，不用拼音**——拼音名不进仓库；界面标题与
应用内文案照常用中文，`software` 是软件设计师、`driver` 是驾考；应用 id 用完整的英文单词，不用自造缩写（`softcert` → `software` 消灭的正是这类），本领域知名缩写可以用（如 `os`，ADR 0097、0100、0104）。

| 目录 / id | 界面 | 进程 | 知识点前缀 |
|---|---|---|---|
| `cpp` | C++ 教程 | `athena-cpp` | `cpp.` |
| `machine` | C 与机器（原 `c`，ADR 0005） | `athena-machine` | `machine.` |
| `dsa` | 数据结构与算法（原 `algorithm`，复名见 ADR 0105） | `athena-dsa` | `dsa.` |
| `english` | 磨砚 | `athena-english` | `en.` |
| `ascent` | 拾阶 | `athena-ascent`（v9.0.0 及之前发行名 Lumi，改名见 ascent ADR 0021） | 无（进度在用户数据目录，见 ADR 0066） |
| `mathematics` | 数学学习 | `athena-math` | `math.` |
| `math-tools` | 数学工具 | `athena-math-tools` | （无进度库） |
| `driver` | 驾考学习 | `athena-driver` | `drive.` |
| `software` | 软件设计师（原 `softcert`，ADR 0097、0100） | `athena-software` | `sc.`（历史前缀，保留） |
| `embedded` | 嵌入式系统设计师（原 `esd`，ADR 0090、0100） | `athena-embedded` | `esd.`（内容层短名，保留） |
| `database` | 数据库（软设第 9 章实践课程，ADR 0103） | `athena-database` | `db.` |
| `design-patterns` | 设计模式（软设第 7 章实践课程，原素材坑转正，ADR 0103） | `athena-design-patterns` | `dp.` |
| `os` | 操作系统（软设第 4 章实践课程；原 `operating-system`，ADR 0103、0104） | `athena-os` | `os.` |
| `network` | 网络与信息安全（软设第 10 章实践课程，ADR 0103） | `athena-network` | `net.` |
| `firmware` | 嵌入式程序设计（嵌入第 6/8/11 章实践课程，ADR 0103） | `athena-firmware` | `fw.` |
| `microcontroller` | 硬件实验台（嵌入第 2/5 章实践课程，ADR 0103） | `athena-microcontroller` | `mcu.` |
| `rtos` | 实时操作系统（嵌入第 4 章实践课程，ADR 0106） | `athena-rtos` | `rtos.` |
| `gtkmm` | gtkmm 官方教程精读 | `athena-gtkmm` | `gtkmm.` |
| `polaris` | 北极星 | `athena-polaris` | （无进度库） |
| `organization` | 计算机组成原理（408，ADR 0115） | `athena-organization` | `org.` |
| `cs408` | 408 计算机学科专业基础（考研考试主应用，ADR 0116） | `athena-cs408` | `cs408.` |
| `competitions` | 赛历（「大赛」圈，ADR 0114） | `athena-competitions` | （无进度库） |

`driver` 是机动车理论考试，不是设备驱动；Dart 包名仍是 `athena_driver`（包名不能有连字符）。
C++ 教程的界面、桌面条目和安装包都叫这门课自己的名字。进程和发行包文件名是
`athena-cpp`（`.app` / `.deb` / `.dmg` / `.zip` / `.msi`）。发行副本的用户数据在
`athena-cpp` 目录；若旧目录 `Athena` 还在、新目录还没有，启动时把旧目录改名过去。

**`subjects/` 下不是清一色的"学习应用"，改动或新增一个目录前先按判据对号入座，
不要去查有没有把它列进某张清单——清单会过期，判据不会：**

- **这个项目要不要让人"学会"什么、要不要追踪掌握度和学习进度？** 要，就是
  **学习应用**，受「跨应用教学规范」（[TEACHING.md](TEACHING.md)）整节约束，且要按 ADR 0037/0053 建自己的
  `progress/learning.db`。当前：`cpp` / `machine` / `dsa` / `english` / `mathematics` /
  `driver` / `ascent`（`ascent` 的规范差距见 ADR 0066）/ 软考两应用及其挂靠实践
  子课程（ADR 0103：`database` / `design-patterns` / `operating-system` / `network` /
  `firmware` / `microcontroller` / `rtos`）。
- **不是学习闭环，是呈现结构化信息供浏览、查阅、决策参考的？** 那是
  **图谱/参考类应用**：仍受「独立应用」一节的平级、隔离、`app.json` 启动规则约束，
  但**不**掌握度、不进度库、不激励——「跨应用教学规范」一节对它不生效，具体规则
  以它自己的 `AGENTS.md` 为准。当前：`polaris`、`math-tools`、`competitions`（赛历，ADR 0114；`math-tools`是数学学习的配套工具，
  因需要在启动器里和 `mathematics` 关联而归 `subjects/`，不是先例，见 ADR 0084）。
- **还没决定做成应用，只是存素材和结论，等以后真正开工？** 那连"应用"都不算，
  不需要 `app.json` 也不需要 `scripts/check.py`，根验证入口按设计静默跳过它——
  这是预期行为，不是遗漏。当前无素材坑目录（`design-patterns` 曾是唯一的素材坑，
  已按 ADR 0103 转正为学习应用）。

判据只有一条主问题：**这东西要不要教会人什么、要不要证明学习者进步了**——答案
决定它落进哪一类，而不是它现在被写在哪张表里。新增应用时先在自己的 `AGENTS.md`
里说清楚属于哪一类，再决定要不要遵守「跨应用教学规范」；上面的"当前"清单只是
例子，过期了直接按判据重新归类，不必先来改这里。三类共同点仅剩「一个目录一个
独立单元，彼此不互相依赖」；除此之外不要把学习应用的规范套到图谱类应用上，也
不要把图谱类应用的例外当成学习应用可以援引的先例。

**`subjects/` 与 `practice/` 按意图分（ADR 0060）**：`subjects/` 负责课程学科学习，
`practice/` 专注项目应用——做出一个能跑的东西，不追求知识点覆盖、不建进度库，
「跨应用教学规范」一节对它不生效。两者平级，都各自一份 `app.json`、都走同一个
启动器；启动器分别从 `subjects/*` 与 `practice/*` 发现应用，分区展示。

只影响单个应用的 ADR 放在**该应用自己的** `docs/decisions/` 下；影响仓库结构或多个
应用的才放仓库级 `docs/decisions/`。两处各自延续编号，历史编号不重排，所以两边都有跳号。

## 独立应用（`subjects/`）

- **一个目录一个独立应用**（ADR 0032、0045），自带构建系统、依赖、界面技术和内容体系。
  目录名按领域取（`cpp`、`machine`、`dsa` 这样的领域名），不带实现技术名——手段会换，领域不会。
- **各应用有自己的 `AGENTS.md`**：改该应用时以它为准，不把别的应用的规则套进去。
  每个应用必须能**脱离其他应用独立开发与运行**。
- **构建完全隔离**：应用之间不互相引用路径、不互相 include 头文件、不读对方的内容配置，
  第三方依赖各拉各的。学习应用之间共用的是教学**规范**（[TEACHING.md](TEACHING.md)，仅对学习应用生效），
  不是配置 schema——复用规范零成本，复用 schema 会立刻产生耦合。
- **约束也各守各的，不从别的应用继承**（ADR 0062）：每个应用的约束只来自仓库级大原则和它
  自己的 `AGENTS.md` 与 ADR。不写「沿用 X 应用的做法」「对齐 X 应用 ADR」作为约束来源——
  来源一改，继承方不会知道，规则就悄悄过时。在本应用也成立的做法，自己写下来、自己说明
  理由，之后各改各的；多个应用都需要且应该一起变的，才提升为仓库级原则。
- **学习应用的学习库各自独立，但随仓库走**（ADR 0037、0053；只约束学习应用，图谱/
 参考类应用不建这个库）：每个学习应用自建、自管、自迁移它自己的进度库，不共用别人
 的库，也不假设别人跑过。库放在应用自己目录下的 `progress/learning.db` 并**进版本
 库**——换一台机器 clone 下来，掌握度、连续日和战绩还在；拿不到工作树的发行副本才
 退回本机用户数据目录。同步用 `launcher sync`（只提交 `progress` 路径，不连带代码
 改动）。知识点 ID 用自己的前缀（C 与机器 `machine.`，数据结构 `dsa.`）。**例外**：已迁中心
 PostgreSQL 的应用（目前只有 `driver`，ADR 0067、0068）个人数据存 PG，不再有
 `learning.db`、也不再靠 `launcher sync` 带着走。
- **应用只声明怎么启动，不写启动脚本**（ADR 0046）：`app.json` 的 `dev` 块写清
  环境变量、准备步骤（装依赖 / 增量构建）、长驻命令和就绪判据，执行统一由
  `launcher/core` 的编排器负责。热更新，改源码即时可见；不要用打包 `.app` / DMG，
  也不要从 `/Applications` 启动——打包副本会让人不知不觉对着旧版本工作。
- **打开哪个应用走 `launcher/` 的启动器**（ADR 0044 / 0046 / 0048）：跨平台版托盘
  常驻，macOS 版在菜单栏（平台专属，理由与降级见 ADR 0048），终端用
  `launcher open <id>`。三个前端同一条执行路径——都不自己读 `app.json`、不自己
  判断状态，一律向编排器要（`launcher list --json`）。新增应用照样放一份带
  `dev` 声明的 `app.json` 即可，启动器不需要改代码。
- `subjects/cpp` 不再有跨应用学科路线图首页——打开别的应用一律走上面这条启动器路径，
  不再有第二个入口（subjects/cpp ADR 0058，推翻 ADR 0032 第 5 条）。

## 学习者目录（`Athena/users.json`）

应用之间**不共用配置 schema**，这是唯一的、有意的例外（ADR 0073）：学习者是「这个人」，
不属于某个应用，所以「这台机器上登录过哪些学习者、上次用的是谁」放在应用无关的全局文件里，
所有接入的应用读写同一份。共用的只有「人」这一层；各应用的本地库、照片、同步配置仍各归各
（ADR 0032、0062）。格式由本节定义，改格式要改本节并走 ADR，不由某个应用单方面决定。

**权威在中心**（ADR 0074、0075）：后台库的 `athena_users(id, name, …)` 才是「有哪些学习者、
各叫什么、编号几号」的唯一来源；本文件只是**本机缓存加本机偏好**。学习者无口令，登录就是
输入名字，重名才再问编号。

**位置**：与各应用自己的数据目录（如 `AthenaDriver/`）平级。

| 平台 | 路径 |
|---|---|
| macOS | `~/Library/Application Support/Athena/users.json` |
| Windows | `%APPDATA%\Athena\users.json` |
| Linux | `$XDG_DATA_HOME/athena/users.json`，未设置则 `~/.local/share/athena/users.json` |

> 注意目录名大小写：macOS、Windows 是 `Athena`，Linux 是 `athena`。

**结构**：

```json
{
  "users": [
    { "id": "1", "name": "tiger" },
    { "id": "3", "name": "小王" }
  ],
  "last": "3"
}
```

| 字段 | 含义 |
|---|---|
| `users[].id` | 学习者编号，**身份**。服务端登记时分配的 1～999 纯数字（存成字符串，无前导零），永不变、不复用。它会进本地库文件名、请求头 `X-Athena-User` 和中心库 `user` 列。**1000～9999 是本地段**：中心目录不用这个段，由应用在目录连不上时自分配给「只存这台电脑、永不参与同步」的本地学习者（目前只有 `subjects/driver`，见其 ADR 0123）；本地编号同样永不变、不复用，且不会发给任何服务端 |
| `users[].name` | 显示名，**只是称呼**。非空、不超过 64 个字符、不含 `/`、`\` 与空字符；不要求唯一，比较时忽略大小写和首尾空白。只能由本人改（改名走中心目录，成功后更新缓存；本地学习者改名只写本机） |
| `last` | 上次使用者的编号，没有则 `null`。各应用共用同一个「上次是谁」 |

**读写约定**：

- 编号一经登记不改、不复用；要换称呼只改 `name`。
- 读取方**忽略未知字段**，写回方**保留未知字段**（顶层与每个学习者条目都是）——将来加字段时，
  旧版应用不能把它抹掉。编号不是 1～999 数字串的条目直接忽略；文件不存在、内容损坏都按
  「还没有学习者」处理，不报错退出。
- **写盘先写临时文件再改名**，断电不会留下半个 JSON。
- 登录成功（无论是缓存命中还是问了中心）后把这位学习者记进 `users` 并设为 `last`。缓存命中
  即可离线进入；缓存里没有的名字，应用**默认在本机新建一个本地学习者**（1000 段编号，只存
  这台电脑、永不同步，见 `users[].id` 行）；要登录中心目录里的人（异地登录）或把新学习者
  建到服务器，得先在应用里明确配置远程访问凭据——目前 `subjects/driver` 以外网访问凭据
  配齐为开关（其 ADR 0124）。
- 两台机器上的 `users.json` 彼此独立，不自动同步。同一个人在另一台机器上输入名字登录，中心
  告诉本机这个人是几号；重名时再输入编号。
- 无口令、无加密：它是本机的称呼缓存，不是凭据。访问控制不在应用里：内网可信，外网由 Cloudflare
  Access 把守（主仓库 ADR 0077）。

**现状**：目前只有 `subjects/driver` 接入（`lib/users.dart`、`lib/user_directory.dart`）。
中心侧接口见 `practice/nas_admin/docs/user-api.md`。

## 新增一个应用时动哪些地方

加应用是最容易攒下混乱的操作——v9.0.0 前后的一次结构侦查发现，几乎每一类
「文档与实际不符」都是加东西时忘了同步别处。清单如下，按顺序走一遍：

1. **目录与四件套**：`subjects/<id>/` 或 `practice/<id>/`，内放 `app.json`（`dev`
   块声明怎么启动，ADR 0046）、`AGENTS.md`（本应用规则）、`CLAUDE.md`（只写
   `@AGENTS.md`）、`README.md`（一段定位与入口）、`scripts/check.py`（本应用
   验证入口，ADR 0007）。`check.py --sources-only` 的结构卫生检查会核对这份清单。
2. **分类对号**：按上面的三类判据写明自己是学习应用 / 图谱参考 / 素材坑；
   学习应用按 ADR 0037/0053 建 `progress/learning.db`。
3. **登记进文档**：本文的结构树与名字表各加一行、根 `README.md` 应用表加一行——
   三处清单结构卫生检查都会与实际目录对账，幽灵行与漏登都会被拦下。
4. **进 CI**：`.github/workflows/ci.yml` 的对应 job 或矩阵，以及
   `workflow_dispatch` 的 `options` 列表（选择项同样与实际目录对账）——工作流改动
   本地先过 `check.py --sources-only` 的工作流检查（actionlint + 变量粘连）。
5. **要进发布矩阵的话**：`release.yml` 加构建 job，`publish` 的校验和清单与
   资产通配两处都要覆盖到（ADR 0081）；产物名遵守 `athena-<id>` 约定。
6. **内容有出处，按档接入**（ADR 0043、0089）：考试/考证考级类学习应用必须接入
   `content-contract.json` 并声明 `tier: "exam"`（违规阻断）；其余学习应用按 `tier: "open"`
   接入（只报告不阻断）；图谱/参考类与素材坑不建契约，出处约束不适用。
7. **图标**：一份彩色图标，启动器、任务栏、应用界面三处同源（ADR 0065）。

启动器不需要改代码——`launcher` 从 `subjects/*` 与 `practice/*` 自动发现应用
（ADR 0046）。
