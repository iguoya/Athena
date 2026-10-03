# 学习者目录 API（/api/users/v1）

全局学习者目录的 REST 接口（主仓库 ADR 0074、0075）。学习者是「这个人」，不属于某个应用，
所以不挂 `/api/driver` 前缀；认证复用驾考 API 的**设备令牌**（`Authorization: Bearer dapi_…`，
发令牌见 `scripts/driver_token.py`）。

数据在后台库（nas_admin）的 `athena_users` 表，与令牌表同库；首次请求时自动建表。

## 模型

- **编号**：服务端顺序分配的纯数字，1～999，永不变、不复用、没有删除接口。
- **名字**：显示名，不要求唯一；比较时忽略大小写和首尾空白。非空、不超过 64 个字符、不含
  `/` `\`。
- **无口令**：登录只是「名字（重名再加编号）→ 这个人是几号」。令牌持有者可以以任何名字进入
  （ADR 0071 的信任模型）；多问一次编号不是安全措施。
- **没有「列出全部学习者」**：按名字查询也不泄露他人的编号。

## 接口

错误一律 `{"error": 代码, "message": 说明}`。

| 方法 路径 | 说明 |
|---|---|
| `POST /users` | 新建。`{"name": "小王"}` → `201 {"user": {"id": 3, "name": "小王"}}`。重名照样新建。编号用完 → `409 directory_full` |
| `POST /login` | 按名字登录。`{"name": "小王"}`，可再带 `"id": 3`。见下 |
| `GET /users/<id>` | 查自己（刷新本机缓存里的名字）。请求头 `X-Athena-User` 必须等于 `<id>`，否则 `403` |
| `PATCH /users/<id>` | 改自己的名字。`{"name": "新名字"}`。请求头 `X-Athena-User` 必须等于 `<id>`，否则 `403`（只能改自己） |

### `POST /login` 的结果

| 情形 | 响应 |
|---|---|
| 恰好一个同名学习者 | `200 {"user": {"id", "name"}}` |
| 没有这个名字；或给了编号却对不上 | `404 not_found`（两种情况同一个答案，不暗示名字存不存在） |
| 不止一个同名、没给编号 | `409 ambiguous`，带 `"matches": 个数`，**不带任何编号**；客户端再问使用者要编号后重发 |

`id` 接受整数或纯数字串，范围 1～999，其余 `400`。

## 与驾考 API 的关系

驾考 API 的 `X-Athena-User` 头里放的就是这里分配的编号（字符串）。当前服务端**还不校验**该编号
是否已登记（ADR 0074 决策 8：等所有客户端都升级、tiger 登记完成之后再打开），所以新旧客户端
可以并存。

## 初始化与迁移

`scripts/driver_migrate_users.py --users-db <后台库属主连接串>`：登记 tiger（空目录上得到 1），
并把 driver 库里 `user` 为 `tiger` 或旧 `u_…` 的行换算成数字编号。幂等。

## 测试

`tests/test_user_api.py`，内存 SQLite，不依赖路由器：

```sh
cd practice/nas_admin && .venv/Scripts/python -m unittest tests.test_user_api -v
```
