# ADR 0008：machine 的壳由 Qt6/QML 迁到 Tauri 2 + React

- 日期：2026-10-11
- 状态：已接受（tiger 2026-10-11：「machine 先改」；`playground/` 保留）。**决定已定，迁移尚未执行**
- 依据：仓库 [ADR 0138](../../../../docs/decisions/0138-course-apps-unify-tauri-react.md) 决策 7；
  取代仓库 [ADR 0042](../../../../docs/decisions/0042-c-language-qt-qml-lessons.md) 决策 1、3
- 不变：本应用 ADR 0001–0007（章级图谱、C23 基准、C 与汇编双线、多目标运行环境等）；
  仓库 ADR 0080 对 `id` 不改嫁的重组豁免与它无关——本次不改任何 `id`

## 背景

ADR 0042 选 Qt Quick / QML 写教案，理由是教案需要自己的描述语言、能画内存条与指针箭头。之后仓库把课程类应用
统一到 Tauri 2 + React（仓库 ADR 0138）。Qt 不是教学内容（machine 教 C 与汇编，不教 Qt），
也不是 C 生态的原生载体，仓库 ADR 0133 已把它记为「不得效仿的历史例外」。

实测规模不大：QML 20 个文件约 1800 行，C++ 壳约 250 行（读课表、从磁盘加载 QML、监视文件热加载）。
课表（`curriculum.json`）、题库（`exercises.json`）、实验（`labs/`、`scripts/lab.py`）、汇编素材（`content/asm/`）、
教材副本都是 JSON 与文件，**与 Qt 无关**。真正要重写的是呈现层。

## 决策

1. **壳改为 Tauri 2 + React + TypeScript + Vite**，页面渲染按仓库 ADR 0138 决策 3 的摘星基线
   （Tailwind v4、shadcn/ui 式组件、Motion、Zustand、React Router）。
2. **保持不变**：`id`、目录名、知识点前缀 `machine.`、`content/` 下全部 JSON 与素材、`labs/`、`scripts/lab.py`、
   `content/asm/`、学习方法原型（预测–运行为主，机制模拟为辅）、先修方向规则与 `scripts/check.py` 的内容校验。
   `playground/` 的 LVGL 小程序**保留**，仍是独立 `cmake` 构建的旁路，不是图谱入口，不随迁移处理。
3. **重写**：`qml/pages/`（章图谱、大纲）、`qml/components/`（章卡片、知识点节点、大纲区块、对照、内存条、随堂考核）、
   `qml/lessons/*.qml` 各节教案——逐节重写为 React 组件，保留动画与交互语义。
   教案的描述语言由 QML 组件树变为 React 组件，「教案有自己的描述语言」这一条精神沿用（ADR 0042 背景）。
4. **删除**：`CMakeLists.txt` 里 Qt 部分、`src/` 的 C++ 壳、`app.json` 与 CI 里的 Qt 步骤、macOS 打包里的 Qt 部分。
   热加载由 Vite HMR 取代。删除要显式：提交信息写清删了什么、在哪能取回。
5. **实验链路先验证再排期**：`lab.py` 与界面的衔接原先由 C++ 壳触发，迁移后由 Tauri 的 Rust 侧命令调用
   `scripts/lab.py`。这是迁移里最不确定的一块，应先做可行性小验证（能在应用内触发 `lab.py run` 并拿到输出），
   通过后再安排整体迁移。
6. **安全网**：迁移前打 `pre-machine-react` tag（已有的 `pre-machine-reorg` 不复用）。
7. **验收**：`pnpm typecheck`、`pnpm build`、`tauri dev` 能跑，`scripts/check.py machine` 通过；`content/` 与 `labs/` 的
   git diff 为空；章图谱、大纲、各节教案、随堂考核逐页截图对照；应用内不再遗留 QML 与 Qt 构建文件。

## 后果

- 本机不再需要 Qt 6；machine 回到仓库统一的 pnpm 构建与 CI 矩阵。
- `AGENTS.md` 的技术栈节与目录表、`README.md`、仓库 ADR 0133 的「历史例外」表述在迁移完成时一并同步
  （迁移前它们描述的仍是实情，不提前改）。
- 迁移工作量集中在 20 个 QML 文件的逐个重写，不涉及内容与进度；第 5 条的验证若不通过，须回头评估，
  不带着未验证的链路排期。
