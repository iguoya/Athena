---
id: T-001
title: comms.py v2 加固：原子写与 status 乐观锁
owner: cursor
status: todo
priority: P1
depends: 
created: 2026-10-15 18:45
updated: 2026-10-15 18:45
---
## 目标

通讯工具 v2 加固（ADR 0166 决策 4），两件事：

1. **原子写**：`comms/comms.py` 里所有写文件的点（send 写 msgs、status/task new 写任务
   与 BOARD、ack 追加 read、chat 追加 log、chat 已读指针）改成「写临时文件 +
   `os.replace` 原子替换」，读方（其他进程的 inbox/notify/watch）永远看不到半截文件。
   追加型写（ack、chat log）保持追加语义，但先拼好整行再一次 write，配合行级完整。
2. **status 乐观锁**：`cmd_status` 在读-改-写之间任务文件可能被别人改过（leader 验收与
   worker 交 review 同时发生）。写前重新 parse 一遍，若当前 status 与第一步读到的
   `old` 不一致，报「<任务> 刚被 <发现的变化> 更新，请重跑一次 status」并不写入。

## 做法

- 只改 `comms/comms.py`；不新增依赖；命令行行为（参数、输出格式、文件格式）不变。
- 写个小的自测脚本 `comms/tests/test_v2.py`（python 直接跑，不引测试框架）：用临时目录
  造一个假舱（config/tasks/msgs），覆盖：原子写后内容完整、并发 status 冲突能被乐观锁
  拦下、既有命令冒烟（inbox/send/ack/status/board/check）。
- 跑 `python comms/comms.py check --project driver` 与 `--project comms-console` 确认真实
  舱不受影响。

## 验收

1. `python comms/tests/test_v2.py` 全绿（输出摘要写进 review note）。
2. 两个真实舱 check 通过。
3. git 提交信息写明两处加固；`git add` 写明确路径（comms/comms.py、comms/tests/）。

## 边界

- 不改文件格式、不改 CLI 参数、不动九州目录。
- 这是本舱第一个任务，用来走通协作流程：开工标 doing，做完标 review 附验证输出摘要。

## 进展记录
