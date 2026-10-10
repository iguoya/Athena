# ADR 0110：network 更名 computer-networks（计算机网络），图标换 Cisco 标志

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10：「网络和信息安全 改名计算机网络吧 才采用
  合适的图标 和合适的课程英文代号」）
- 关系：修订 [ADR 0103](0103-practice-courses-as-attached-subapps.md) 决策 2 表格
  的「network | 网络 | software | 软设第 10 章」行（原文不改，本条取代其名字与
  领域圈）；名字规则沿 [0100](0100-single-word-app-ids.md)、
  [0104](0104-os-rename.md) 的词组例外先例；进程前缀规则沿
  [0108](0108-dsa-split.md) 决策 4

## 背景

1. 「网络与信息安全」是软考考纲的章名，不是课程名——这门课的通行名是
   **计算机网络**（大学课程《Computer Networks》，Tanenbaum、Kurose & Ross
   教材均用此名）。tiger 决定应用名与领域圈改从课程名。
2. 英文代号：单词 `network` 泛指一切网络，区分不出「计算机网络」这门课；
   单数复数变体（networks、networking）同样泛。按 0104 的 operating-system
   先例（单词候选无一达课程全意，收完整词组），取 `computer-networks`。
3. 进度库：应用自 0103 建立以来 progress/learning.db 从未生成，知识点前缀
   `network.` 没有任何已写记录——按 0108 决策 4 的先例（旧库不存在则新起
   前缀），改用 `net.`。
4. 图标：现行「地球+锁」是通用符号。计算机网络领域唯一有全球共识的标志是
   **Cisco 信号塔**（九柱桥形）——网络设备与 CCNA 课程体系的代名词。

## 决策

1. **更名**：目录 `subjects/network` → `subjects/computer-networks`；id
   `computer-networks`；title「计算机网络」；group（领域圈）「计算机网络」；
   进程/二进制 `athena-computer-networks`；crate `athena_computer_networks_lib`；
   env `ATHENA_COMPUTER_NETWORKS_ROOT`；identifier `cn.athena.computer-networks`；
   知识点前缀 `net.`。端口 1493 不变（0104 先例：改名不动端口）。
2. **承接不变**：仍挂 software、承接软设第 10 章的实践路径 B 实验（socket 真连、
   子网计算、加密真算）——章名（考纲「网络与信息安全」）与应用名（计算机网络）
   各归各，课程树承接表述里写清对应关系。
3. **图标**：换 Cisco 标志（simple-icons `cisco`，上 Cisco 品牌蓝），icon.svg
   头部注明出处与 Cisco 商标归属。
4. 0103 决策 2 表格与决策 6 中 network 的名字由本条取代；0103 表内「网络」
   领域圈改为「计算机网络」。

## 后果

- 目录、id、进程名全链路更名；进度库为零成本新起。
- 启动器零改动：领域圈「计算机网络」单成员圈，同 algorithm「算法」圈先例。
- software 的 content-plan 承接表述、根登记同步。
