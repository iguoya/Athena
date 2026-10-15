# ADR 0165：多代理协作通讯抽取为仓库公共服务（comms/）

- 日期：2026-10-15
- 状态：已接受
- 影响：新增顶层 `comms/`（通用协议 README、通用化 `comms.py`、通用 hook）；新增首个舱
  `comms/driver/`；登记 `AGENTS.md`「多个代理并行」、`docs/REPOSITORY.md`
- 关系：机制原型是九州的双通道通讯（`mentor/jiuzhou/scripts/comms.py` 及其
  `docs/comms/`，2026-10-13 起三方实战）；不修改九州现有文件；仓库 AGENTS.md
  「多个代理并行」的书面约定不变，本 ADR 给它补一套可执行的机制

## 背景

九州项目从 2026-10-13 起用一套**文件制的多代理通讯**协作（claude-code 指挥、cursor
与 zcode 执行），核心是 `mentor/jiuzhou/scripts/comms.py`（621 行）加 `docs/comms/`
下的数据目录：任务（`tasks/T-xxx-*.md`）、正式消息（`msgs/`，只增不改）、已读游标
（`read/`，各写各的）、即时消息（`chat/`，各写各的 log）、生成的看板（`BOARD.md`），
外加正式与即时两条通道（inbox/status/thread 与 say/chat/notify/watch）和按 git 痕迹
判在线的 presence。这套机制实战跑了五十多个任务，验证有效，且它的核心设计——
**任何一方永远不修改别人写的文件**——从机制上杜绝了互相覆盖。

现在驾考应用（certification/driver）也要多代理协作：zcode 指挥 cursor 补强科目二
教程。机制长在九州目录里没法复用；且九州版把角色硬编码在工具里（`claude-code`
独占建任务与验收特权、任务号百位段写死、presence 的名下路径写死九州路径），
换一组角色就用不了。

## 决策

1. **新增仓库级公共服务 `comms/`**：通用协议文档（`comms/README.md`）、按舱参数化的
   `comms/comms.py`、给代理环境接线的通用 hook（`comms/hooks/agent-notify.py`）。
   工具行为与九州版一致，只做三处通用化：
   - **舱模型**：`comms/<project>/` 一个协作主题一个舱，数据（tasks/msgs/read/chat/
     artifacts/BOARD.md）全在舱内；命令一律带 `--project <名>`（可用环境变量
     `ATHENA_COMMS_PROJECT` 省略）。不同主题互不混、各自的看板各自生成。
   - **角色跟配置走**：舱内 `config.json` 声明 `leader`、`agents`、`bands`（各成员的
     任务号百位段）、`owned`（各成员名下路径，presence 用）。建任务、验收 `done`、
     `ping` 的特权属于 `leader`，不再写死 claude-code；worker 之间平级，不下发任务、
     不改对方文件。任务号段惯例：leader 占 9 段（T-9xx），worker 依次 0、1、2 段。
   - **文案去项目化**：看板标题等不再带「九州」。
2. **两类角色的语义**（写进通用协议）：**leader**——拆任务、写任务书（含验收口径）、
   验收（review → done 只有 leader 能标）、裁决分歧、打回返工；采纳 worker 建议以
   leader 确认为准。**worker**——按任务书执行、交 review 必须附验证证据、卡住转
   blocked 并说明要谁帮忙；对设计有建议发消息给 leader，不自行改方向。
3. **双机制定位**：长效任务沟通（tasks/status/board/inbox/reply/thread）承载任务书、
   验收证据、裁决与留档；即时通讯（say/chat/notify/watch）承载一句话快问快答与
   在线确认。消息只增不改；已读游标各写各的；看板由工具生成。
4. **九州舱暂不迁移**：九州目录下的机制照旧运行（其工作区有活跃未提交改动，本轮
   不碰）。择机迁移步骤：建 `comms/jiuzhou/config.json` → 搬 `docs/comms/` 数据 →
   改 `.cursor/hooks.json` 等接线指向公共工具 → 删除九州副本。迁移完成前存在两份
   `comms.py`，属已知代价。
5. **首个使用方 `comms/driver/`**：leader=zcode、worker=cursor（使用者指定），首个
   主题是科目二（C2）教程补强。cursor 侧的提醒接线暂沿用九州 hook（它只通知九州
   舱）；通用 hook 已随服务提供，接线由 cursor 侧择机切换，切换前 cursor 按约定
   每轮开工先跑 `inbox`。

## 后果

- 新主题要协作时，建一个舱（config.json + 目录）即用，不再复制脚本。
- 消息、任务、看板进 git，协作史可追溯；`comms/` 不是应用，不参与 check.py 的
  应用扫描。
- 通用 hook 未接线前，driver 舱的未读提醒依赖各代理自觉跑 `inbox`（舱 README 与
  `.cursor/rules/` 各写一条提示兜底）。
- 九州迁移完成后应删除旧副本，工具只留公共版一份；在那之前改协议要两处同步，
  所以协议变更尽量攒到迁移时一起做。
