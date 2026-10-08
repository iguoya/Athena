# 0021 — 发布名与二进制名改用 athena-ascent

日期：2026-10-08

## 背景

并入 Athena（[0020](0020-merged-into-athena.md)）时保留了独立时代的发布名 Lumi：
`productName`、`app.json` 的 `binary`、npm 包名都是 lumi/Lumi，安装包叫
`Lumi_<版本>_x64-setup.exe`。仓库其余应用的发布产物统一遵守 `athena-<id>` 命名
（主仓库 ADR 0046），v9.0.0 起六个应用同台发布，唯独拾阶的资产不带前缀，名字表
为此留了例外。使用者在结构提案 P3 上拍板：改为加前缀，发布统一。

## 决策

1. `productName`、`app.json` 的 `binary`、npm 包名从 lumi/Lumi 改为
   `athena-ascent`；安装包随之变为 `athena-ascent_<版本>_x64-setup.exe`。
2. **窗口标题与应用内的中文名保持「拾阶」不变**——改名只发生在工程面
   （二进制、包、发布资产），不动品牌与界面文案。
3. 主仓库 `docs/REPOSITORY.md` 名字表的例外条目随之删除。

## 后果

- v9.0.0 是最后一个叫 Lumi 的版本。下一版起 latest.json 由 tauri-action 按新
  productName 生成、指向新名字的安装包——老用户的应用内更新器拉到新清单后
  下载新包完成升级，链路自动切换，不需要迁移动作。
- 历史发布的 `Lumi_9.0.0_x64-setup.exe` 保留在 GitHub Release 上，作为独立
  时代的存档，不回删。
- 「Lumi」作为历史名保留在本文与 README 的背景叙述里；工程配置、发布资产与
  文档的当前态一律用 athena-ascent。
- 顺带清理：独立时代的开发脚本 `lumi-dev.ps1`（配套的「启动 Lumi（开发版）.cmd」
  已按主仓库大扫除删除）与应用内 `.github/workflows/release.yml`（ADR 0081 把
  发版机制迁回仓库根后的死文件）一并删除。
