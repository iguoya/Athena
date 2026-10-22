# ADR 0181：通讯机制 v4——会话注册表、投递守护（commsd）与协作中心（comms-console 扩权）

- 日期：2026-10-22
- 状态：已接受（使用者对「通讯机制笨、不即时、多标签页互相干扰」的三项抱怨逐条
  拷问后拍板：Q1 会话注册 A / Q2 落 daemon 且宿主判给 comms-console / Q3 订阅静音 A /
  Q8 独立 Python 守护、默认自启 / Q9 窄职责 + comms-console 扩权 / Q10 只弹需要人的 /
  Q5 注入即投递 / Q6 spawn 窄口径 / Q7 旁观走观察台）
- 关系：修订 [ADR 0167](0167-multi-session-task-routing.md) 决策 1（「不新造会话注册
  机制」——本 ADR 引入会话注册表，任务仍是路由单位，注册表只管投给谁）；修订
  [ADR 0166](0166-comms-console-and-projection.md)（「观察台只读」收窄为「写走 CLI +
  operator 已读一条例外」，「实时推送总线不做」收窄为「存储与写路径不中心化不变，
  投递加速器可以有」）；建立在 [ADR 0165](0165-agent-comms-service.md)（文件制、
  舱模型、防覆盖铁律原样不动）之上

## 背景

ADR 0165 的文件制通讯实战跑了五十多个任务，但三个痛点在使用中持续累积：

- **多标签页干扰**：hook 接线硬编码代理名（`--agent zcode`），同一代理的所有
  会话——包括纯对话会话——一律收到全舱全量未读摘要。ADR 0167 的任务分箱
  （`--mine`/`--task`）只落在手动 `inbox` 上，自动注入通道没有享受到。
- **不即时**：提醒只挂在 SessionStart / UserPromptSubmit 上；代理在长任务里收不到，
  空闲代理「没有下一轮」更收不到；消息的最终收件人常常是使用者本人，却没有任何
  东西通知人。
- **笨**：提醒与动作两层皮——收到摘要还要自己跑 inbox、ack、流转，每轮都有
  token 与纪律成本。

平台事实（本次查实）：ZCode/Claude Code 的 hook payload 带 `session_id`；hook 注入
只能发生在轮次边界；跨代理唯一可靠的共享写空间是仓库文件；「唤醒一个代理」的唯一
手段是 spawn 无头会话（`spawn.py` 已有）。任何「更底层」的机制都只能落在这三条
通道的组合上——不存在绕过轮次边界向运行中会话推送的通道。

使用者指出：comms-console 反正要常驻（托盘 + 开机自启），daemon 的生命周期成本由
宿主摊掉，剩下的全是值班 hook 给不了的收益（无会话时的监听、系统通知到人、自动
唤醒）——daemon 由此改判落地，宿主判给 comms-console。

## 决策

1. **会话注册表（修订 0167 决策 1）**：`comms/sessions/`（跨舱、gitignore、不进
   git——高频写的临时实体，协作史仍在各舱）。会话 = 代理的一个标签页/进程实例，
   文件 `<代理>.<session_id 前 8 位>.json`，字段：agent、sid、role（worker/operator）、
   projects 订阅、mute、registered、heartbeat。hook 在 SessionStart 自动登记
   （`session touch`）、每轮刷新心跳；超时 15 分钟视为不活跃。**任务仍是路由单位**
   ——箱仍由 doing 状态推导，注册表只决定「哪个会话看哪些舱、要不要静音」。
2. **投递语义（注入即投递）**：hook 新走 `deliver`——按会话订阅过滤出未读消息
   **全文**（每舱至多 3 条、全局至多 6 条，紧急优先，紧急无视订阅），注入上下文并
   写 `<代理>.<sid>.delivered.txt` 标记；已投递的消息并入已读判定，手动
   `inbox`/`notify` 不再重复显示。operator / mute 会话零注入。无 session_id 的代理
   （Cursor）自动降级为旧的逐舱摘要提醒——hook 接线签名不变，三处接线零改动。
3. **投递守护 `comms/commsd.py`（职责窄四件）**：轮询监听 `comms/*/msgs` 落盘；
   维护自身心跳（`sessions/.daemon.json`，mtime 即心跳）；把「需要使用者」的消息
   （`to=operator` 或标题含「转向使用者」）写进 `sessions/notify-queue/`；按**窄
   口径**自动唤醒——标题带「紧急」+ 收件方是具体代理且全部会话心跳超时 15 分钟 +
   消息创建在 30 分钟内 + 每条消息至多一次（`.spawned/` 幂等标记），调 `spawn.py`。
   纯标准库、协议逻辑 import comms.py 只留一份；不存消息、不改任何舱内文件。
4. **comms-console 扩权为协作中心宿主**：开机自启（自启命令带 `--hidden`，登录拉起
   不弹窗）、托盘常驻（关窗=藏进托盘）、15 秒一拍保活 commsd（心跳 mtime 判活，死
   了重拉）并消费 notify-queue 弹系统通知。**系统通知只弹需要使用者的**，落地处是
   新增的「我的收件箱」视图（聚合 `--to operator`）；「标为已处理」调
   `comms.py ack operator`——写走 CLI 的铁律不变，唯一例外只是 operator 已读游标。
5. **`operator` 成为保留名**：不需要舱 config 声明，`send --to operator` /
   `inbox operator` / `ack operator` 全部合法；约定「需要使用者的消息一律发
   `--to operator`」。代理主动查收用新命令 `triage <名>`（各舱未处理消息全文 +
   我的任务 + 建议动作，看过的自动标记，hook 不再重复注入）。
6. **旧舱零迁移**：msgs/tasks/chat/游标格式全不动；九州遗留副本不动；观察台
   （PG 投影）与 presence（痕迹推导）的职责不变。

## 后果

- 多标签页各看各的：干活的标签页只收自己订阅舱的相关消息全文，纯对话会话可声明
  `--role operator` 归零；「收件箱混流、已读互踩、消息无地址」从自动通道上消失。
- 使用者第一次有了「被通知」的通道：需要人的消息弹系统通知、聚在收件箱，不再
  依赖人主动翻会话或看板。
- 紧急且无人值守的消息在 30 分钟窗口内被自动唤醒一次；其余积压仍在箱里，由
  观察台与 triage 兜底——即时性天花板仍是轮次边界，本机制把「下一次边界一定看到
  相关的、且只看到相关的」做实。
- 代价：`sessions/` 目录与 delivered 标记多一套运行时状态（gitignore，丢了可重建，
  重建后消息会重投一次）；comms-console 的 Rust 侧多一个保活线程与托盘（关窗不再
  退出，退出走托盘菜单）；comms.py 长约 300 行（会话层）。
- 第二步（未落，待平台实测接线）：PostToolUse / Stop 级 hook 做轮内注入，让长任务
  中间也能看到紧急消息；ZCode/Claude Code 的事件已确认支持，接线与打扰控制另议。
