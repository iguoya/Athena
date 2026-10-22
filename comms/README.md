# Athena 多代理协作通讯（ADR 0165）

多个 AI 代理（Claude Code、Cursor、ZCode 等）在同一仓库协作时的通讯公共服务。
原型是九州项目的双通道机制（2026-10-13 起实战验证），抽取时按**舱**参数化：
一个协作主题一个舱，`comms/<project>/`，角色由舱内 `config.json` 声明。

**每轮开工先跑一条命令看收件箱，做完用命令改任务状态，需要说话就发一条消息。**
所有操作都是新增文件或改自己名下任务的状态，所以各方永远不会互相覆盖。

```sh
# 在仓库根目录运行（Windows / macOS / Linux 通用）；舱名用 --project 指定，
# 或设环境变量 ATHENA_COMMS_PROJECT 省略它
python comms/comms.py inbox  <你的名字> --project <舱>    # ① 每轮开工第一件事
python comms/comms.py ack    <你的名字> --all --project <舱>
python comms/comms.py status T-001 doing  --by <你的名字> --project <舱>
python comms/comms.py status T-001 review --by <你的名字> --note "验证命令输出摘要 + 证据路径" --project <舱>
python comms/comms.py send --from <你的名字> --to <对方名字|all> --subject "主题" --body "正文" --project <舱>
python comms/comms.py board --project <舱>                # 重新生成看板（status 命令会自动做）
python comms/comms.py check --project <舱>                # 校验通讯结构
python comms/comms.py triage <你的名字>                    # 一条命令查收：全部舱的未处理消息 + 我的任务
```

会话层（ADR 0181，一般由 hook 自动调，人只在声明角色时用）：

```sh
python comms/comms.py session touch --agent zcode --sid <session_id> --role operator
python comms/comms.py session list                       # 看活跃会话
python comms/comms.py deliver --agent zcode --sid <sid>  # 本会话订阅内的未读全文（自动标记已投递）
```

正文较长时用 `--body-file 文件路径`，或 `--body -` 从标准输入读。

## 舱与角色

| 舱 | 主题 | leader | worker |
|---|---|---|---|
| `driver/` | 驾考应用（certification/driver） | zcode | cursor |
| `comms-console/` | 协作观察台（ADR 0166，`tools/comms-console`） | zcode | cursor |
| `jiuzhou/` | 九州历史地理图鉴（`mentor/jiuzhou`；机制原型，2026-10-15 迁入） | claude-code | cursor、zcode |
| `pocket-cube-solver/` | 二阶魔方教材整改（`programming/pocket-cube-solver`，2026-10-19；worker 只写 artifacts，leader 集成） | claude-code | cursor |

新开一个舱：建 `comms/<舱>/config.json`（`leader`、`agents`、`bands`、`owned` 四个键，
见 [comms.py](comms.py) 文件头示例）和一份本舱 README 写主题与文件归属，即可用同一
工具协作。任务号段惯例：**leader 占 9 段（T-9xx），worker 依次 0、1、2 段**。

## 两类角色

- **leader（领导指挥）**：拆任务、写任务书（含目标、做法、**验收口径**）、验收
  （`review → done` 只有 leader 能标）、裁决分歧、打回返工（`--note` 以「返工：」开头）。
  worker 的建议有道理就采纳，但采纳与否由 leader 确认，方向以 leader 为主。
- **worker（配合执行）**：按任务书执行；做完转 `review` 并附验证证据；卡住转 `blocked`
  并写明卡在哪、要谁帮忙；对设计有建议发消息给 leader，**不自行改方向**。
- worker 之间平级：不下发任务、不改对方文件；要对方做事，发给 leader 转成任务。

## 目录（舱内）

| 路径 | 内容 | 谁写 |
|---|---|---|
| `config.json` | 角色、任务号段、名下路径 | leader（改前先在舱内说一声） |
| `tasks/T-xxx-*.md` | 任务：目标、做法、验收、进展记录 | 任务由 leader 创建；状态由负责人改 |
| `msgs/*.md` | 正式消息，**只新增、不修改** | 发信人 |
| `read/<名字>.txt` | 各人的已读记录 | 各自 |
| `chat/<名字>.log` | 各人的即时消息（只追加） | 各自 |
| `artifacts/T-xxx/` | 交付物附件（截图、核对记录） | 负责人 |
| `BOARD.md` | 看板，由工具**生成，不要手改** | 工具 |

## 任务状态与谁能改

```
todo ──> doing ──> review ──> done
            └────> blocked ──> doing
```

- 负责人把状态改成 `doing`（开工）、`review`（做完，**必须写 `--note`：验证命令输出
  摘要、证据路径**）、`blocked`（卡住，**必须写 `--note`：卡在哪、要谁帮忙**）。
- **`done` 只有 leader 能标**：实机验收后才标。worker 做完就停在 `review`。
- 任务里写了 `depends: T-xxx` 的，前置没 `done` 前先做别的，`inbox` 会提示「等待」。
- 优先级 `P0` > `P1` > `P2`；同级先做 `doing`，再做 `todo`。

## 消息怎么用

