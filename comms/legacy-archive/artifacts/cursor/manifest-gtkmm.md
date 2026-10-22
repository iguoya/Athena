# gtkmm 领域清单摘要（T-102）

- 生成：2026-10-21T15:48:45
- 目标：**新建** `programming/gtkmm-lab`（与 `guide/gtkmm` 官方手册精读互不引用）
- 范围：`Linux/GTKMM/`；`Examples_Gtkmm/`、`gtkmm-application-template/` 为空
- 对照：`guide/gtkmm` = gtkmm4 教程翻译；本清单旧练习 ≈ gtkmm3
- 本机未装 gtkmm，未编译

## 统计

| 项 | 数量 |
|---|---:|
| 单元 | 15 |
| keep | 7 |
| drop-third-party | 0 |
| drop-junk | 8 |
| 生成物文件（drop-junk 桶内） | 100 |
| scoped 文件 | 192 |
| 覆盖遗漏 | 0 |

### keep 版本分布（静态判断）

| version | n |
|---|---:|
| `gtkmm3` | 7 |

### topic_hint

| hint | n |
|---|---:|
| `archive.gtkmm.layout` | 5 |
| `archive.gtkmm.basics` | 1 |
| `archive.gtkmm.glade` | 1 |

## keep 一览

- `gtkmm-1-hello` — 1-Hello ← `Linux/GTKMM/1-Hello` ver=gtkmm3 run=toolchain files=5 first=2023-01-28（dup 1）
  - 静态判断工具链版本≈gtkmm3
- `gtkmm-2-glade` — 2-glade ← `Linux/GTKMM/2-glade` ver=gtkmm3 run=toolchain files=16 first=2023-01-28
  - 静态判断工具链版本≈gtkmm3；含 Anjuta 工程痕迹
- `gtkmm-3-frame` — 3-frame ← `Linux/GTKMM/3-frame` ver=gtkmm3 run=toolchain files=15 first=2023-01-28
  - 静态判断工具链版本≈gtkmm3；含 Anjuta 工程痕迹
- `gtkmm-4-paned` — 4-paned ← `Linux/GTKMM/4-paned` ver=gtkmm3 run=toolchain files=15 first=2023-01-28
  - 静态判断工具链版本≈gtkmm3；含 Anjuta 工程痕迹
- `gtkmm-5-asspectframe` — 5-asspectframe ← `Linux/GTKMM/5-asspectframe` ver=gtkmm3 run=toolchain files=15 first=2023-01-28
  - 静态判断工具链版本≈gtkmm3；含 Anjuta 工程痕迹
- `gtkmm-6-box` — 6-box ← `Linux/GTKMM/6-box` ver=gtkmm3 run=toolchain files=15 first=2023-01-28
  - 静态判断工具链版本≈gtkmm3；含 Anjuta 工程痕迹
- `gtkmm-7-box` — 7-box ← `Linux/GTKMM/7-box` ver=gtkmm3 run=toolchain files=5 first=2023-01-28
  - 静态判断工具链版本≈gtkmm3

## 待裁决

1. `Examples_Gtkmm/` 与 `gtkmm-application-template/` 在仓库中为空目录（0 tracked / 0 on-disk files），仅作记录。
2. 旧练习为 gtkmm3 形态；`guide/gtkmm` 是官方 gtkmm4 教程翻译——互不引用。归档进新建 `programming/gtkmm-lab` 是否只收「有手写逻辑」的单元？
3. Windows 无 gtkmm 开发库：一律未实测编译（`build_checked: false`），符合任务书。
