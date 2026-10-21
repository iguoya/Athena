# legacy-archive 舱：六个旧 GitHub 仓库并入「历史归档」章节

依据 [ADR 0176](../../docs/decisions/0176-legacy-github-repos-archive-merge.md)，先读它。

目标：`Practice`、`Linux`、`algorithm`、`DesignPatterns`、`DesignPattern`、`Qt5` 六个旧仓库去重、分类，
并入对应教学应用各自独立的「历史归档」章节（原代码原样保留、能运行、另写批注指出不足），最后归档远程仓库。

## 源码在哪

六个仓库已克隆在 **`.cache/legacy-src/`**（仓库根下，已被 gitignore，只读使用，**不要改、不要提交**）：
`Practice/ Linux/ algorithm/ DesignPatterns/ DesignPattern/ Qt5/`。路径用 `git -C .cache/legacy-src/<仓库> ls-files` 看被跟踪文件，
`git -C ... log --follow --format=%ad --date=short -- <路径>` 取首次提交日期。

## 分工与文件归属

- leader（claude-code）：ADR、任务书、验收、共用壳与各应用前端、`curriculum.json` 集成、新应用建立、提交。
- zcode、cursor（worker）：**第一阶段只写自己的 `artifacts/<名字>/`**（清单与证据），不改 `programming/`、`postgraduate/`、
  `practice/`、`packages/` 下任何文件，不提交 git。后续阶段由任务书另行授权具体目录。
- 工作区里 `release-next` 舱的人正在改各应用的 `main.ts`、`lib.rs`、`package.json` 等（更新器接入），**这些文件一律不碰**。

## 清单格式（第一阶段产出）

每个领域一个文件 `artifacts/<名字>/manifest-<领域>.json`，外加一份 `manifest-<领域>.md` 写给人看的摘要
（统计、争议项、建议）。JSON 顶层为数组，每个元素是一个**历史练习单元**（一个模式 / 一个数据结构 / 一个小工程 / 一个主题目录）：

```json
{
  "unit": "dp-adapter",                     // 小写英文短名，全清单唯一
  "title": "适配器模式（类适配器实验）",
  "target": "programming/design-patterns",  // 目标应用目录，见 ADR 0176 对照表
  "verdict": "keep",                        // keep | merge-into:<unit> | drop-duplicate | drop-third-party | drop-junk
  "canonical": ["DesignPattern/Adapter"],   // 规范版路径：<仓库>/<相对路径>，可多个
  "duplicates": ["DesignPatterns/workspace/Adapter", "Practice/DesignPatterns/Adapter", "Linux/DesignPattern/Adapter"],
  "first_commit": "2022-03-04",             // 规范版最早提交日期（git 取）
  "files": 24,                              // 规范版文件数
  "run": "cli",                             // cli | toolchain | linux-only | read-only
  "build": "g++ -std=c++17 *.cpp",          // 实测能过的最短编译命令；toolchain 类写需要什么库
  "build_checked": true,                    // 你是否真的编译运行过（true 才算数，不得凭印象）
  "topic_hint": "对应现有章节 dp.adapter",   // 在目标应用里的落点；无对应写“新增”
  "quality_notes": "一两句：原代码主要问题，供后续批注（命名/资源管理/耦合/缺测试等）",
  "reason": "verdict 不是 keep 时必填：为什么，依据是什么（如内容哈希相同、官方库自带）"
}
```

要求：**每个被跟踪的源码文件必须被某个单元覆盖或明确 drop**（写个小脚本校验“零遗漏”并把输出放进 md）；
第三方判定要给依据（上游名称/URL 或文件头版权声明）；`run` 为 `cli` 的必须在本机真编译真运行过再标 `build_checked: true`；
编译失败的如实写失败原因。不要凭文件名猜内容，不要编造首次提交日期。

## 通讯

按 [../README.md](../README.md)：开工先 `python comms/comms.py inbox <名字> --project legacy-archive`，
做完 `status T-xxx review --note "证据"`，需要裁决发消息给 claude-code。
