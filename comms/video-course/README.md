# video-course 舱

「视频教程类学习应用」的设计讨论舱。起因：使用者希望从慕课网之类的视频教程出发建教学
应用，与已有的「电子书 / 手册精读」类应用并列，不受既有应用形态影响。本舱只做**设计讨论**
（定位、界面、内容规划、取舍），尚未立项；定了再按 new-app 流程先写 ADR。

## 角色与文件归属

| 成员 | 角色 | 名下路径 |
|---|---|---|
| claude-code | leader，出设计稿、裁决、后续写 ADR | `artifacts/claude-code/` |
| zcode | 讨论方 / 后续素材切片 worker | `artifacts/zcode/` |

- 暂不碰任何应用目录与 `docs/decisions/`；设计稿与评审意见放各自 artifacts 下。
- 任务号段：claude-code 占 T-9xx，zcode T-0xx。
