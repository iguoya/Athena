# ADR 0010：翻译术语约定——以社区 PO 为基线定主译法，禁用写法由 check 阻断

- 日期：2026-10-17
- 状态：已接受
- 延续：应用 ADR 0002（官方译文优先）、0004（贡献产出走导出脚本）；
  审查依据 `comms/gtkmm-review/SUMMARY.md`（widget 在前十章四种译法并存）

## 背景

全书译文来自两个来源：社区 PO（`po/reference.zh_CN.po`，经 `apply_po.py` 填进快照 zh）
和本应用自己的手写（知识点、测验、模拟、术语表）。两边各用各的词：全书快照里
「部件」311 处、「控件」66 处、「小部件」4 处；手写文字却是「控件」45 : 「部件」10。
同一页里「装填 / 打包 / 组装」、「信号处理函数 / 程序 / 器」混用，学习者会以为是不同概念。

## 决策

1. **术语表 `content/glossary.json` 是唯一事实源**：每条给主译法 `use`、禁用写法 `avoid`
   （正则）、批量统一用的 `replace`、以及依据 `why`。未决项写在 `open`，不假装已定。
2. **选词以社区 PO 的多数为基线**：这样统一后，与上游社区译文的差异（`export_contribution.py`
   的 differs 清单）最小，将来反哺上游不增加人工确认量。已定七条：widget=部件、
   packing=装填、signal handler=信号处理函数、CheckButton=复选按钮、top-level=顶级窗口/容器、
   TreeView=树形视图、event loop=事件循环（main loop 仍是主循环）。
3. **只统一能无歧义统一的**：「打包」留给发行版打包与资源打包，只改 packing 义的几个固定搭配；
   `wrap`（包装 / 封装）、`Entry`（条目 / 输入框）、`Adjustment` 同形多义，列入 `open`，
   逐处判断后再定，不机械替换。
4. **执行与守卫**：`scripts/glossary.py` 无参数检查、`--apply` 批量改写（只动 zh 字符串值、
   手写文件与 `src/simulations.tsx`，不动英文原文、po-units 镜像和 ADR）；
   `scripts/check.py` 调用同一检查，禁用写法出现即失败。新译文先对照术语表。
5. **术语表可演进**：改规则 = 改 `glossary.json` + 重跑 `--apply` + 一个提交；不为个别段落放宽。

## 后果

- 本次统一涉及 37 个文件 146 行（快照 zh、curriculum、demos、vocab、模拟文案）。
- po-units 是社区 PO 的镜像，仍含「控件」等写法，只在多段单元展示时出现；重跑
  `align_po.py` 会还原镜像，不影响快照 zh。
- 社区 PO 与本应用术语表冲突时，以本表为准，冲突条目会出现在贡献导出的 differs 清单里，
  由人工决定是否上推。
