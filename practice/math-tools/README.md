# 数学工具 · Math Tools

实践类数学工具箱(`practice/`,ADR 0060):矩阵实验室、函数绘图,后续按需扩充。
技术栈:Tauri 2 + Vue 3 + TypeScript + Tailwind CSS 4 + motion-v + mathjs。
选型理由与协作规则见 [AGENTS.md](AGENTS.md)。

## 运行

走启动器(推荐):

```sh
launcher open math-tools --root practice
```

手动开发:

```sh
npm install
npm run tauri:dev   # Tauri 桌面窗口,前端热更
npm run dev         # 仅前端,浏览器 http://localhost:1451
```

## 功能

| 工具 | 说明 |
| --- | --- |
| 练习纲要 | 七章二十四条练习(工具就绪 → 函数 → 线代 → 导数极限 → 积分 → ODE → 综合),每条带工具标签与验收要求;勾选打卡存 localStorage |
| 矩阵实验室 | 2×2 / 3×3 矩阵的行列式、迹、逆、转置、秩、幂、特征值(mathjs 数值内核) |
| 函数绘图 | 表达式 `f(x)` 采样绘制,渐变描边;拖拽平移、滚轮缩放、示例快选 |
| 三套皮肤 | 星穹(深空网格·暗)/ 晨读(暖纸·衬线)/ 草稿(米纸·快乐体),侧栏色点切换,机制同拾阶 skins(令牌驱动) |

纲要数据在 `src/data/curriculum.ts`,配套学习资源(3Blue1Brown、GeoGebra Materials、
MATLAB Onramp 等)的入口见仓库对话记录;每条练习的路径是:看一遍直觉(视频/图文)→
拖一遍图形(GeoGebra)→ 算一遍数值(Octave)。

## 目录

| 位置 | 内容 |
| --- | --- |
| `src/views/` | 各工具页(Home / MatrixLab / Plot) |
| `src/style.css` | Tailwind 4 入口与 `@theme` 主题令牌 |
| `src-tauri/` | Tauri 2 壳(Rust) |
| `scripts/check.py` | 应用级验证(app.json + typecheck + build) |
