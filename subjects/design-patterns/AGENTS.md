# 设计模式 应用协作规则

仓库级规则见根 `AGENTS.md`，本文只写本应用自己的约定。本应用目录 id `design-patterns`，
知识点前缀 `dp.`。本应用是**学习应用**（三类判据见 `docs/REPOSITORY.md`）：教会人设计模式
与程序代码组织，并用可观察的证据（随堂考核作答、实验输出判分）证明掌握度在进步。
跨应用教学规范（`docs/TEACHING.md`）全部生效。

## 应用定位

- **主轴是「遇到什么代码问题，用什么组织方式与规范解决」**（本应用 ADR 0001），不局限于
  23 个模式。启动器里在「程序设计」圈，与 gtkmm、linux 同圈，**不挂靠**任何应用（仓库
  ADR 0121；`app.json` 不得有 `parent`，`check.py` 校验）。
- 章节骨架：UML 读图 → 设计原则 → **情境篇一**（从坏味道出发）→ **情境篇二**（C++ 的资源、
  所有权与错误）→ **情境篇三**（C 的代码组织）→ **情境篇四**（并发下的代码组织）→ **模式工具箱**
  （创建型、结构型、行为型）→ **模式辨析**（易混模式并排比较与常见搭配，ADR 0001 补充四）→ **软考专题**（`layer: "topic"`）→ **延伸篇**（`layer: "extension"`：
  现代工程的程序组织写法，含「模式的现状」批判课；正式内容写成后去掉延伸标记、并入主线）。
- 情境篇三的实验按 C 的写法写，但用同一个 C++ 编译器编译（malloc 结果显式转换、goto 不跨越
  带初始化的声明），讲解里写明这一点；情境篇四的实验用 std::thread，必须输出确定，不能依赖时序巧合。
- **情境篇每节的体例**：一种代码问题 = 一个知识点。情境选择 → 讲解（症状名与手法名）→
  改造前后代码对照（`codecompare`）→ 怎么改 → 代价与边界 → 「工具箱里的对应模式」→ 小测 →
  取材；配一个重构实验：骨架是有问题的代码，学习者改造它并完成一个只有改造后才容易实现的
  新需求。新写的模式讲解要能被情境篇引用；新增情境优先于新增模式。
- **软考是专题，不是主线**：真题集中在软考专题一章；模式讲解里保留的「软考考点」提示
  用 `callout` 的 `tone: "exam"`，界面默认收起。新写的模式讲解不再加软考提示。
  软件设计师第 7 章可以用文字指引学习者来这里（ADR 0098 模式），本应用不反向依赖 software。
- **学习方法原型（ADR 0113）**：主原型**辨析决策**，辅**预测–运行**。易混模式并排呈现
  （策略/状态、装饰/代理、适配器/外观），练习是混合情境判别并要求写出依据，不按模式一块块
  学完再测；代码类练习先读码预测行为再动手。

## 取材：有所本，不自由发挥

- **情境篇**的依据：Martin Fowler《重构：改善既有代码的设计》第 2 版（2018）第 3 章「代码的
  坏味道」与重构手法目录（手法英文名以 refactoring.com/catalog 为准）；C++ Core Guidelines
  （isocpp.github.io/CppCoreGuidelines）的编号条目；依赖注入取自 Fowler 2004 年的文章。
  条目编号与手法名写进讲解前要对照原文核对。
- **模式工具箱**的讲解依据按优先级：GoF《Design Patterns: Elements of Reusable Object-Oriented Software》
  （1994，23 个模式的原始出处）→《软件设计师教程（第 5 版）》§7.3（按 GoF 体例转述了
  23 个模式的意图、结构、参与者、适用性）→ Refactoring.Guru。三者登记在
  `content/sources.json`。
- 每个模式的**意图、参与者、适用性**以上述材料为准，不凭印象改写含义；可以用自己的话
  讲，但不能讲出原著没有的结论。超出原著的内容（现代视角、语言对照）要标清楚是哪一方的
  判断与依据。
