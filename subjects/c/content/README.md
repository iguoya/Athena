# 内容

课表在 `curriculum.json`：章节带一份大纲（题注、五节、分档说明），知识点只登记
ID、先修、难度、掌握目标、哪一份 QML，以及 `source_refs`。教学过程写在
`qml/lessons/`，不把大纲再写进每一节。

随堂考核和课后习题在 `exercises.json`，按知识点 ID 挂上。每题必须能在
`sources/catalog.json` 对上节号。写题前打开 `sources/reference/` 里对应文件。

知识点 ID 一律以 `c.` 开头。路线图由 `requires` / `difficulty` / `mastery_goal`
在运行时画出来，不要手抄一份会漂移的清单。

共用主仓库的教学规范（大纲三层、难度、知识类型、随堂多题），不套主程序的
`athena.json` schema。语言语义以 **C23**（ISO/IEC 9899:2024）为基准，见 ADR 0004。
