# 驾考中心服务后台

Flask-AppBuilder + PostgreSQL 的中心服务管理端：学习者目录、作答同步 API、
进度仪表盘。部署目标是软路由（ImmortalWrt `/opt/webapp`），不是桌面应用；
外网入口由 Cloudflare Access 把守（ADR 0077）。

- 接口文档：[`docs/user-api.md`](docs/user-api.md)。
- 验证：`python scripts/check.py`。
- 客户端侧的对接方是 [`subjects/driver`](../../subjects/driver)（ADR 0068、0070）。
