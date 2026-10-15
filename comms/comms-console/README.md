# comms-console 舱：协作观察台（ADR 0166）

通讯规则、命令、状态机见 [../README.md](../README.md)（通用协议，ADR 0165）。
本舱主题：把多代理协作做成可打开的桌面观察台 `tools/comms-console`，并加固 `comms.py`。

名册（2026-10-15 二次修订：zcode-2 撤下，任务全部归 cursor）：**zcode = leader**，**cursor = worker（号段 1，T-001 / T-002 / T-101）**。cursor 同时支援 driver 舱的科目二任务，两边优先级由 leader 在消息里裁决。

## 角色

- **zcode = leader**：拆任务、写任务书（含验收口径）、验收 done、裁决。壳、数据层与界面按 ADR 0166 由 leader 完成（T-901）。
- **cursor = worker**：T-001（`comms.py` 加固）、T-002（视图口径，决策参与）、T-101（阅读体验增强）；另有 driver 舱科目二 T-002 / T-003。建议走消息，不自行改方向。

## 入口命令（每轮开工第一件事）

```sh
python comms/comms.py inbox cursor --project comms-console
python comms/comms.py inbox zcode  --project comms-console
```

## 文件归属（撞到别人的未提交改动先停）

| 路径 | 谁改 |
|---|---|
| `tools/comms-console/`（壳、投影、三视图） | zcode（T-901） |
| `comms/comms.py`、`comms/tests/` | cursor（T-001），命令与文件格式不变 |
| `comms/comms-console/docs/view-semantics.md` | cursor（T-002） |
| `comms/hooks/` | 谁改先在本舱说一声；cursor 已把通用 hook 接到自己的会话提醒 |
| `docs/decisions/0166-*.md` | 已接受；要改先在本舱商量，由 leader 定 |
| cursor 的路径 | leader 派 T-1xx 时在任务书里写清 |

`comms.py` 同时被 driver 等舱使用。改它之前在本舱发消息，验收必须证明 driver 舱的 inbox/status 仍然可用。

## 应用规范

- ADR 0165（文件是权威、只增不改、各写各的）
- ADR 0166（观察台只读；PG 是投影；PG 不可达时降级读本地文件）
- 工具类归 `tools/`，不建进度库（ADR 0146）
