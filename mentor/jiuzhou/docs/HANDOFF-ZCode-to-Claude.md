# 已迁移到新通讯机制

这份文件**不再使用**。九州三方（claude-code / cursor / zcode）的通讯已改成"任务文件 + 消息文件 + 命令行工具"，
不再靠互相读写同一份交接单。旧内容已存档在 `comms/archive/`。

**你（claude-code）现在这样开工：**

```sh
python mentor/jiuzhou/scripts/comms.py inbox claude-code
```

它会列出你的未读消息和待办任务（按优先级）。完整规则见 [comms/README.md](comms/README.md)，
分工与路径归属见 [PARALLEL.md](PARALLEL.md)，全局路线见 [ROADMAP.md](ROADMAP.md)。

回报与提问请用 `comms.py send --from zcode --to claude-code ...`。
