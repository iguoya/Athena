# 九州协作协议（Claude Code 指挥 · Cursor 与 ZCode 执行）

根 `AGENTS.md`「多个代理并行」：代理之间没有私聊通道，约定只能写在文件里。
**本应用约定：claude-code 只管大局、规划与验收；cursor 做前端与地图；zcode 做内容。**
cursor 与 zcode 是**伙伴**（平级协同），共同服从 claude-code 的任务单。使用者已授权三方在
ADR 0001 / 0158 的大方向下自主推进，小事不必问使用者；方向有分歧时以 claude-code 为准。

通讯机制（任务文件 + 消息文件 + 命令行工具）：**[comms/README.md](comms/README.md)** ·
看板：[comms/BOARD.md](comms/BOARD.md) · 路线图：[ROADMAP.md](ROADMAP.md) ·
立项意图验收：[INTENT-CHECKLIST.md](INTENT-CHECKLIST.md) · 架构：[decisions/0001](decisions/0001-year-driven-spatial-history.md)

## 三方职责

| 角色 | 名字（命令里用） | 做什么 | 不做什么 |
|---|---|---|---|
| **指挥 / 规划 / 验收** | `claude-code` | 定大局、拆里程碑、创建任务、实机验收并标 `done`、裁决冲突、维护路线图与意图清单 | 不写内容、不写前端（紧急修复除外，须发消息说明） |
| **前端 / 地图** | `cursor` | 界面、地图渲染、`@athena/maps`、检查脚本接入、打包发行 | 不改 `content/**` |
| **内容** | `zcode` | 事件、地点、人物、疆域快照、路线、叙事、出处核对、事实审查 | 不改 `src/**` 与 `packages/maps/**` |

## 路径归属（同一时间只有主人能写，其余只读）

| 路径 | 主人 |
|---|---|
| `src/**`、`src-tauri/**`、`packages/maps/**`、`scripts/check.py`、应用根 `README.md` / `AGENTS.md` | cursor |
| `content/**`、`scripts/check_layers.py`、`scripts/add_content.py` | zcode |
| `docs/PARALLEL.md`、`docs/ROADMAP.md`、`docs/INTENT-CHECKLIST.md`、`docs/comms/tasks/**`（创建）、`scripts/comms.py` | claude-code |
| `docs/comms/msgs/**`、`docs/comms/read/<自己>.txt` | 发信人 / 各自 |
| `docs/decisions/**`（应用 ADR） | claude-code 起草，涉及哪方由哪方落实 |

## 指挥链与平级协同

- **claude-code → cursor / zcode**：任务（`comms/tasks/`）+ 消息。**任务优先级以 claude-code 为准。**
- **cursor / zcode → claude-code**：状态回报（`status ... review --note`）、提问、需求、数据缺口。
- **cursor ↔ zcode（平级）**：直接互发消息，用于接口约定、字段已落地通知、验收口径对齐、撞车预警。
  **平级之间不下发任务、不改对方文件**；要对方做事，发给 claude-code 转成任务。
- 任务队列排好后，做完前不必回来问“下一步做什么”；做完了发一条“待命”。
- 撞到别人的未提交改动：先停，发消息说明，不覆盖、不合并半成品。

## 跨方契约（改 schema 的流程）

1. 提出方（通常是 zcode 发现字段不够用，或 cursor 发现读不了）发消息给 claude-code，写清需求。
2. claude-code 裁决，必要时先写 ADR，并在两方的任务里分别写落实项。
3. **先改内容与校验（zcode），再改前端读取（cursor）**，顺序不要反。
4. 新字段一律可选；前端读不到时静默降级，不报错。

## 验证与提交

```sh
python mentor/jiuzhou/scripts/check.py --skip-rust   # 日常，改完必须绿
python mentor/jiuzhou/scripts/check.py               # 发版前（含 Rust）
python mentor/jiuzhou/scripts/comms.py check         # 通讯结构
```

**git 只提交自己名下的路径，`git add` 写明确路径，不整目录添加。**
旧的 `HANDOFF-*.md` 已废弃，只作指路牌，旧内容存档在 `comms/archive/`。
