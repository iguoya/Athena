# ADR 0112：computer-networks 复名 network

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10：「computer-networks 改名 network」）
- 关系：修订 [ADR 0110](0110-computer-networks-rename.md) 决策 1 的 id 与进程命名
  （由本条改回；原文不改）；复名先例 [0105](0105-dsa-rename-back.md)；title
  「计算机网络」、group「计算机网络」、Cisco 图标、端口与承接均不变

## 背景

tiger 使用 `computer-networks` 后决定回到单词 `network`。该应用无发行历史、
进度库从未生成（前缀 `net.` 零数据），复名零成本；名字来回调整由 ADR 只增
不改的原则记录（0105 algorithm→dsa 复名先例）。

## 决策

1. **复名**：目录 `subjects/computer-networks` → `subjects/network`；id
   `network`；进程/二进制 `athena-network`；crate `athena_network_lib`；env
   `ATHENA_NETWORK_ROOT`；identifier `cn.athena.network`；check.py 的
   EXPECTED_ID 同步。端口 1493、知识点前缀 `net.` 不变。
2. **其余不动**：title「计算机网络」、group（领域圈）「计算机网络」、Cisco
   图标、`parent: software` 承接软设第 10 章——0110 决策 2、3 原样有效，
   仅其决策 1 的英文代号由本条改回。

## 后果

- 应用名链路（目录/id/进程/identifier/env）与启动器显示名（计算机网络）解耦：
  显示是中文课程名，代号是单词。
- 0100「单词优先」口径下 `network` 重新成立；0110 的词组论证不再适用，由本条
  记录使用者偏好（0110 原文不改）。
