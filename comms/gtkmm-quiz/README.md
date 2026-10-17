# gtkmm-quiz 舱：gtkmm 测验标准版铺开（应用 ADR 0011）

leader（claude-code）定标准、审题、改 `guide/gtkmm/content/curriculum.json` 并提交；worker 只在
`artifacts/<名字>/` 里写题目草稿（Python 规格文件），**不改 `guide/gtkmm/` 下任何文件、不提交 git**。
标准与写法见 [tools/STANDARD.md](tools/STANDARD.md)，已落地的范例见 `examples/ch3.py`、`examples/ch6.py`。
