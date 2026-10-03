# 驾考进度 REST API

挂在 nas_admin 后台里（`nas_admin/driver_api/`），让驾考客户端**离开内网也能读写同一份进度数据**。

数据库端口不出内网：数据库密码只留在路由器上。**应用里不认证**——内网直连可信，外网的门放在
Cloudflare 访问规则上（主仓库 ADR 0077，已取消设备令牌）。
API 读写的是中心库 `athena_driver` 的全部个人数据表。

> 状态：已实现、已测试。仓库级 ADR：0067（中心 PG）、0068（本 API 的由来）、0070（客户端已接入，
> 内网直连 PG 的通道退役）、0077（取消设备令牌，门放在 Cloudflare 上，取代 0068 的令牌认证）。

## 一、同步模型

驾考的进度记录绝大多数是**只追加**的事件（作答、考试、练车记录、笔记……），产生后不再修改。
这类数据两台机器各自产生的记录取并集即可，**没有「合并冲突」**。所以同步 = 两个动作：

1. **上传**自己还没发出去的记录：`POST /<资源>`，幂等——同一条重复上传会被跳过。
2. **拉取**别处新增的记录：`GET /<资源>?after_id=<上次的游标>`。

**幂等靠去重键**（沿用旧同步约定「题号 + 时间」，driver ADR 0010）：

| 资源 | 去重键 |
|---|---|
| attempts | question_id + at |
| exams | subject_id + at |
| drill-runs / rehearsals / drill-notes | item_id + at |
| point-notes | item_id + step + at |
| notices | kind + title + at |
| explain-views | question_id + attempt_at |

`at` 是客户端的 ISO-8601 时间串，**服务端原样保存**（不转时区、不改精度），两端字符串一致去重才成立。

库里的 `id` 是服务端自增，只当**拉取游标**用，不是全局标识：内网直连写入的记录和 API 写入的共用一个序列。

少数可变数据另有规则：

- **成就** `PUT /achievements/<key>`：按键幂等，已存在时保留**更早**的解锁时间。
- **试卷草稿** `PUT /exam-drafts/<key>`：整份覆盖；库里的 `saved_at` 比传来的更新则**不覆盖**（返回 `applied:false`）。

## 二、访问控制与用户

**应用里不认证**（ADR 0077）。谁能碰到这个接口，由网络决定：

- **内网**：客户端直连路由器上的后台，家用网络内视为可信，不需要任何凭据。
- **外网**：经 Cloudflare 隧道，整个主机名（含 `/api/`）由 Cloudflare Access 把守。桌面客户端用
  Access 的**服务令牌**（请求头 `CF-Access-Client-Id` / `CF-Access-Client-Secret`），全家共用一对，
  在客户端的可选配置里填。一次性配置和自检见 [cloudflare-access.md](cloudflare-access.md)。

用户来自**必填**的 `X-Athena-User` 头（ADR 0071、0075），值是学习者编号（服务端分配的
1～999 数字，见 [user-api.md](user-api.md)）。同一份题库给多个学习者用，个人数据按用户隔离；
缺头或空值是 400（`/ping` 例外）。上传的去重键、拉取的行、成就、草稿、已读、统计全部按用户隔离；
返回的行里不带 `user` 字段——那是请求方自己的身份。无口令：防误看，不防对抗。中心表的迁移与
全新建库用 `scripts/driver_migrate_users.py`。

限流按来源地址（经 Cloudflare 来的取 `Cf-Connecting-Ip`），每个地址每分钟最多 300 个请求，超出
返回 429。目的只是不让失控的客户端把库打爆。

旧客户端若还带着 `Authorization` 头，服务端直接忽略。

## 三、接口

前缀 `/api/driver/v1`，请求与响应均为 UTF-8 JSON。

