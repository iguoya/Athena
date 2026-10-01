# 0018 启动时自动更新

- 状态：已采纳
- 日期：2026-09-30
- 决策人：tiger

## 背景

tiger 希望软件每次运行前能主动拉取最新代码、自己编译、自动运行。但侄女的笔记本不应该为了更新去装 Node、Rust 和 6 到 8 GB 的 C++ 生成工具：安装麻烦，每次启动还要编译几分钟，编译出错她也处理不了。

## 决策

分两条路：

1. **侄女的电脑（正式使用）：编译放在云端，本机只下载更新。**
   - 每次推送到 master，GitHub Actions 在 Windows 上编译出签名的安装包，发布成 GitHub Release（版本号 0.1.构建序号）。
   - 软件每次启动时用 Tauri 的 updater 插件查一次最新版本；有新版本就在右下角显示进度，静默安装后自动重启。学习记录在用户数据目录，更新不受影响。
   - 断网或检查失败时直接跳过，照常打开（ADR 0002）。
   - 安装包用 updater 私钥签名，软件只接受签名对得上的更新。
2. **tiger 的电脑（开发）：一键拉代码、编译、运行。**
   - 双击仓库根目录的“启动 Lumi（开发版）.cmd”：执行 `git pull`，依赖有变化时自动 `pnpm install`，然后 `pnpm tauri dev`。

只改了 `adr/`、`archive/` 或 Markdown 文件的提交不触发构建。

## 需要 tiger 做一次的设置

1. 在自己电脑上生成签名密钥：`pnpm tauri signer generate -w %USERPROFILE%\.tauri\lumi.key`（设不设密码都可以）。
2. 把公钥（`lumi.key.pub` 的内容）填进 `src-tauri/tauri.conf.json` 的 `plugins.updater.pubkey`，提交推送。
3. 在 GitHub 仓库 Settings → Secrets and variables → Actions 里新建 `TAURI_SIGNING_PRIVATE_KEY`（私钥文件的内容），设了密码的话再建 `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`。
4. 私钥只存在他电脑和 GitHub Secrets 里，永远不提交进仓库；丢了私钥，已安装的软件就收不到更新，只能手动重装一次。

没设私钥之前，发布流程会跳过构建并给出提示，不会报错。

## 后果

- 侄女的电脑第一次需要手动装一次安装包，之后都自动更新。
- 每次推送 master 都会发布新版本，所以 master 上的代码要保证能用。
- 本机 `pnpm tauri build` 也需要设置私钥环境变量，否则签名更新包那一步会失败；日常开发用 `pnpm tauri dev` 不受影响。
- 仓库是公开的，安装包也公开可下载。
