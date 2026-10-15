# driver 舱：驾考应用协作（certification/driver）

通讯规则、命令、状态机见 [../README.md](../README.md)（通用协议，ADR 0165）。
本舱当前主题：**科目二（C2）教程补强**——审视意见与任务背景见 tasks/ 任务书。

## 角色

- **zcode = leader**：写任务书、验收、裁决；方向性意见以它为主，cursor 建议有道理它就采纳。
- **cursor = worker**：按任务书执行，交 review 附验证证据；建议走消息。

## 入口命令（每轮开工第一件事）

```sh
python comms/comms.py inbox cursor --project driver    # cursor
python comms/comms.py inbox zcode  --project driver    # zcode
```

## 文件归属（撞到别人的未提交改动先停）

| 路径 | 谁改 |
|---|---|
| `certification/driver/content/subject2.json` 的 `general.c2` 区块、直角转弯 caution 行 | cursor |
| `certification/driver/content/subject2.json` 的 `exam_day` 区块 | zcode |
| `certification/driver/lib/subject2/guide.dart` 及对应测试 | cursor |
| `certification/driver/lib/subject2/subject2.dart` 的项目手册分区（_handbookTab） | cursor |
| `certification/driver/lib/subject2/subject2.dart` 的考前分区（_examTab） | zcode |
| `certification/driver/` 其余文件 | 动之前先发消息说明 |

同一文件（subject2.json）的改动用任务依赖串行化：T-001 → T-002 → T-901，不并行写。

## 应用规范（做内容与改代码前必读）

- `certification/driver/AGENTS.md`（尤其「科目二（C2 四项）」一节）
- 该应用 ADR 0036（内容与动画）、0037（简报/点位/默演）、0039（练车日组织）、0040（讲解与标注）
- 改完跑：`python3 scripts/check.py driver`（或应用内 `python3 scripts/check.py --skip-build`，只改内容时）

## 事实基线（leader 审视结论，任务书引用）

- 评判标准全国统一：GA 1026—2022；河南地方题只在理论考，科目二无地方项目。
- 「制动、加速踏板使用错误」是通用不合格项（6.2.2.1 k)），对 C2 是高频冤死点。
- 当场补考一次（162 号令第 37 条）已有题（drive.s2.general.017），但考前分区没有流程性呈现。
