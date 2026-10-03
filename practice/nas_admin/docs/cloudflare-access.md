# 外网访问：Cloudflare Access

主仓库 ADR 0077：**应用里不认证，外网的门放在 Cloudflare 访问规则上。**
内网直连路由器的客户端不需要这一页的任何东西。

## 为什么需要它

`www.yatiger.cn` 经 Cloudflare 隧道（路由器上的 `cloudflared`）指向后台。应用本身不检查任何凭据，
所以**必须**让 Cloudflare Access 挡在整个主机名前面；它配错或被删，外网就是敞开的。

## 现状（2026-10-03 只读检查）

对 `www.yatiger.cn` 的 `/`、`/api/health`、`/api/driver/v1/ping`、`/api/users/v1/login`、`/driver/`
发不带凭据的 GET，全部在 Cloudflare 边缘被 302 到 `*.cloudflareaccess.com` 的登录页，没有请求到达
应用。也就是说整个主机名已经被一个 Access 应用覆盖。

## 一次性配置：让桌面客户端能过

浏览器看仪表盘走现有的「允许」策略（邮箱验证码等）。桌面程序没有浏览器可以登录，要用
**服务令牌**。在 Cloudflare Zero Trust 控制台（菜单名称以控制台当前界面为准）：

1. **建服务令牌**：Access → Service Auth（服务认证）→ Create Service Token。名字随意，如
   `athena-family`。创建后会显示 **Client ID** 和 **Client Secret**——Secret 只显示一次，立刻存好。
   （这是 Cloudflare 的概念，全家共用一对，不是应用里的设备令牌。）
2. **加策略**：Access → Applications → 选覆盖 `www.yatiger.cn` 的那个应用 → Policies → 新增一条，
   **Action 选 Service Auth**，Include 选刚建的服务令牌。**不要**改动已有的「允许」策略。
3. **填进客户端**：驾考客户端的「同步设置」里，外网端点填 `https://www.yatiger.cn`，把 Client ID 和
   Client Secret 填进「外网访问凭据」。内网端点保持默认。

## 常见误解：邮箱不能填进客户端

Access 策略里写的邮箱，意思是「这个邮箱的主人可以进」，验证方式是 Cloudflare 给这个邮箱发一个
**一次性验证码，在浏览器里输入**。这是给人用的，桌面程序没有浏览器可以收验证码，所以**邮箱不是
程序的钥匙**，填进客户端的「外网访问凭据」不会生效。程序用的是上面第 1 步建出来的**服务令牌**：
一对 Client ID（以 `.access` 结尾）和 Client Secret。客户端的同步设置页发现 ID 里有 `@` 会直接拦住
并提示。

## 自检（每次改完 Access 都做一次）

不带凭据请求，应该被 Cloudflare 拦住，**不应**得到应用自己的响应：

```sh
curl -sS -o /dev/null -D - --max-time 15 https://www.yatiger.cn/api/driver/v1/ping | head -5
```

- 看到 `HTTP/1.1 302` 且 `Location` 指向 `cloudflareaccess.com`（或 `403`）→ 门在。
- 看到 `HTTP/1.1 200` 和 `{"ok":true,...}` → **门没了**，外网敞开，立刻去控制台检查。

带上服务令牌，应该能通：

```sh
curl -sS --max-time 15 \
  -H "CF-Access-Client-Id: <Client ID>" -H "CF-Access-Client-Secret: <Client Secret>" \
  https://www.yatiger.cn/api/driver/v1/ping
```

应返回 `{"ok":true,"server_time":...}`。

## 凭据泄露了怎么办

没有「撤销一台设备」，只有换一对：在 Cloudflare 里删掉旧服务令牌、建新的、改策略指向新的，
然后每台外网使用的电脑重新填一次。内网使用不受影响。

## 可选的后续加固

服务端校验 `Cf-Access-Jwt-Assertion` 的签名，经隧道进来的请求一律要求有效 JWT（失败即拒），
这样即使 Access 策略被误删，应用自己仍会拒绝。需要在路由器上引入密码学依赖，暂不做（ADR 0077）。
