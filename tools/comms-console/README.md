# 协作观察台（comms-console）

打开就能看 `comms/` 各舱多智能体协作的桌面应用：任务泳道看板、任务发布与流转
（含 leader 裁决与验收的决策记录）、正式消息与即时对话的统一时间线、按日活动统计。
只读——写操作一律走 `comms/comms.py`（ADR 0165、0166）。

数据来源：路由器 PostgreSQL（库 `athena_comms`，多机汇聚的投影）为主，
没配或连不上时直读本机仓库文件，界面左下角标明当前来源。

```sh
launcher open comms-console   # 打开
python3 scripts/check.py      # 验证
```

DSN 配置：环境变量 `ATHENA_COMMS_PG`（postgres 连接串）或用户数据目录
`AthenaCommsConsole/pg.json` 的 `{"dsn": "..."}`；都不配就是纯本地模式。
细则见 [AGENTS.md](AGENTS.md)。
