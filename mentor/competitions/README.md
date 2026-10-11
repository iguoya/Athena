# Athena · 赛历（独立应用）

竞赛清单与参赛资格参考（主仓库 ADR 0114）：程序设计、数学建模、电子与嵌入式、网络安全、
数据与 AI、英语等方向，按「在校生可参 / 社会人士可参」筛选，每条注明来源等级与核对日期，
并对上 Athena 里的课程。图谱/参考类应用，不判分、不记进度。

```
content/competitions.json   赛事数据（唯一数据源）
src/                        前端：筛选与卡片
src-tauri/                  薄壳：窗口 + 用系统浏览器打开官网
```

```sh
launcher open competitions
python3 scripts/check.py competitions
```

协作规则与数据纪律见 [AGENTS.md](AGENTS.md)。
