# ADR 0120：新增「人工智能」领域圈与 LLM 应用开发课程路线；首门课 python 立项

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10：「我感觉还是需要增加一个人工智能的分组 从软件或者
  计算机专业的眼中 需要分成哪些课程循序渐进 掌握大模型或者人工智能的开发 特别是实践
  应用角度」）
- 关系：领域圈机制按 [ADR 0083](0083-launcher-mind-map.md)（`group` 自由文本即圈）；
  学习方法原型按 [ADR 0113](0113-method-archetypes-per-course.md)；出处档位按
  [ADR 0089](0089-source-tiers-by-app-nature.md)；循序渐进的先修关系用各应用
  `AGENTS.md` 的文字指引表达（课程归属声明，不是运行时依赖，ADR 0032）

## 背景

1. 受众画像明确：软件/计算机专业背景（会编程、懂工程），不缺语言与工程基本功，缺的是
   AI 领域的知识体系与动手经验。目标不是科研，是**掌握大模型/人工智能的开发，特别是
   实践应用**——能做 RAG、Agent、微调与部署，而不是推导公式。
2. 现有应用没有 AI 承载：machine 是「C 与机器」，organization 是组成原理，都与 AI
   无关。人工智能的学习需要自己的领域圈。

## 决策

### A. 课程路线（循序渐进，两条线）

| 序 | 应用 | 承载 | 先修 |
|---|---|---|---|
| 1 | `python` | Python 与 AI 工具链：面向会编程的人的语法速成、uv 环境管理、numpy/pandas 数据操作、HTTP 与异步、Jupyter 与工程工作流 | — |
| 2 | `machine-learning` | 机器学习基础：回归/分类/聚类、交叉验证、特征工程、sklearn 实战、评估指标——建立「从数据学规律」的直觉 | python |
| 3 | `deep-learning` | 深度学习与 PyTorch：张量与自动微分、训练循环、CNN/RNN、**Transformer**、预训练-微调范式 | machine-learning |
| 4 | `llm-app` | 大模型应用开发：提示工程与上下文工程、结构化输出、RAG（嵌入/向量库/检索）、Agent 与工具调用、评估（evals）与成本——**实践应用的主场** | 应用线：python；原理线：deep-learning |
| 5 | `llm-finetune` | 微调与本地部署：数据准备、LoRA/QLoRA、量化、ollama/vLLM 推理、GPU 基础、服务化 | deep-learning、llm-app |

- **应用线**（最快做出东西）：python → llm-app。调用大模型不需要先懂反向传播。
- **原理线**（理解底层、深入优化）：machine-learning → deep-learning → llm-finetune。
- 端口预留 1505–1509 按上表顺序分配；知识点前缀 `python.` / `ml.` / `dl.` /
  `llmapp.` / `finetune.`。
- 主原型建议（ADR 0113，各应用立项时在自己的 ADR/AGENTS 里定稿）：python 主
  **预测–运行**（脚本输出先预测再真跑）辅**真做校验**；machine-learning 主**机制
  模拟**辅**真做校验**；deep-learning 主**预测–运行**（训练曲线、梯度）辅**机制
  模拟**；llm-app 主**真做校验**（做出能跑的小应用）辅**辨析决策**（RAG、长上下文、
  微调的选型判别）；llm-finetune 主**真做校验**。
- 出处档位：五门全是技术学习类（open 档，ADR 0089）——出处是默认习惯不做门禁，
  官方文档与论文鼓励当场标注，不凭印象伪造。
- 实验形态：实验在本机真跑（Python 解释器、uv、notebook、ollama 等），应用只执行
  白名单内的预设命令（ADR 0091 决策 3 同规），不提供任意 shell。
- 每门课开工前按本仓库规则立自己的 ADR 与骨架（AGENTS.md、CLAUDE.md、check.py
  一起建，ADR 0061）。**本次只立项第一门 `python`**，其余四门的定位以本表为准，
  立项时不得与表冲突；课程名字与边界若要改，先修订本条。

### B. 边界

1. **python 与 machine 的边界**：machine（C 与机器）从 C 程序往下看系统；python 从
   工程效率往上看 AI 生态。两边都写代码实验，教的东西不同。
2. **llm-app 与 llm-finetune 的边界**：llm-app 假定模型是黑盒服务（API/本地推理端点），
   专注把应用做出来；llm-finetune 打开盒子改模型。llm-app 里「什么时候该微调」是
   选型判断（辨析决策），具体怎么微调在 llm-finetune。
3. 与 cs408 无关联：408 是考试档的计算机基础综合，AI 路线是技术学习类的应用技能，
   互不挂靠。

## 后果

- 启动器出现「人工智能」圈：首门课 python（group 人工智能）落地后即呈现，后续课程
  立项后自然长成一组。
- `subjects/python` 骨架今天建立（壳：Tauri 2 + React，实验引擎随内容填充期落地）；
  骨架阶段 check.py 默认结构校验（ADR 0103 同规）。
- machine-learning、deep-learning、llm-app、llm-finetune 进路线图待办；缺口登记：
  政治考研课（ADR 0116）与本路线互不影响。
- 根文档的应用清单、名字表与学习应用分类同步登记 python。
