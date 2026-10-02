# practice/nas_admin 协作规则（NAS 后台管理）

仓库级通用规则在 [`../../AGENTS.md`](../../AGENTS.md)，这里只写本项目自己的。

## 是什么

`practice/` 下的项目应用（ADR 0060）：跑在软路由（ImmortalWrt x86_64，
192.168.6.1）上的后台管理面板。**不是学习应用**，教学规范不生效、不建进度库。

技术选型原则（使用者定的）：通用主流方案、开发效率与维护便利优先。
技术栈：**Flask-AppBuilder**（后台框架：认证/权限/视图）+ **PostgreSQL**
（路由器上 opkg 装的 17.5，数据目录 /opt/postgresql/data）+ psycopg 3。

## 与路由器 /opt/webapp 的关联（本项目的核心约定）

- **本目录是唯一源**，路由器上的 /opt/webapp 是部署产物，不直接改。
- `python3 scripts/deploy.py` 完成部署：打包（排除 .venv/__pycache__/
  db-local.json）→ ssh 管道上传 → 远程备份 /opt/webapp.bak-<时间戳> →
  解包覆盖 → 写连接串（600）→ pip3 装依赖 → 首次自动 create-admin →
  `/etc/init.d/webapp restart` → curl 探活。
- **入口文件名必须是 `app.py`**：路由器的 `/etc/init.d/webapp`（procd）以
  `/usr/bin/python3 /opt/webapp/app.py` 拉起服务，这个约定不动，init 脚本
  永远不需要改。
- 数据不随部署走：全部在 PostgreSQL（库 nas_admin，角色 nas_admin），
  pg_hba 放行 192.168.6.0/24 密码连接，**本机开发与路由器运行用同一条
  连接串、同一套数据**。

## 环境与账号（凭据不进仓库，ADR 0068）

- 数据库连接串：环境变量 `NAS_ADMIN_DATABASE_URL` 或本目录 `db-local.json`
  （已 gitignore，`{"url": ...}`）。deploy 会把它写到路由器
  `/opt/webapp/db-local.json`（600）。
- 驾考 API 的 driver 库连接串：环境变量 `DRIVER_API_DATABASE_URL` 或本目录 `driver-db.json`
  （已 gitignore，600，属主为运行用户）。用专用低权限角色 `driver_api`（只有增删改查、
  无 DDL），不是 driver 客户端的账号；没配时 API 返回 503，不影响后台其他功能。
- 后台管理员密码：部署时环境变量 `NAS_ADMIN_ADMIN_PASSWORD`（首次建号用，
  没有就拒绝部署）；改密码走 LuCI/FAB 界面。
- 路由器 SSH 免密（root@192.168.6.1），deploy 直接可用。

## 目录

```
app.py              入口（本机/路由器同一个）
config.py           FAB 配置（连接串、密钥，全走环境变量可覆盖）
nas_admin/          应用包（__init__ 工厂、views 首页与探活、templates）
nas_admin/driver_api/  驾考进度 REST API（/api/driver/v1，设备令牌认证；ADR 0068）
tests/              单元测试（SQLite）、真实 FAB 冒烟、对真实 PG 的集成测试（设环境变量才跑）
docs/driver-api.md  API 接口、认证、部署（含数据库低权限角色）与测试说明
scripts/driver_token.py  管理设备令牌（create / list / revoke）
scripts/run_dev.py  本机自举：bootstrap 建 .venv，serve 起 app.py
scripts/check.py    验证入口（依赖就绪 + smoke：/api/health、/login/、/）
scripts/deploy.py   部署到 /opt/webapp（含备份、建管理员、探活）
```

## 启动与验证

```sh
launcher --root practice open nas-admin     # 或 python3 scripts/run_dev.py serve
python3 scripts/check.py                    # 仓库根或本目录执行
python3 scripts/deploy.py                   # 部署到路由器
```

注意：check/deploy 依赖路由器在线（PG 和部署目标都在它上面）；路由器不在线
时本机起服务也会因数据库不可达降级（首页能看到「数据库不可达」，探活仍 ok）。

## 待办

- `SECRET_KEY` 生产化（环境变量已留好，差路由器端配置）。
- icon.svg 与启动器位图（现在用 letter 兜底色块）。
- 仪表盘的 CPU/内存/磁盘监控（要跨平台取数，引平台分支前先想清楚）。
