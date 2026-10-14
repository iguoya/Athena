# 学习进度通用同步接口（/api/progress/v1）

各学习应用的本地 SQLite 进度库由启动器里的同步代理推拉到这里（主仓库 ADR 0155）。
服务端**不认识任何应用的表结构**：一行 = 某学习者在某应用某张表里的一条记录，内容是客户端
原样传来的 JSON 对象。**应用里不认证**（ADR 0077）：内网直连可信，外网由 Cloudflare Access
把守，见 [cloudflare-access.md](cloudflare-access.md)。

数据在后台库（nas_admin）的 `athena_progress_rows` 表（PG 上 `data` 是 JSONB）；首次请求时自动建表。

## 通用约定

- 学习者：请求头 `X-Athena-User`，全局目录分配的编号 1～999（[user-api.md](user-api.md)），目前不校验是否登记。
- 应用 id：小写字母、数字、连字符，如 `c-plus-plus`。
- 时间：一律 UTC、`2026-10-13T01:02:03.123Z` 这种形状，**固定三位毫秒**，其他写法一律 400。格式逐字一致，字符串比较才等于时间比较。
- 错误：`{"error": 代码, "message": 说明}`；校验失败 `400 invalid`，限流 `429`，库不可达 `503`。
- 限流按来源地址，同其他接口。响应一律 `Cache-Control: no-store`。

## 行与合并规则

| 字段 | 说明 |
|---|---|
| `tbl` | 本地表名，字母数字下划线，≤64 |
| `pk` | 该行的主键串（复合主键由客户端编成一个串），≤400 |
| `mode` | `append`：事件，同一键只记第一次，之后重复上传一律忽略，唯一能改它的是墓碑（见 `deleted`）；`lww`：可变记录，按 (`stamp`, 设备名) 新者胜 |
| `stamp` | 这条记录的更新时间（UTC） |
| `data` | JSON 对象，序列化后 ≤64 KB；`deleted` 为真时可省略 |
| `deleted` | 删除标记。删除是一行带标记的记录，不真删，所以更旧的写入不会让它复活。`lww` 的删除清掉 `data`；`append` 的删除是**墓碑**（ADR 0160）：存活 → 已删单向生效，原 `data` 保留，已删的事件再收到任何写入都被忽略 |

服务端每次写入（新增或改写）都给这行分配新的 `seq`（全局单调），客户端用它做增量拉取的游标。

## 接口

### `POST /push`

```json
{"app": "c-plus-plus", "device": "pc-a", "rows": [
  {"tbl": "knowledge_progress", "pk": "c.1", "mode": "lww", "stamp": "2026-10-13T01:00:00.000Z", "data": {"mastery": 3}},
  {"tbl": "run_history", "pk": "2026-10-13T00:59:00|7", "mode": "append", "stamp": "2026-10-13T00:59:00.000Z", "data": {}},
  {"tbl": "knowledge_progress", "pk": "c.9", "mode": "lww", "stamp": "2026-10-13T01:00:00.000Z", "deleted": true}
]}
```

一批最多 500 行、请求体 ≤2 MB；**任何一行校验失败，整批不落库**。重复推送结果不变（幂等）。
→ `200 {"accepted": 2, "ignored": 1, "cursor": 17}`，`cursor` 是当前最大序号。

### `GET /pull?app=<id>&since=<序号>&limit=<n>`

拉序号大于 `since` 的行（`limit` 1～500，默认 500），按序号升序：

```json
{"rows": [{"tbl": "...", "pk": "...", "data": {}, "mode": "lww", "stamp": "...", "deleted": false, "device": "pc-a", "seq": 18}],
 "next": 18, "more": false}
```

`more` 为真就拿 `next` 当新的 `since` 接着拉。客户端自己推上去的行也会拉回来，按 `device` 跳过即可。

## 测试

`tests/test_progress_api.py`，内存 SQLite，不依赖路由器：

```sh
cd practice/nas_admin && .venv/Scripts/python -m unittest tests.test_progress_api -v
```