- **leader → worker**：任务之外的指示、裁决、验收意见。`inbox` 会显示，读完 `ack`。
- **worker → leader**：需要裁决的问题、建议、数据缺口、「做完了待命」。
- **worker ↔ worker（平级）**：接口约定、字段已落地的通知、验收口径对齐、撞车预警。
  平级之间**不下发任务、不改对方文件**；要对方做事，发给 leader 转成任务。
- `--to all` 广播。`--task T-xxx` 关联任务，方便追溯。
- 消息发出后不能改。写错了就再发一条更正。
- 标题以「FYI」开头的不需要回复；以「请回」或带问号的才需要。回复用 `reply`，一行就够。

## 铁律

1. **只改自己名下的路径**（舱 README 写归属表；仓库级见根 `AGENTS.md`「多个代理并行」）。
   撞到别人的未提交改动先停，发消息说明。
2. **不要改别人的任务文件**；你的任务只用 `status` 命令改状态。
3. 提交 git 时 `git add` 写明确路径，不整目录添加；提交前跑应用自己的 check（各应用
   `scripts/check.py`）必须绿。
4. 质量底线按各应用的规范走（如教学内容按该应用 `AGENTS.md` 与相关 ADR）。

## 单开会话（`spawn.py`）

`comms.py` 只管说话，对方下一轮才看得到；要「叫人开工」用 `spawn.py`：为某个代理
**另起一个全新的会话**（不碰它正在跑的旧会话），首句就是「先 inbox、认领 T-xxx、
做完转 review」。只给 `owner` 是该代理、状态为 `todo` 的任务开会话，避免和已认领的重复。

```sh
python comms/spawn.py zcode  --project driver --task T-104 [--note "补充说明"] [--dry-run]
```

| 代理 | 怎么开 | 前提 |
|---|---|---|
| zcode | `zcode.cjs -p` 无头后台（经 `~/.zcode/spawn-cli/` 垫片，自动生成）；会话也写进 ZCode 自己的会话库 | 命令行登录过一次：`node ~/.zcode/spawn-cli/run.cjs login bigmodel`（需设 `ZCODE_REAL_CJS`，见 `spawn.py`） |
| cursor | 独立 CLI `cursor-agent` 无头（`--force --trust`），一次约 2~4 分钟、结束才输出；没装则只打印提示词，加 `--open-cursor` 才用深链弹出预填的新对话（要按回车） | 装 CLI 并 `agent login` 一次。本机 `python` 是商店别名看不到 AppData\Local 新目录，用 **`py comms/spawn.py`** |
| claude-code | `claude -p` 无头 | 无 |

无头输出在 `comms/<舱>/runs/*.log`（已 gitignore）。无头会话没人实时回答，提示词已要求它
遇事发消息给 leader 并转 `blocked`。文件层面的撞车仍靠任务书里的 owned 路径约束。

## 多标签页工作法（一个代理开多个会话并行）

机制是 ADR 0181 的会话注册表 + ADR 0167 的任务分箱，两层各管一半：

- **会话注册表**（`comms/sessions/`，hook 自动维护）：投递精确到标签页。hook 拿到
  session_id 就登记并按会话投递——干活的标签页只注入自己订阅舱的未读**全文**
  （自动标记已投递，无需 ack）；纯对话会话让代理跑一次
  `session touch --agent <名> --sid <session_id> --role operator` 即永久静音。
  未注册的会话走旧的逐舱摘要提醒（降级不缺席）。
- **任务分箱**（ADR 0167）：任务是路由单位，`status T-xxx doing` 就是认领声明。
  同舱开工先 `triage <名>`（或 `inbox`）认清全局，认领后消息带 `--task T-xxx`；
  看到任务已被别人 doing 就不碰；做完即离。
- `--to operator` 是发给使用者本人的保留通道：comms-console 会弹系统通知并聚进
  「我的收件箱」；需要人拍板的事不要发给别人转达。

## 实时沟通（ADR 0181 起自动投递）

1. **线程**：`reply <消息文件名片段> --from <名字> --body 正文` 回复一条消息，收件人、
   标题（`Re:`）、线程 id 自动处理；`thread <片段>` 按时间顺序看整个来回。
2. **自动投递（hook）**：`comms/hooks/agent-notify.py` 挂在 SessionStart /
   UserPromptSubmit 上，有 session_id 的代理（ZCode、Claude Code）自动登记会话并
   `deliver` 本会话订阅内的未读全文；没有的（Cursor）降级为逐舱摘要。已投递的
   自动标记，无需 ack。另挂 PostToolUse（每 60 秒至多真查一次）：长任务中间
   也会看到「紧急且尚未投递」的插报。
3. **投递守护（commsd）**：`python comms/commsd.py`（通常由 comms-console 拉起并
   保活）监听消息落盘：需要使用者的写进 notify-queue 由协作中心弹系统通知；
   紧急且收件方全部会话心跳超时的，30 分钟窗口内自动 spawn 唤醒一次。
4. **即时消息**：`say --from <名字> --to <对方|all> "一句话"` 快问快答，不进任务系统；
   `chat <名字>` 读未读并标记已读。在线判定用 `presence`（按发消息、读消息、更新任务、
   提交名下路径这些可观察痕迹算，不靠自报）。
5. **协作中心**：`tools/comms-console`（ADR 0166、0181）开机自启、托盘常驻——观察
   全貌、收 operator 通知与收件箱。临时静音某个纯对话会话见「多标签页工作法」。
