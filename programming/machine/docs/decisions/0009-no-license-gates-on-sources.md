# ADR 0009：参考资料不按许可分流，只按体积决定放哪

- 日期：2026-10-14
- 状态：已接受（tiger 2026-10-14：「只要互联网上能找到的数据，一律默认公域」；见仓库
  [ADR 0159](../../../../docs/decisions/0159-jiuzhou-academic-layer-in-repo.md)）
- 修订：[ADR 0003](0003-local-sources-and-sourced-exercises.md) 决策 1、2 中按许可限制存放与写法的部分

## 决策

1. **c-faq 的 HTML 不再忽略**：脚本下载后直接提交。0003 里「c-faq 只供本机查阅、HTML 不进 git」撤销。
2. **PDF 的忽略理由改为体积**：`modern-c`、`c23`、`sysv-abi`、`intel-sdm` 的 PDF 体积大、可由
   `scripts/fetch-sources.py` 重抓，所以不入库；这是工程理由，与许可无关。
3. **「DIS 禁止派生、不整段复制 NC-ND 正文」不再是许可约束**：题干仍用中文改写该节事实、
   教案仍只引节名，但原因是改写更利于学习，且 `source_refs` 要能核对到节，不是怕侵权。
4. `catalog.json` 与 `reference/README.md` 的许可字段继续保留，作为出处记录。
