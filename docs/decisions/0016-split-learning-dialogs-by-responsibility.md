# ADR 0016：按单一职责拆分 LearningDialogs

- 日期：2026-08-28
- 状态：已接受，实施完成
- 依据提交：（本 ADR 与对应实现同批提交）

## 背景

ADR 0014 把 `MainWindow` 按功能边界拆开时，把“设置、运行历史、AI 回答和自测题”
合并成一个叶子对话框模块 `LearningDialogs`。随后又给它加了“AI 讲解”（整体+局部
双视角、结果缓存）和“AI 讲解差异”。到目前为止 `ui/learning_dialogs.cc` 已经约
1000 行，一个类里同时装着：

- 两个 AI 服务商 Key 的存储键、读取顺序和保存逻辑；
- 设置面板的控件装配；
- 运行历史对话框（列表、双栏源码/输出对比、git 版本标记、默认选中规则）；
- AI 回答的 Markdown → HTML → WKWebView 展示通道（讲解和讲解差异共用）；
- AI 讲解的缓存命中判断、提示词和缓存回写；
- AI 自测的提示词、JSON 解码、逐题 GTK 渲染和本地判分。

这些部分各自有独立的变化原因（换 Key 存储、改历史对比布局、调渲染字号、改出题
提示词……），却必须一起编译、一起阅读、一起测试。这正是 `AGENTS.md`“架构原则”
里单一职责（SRP）一条要避免的形态：单文件持续膨胀应视为拆分信号。

## 决策

把 `LearningDialogs` 从“一个大对话框类”改成“一个门面 + 一组单一职责子模块”，
依赖方向不变（都在表示层内、向下依赖基础能力，不反向调用 `MainWindow`）：

```text
LearningDialogs（门面：装配共享依赖，转发四个入口）
├── SettingsDialog      —— AI 服务商 Key 设置面板
├── HistoryDialog       —— 运行历史对比 +“AI 讲解差异”动作
├── QuizDialog          —— AI 自测：出题提示词、JSON 解码、逐题渲染、本地判分、熟练度回写
├── AiInsightDialog     —— AI 讲解：缓存命中判断、提示词、缓存回写
├── ApiKeyStore         —— Key 读写：应用内设置优先、回退同名环境变量
└── AiMarkdownDialog    —— AI 回答的 Markdown/WebView 展示通道（讲解、讲解差异共用）
```

边界规则：

- `LearningDialogs` 只做组合和转发，保持 `show_settings()` / `show_history()` /
  `show_quiz()` / `show_ai_insight()` 四个入口和构造函数签名不变，`CodeChapterPage`
  与 `MainWindow` 一侧不改。
- `ApiKeyStore` 是 Key 读写的唯一入口；其余模块不直接碰 `LearningStore` 的设置表，
  也不各自读环境变量。
- `AiMarkdownDialog` 只负责“把一段 Markdown（现成的或异步取回的）显示出来”，
  不含任何提示词或业务判断；`HistoryDialog` 和 `AiInsightDialog` 复用它。
- `DialogTopic` 移到独立头文件 `ui/dialog_topic.h`，供各子模块和 `CodeChapterPage`
  共享，不再从门面头文件传递。
- 子模块之间不互相持有；共享的 `ApiKeyStore` 和 `AiMarkdownDialog` 由门面在构造
  时装配，按引用注入需要它们的子模块。

## 后果

- 每个对话框现在能单独阅读和修改，变化原因单一；`ui/learning_dialogs.cc` 从约
  1000 行缩成一个几十行的构造与转发文件。
- 头文件和构造样板带来约 300 行净增；换来更窄的职责范围和更清晰的复用关系，
  符合“不以行数为唯一目标”的既有取舍。
- 行为、控件样式、提示词文案和缓存规则保持不变，本次只搬运不改逻辑。
- 未来给某一类对话框加功能（例如运行历史加筛选、AI 讲解加多轮追问）只动对应
  子模块，不再牵动其他三类。
- ADR 0014 的模块树相应更新：`LearningDialogs` 一项展开为上表的门面 + 子模块。
