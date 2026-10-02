# 驾考进度 REST API

挂在 nas_admin 后台里（`nas_admin/driver_api/`），让驾考客户端**离开内网也能读写同一份进度数据**。

数据库端口不出内网：客户端只拿一个可撤销的设备令牌，数据库密码只留在路由器上。
内网里驾考客户端仍可直连 PostgreSQL；API 读写的是**同一批表**（`athena_driver` 库），
两条通路的数据天然一致。

> 状态：已实现并测试，**尚未部署**。仓库级 ADR（修订 ADR 0067 的「外网走隧道直连 PG」）待补，
> 编号由使用者定。

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

`at` 是客户端的 ISO-8601 时间串，**服务端原样保存**（不转时区、不改精度），两端字符串一致去重才成立。

库里的 `id` 是服务端自增，只当**拉取游标**用，不是全局标识：内网直连写入的记录和 API 写入的共用一个序列。

少数可变数据另有规则：

- **成就** `PUT /achievements/<key>`：按键幂等，已存在时保留**更早**的解锁时间。
- **试卷草稿** `PUT /exam-drafts/<key>`：整份覆盖；库里的 `saved_at` 比传来的更新则**不覆盖**（返回 `applied:false`）。

## 二、认证

所有接口都要设备令牌：`Authorization: Bearer dapi_xxxx`。没有匿名接口。

- 每台设备一个令牌，服务端**只存 SHA-256 哈希**，库被读走也还原不出令牌。
- 丢了一台设备就撤销那一个，不影响别的。
- 令牌表在后台自己的库（`nas_admin`），不放进 driver 的个人数据库。
- 每个令牌每分钟最多 300 个请求，超出返回 429。

管理令牌（路由器或本机，需能连后台库）：

```sh
python3 scripts/driver_token.py create "笔记本"   # 令牌明文只显示这一次
python3 scripts/driver_token.py list
python3 scripts/driver_token.py revoke 3
```

外网访问时前面还有 Cloudflare Access（`www.yatiger.cn` 已有）：程序调用用 Access 的
**Service Token**（请求头 `CF-Access-Client-Id` / `CF-Access-Client-Secret`），两层都要带。
设备令牌不依赖 Access——Access 挡陌生人，设备令牌挡「进来了但不该写数据」的人，也让每次写入能追溯到设备。

## 三、接口

前缀 `/api/driver/v1`，请求与响应均为 UTF-8 JSON。

| 方法与路径 | 说明 |
|---|---|
| `GET /ping` | 令牌自检，返回设备名与服务器时间（客户端「测试连接」用） |
| `GET /stats` | 各表条数与最大 id，用来快速判断是否落后 |
| `GET /<资源>?after_id=0&limit=200` | 增量拉取，`limit` 1～500 |
| `POST /<资源>` | 批量上传 `{"items":[...]}`，1～500 条，返回 `{inserted, skipped}` |
| `POST /notices/read-all` | 全部标已读，返回 `{updated}` |
| `GET /achievements` | 全部成就 |
| `PUT /achievements/<key>` | body `{"at": "..."}`，返回生效的时间 |
| `GET /exam-drafts/<key>` | 取草稿，没有则 404 |
| `PUT /exam-drafts/<key>` | 存草稿，返回 `{applied}` |
| `DELETE /exam-drafts/<key>` | 删草稿，204（不存在也 204） |

资源（`<资源>`）：`attempts`、`exams`、`drill-runs`、`rehearsals`、`drill-notes`、`point-notes`、`notices`。
字段与旧版客户端本地表一致，字段名、类型、长度上限见 `nas_admin/driver_api/resources.py`。

拉取响应：`{"items":[...], "has_more": bool, "next_after_id": N}`。下次从 `next_after_id` 继续；
`has_more` 为 false 就是拉完了。

校验规则（违反一律 400，**整批拒绝、不会写一半**）：

- 未知字段拒绝（字段名写错立刻发现，不悄悄丢数据）。
- 字符串不为空（除正文类）、不含空字符、有长度上限；整数有范围；`correct`/`hesitant`/`passed`/`full_bank`/`read` 取 0/1 或 true/false；`at` 必须是合法 ISO-8601。
- 请求体上限 1 MB，批量上限 500 条。

错误统一为 `{"error": 代码, "message": 说明}`，**不返回堆栈、路径或数据库细节**（细节只进服务端日志）：

| 状态 | error | 含义 |
|---|---|---|
| 400 | invalid | 校验失败，message 指到字段（如 `items[3].at`） |
| 401 | unauthorized | 缺少或无效的令牌，已撤销也是 401 |
| 413 | too_large | 请求体过大 |
| 429 | rate_limited | 请求太频繁 |
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
   令牌表 `driver_api_tokens` 会在首次使用时自动建在后台库里。

4. **发令牌**：`python3 scripts/driver_token.py create "<设备名>"`，把输出的令牌配到该设备的本地配置（不进仓库）。

5. **Cloudflare**：为 API 调用建一个 Access **Service Token**，并在 `www` 应用的策略里加一条
   「Service Auth」放行；浏览器访问仍走邮箱验证码。

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
- 速率限制是进程内的；路由器上后台只有一个进程，够用，多进程部署要换共享存储。
- 后台入口仍是 Flask 自带服务器；对外前建议换 `waitress`（纯 Python，路由器能装）。
- 客户端（`subjects/driver`）还没接这套 API；接口契约见上，客户端建议本地保留一个「待发送队列」，
  断网时照常做题，联网后补发（事件追加型 + 幂等，队列很简单）。
