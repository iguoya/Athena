# 内容

课表在 `curriculum.json`：章节带一份大纲（题注、五节、分档说明），知识点只登记
ID、先修、难度、掌握目标和哪一份 QML。教学过程写在 `qml/lessons/`，不把大纲
再写进每一节。

知识点 ID 一律以 `c.` 开头。路线图由 `requires` / `difficulty` / `mastery_goal`
在运行时画出来，不要手抄一份会漂移的清单。

知识点 ID 一律以 `c.` 开头。共用主仓库的教学规范（大纲三层、难度、知识类型），
不套主程序的 `athena.json` schema。
