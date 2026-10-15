# jiuzhou 舱：九州历史地理图鉴

九州（`mentor/jiuzhou`）的三方协作。通讯规则、命令、状态机见 [../README.md](../README.md)
（通用协议，ADR 0165）；本舱就是该机制 2026-10-13 起的原型实战现场，2026-10-15 从
`mentor/jiuzhou/docs/comms/` 与 `mentor/jiuzhou/scripts/comms.py` 迁入公共机制，旧工具已删。

名册：**claude-code = leader**（指挥 / 规划 / 验收），**cursor = worker**（前端 / 地图，
号段 0），**zcode = worker**（内容，号段 1）。三方职责与 schema 变更流程见
[`../../mentor/jiuzhou/docs/PARALLEL.md`](../../mentor/jiuzhou/docs/PARALLEL.md)。

## 入口命令（每轮开工第一件事）

```sh
python comms/comms.py inbox claude-code --project jiuzhou
python comms/comms.py inbox cursor     --project jiuzhou
python comms/comms.py inbox zcode      --project jiuzhou
```

## 文件归属（撞到别人的未提交改动先停）

| 路径 | 谁改 |
|---|---|
| `mentor/jiuzhou/src/**`、`src-tauri/**`、`packages/maps/**`、九州 `scripts/check.py` | cursor |
| `mentor/jiuzhou/content/**`、`scripts/check_layers.py`、`scripts/add_content.py` | zcode |
| `mentor/jiuzhou/docs/**`（PARALLEL / ROADMAP / INTENT-CHECKLIST / decisions） | claude-code |
| 舱内 `tasks/`（创建） | claude-code（leader） |
| 舱内 `msgs/` | 发信人（只增不改） |
| 舱内 `read/`、`chat/` | 各自 |
| 舱内 `BOARD.md` | 工具生成，不要手改 |
| 舱内 `archive/` | 旧交接单存档，只读 |

## 质量底线

- 不凭印象写史实与出处；不灌水凑字；不确定的写「约」「估计」。
- 九州应用检查：`python mentor/jiuzhou/scripts/check.py --skip-rust`（日常必须绿）。
- git 只提交自己名下的路径，`git add` 写明确路径。
