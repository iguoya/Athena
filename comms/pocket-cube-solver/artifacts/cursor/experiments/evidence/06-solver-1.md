# 证据 06-solver-1 · 关掉 twist 模 3

## 环境
- 临时副本：`%TEMP%\pcs-t002-experiments\06-solver`（从 `programming/pocket-cube-solver/exercise/06-solver` 复制，不改仓库）
- PATH 前置 `C:\msys64\mingw64\bin`；`PKG_CONFIG_PATH=C:\msys64\mingw64\lib\pkgconfig`
- 命令：`meson setup build`（首次）→ `meson compile -C build` → `build\cube-test.exe`

## 改动
- 文件：`cube.cc`
- Diff 摘要：if (twist_sum % 3 != 0) → if (false && ...)

## 观察（原样）
- exit=1; FAIL line 162; 1 项失败
- 完整编译/运行日志：`evidence/_raw_logs/06-1.log`

## 对应草稿
- `experiments/06-solver.json` 第 1 条
