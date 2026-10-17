# 下一版再做

本文件记下 10.0.0 窗口里没收口的事。发版说明写进 `CHANGELOG.md` 的时候，这些不要写成已经完成。

## 发布

- [ ] 写 `CHANGELOG.md` 的 `[10.0.0]` 节（v9.0.0 以来的主线，不兼容项标 ⚠️），再 `python scripts/release.py prepare 10.0.0` 与 `push`。工作区还有未提交改动时 `prepare` 会拒绝。
- [ ] 把本地超前 `origin/main` 的提交推上去。`prepare` 要求两边一致。
- [ ] Qt / Electron / 纯 Meson 的成熟应用补安装包作业后，按 ADR 0168 加进同一次 Release：`programming/machine`、`practice/pocket_cube`、`practice/c-gui-lab`、启动器 `launcher/webui`。
- [ ] `edge-ai` 和所有 `lifecycle: archived` 的空壳，等有真实内容再按同一标准加入。不要单独开名单。

## 驾考

代码已在本地历史里的，停在验收，不在本版重做：

- [ ] T-008、T-011 停在 review，等验收后标 done。
- [ ] T-005 仍是 blocked（手册阅读页的决策点四行）。
- [ ] T-012 练车用时、T-013 场地余量写进步骤、T-104 真实图素材。依赖关系见 `comms/driver/BOARD.md`。

## 九州

- [ ] T-034 时间轴延伸到当下，以及看板里仍是 todo / doing 的条目（T-016、T-025、T-032–T-037 等）。
- [ ] 工作区里未提交的 `mentor/jiuzhou` 界面、学术层、`atlas.json` 和图标。看完再提交，不要跟发版脚本捆在一起。

## 协作通讯

- [ ] `comms/comms.py` 与 `comms/tests/` 的未提交改动，以及各舱任务书、消息、已读游标。那是协作记录，不是安装包内容。

## gtkmm

- [ ] 原生演示的 Windows / macOS 检查仍只有 Linux（`ci.yml` 的 `gtkmm-native`）。安装包打的是教程壳。
