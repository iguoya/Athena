# gtkmm 前十章审查 · leader 自审（教学设计与初衷）

范围：课表 order 1–10。尺子：`guide/gtkmm/AGENTS.md`（定位、预测–运行原型、模拟与真机配对）、
应用 ADR 0001–0009、根 `AGENTS.md`「跨应用教学规范」（ADR 0096 检索/间隔、ADR 0113 主原型）。
`python scripts/check.py`（gtkmm）自身全绿：课表、清单、PO、66 个官方示例编译、两个 self-check 都过。
也就是说**机械一致性没问题，问题在教学有效性**。

## 总体结论

内容底座（官方全量翻译、段落级上游追踪、66 个官方示例原样可编译）扎实，忠实于「理论文档为主体、
结构严格跟官方」的初衷。偏离的是另一半初衷：**「实践是理论的具象化」「预测–运行」「完成度只由
作答反映真实掌握」在前十章几乎只在第 6 章落地**，其余章节是「官方译文 + 一组选择题」，
而选择题本身有系统性缺陷，使「通过」不能说明学会了。

## 发现

| # | 级别 | 发现 | 证据 |
|---|---|---|---|
| 1 | P0 | **测验答案位置严重偏置**：全 31 章 112 道题，正确答案在 B 的有 76 道（68%），D 仅 4、C 仅 1；前十章里第 8、9 章 16 题**全是 B**，第 3 章 18 题 15 道是 B。学习者不读也能靠「选 B」过关 | 统计自 `content/curriculum.json` 各章 `knowledge_points[].blocks[]` 与 `checkpoint[]` 的 `answer` |
| 2 | P0 | **正确选项最长**：112 题里 90 题（80%）正确项是字数最长的选项，「选最长的」是第二条免学通道 | 同上，比较 `options[answer]` 与其它项长度 |
| 3 | P1 | **完成度判定过松，与 ADR 0096 的检索练习方向相悖**：「每题答对过一次即计通过」，且答错后立即「再试一次」，4 选 1 逐个排除必过；没有间隔、没有跨知识点混合 | `src/App.tsx:177` 注释与 `correctItems`；`src/blocks.tsx` 的 `retry` |
| 4 | P1 | **答错无任何反馈**：所有题没有 `explanation` 字段，界面只标红标绿。教学闭环里「修正理解」一环缺失；官方原文里现成有依据，可直接引段落作解析 | `QuizItem` 字段仅 `answer/demo_ref/id/options/page_ref/source_refs/stem/type`；`blocks.tsx` 无解析渲染 |
| 5 | P1 | **预测–运行（主原型，ADR 0113）只在第 6 章有**：全应用 1 个演示 + 1 个实验（都是 buttons），`observation_quiz` 只出现在 `gtkmm.buttons.toggle` 一处。第 3 章基础（信号、`make_window_and_run`、`Glib::ustring`、`gobj/wrap`）是后续全书的地基，却没有任何演示或预测题 | `content/demos.json`；各章 `knowledge_points` 的 block 类型统计 |
| 6 | P1 | **「知识点」被一个 quizset 取代**：第 1、2、3、7、8、9、10 章各只有一个 `…quizset`（type 全是 concept，`requires` 全空），不是按概念拆分的知识点。先修关系（ADR 0030）、概念/技能/策略分类（ADR 0031）、难度与掌握目标分级（ADR 0029）因此在这些章基本形同虚设 | 同上；`requires` 只在第 6 章出现 |
| 7 | P1 | **题型几乎全是事实回忆**：「X 的作用是？」「哪个库实现信号？」「pkg-config 外的反引号作用？」。缺代码阅读、预测输出、找 bug、辨析（`append` vs `set_child` 何时用）等能检验理解的题；第 9 章布局（expand/align/homogeneous）本是最适合「预测界面结果」的内容，却用词汇题 | 抽样第 3、9 章全部题面 |
| 8 | P2 | **翻译状态标注与实际不符**：第 8、9、10 章与 changes-gtkmm3 标 `pending`，但正文段落几乎全部已译，仅标题/图注缺；第 6、7 章同样缺标题/图注却标 `translated`。两条标准不一致 | 逐块统计：misc 缺 heading 15/figure 9，container heading 24/figure 10，button heading 5/figure 3 |
| 9 | P2 | **changes-gtkmm4 真有未译段**：`sec-deprecations-4-10.json` 里 5 个 para + 2 个 listitem 无 `zh`（含「行为变化，必须适配」这类重要内容）；`pending` 标注属实 | 同上 |
| 10 | P2 | **第 4、5 章无知识点也无章末考核**，按现有判定它们永远不会「点亮」，章进度列表里会长期缺口 | `chapterPassed` 要求 `checkpoint.length > 0` |
| 11 | P2 | **文档漂移**：`docs/decisions/README.md` 仍写「`subjects/gtkmm` 独立应用」；`src-tauri/src/lib.rs:666` 有 `unused variable: target` 编译警告 | check 输出 |
| 12 | P2 | **答案存两处**：作答同时写 `localStorage('answer:…')` 与 SQLite `attempts`；重置只在界面层清 localStorage，换机/清缓存后「已答」状态与库可能不一致 | `blocks.tsx` QuizView；`App.tsx` `resetSectionAttempts` |

## 布局与开发顺序建议（不改官方结构）

结构规则不允许重排章序（应用 ADR 0003），以下全部是**呈现层与投入顺序**建议：

1. **先补质量，再补数量**：在继续翻译第 11 章以后之前，先把前十章的测验重做一遍（见下条），
   否则后面 20 章会复制同样的缺陷。
2. **测验重做的最低标准**：①答案位置随机均匀（可在题库里均匀分配，也可渲染时按题 id 稳定洗牌）；
   ②选项等长或长度不可预测；③每题带 `explanation`，并给 `source_refs` 具体到段落；④每章至少
   三分之一的题改成「读代码预测结果 / 找错」；⑤答错不立即允许同题重试，改成隔一段内容或下次复习再出。
3. **把演示投入给第 3 章**：Basics 的信号时序与 `make_window_and_run` 生命周期最值得做一个
   「点了之后先发生什么」的预测–运行演示，其次是第 9 章的 Box/Grid 布局模拟（已有 13 个官方示例可复用为
   真机锚点，模拟遵守 ADR 0001 的配对规则）。
4. **第 4、5 章（迁移）在目录里加「迁移者读」标记**，不改位置；初学者可跳过，并让进度统计把
   「无考核章」排除在分母之外。
5. **知识点拆分**：把各章 quizset 拆成按概念命名的知识点并写 `requires`，题挂在知识点上，
   这是复习调度（ADR 0096）的前提。
6. **状态口径统一**：定一条「translated = 所有 para/listitem/note 有 zh；标题与图注另计」并让
   `check.py` 校验，再批量改 misc/container/listmodel 的状态。

## 没发现问题的部分（避免误伤）

- 上游追踪、段落指纹、`exercise/` 逐字镜像、官方示例卡先演示后读文的布局，设计合理且与 ADR 0006–0009 一致。
- 代码块原样不译、术语出处记录、GFDL 声明，符合规则。
