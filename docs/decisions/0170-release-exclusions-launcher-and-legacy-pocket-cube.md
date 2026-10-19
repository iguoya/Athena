# ADR 0170：启动器与旧版 pocket_cube 不进发布矩阵，理由写明

- 日期：2026-10-19
- 状态：已接受（leader 在 10.0.0 遗留清理时按 ADR 0168 的同一标准判定；使用者可推翻）
- 关系：落实 [ADR 0168](0168-release-mature-apps-uniformly.md) 第 2 条「还不算成熟的，同一条标准挡在外面」与 [ADR 0049](0049-portability-is-a-cost-benefit-call.md)「成本过高的可整体排除，要写明」。0168 后果里「启动器本身还没有安装包作业」一句，由本篇给出结论。

## 背景

0168 把「作业还没接上」与「成熟度例外」分开：Qt、Electron 这类应用补上作业后同标准进入。`docs/RELEASE-TODO.md` 把四项列为待补：`programming/machine`、`practice/pocket_cube`、`practice/c-gui-lab`、`launcher/webui`。逐项核对后，后两个里有两项不是「作业没接上」。

## 决策

1. **`launcher/webui`（启动器）不做安装包。** 启动器靠 `ATHENA_ROOT` 或当前目录找到 Athena 仓库，扫 `<分类>/<id>/app.json`，再执行各应用 `dev` 块里的命令（ADR 0044、0046、0057：应用只声明怎么启动，不打包副本）。装在没有仓库、没有开发工具链的机器上，它找不到任何东西可以启动（`launcher/core/src/main.rs`：「找不到 Athena 仓库」）。它是仓库的使用方式，不是可独立安装的应用。`tauri.conf.json` 的 `bundle.active: false` 本来就是这个意思。本地用 `pnpm run tauri:build` 出可执行文件的做法不变。
2. **`practice/pocket_cube` 不进发布。** ADR 0169 已把它定为「旧版，供参考」，`AGENTS.md` 写明「不再往下做」「打乱与求解算法还没做」。按 0168 第 2 条，它不是相对成熟的应用。继任者 `programming/pocket-cube-solver` 已进矩阵。
3. **`programming/machine`（Qt）与 `practice/c-gui-lab`（Electron）仍按 0168 第 3 条处理**：它们是成熟应用，缺的是打包作业，补作业时用同一条标准，不在本篇豁免之列。

## 后果

- `docs/RELEASE-TODO.md` 里这两项改为「已决定不做」并指向本篇，下一次发版不再把它们当遗留。
- 若日后启动器要给没有仓库的使用者用，那是产品方向变化（内置课程内容与应用清单），先写新 ADR，不在发布作业里悄悄加。
- 旧版 pocket_cube 若有一天重新活跃（补上求解并有人在用），按 0168 第 1 条加入，不需要改本篇之外的东西。