| 方法与路径 | 说明 |
|---|---|
| `GET /ping` | 连通自检，不要求学习者头，返回服务器时间（客户端「测试连接」用） |
| `GET /stats` | 各表条数与最大 id，用来快速判断是否落后 |
| `GET /<资源>?after_id=0&limit=200` | 增量拉取，`limit` 1～500 |
| `POST /<资源>` | 批量上传 `{"items":[...]}`，1～500 条，返回 `{inserted, skipped}` |
| `POST /notices/read-all` | 全部标已读，返回 `{updated}` |
| `GET /achievements` | 全部成就 |
| `PUT /achievements/<key>` | body `{"at": "..."}`，返回生效的时间 |
| `GET /exam-drafts/<key>` | 取草稿，没有则 404 |
| `PUT /exam-drafts/<key>` | 存草稿，返回 `{applied}` |
| `DELETE /exam-drafts/<key>` | 删草稿，204（不存在也 204） |

资源（`<资源>`）：`attempts`、`exams`、`drill-runs`、`rehearsals`、`drill-notes`、`point-notes`、`notices`、`explain-views`。
字段与旧版客户端本地表一致，字段名、类型、长度上限见 `nas_admin/driver_api/resources.py`。

**归因字段（主仓库 ADR 0076）**：都是可选字段，旧客户端不传即为空；不参与去重键；旧数据全为空。

| 资源 | 字段 | 含义 |
|---|---|---|
| attempts | `chosen` | 所选选项的稳定标识（题库里的 `Choice.id`，多选排序后逗号拼接），≤ 40 字符 |
| attempts | `session_id` | 这次作答所属的会话（客户端随机生成，不含个人信息），≤ 64 字符 |
| attempts | `reason` | 仅强化练习使用：这道题为什么被选中（`retest`/`weak`/`due`/`fill`），≤ 32 字符 |
| attempts | `kind` | 场合标记，现有 `practice`/`exam`，新增 `reinforce`（强化练习） |
| exams | `session_id` | 与该场考试内所有 `attempts.session_id` 相同，即「作答属于哪场考试」的关联键 |
| exams | `used_ms` | 整场实际用时（不含挂起） |
| exam-drafts | `session_id` | 续答沿用同一个会话；整份覆盖，没带就清空 |
| explain-views | `question_id`、`attempt_at`、`dwell_ms` | 答错后看解析的停留（≤ 300000 ms）；`attempt_at` 对上那次作答的 `at`。独立成一个事件，因为停留在判定之后才知道，回头改作答行会破坏追加型同步 |

**部署顺序**：服务端**拒绝未知字段**，所以必须先部署服务端、再发客户端，否则新客户端上传会得到 400。
中心库加列与建 `explain_views` 表用 `scripts/driver_migrate_users.py`（属主执行，幂等）。API 的低权限
角色若是在建表之前授的权，新表需要补授 `SELECT, INSERT, UPDATE, DELETE`（`ALTER DEFAULT PRIVILEGES`
设置过的话自动具备）。

拉取响应：`{"items":[...], "has_more": bool, "next_after_id": N}`。**标志位**（`correct`、`hesitant`、
`passed`、`read`、`full_bank`）上传时可以用 0/1 或 true/false，但**拉回来一律是 0/1 整数**，客户端不要直接当布尔强转。
`GET /exam-drafts/<key>` 的字段**直接放在响应顶层**（不包一层 `draft`）。下次从 `next_after_id` 继续；
`has_more` 为 false 就是拉完了。

校验规则（违反一律 400，**整批拒绝、不会写一半**）：

- 未知字段拒绝（字段名写错立刻发现，不悄悄丢数据）。
- 字符串不为空（除正文类）、不含空字符、有长度上限；整数有范围；`correct`/`hesitant`/`passed`/`full_bank`/`read` 取 0/1 或 true/false；`at` 必须是合法 ISO-8601。
- 请求体上限 1 MB，批量上限 500 条。

错误统一为 `{"error": 代码, "message": 说明}`，**不返回堆栈、路径或数据库细节**（细节只进服务端日志）：

