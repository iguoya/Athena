# Athena · 计算机组成原理（独立应用）

承载 408 计算机组成原理的学习应用（主仓库 ADR 0115）：数据表示与运算、存储层次、
指令系统、中央处理器、总线与输入输出。机制类内容先预测再单步模拟，数据表示类内容用
本机 C++ 实验真跑验证。从启动器打开，不依赖别的应用。

```
content/          课表与 C++ 案例（唯一内容源）
src/              前端：导航 + 导读 / 讲解 / 实验
src-tauri/        壳：读内容、进度库、compile_and_run
app.json          启动声明
docs/decisions/   本应用 ADR
```

```sh
launcher open organization
python3 scripts/check.py organization
```

协作规则见 [AGENTS.md](AGENTS.md)。
