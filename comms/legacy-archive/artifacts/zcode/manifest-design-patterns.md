# 设计模式领域清单摘要（T-001）

范围：`DesignPattern/`（整仓 312 文件）、`DesignPatterns/`（整仓 194）、`Practice/DesignPatterns/`（71）、
`Linux/DesignPattern/`（311）+ `Linux/DesignEvolutionCpp/`（5）、`algorithm/design-patterns/`（18），共 **911 个被跟踪文件**。
清单：[manifest-design-patterns.json](manifest-design-patterns.json) · 去重证据：[dedup-report.txt](dedup-report.txt)（286 个多份簇）
· 编译证据：[build-log.txt](build-log.txt) · 零遗漏校验：[verify-design-patterns.txt](verify-design-patterns.txt)（退出码 0，911/911 覆盖）。

## 统计

| 类别 | 数量 |
|---|---|
| 单元总数 | 24（keep 15 / drop 9） |
| keep（进「历史归档」章节） | 15 单元、238 个负责文件 |
| drop-duplicate（三处镜像） | 3 单元、450 文件（linux 311 + practice 71 + workspace 68） |
| drop-third-party | 2 单元、103 文件（课件 58 + sphinx-gallery 45） |
| drop-junk | 4 单元、152 文件（ide 产物 84 + build-ci 32 + doc 练习 22 + xcode 壳 14） |

## 哈希去重结论（任务书特别要求）

- **`Linux/DesignPattern/` 是 `DesignPattern/` 独立仓库的完整镜像**：311 个文件逐文件内容哈希一致（dedup-report
  中所有 `[DesignPattern, Linux]` 两份簇），无一独有。规范版统一取独立仓库 `DesignPattern/`。
- **六个经典模式四处重复**（AbstractFactory/Adapter/Factory/Observer/SimpleFactory/Singleton）：`DesignPattern` ≡
  `DesignPatterns/workspace` ≡ `Practice/DesignPatterns` ≡ `Linux`（4 份簇），内容完全一致。
  最早提交在 `Practice`（2020-03-13），但「最新最完整」取 `DesignPattern` 仓库版（2022-05-02 导入，带 CMake）。
- **演进不是重复（分开成独立单元）**：
  - Strategy 经典 Context 版（`DesignPattern/StrategyV0` ≡ `DesignPatterns/workspace/Strategy`，逐文件一致）→ `dp-arch-strategy-classic`
  - Strategy 排序算法版（`DesignPattern/Strategy`：BubbleSort/QuickSort/SortAlgorithm/StrategyContext，独有）→ `dp-arch-strategy-sort`
  - TemplateMethod 坦克纯虚版（`DesignPattern/TemplateMethod`，独有）→ `dp-arch-template-method-tank`
  - TemplateMethod 默认实现版（`DesignPatterns/workspace/TemplateMethod`，独有）→ `dp-arch-template-method-default`
- **笔记六份重复**：`algorithm/design-patterns`（规范版，独有 3 篇：时序图/观察者/装饰者）≡ DesignPattern/docs 两套改名目录
  ≡ DesignPatterns/docs ≡ Linux 两套。`DesignPattern/docs` 内部还有 `1-design-principles` 与 `1-principle` 等同内容改名重复。

## 编译实测（g++ 15.2.0，-std=c++20，与应用实验引擎一致）

| 结果 | 单元 |
|---|---|
| 链接+运行通过（7） | simple-factory、factory-method、abstract-factory、singleton、observer、strategy-classic、template-method-default |
| 无 main.cpp，`-c` 目标文件通过（3） | facade、strategy-sort、template-method-tank（实际入口是 Qt 壳的按钮） |
| **编译失败（1）** | **adapter**：`Adaptee.h:6` 的 `#include vector` 缺尖括号是语法错误——该目录代码从未编译通过；且 `Adapter::request()` 是空实现，适配逻辑实际没写 |
| toolchain 未实测（2） | qt-shell（需 Qt6+Svg）、gtkmm-evolution（需 gtkmm-4，本机无） |

运行输出首行见 [build-log.txt](build-log.txt)（如 abstractfactory → `ProductA1...`、observer → `ConcreteObserverB observer....old`）。

## 第三方判定依据

- **`DesignPatterns/docs/W设计模式课件`（58 文件）**：zip 内为 `MyPaint1/2`、`FileSplitter` 等
  「C++设计模式代码资源NN_模式名.zip」——李建忠《C++设计模式》网课**官方配套代码资源包**整套拷贝
  （zip 内 GBK 文件名乱码、macOS `._` 资源叉残留、`_desktop.ini`，均非自写痕迹）；pdf 为课程讲义。按 ADR 0176 决策 4 不入库。
