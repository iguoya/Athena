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
```

正文较长时用 `--body-file 文件路径`，或 `--body -` 从标准输入读。

## 舱与角色

| 舱 | 主题 | leader | worker |
|---|---|---|---|
| `driver/` | 驾考应用（certification/driver） | zcode | cursor |
| `jiuzhou/` | （暂未迁移，仍用 `mentor/jiuzhou/scripts/comms.py`） | claude-code | cursor、zcode |

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

## 实时沟通（不打扰的提醒）

1. **线程**：`reply <消息文件名片段> --from <名字> --body 正文` 回复一条消息，收件人、
   标题（`Re:`）、线程 id 自动处理；`thread <片段>` 按时间顺序看整个来回。
2. **提醒（hook 用）**：`notify <名字>`——没有未读时什么都不打印，有未读时最多 3 行
   摘要。接在代理环境的「每轮开始 / 提交提示前」钩子上让未读自然出现；
   通用 hook 见 [hooks/agent-notify.py](hooks/agent-notify.py)（一次扫描所有舱）。
3. **阻塞等待**：`watch <名字>` 后台运行，有新消息进程退出即被唤醒。
4. **即时消息**：`say --from <名字> --to <对方|all> "一句话"` 快问快答，不进任务系统；
   `chat <名字>` 读未读并标记已读。在线判定用 `presence`（按发消息、读消息、更新任务、
   提交名下路径这些可观察痕迹算，不靠自报）。
