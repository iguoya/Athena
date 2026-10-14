# 九州三方通讯机制

参与者：**claude-code**（指挥 / 规划 / 验收）· **cursor**（前端 / 地图）· **zcode**（内容）。
这里的名字就是命令里用的名字，一字不差。

## 一句话

**每轮开工先跑一条命令看收件箱，做完用命令改任务状态，需要说话就发一条消息。**
所有操作都是新增文件或改自己名下任务的状态，所以三方永远不会互相覆盖。

```sh
# 在仓库根目录运行（Windows / macOS / Linux 通用）
python mentor/jiuzhou/scripts/comms.py inbox  <你的名字>     # ① 每轮开工第一件事
python mentor/jiuzhou/scripts/comms.py ack    <你的名字> --all  # 读完后标记已读
python mentor/jiuzhou/scripts/comms.py status T-001 doing  --by <你的名字>
python mentor/jiuzhou/scripts/comms.py status T-001 review --by <你的名字> --note "验证命令输出摘要 + 截图路径"
python mentor/jiuzhou/scripts/comms.py send --from <你的名字> --to <对方名字|all> --subject "主题" --body "正文" [--task T-001]
python mentor/jiuzhou/scripts/comms.py board                  # 重新生成 BOARD.md（status 命令会自动做）
python mentor/jiuzhou/scripts/comms.py check                  # 校验通讯结构
```

正文较长时用 `--body-file 文件路径`，或 `--body -` 从标准输入读。

## 目录

| 路径 | 内容 | 谁写 |
|---|---|---|
| `tasks/T-xxx-*.md` | 任务：目标、做法、验收、进展记录 | 任务由 claude-code 创建；状态由负责人改 |
| `msgs/*.md` | 消息，**只新增、不修改** | 发信人 |
| `read/<名字>.txt` | 各人的已读记录 | 各自 |
| `BOARD.md` | 看板，由工具**生成，不要手改** | 工具 |
| `archive/` | 旧交接单存档，只读 | — |

任务编号：`T-0xx` 属 cursor，`T-1xx` 属 zcode，`T-9xx` 属 claude-code。

## 任务状态与谁能改

```
todo ──> doing ──> review ──> done
            └────> blocked ──> doing
```

- 负责人把状态改成 `doing`（开工）、`review`（做完，**必须写 `--note`：验证命令输出摘要、截图路径**）、
  `blocked`（卡住，**必须写 `--note`：卡在哪、要谁帮忙**）。
- **`done` 只有 claude-code 能标**：它实机验收后才标。你做完就停在 `review`。
- 任务里写了 `depends: T-xxx` 的，前置没 `done` 前先做别的，`inbox` 会提示“等待”。
- 优先级 `P0` > `P1` > `P2`；同级先做 `doing`，再做 `todo`。

## 消息怎么用

- **claude-code → 你**：任务之外的指示、裁决、验收意见。`inbox` 会显示，读完 `ack`。
- **你 → claude-code**：需要裁决的问题、schema 变更需求、数据缺口、“做完了待命”。
- **cursor ↔ zcode（平级）**：接口约定、字段已落地的通知、验收口径对齐、撞车预警。
  平级之间**不下发任务、不改对方文件**；要对方做事，发给 claude-code 转成任务。
- `--to all` 广播。`--task T-xxx` 关联任务，方便追溯。
- 消息发出后不能改。写错了就再发一条更正。

## 铁律

1. **只改自己名下的路径**，路径归属见 [`../PARALLEL.md`](../PARALLEL.md)。撞到别人的未提交改动先停，发消息说明。
2. **不要改别人的任务文件**；你的任务只用 `status` 命令改状态。
3. **改 schema 的流程**：提出方发消息给 claude-code → claude-code 裁决（必要时先写 ADR）→
   **先改内容与校验（zcode），再改前端读取（cursor）**。新字段一律可选，前端读不到时静默降级。
4. **质量底线**：不凭印象写史实与出处；不灌水凑字；不确定的写“约”“估计”。
5. 提交 git 时 `git add` 写明确路径，不整目录添加；提交前 `python mentor/jiuzhou/scripts/check.py --skip-rust` 必须绿。

## 实时沟通（线程 + 不打扰的提醒）

目标：能随时对话，但**绝不打断你们正在做的事**。三块，都是可选的轻量件：

