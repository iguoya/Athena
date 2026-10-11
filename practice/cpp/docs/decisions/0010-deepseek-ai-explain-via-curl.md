# ADR 0010：知识点讲解可选接入 DeepSeek API，经 curl 子进程调用

- 日期：2026-08-17
- 状态：已接受
- 依据提交：（本 ADR 与对应实现同批提交）

## 背景

"AI 讲解"按钮此前只有一种机制：把知识点说明与源码拼成提示词复制到剪贴板，
再唤起本机 AI 客户端（默认 `doubao://`），由用户自己粘贴查看结果——全程
不联网，Athena 本身不发起任何网络请求。

用户希望配置 DeepSeek API Key 后，点击"AI 讲解"能直接在对话框里显示
讲解结果，不用手动切换到外部客户端粘贴。这是 Athena 第一次需要主动发起
出站网络请求，属于影响架构边界的决策，按项目规则先记 ADR。

## 决策

- **网络请求走 curl 子进程，不引入新的生产依赖**。项目此前已经用
  `Glib::spawn_command_line_sync` 调用 `git` 查询提交信息（历史对比功能），
  这里复用同一模式：`call_deepseek_chat()` 构造 DeepSeek 的 chat completions
  请求，通过 curl 子进程同步发出，解析 JSON 响应。不链接 libcurl，不新增
  Objective-C++ 平台代码（如 `NSURLSession`），避免为 macOS/Linux 分别维护
  一套网络客户端。
- **API Key 通过环境变量 `ATHENA_DEEPSEEK_API_KEY` 传入**，与既有的
  `ATHENA_AI_COMMAND` 是同一约定；不在 `athena.json`、代码或任何提交的文件
  中保存 Key。
- **Key 和请求体都不出现在进程命令行参数里**：分别写入两个临时文件（Key
  经 curl `-K` 配置文件、请求体经 `--data @文件`），调用后立即删除，避免
  `ps` 等工具能看到 Key 明文。
- **未配置 Key 时静默退回到原有的剪贴板 + 唤起本机 AI 助手流程**，"AI 讲解"
  按钮的可用性不依赖是否配置了 DeepSeek，两条路径共存。
- **请求在独立工作线程执行**，结果经 `Glib::signal_idle()` 回主线程更新
  对话框，遵循项目已有的"耗时操作不阻塞主线程"惯例（与 `start_experiment`
  的实验执行线程同构）。

## 后果

- Athena 从"完全离线"变成"可选联网"：只有用户主动配置了 Key 才会发生
  出站请求，默认状态（未配置）行为与之前完全一致。
- 新增了对 `curl` 命令行工具存在的隐式依赖（macOS/主流 Linux 发行版默认
  自带，不需要额外安装）；`curl` 缺失或网络不可用时在对话框里显示错误
  信息，不影响应用其余功能。
- "本章总纲"按钮目前仍只有剪贴板方案，未接入 DeepSeek；如果以后要统一，
  应复用 `call_deepseek_chat()`，不要另起一套调用逻辑。
- 如果未来要支持 DeepSeek 之外的其他云端模型，应在 `call_deepseek_chat()`
  之外抽象出统一的请求/响应结构，而不是每接入一家就复制一份 curl 调用。