- **`DesignPattern/docs/SampleModule|auto_gallery|sample_gallery`（45 文件）**：`module.py`
  （fun_power/class_power、numpydoc 英文注释）与 `sphx_glr_*` 命名是 sphinx-gallery 官方文档示例模块原样拷贝，
  是搭 Sphinx 文档时带进来的样板，与设计模式无关。
- Xcode 三壳（AAA/CCC/DesignPatterns）为 2020-09-19 生成的 Hello World 模板，未改一行，判 junk 不判第三方。

## topic_hint 核对（对照 curriculum.json）

任务书问「SimpleFactory 属于已有的 simple_factory？」——核对结果：现行 id 是 **`dp.simple-factory`**（连字符），
不是 simple_factory。其余映射：Factory→`dp.factory-method`、AbstractFactory→`dp.abstract-factory`、Singleton→`dp.singleton`、
Observer→`dp.observer`、Adapter→`dp.adapter`、Facade→`dp.facade`、两版 Strategy→`dp.strategy`、两版 TemplateMethod→`dp.template-method`、
State(UML)→`dp.state`。均在 JSON 的 `topic_hint` 写明。

## 笔记价值评估（algorithm/design-patterns）

提纲式随堂笔记（李建忠课框架：问题/动机/使用条件/组成），多处只有标题空壳、有错别字（「校色」→「角色」）。
现行应用已完整覆盖 23 模式与七原则，**不宜并入正文**；建议作为归档条目的对照素材保留，其中两块有真实增量：
① `0-时序图.md`（现行 `dp.uml.class` 只讲类图，可补时序图视角）；② 各模式的「使用条件」三段式清单可给现行章节
「何时选用」小节当对照。装饰者笔记是旧笔记里唯一涉及 dp.decorator 的，价值有限。

## 待裁决（已按保守口径填 manifest，请 leader 定夺）

1. **qt-shell 归属**：`DesignPattern/{main.cpp,mainwindow.*,resource.qrc}` 是把 Strategy/Facade/TemplateMethod
   跑起来并显示 UML svg 的 Qt 主程序。我按内容填 `programming/design-patterns`（它是这批模式的 GUI 演示器）；
   但按 ADR 0176 对照表「Qt Widgets → 新建 programming/qt」也成立。二选一。
2. **gtkmm-evolution 归属**：`Linux/DesignEvolutionCpp` 实为 gtkmm 官方示例跟练改造（含自有 Basic 类与 CMake），
   我按 ADR 对照表填 `programming/gtkmm-lab`（ADR 原文 gtkmm 归新建 gtkmm-lab），非本任务书的目标应用。
3. **adapter 建议保留**：代码从未编译通过且适配逻辑为空壳，教学上是「反面教材」；我判 keep（配批注与最小修复），
   若 leader 认为负面价值不值一条目可改 drop-junk。

## 补充核对（leader 15:37/15:47 消息要求）

1. **`Linux/CPlusPlus/FrameWork` 与 T-001 的 Factory/Singleton 不重复**：六个文件（factory/product/singleton）
   与 `DesignPattern/Factory`、`DesignPattern/Singleton` 对应文件内容哈希全部不同。它是**另一代独立实现**：
   singleton.h 是 CRTP 单例模板（Meyers 式 `static T instance` + deleted 拷贝），factory.h 是
   `std::function<void(*)()> + unordered_map` 注册式工厂——比 DesignPattern 的懒汉指针版/教科书工厂现代一代。
   该目录按归属表归 claude-code 的 T-901，T-001 不收；两代的对照可分别在各应用批注里引用。
2. **`algorithm/docs/`（29 个文件）转交 T-002**：内容是 vuepress 站点「算法和编程语言练习」——算法常识、减治法、
   分治法、贪心、回溯、枚举、动态规划、线性表、树、数据结构总纲、查找、排序——**是算法/数据结构文档，不是设计模式**
   （唯 `.vuepress/config.js` 为站点配置）。按 leader 指示从 T-001 转交，纳入 T-002 的算法清单（见
   manifest-algorithms.md）。T-001 零遗漏校验的 911 个文件不含 algorithm/docs，无需改动。
3. 路径归属以 [../claude-code/path-owners.txt](../claude-code/path-owners.txt) 为准，T-001 名下 940 文件 = 本清单
   911 + algorithm/docs 29（已转交 T-002），数字对账一致。

## 产物清单


- `manifest-design-patterns.json` — 24 单元清单（本文件的人读版说明见上）
- `manifest-design-patterns.md` — 本摘要
- `dedup.py` / `dedup-report.txt` — 内容哈希去重（911 文件 → 372 唯一内容、286 多份簇）
- `build-test.py` / `build-log.txt` — -std=c++20 真编译真运行记录
- `verify-design-patterns.py` / `verify-design-patterns.txt` — 零遗漏校验（每文件→负责单元，911/911，退出码 0）
