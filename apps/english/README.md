# Athena · 英语自学（独立应用）

与主程序**平级**的独立学习应用（主仓库 ADR 0032）。技术栈：Tauri 2 + Web UI。
**不启动主程序也可以完成全部练习。** 决策见 [`docs/decisions/`](docs/decisions/)。

## 做什么

从实用高频英语起步，经过初级、中级、高级逐步衔接英语二。首页保持「英语自学」的
学习口吻，高级阶段和路线终点明确说明最终应试方向。

课表分**初级、中级、高级**三个等级，每级同时练三条轨（ADR 0004）：

1. **单词**——按义项和例句认识，不是「单词 = 一个中文」
2. **例句**——切分、指代、句间逻辑；高级那条挂一篇短文当语境
3. **作文**——开放练习写真实段落；机器只提示形式条件，独立考核另测任务回应、组织、
   衔接和语言选择，不把字数冒充作文质量

答错的题进错题本，**连着两天做对、并且做对一次变式**才出库。做题在电脑上；
公众号若使用，只看导出的讲解，不在手机上做题（ADR 0002）。

## 构建与运行

依赖：Node.js、Rust（rustup），以及系统 `sqlite3`（pkg-config）。

```sh
cd apps/english
./scripts/dev.sh
# 或
npm install
npm run tauri:dev
```

不要只跑 `npm run dev` 再用浏览器打开：没有进度库，复习写不进去。

发行 / 独立窗口：

```sh
cd apps/english
npm install
LIBSQLITE3_SYS_USE_PKG_CONFIG=1 npm run build:app
./bin/athena-english
```

环境变量 `ATHENA_ENGLISH_ROOT` 可指定应用根目录。

## 目录

| 路径 | 内容 |
|---|---|
| `content/curriculum.json` | 等级与练习轨 |
| `content/vocab/` | 词卡（义项 + 例句） |
| `content/sentences/` | 例句练习 |
| `content/passages/` | 短文 Markdown + 题目 JSON |
| `content/writing/` | 作文题（题干、起句、自查项、参考） |
| `content/assessments/` | 各等级三条轨的独立平行题；首次作答时相对练习材料未见 |
| `content/README.md` | 分级、选材来源和练习/考核边界 |
| `src/` | 前端：书桌与练习台 |
| `src-tauri/` | Tauri / Rust |
| `app.json` | 仅供主程序发现 |

`npm run check:content` 检查路线引用、ID、正确选项、练习变式，以及考核材料没有与
练习原题重复；`npm run build` 会先自动执行这项检查。