| 状态 | error | 含义 |
|---|---|---|
| 400 | invalid | 校验失败，message 指到字段（如 `items[3].at`） |
| 413 | too_large | 请求体过大 |
| 429 | rate_limited | 同一来源地址请求太频繁 |
| 503 | not_configured | 没配 driver 数据库连接串 |
| 503 | not_initialized | 表还没建（需先在内网用驾考客户端连一次） |
| 503 | database_unavailable | 数据库暂不可用 |

## 四、部署

1. **建 API 专用的低权限数据库角色**（路由器上，以 postgres 身份；密码随机生成，不要贴到聊天或仓库）：

   ```sql
   CREATE ROLE driver_api LOGIN PASSWORD '<随机强密码>' NOSUPERUSER NOCREATEDB NOCREATEROLE CONNECTION LIMIT 10;
   GRANT CONNECT ON DATABASE athena_driver TO driver_api;
   \c athena_driver
   GRANT USAGE ON SCHEMA public TO driver_api;
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO driver_api;
   ALTER DEFAULT PRIVILEGES FOR ROLE athena_driver IN SCHEMA public
     GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO driver_api;
   ```

   该角色**没有 DDL 权限**，不建表、不改表；表由驾考客户端在内网首次连接时创建。
   （2026-10-02 在路由器上用临时库验证过：增删改查够用、identity 列无需额外授权、不能建表/删表/清表、连不上别的库。）

2. **配置连接串**（不进仓库）：环境变量 `DRIVER_API_DATABASE_URL`，或后台目录下 `driver-db.json`
   （已 gitignore，`{"url": "postgresql://driver_api:密码@192.168.6.1:5432/athena_driver"}`，权限 600）。
   API 与 PG 同在路由器上，连内网口 `192.168.6.1`（pg_hba 已放行该网段，路由器连自己的内网口
   不依赖外部网络状态）。**不要写 `127.0.0.1`**：PG 的 `listen_addresses` 虽已加上它，但在 PG
   下次重启前并不实际监听，连接会 refused（2026-10-02 部署仪表盘时踩过，症状是
   `database_unavailable`）。没配时 API 返回 503 `not_configured`，不影响后台其他功能。

3. **部署后台**（deploy 脚本，或同步 `nas_admin/` 到 `/opt/webapp` 后重启 `webapp` 服务）。

4. **Cloudflare**：为桌面客户端建服务令牌与「服务认证」策略，部署后做一次自检——见
   [cloudflare-access.md](cloudflare-access.md)。只在家里内网用的话可以跳过。

## 五、测试

```sh
cd practice/nas_admin
.venv/Scripts/python -m unittest discover -s tests -v     # 不依赖路由器：SQLite + 真实 FAB 应用冒烟
```

`tests/test_driver_api_pg.py` 对真实 PostgreSQL 的集成测试，设了两个环境变量才跑（否则整体跳过）：
`DRIVER_API_TEST_PG_OWNER_URL`（属主，建表清表用）、`DRIVER_API_TEST_PG_URL`（被测的低权限角色）。
它会核对 `schema.py` 与真实表的列是否一致、并发上传不产生重复行、低权限角色的权限边界。
测试库与角色用完即删，不要对生产的 `athena_driver` 库跑。

## 六、已知限制与后续

- **照片**（`point_photos`）暂不开放：照片是文件、体积大，v1 只同步文字数据。
- 没有服务端汇总统计（连续天数、平均用时等），客户端从拉到的记录自己算，和现在本地的算法一致。
- 速率限制是进程内的、按来源地址；路由器上后台只有一个进程，够用，多进程部署要换共享存储。
- 应用里没有第二道门：Cloudflare Access 配错或被删时，外网就是敞开的，所以每次改完要做自检。
  可选的后续加固是服务端校验 `Cf-Access-Jwt-Assertion` 的签名（ADR 0077 风险一节）。
- 后台入口仍是 Flask 自带服务器；对外前建议换 `waitress`（纯 Python，路由器能装）。
- 客户端（`subjects/driver`）已接入（主仓库 ADR 0070）：本地优先 + 待发送队列 + 游标拉取，
  断网照常做题、联网后补发；内网也走本 API，直连 PG 的通道已退役。
