# 数据库（软考中级·软件设计师 实践课程）

软考中级·软件设计师「第 9 章」的实践课程应用，按仓库 ADR 0103 挂靠 `software`
（软件设计师），可单独使用。实验引擎：rusqlite 嵌进程 SQL 真跑。

## 状态

**骨架阶段**：工程壳与规范先行，内容待填充（ADR 0103）。
内容填充顺序见 software/embedded 的 `docs/content-plan.md`。

## 运行

```sh
launcher open database        # 推荐：启动器拉起（ADR 0044/0046）
python3 scripts/check.py # 验证（--full 加构建检查）
```

## 规则

协作规则见 [AGENTS.md](AGENTS.md)；目录职责与内容契约同见该文。