1. **线程**：`comms.py reply <消息文件名片段> --from <名字> --body 正文` 回复一条消息，收件人、标题（`Re:`）、线程 id 自动处理；
   `comms.py thread <文件名片段>` 按时间顺序看整个来回。一来一回就是一个线程，不必再新开标题。
2. **提醒（给你们的 hook 或开工脚本用）**：`comms.py notify <你的名字>`——**没有未读时什么都不打印**，有未读时最多 3 行摘要。
   可以接到你们环境里「每轮开始前 / 提交前」之类的钩子上，让未读消息在你们下一步自然出现，而不是靠我催。
   接不接、接在哪，由你们自己的环境决定（Cursor 的 hooks / rules，ZCode 的对应机制）；我不改你们的配置。
3. **我这边的即时接收**：`comms.py watch claude-code` 在后台阻塞，**你们一发消息我立刻被唤醒**，不用等轮询。

约定：消息标题以「FYI」开头的不需要回复；以「请回」或带问号的才需要。你们回复时用 `reply`，一行就够。

## 即时消息（chat）——任务机制照旧，另加一条「一句话」通道

任务与正式消息（`send` / `reply` / `inbox`）原样保留，用于需要留档、带验收口径的事。**chat 是新增的轻量即时通道**：一句话，不进任务系统，不需要标题。

```sh
python mentor/jiuzhou/scripts/comms.py say --from <我> --to <对方|all> "一句话"   # 发
python mentor/jiuzhou/scripts/comms.py chat <我>                                  # 看发给我的未读并标记已读
python mentor/jiuzhou/scripts/comms.py chat <我> --tail 10                        # 看最近 10 条（不改已读）
python mentor/jiuzhou/scripts/comms.py notify <我>                                # 钩子/开工脚本用：没有未读就静默
```

- 每个人只写自己的 `docs/comms/chat/<名字>.log`（只追加），读取时合并排序，和消息一样**永远不改别人的文件**；已读位置在 `read/<名字>.chat`。
- **不打扰**：`notify` 没有未读就什么都不打印；有未读也只给 ≤3 行摘要，是否马上回由你自己决定。快问快答用 chat，正经的交付、裁决、验收仍走任务和消息。
- **主动而非等待**：claude-code 在后台常驻 `comms.py watch claude-code`，你们一发消息或 chat，我**立刻被唤醒**，不靠轮询；你们这边把 `notify` 接进自己的钩子/规则，未读就会在下一步自然出现。
- `presence` 把 chat 也算作在线痕迹。

## 在线判定（presence）

对方在不在线不能靠自报，只看可观察的痕迹：**发过消息 / 读过消息（ack）/ 更新过任务进展 / 提交过自己名下的路径**，
取其中最新的一个。再配合「联络」：`comms.py ping <名字|all>` 发一条标题以「联络」开头的消息，对方在 15 分钟内没有任何新痕迹就算没有回应。

```sh
python mentor/jiuzhou/scripts/comms.py presence           # 看所有人：状态、最近痕迹、距今、最近联络
python mentor/jiuzhou/scripts/comms.py presence cursor    # 只输出一个词：online / quiet / unreachable
python mentor/jiuzhou/scripts/comms.py ping all           # 发联络消息
```

| 状态 | 判据 | claude-code 怎么做 |
|---|---|---|
| `online` | 30 分钟内有痕迹 | 正常验收、指派、回应 |
| `quiet` | 30 分钟~4 小时没痕迹，且没有「已发联络却无回应」 | 只被动读收件箱，不催办，保留队列 |
| `unreachable` | 联络发出超过 15 分钟仍无痕迹，或 4 小时以上无痕迹 | **停止监督**：不验收、不指派新任务、不催办、不替它改状态；回来之后（`online`）再恢复 |

你们的做法：每轮开工先 `inbox`、做完 `ack`，这本身就是在线痕迹；被 `ping` 时回一行即可。看板（BOARD.md）顶部有「在线状态」表。

## 开工清单（每轮）

1. `inbox <我>` → 读消息、看待办。
2. 挑最高优先级且不在“等待”的任务，`status ... doing`。
3. 做。做的过程中发现问题 → `send`。
4. 做完 → 跑验证命令 → `status ... review --note "..."`。
5. `ack <我> --all`。
6. 队列空了：给 claude-code 发一条“待命”。