- 每个模式讲解末尾放一条「取材」`callout`，写明本节依据（如「GoF Adapter · 软设教程
  §7.3.3 · Refactoring.Guru Adapter」）。**页码、题号记不清就不写**，绝不编造。
- 软设教程 OCR 全文在 software 应用的 `content/textbooks/swd5ed/chapters/swd-ch07.txt`，
  写作时可以读它核对，但本应用不在构建或运行时引用 software 的任何路径（ADR 0032、0062）。

## 技术栈与选型理由

- 壳 **Tauri 2**（Rust + 系统 WebView）。前端是**原生 TypeScript + Vite，无框架**：界面
  由内容块驱动（ADR 0058），一个渲染函数对应一种块，框架带来的状态管理在这里用不上。
  代码编辑器用 CodeMirror 6（C++ 高亮）。
- **实验引擎**：编辑器里的源码写到临时目录，用本机编译器编译运行（ADR 0057：不内嵌
  编译器）。GCC/Clang 用 `-std=c++20 -O0 -Wall -Wextra -pthread`，找不到时退到 MSVC
  `/std:c++20 /W4`。`content/cases/_shared/` 挂在 include 路径上。
- **判分**：实验的 `pass.includes` 列出运行输出必须包含的子串，全部出现即「已完成」。
  早期设想的「结构断言」（如「Client 不得直接依赖 ConcreteProduct」用编译期检查表达）
  **尚未实现**，目前只有输出比对。
- **安全边界**（沿 ADR 0091 决策 3）：应用只编译运行实验源码，不提供任意 shell。
- dev 端口 **1491**（strictPort）；进程/二进制 `athena-design-patterns`；窗口标题
  「设计模式」；应用内文案用中文。

## 内容组织

```
content/
├── curriculum.json        课程全部内容：章 → 知识点（outline、lesson.blocks、labs）→ 章节随堂考核
├── cases/<case>/main.cpp  实验骨架；cases/_shared/ 是共享头
└── sources.json           来源登记（出处检查的 catalog）
```

- **块类型**（ADR 0058，`src/main.ts` 的 `Block`）：`lead` `prose` `callout`（`tone`：
  `warn` / `exam`）`compare` `steps` `predict` `scenario` `practice` `quiz` `uml` `table`
  `summary` `fillcode`。正文只认 `**加粗**` 一种行内标记。需要新块先确认现有块表达不了。
- **`fillcode` 块**（`src/fill-code.ts`）是软考下午题的作答形态：`code` 是展示用的原题代码，
  `{{n}}` 处渲染为输入框；`template` 是补全了「代码省略」处、带输出的完整程序，空位同样标
  `{{n}}`；`expect` 是运行输出必须包含的子串。判分先与 `blanks[].answers` 规范化比对（去空白
  与末尾分号、全角转半角），比对不上可「代入编译运行」由编译器判断等价写法。做完的题按占比
  写入该知识点的完成度（只用于没被章节考核覆盖的知识点）。
- **`uml` 块**是标准 UML 类图：类框三格 + 六种关系线（泛化、实现、组合、聚合、关联、
  依赖），坐标由内容作者给定。每个模式至少一张类图。
- **实验**（`labs`，ADR 0059 骨架可运行）：骨架原样能编译运行（`-Wall -Wextra` 无警告），
  但输出**不**满足 `pass.includes`；学习者补完 `TODO(实验)` 标出的空缺才达标。`prompt`
  是题干（先预测），`goal` 是动手要求，`hint` 可选。写骨架时要在本地备一份参考解，
  确认补完后能达标（参考解不进仓库）。
- **随堂考核**（章的 `checkpoint`）：每题 `covers` 指向本章一个知识点；同一知识点的题
  不相邻；每个知识点至少 2 题，完成度按正确率写入。考核题的 `source` 用结构化写法
  （见下节）。
