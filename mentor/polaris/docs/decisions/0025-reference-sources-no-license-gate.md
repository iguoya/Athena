# ADR 0025：路线图对照来源不按许可证筛选

- 日期：2026-10-14
- 状态：已接受（tiger 2026-10-14：「只要互联网上能找到的数据，一律默认公域」；见仓库
  [ADR 0159](../../../../docs/decisions/0159-jiuzhou-academic-layer-in-repo.md)）
- 取代：[ADR 0016](0016-routes-over-a-shared-base.md) 决策 7 中按许可证决定「拷贝入库还是只记链接」的规则

## 决策

1. **所有对照来源一律拷贝说明文件入库**：roadmap.sh、coding-interview-university、
   TeachYourselfCS-CN、Embedded-Engineering-Roadmap、awesome-hdl、awesome-embedded-systems、
   awesome-fpga 与原有四个仓库同等对待。`scripts/fetch_references.py` 删去「只拷贝 MIT / CC0」
   的检查与「仅引用」清单（`--linked-only` 改为 `--roles`）。
2. **许可证只作出处记录**，写进 `MANIFEST.json`，不决定拷不拷。
3. **其余不变**：对照原料不进应用界面，也不被直接搬进节点正文（那是出处与质量的要求，
   ADR 0016 决策 7 后半）；新增路线与节点仍用北极星自己的语言与出处。

## 后果

- 新增的七个仓库要重跑一次 `python scripts/fetch_references.py` 才会真正落到
  `content/sources/reference/roadmaps/`；该脚本会把已有四项一并换成上游当前快照，所以重跑前
  先确认可以接受 sha256 变化。脚本改动本身不会下载任何东西。
