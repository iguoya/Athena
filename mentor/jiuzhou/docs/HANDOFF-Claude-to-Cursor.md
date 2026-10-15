# 已迁移到新通讯机制

这份文件**不再使用**。九州三方（claude-code / cursor / zcode）的通讯已改成"任务文件 + 消息文件 + 命令行工具"，
不再靠互相读写同一份交接单。旧内容已存档在 `comms/jiuzhou/archive/`。

**你（cursor）现在这样开工：**

```sh
python comms/comms.py inbox cursor --project jiuzhou
```

它会列出你的未读消息和待办任务（按优先级）。完整规则见 [../../../comms/jiuzhou/README.md](../../../comms/jiuzhou/README.md)，
分工与路径归属见 [PARALLEL.md](PARALLEL.md)，全局路线见 [ROADMAP.md](ROADMAP.md)。

你的任务在 `comms/jiuzhou/tasks/` 里（`T-0xx`），看板见 [../../../comms/jiuzhou/BOARD.md](../../../comms/jiuzhou/BOARD.md)。原来任务单里的 Q1–Q8、R1–R8 已全部迁移成任务。