- 知识点 id 前缀 `dp.`，与目录 id 解耦（ADR 0097 决策 3 同规）；已进进度库的 id 不改，
  知识点换章不换 id。

## 出处（档位 open，软考专题例外）

- 出处档位 **open**（ADR 0089、0121）：出处是默认写作习惯，不做仓库级门禁；
  `content-contract.json` 以带 `choices` 的题为判分条目，未标注只报告。
- 题目 `source` 的结构化写法：`{"relation": "verbatim|adapted|authored", "sourceId": …,
  "locator": …, "url": …, "why": …}`。自造题标 `authored` 并写 `why`。
- **软考专题例外，从严**：专题章里的每一道题都必须是真题原题，`relation: "verbatim"`，
  `sourceId` 在 catalog 里，`locator` 写「年份 + 上/下半年 + 上午/下午 + 第 N 题（第 k 空）」，
  `url` 指向可核对的页面。**年份与题号必须来自真实试卷页面，严禁凭记忆编造**；含图的题
  在没有图的情况下不收。`scripts/check.py` 逐题检查。
- **下午题（`fillcode`）可以是 `adapted`**：网页转录常丢失 `#`、`*`、注释符或有笔误，按官方
  答案还原后标 `adapted`，并在 `why` 里逐项写明改了什么；代码与网页一致的标 `verbatim`。
  用 C++ 版（每年试题五、试题六分别是 C++ 与 Java 版的同一道题）；代码是图片的年份不收。

## 掌握度与进度库

- **掌握度只由作答写入**（ADR 0052）：章节随堂考核交卷后，按 `covers` 统计每个知识点的
  正确率，换算成 0–5 写入 `knowledge_progress`。讲解里的小测只记作答、不写掌握度。
- 实验状态（未开始/已开始/未完成/已完成）写 `lab_progress`，「已完成」只由运行输出满足
  `pass.includes` 触发；不设「实验币」等旁路激励，激励只展示由记录派生的量。
- `progress/learning.db` 随仓库走（ADR 0037、0053），Rust 侧自建自迁移：仓库工作树内
  （以 `app.json` 存在为准）写 `progress/learning.db`，发行包写系统数据目录。表：
  `knowledge_progress`、`lab_progress`、`lab_draft`、`quiz_picks`。schema 变更直接改
  建表语句并保证旧库可迁移，不引迁移框架。

## 验证与构建

```sh
python3 scripts/check.py              # 结构与内容校验 + 前端构建 + Rust 检查
python3 scripts/check.py --skip-rust  # 只改内容或前端时用
python3 scripts/check.py --quick      # 只做结构与内容校验
```

- 内容校验：知识点 id 前缀与唯一性、`requires` 与 `covers` 指向存在的知识点、实验案例
  文件存在且带 `pass.includes`、软考专题题目的原题出处、代码填空的空位与出处。
- 编译验证（非 `--quick` 时）：每个实验骨架原样零警告编译运行且**不**达标；每道代码填空
  代入官方答案通过、空着不填**不**通过。
- 跨应用出处检查由根 `scripts/check-app-sources.mjs` 按 `content-contract.json` 接入。

## 约定

- 影响本应用架构边界的新决定，在 `docs/decisions/` 增补 ADR 后再动代码。
- 与其他应用构建完全隔离（ADR 0032、0062）：不引用任何应用的路径、配置或代码。

## 素材坑历史

本目录原是素材坑（只有 docs/ 素材、无工程），仓库 ADR 0103 决策 4 转正为学习应用，
ADR 0121 去挂靠。转正前的结论文档保留在 `docs/`：

- `docs/inherited-from-cpp.md`：23 个模式的中文命名与一句话定位（自 cpp 剥离）。
- `docs/cpp-foundations-reference.md`：模式实验的 C++ 前置能力与边界。
