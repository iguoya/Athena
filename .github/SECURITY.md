# 安全策略

Athena 是个人自用的学习软件平台，没有对外提供的在线服务，也没有多用户部署。
各应用都在本机运行，进度数据存在本地 `progress/learning.db`。唯一的例外是
`certification/driver` 连接的中心 PostgreSQL 服务（ADR 0067、0068、0070），凭据
不进仓库。

## 支持的版本

只维护最新的发布版本和 `main` 分支，旧版本不再修补。

## 报告漏洞

发现安全问题（例如仓库里误提交的密钥、依赖里的已知漏洞、应用的本地提权或数据泄露）
请**不要**公开开 issue，通过 GitHub 的私密渠道报告：

[Security → Report a vulnerability](https://github.com/iguoya/Athena/security/advisories/new)

这是个人项目，没有固定的响应时限，尽量在几天内回复。

## 已开启的自动防护

- Secret scanning 与 push protection：推送含已知格式密钥的提交会被拦下。
- Dependabot alerts：依赖出现已披露漏洞时告警。
- CodeQL（默认配置，每周扫描）：覆盖 actions、c-cpp、javascript-typescript、python、rust 等。
