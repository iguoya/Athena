# 实时操作系统（RTOS）（软考中级·嵌入式系统设计师 实践课程）

软考中级·嵌入式系统设计师「第 4 章」的实践课程应用，按仓库 ADR 0106 挂靠 `embedded`
（嵌入式系统设计师），可单独使用。实验引擎：FreeRTOS 真板观测 + QEMU 交叉编译 +
线程级调度模拟。

## 状态

**骨架阶段**：工程壳与规范先行，内容待填充（ADR 0106）。
内容填充顺序见 embedded 的 `docs/` 与 software 的 `docs/content-plan.md`。

## 运行

```sh
launcher open rtos        # 推荐：启动器拉起（ADR 0044/0046）
python3 scripts/check.py # 验证（--full 加构建检查）
```

## 规则

协作规则见 [AGENTS.md](AGENTS.md)；目录职责与内容契约同见该文。
