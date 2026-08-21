# ADR 0011：AI 讲解/自测新增火山方舟豆包服务商，按优先级回退到 DeepSeek

- 日期：2026-08-17
- 状态：已接受
- 依据提交：（本 ADR 与对应实现同批提交）

## 背景

ADR 0010 让"AI 讲解"等功能可选接入 DeepSeek，并且已经预见到"如果未来要
支持 DeepSeek 之外的其他云端模型，应抽象出统一的请求/响应结构，而不是
每接入一家就复制一份 curl 调用"。

用户希望新增火山方舟（Volcengine Ark）的豆包模型
（`doubao-seed-2-1-pro-260628`）作为讲解/自测/讲解差异功能的服务商，且
**优先使用豆包，失败或未配置时才退回 DeepSeek**，而不是让用户在两者间
手动选择。

## 决策

- **抽出通用的 `call_llm_chat(endpoint, model, api_key, prompt)`**，替代
  原来只认 DeepSeek 的 `call_deepseek_chat()` 内部实现；两家服务商的
  chat completions 接口都是 OpenAI 兼容协议（`Authorization: Bearer`、
  `{"model":...,"messages":[...]}`），只是 endpoint 和 model 不同，不需要
  两套 curl 调用逻辑。`call_deepseek_chat()`、`call_ark_doubao_chat()` 都
  只是对 `call_llm_chat()` 填好各自 endpoint/model 的薄封装。
- **新增 `call_ai_chat_with_fallback(ark_api_key, deepseek_api_key, prompt)`**
  作为所有调用方的统一入口：配置了豆包 Key 就先试豆包；豆包失败且配置了
  DeepSeek Key 就退回 DeepSeek；都没配置就返回明确的错误结果。调用方
  （讲解、自测、讲解差异对话框）不再各自判断"用哪个服务商"，只传两个
  Key 进去。
- **豆包 Key 通过新的环境变量 `ATHENA_ARK_API_KEY` 传入**，与
  `ATHENA_DEEPSEEK_API_KEY` 是同一约定（curl `-K` 配置文件传 Key、
  临时文件用完即删，不出现在 `ps` 命令行参数里），两个环境变量互相独立，
  可以只配一个、配两个或都不配。
- **按钮可用性看"是否至少配置了一个 Key"**，不要求两个都配置；只有两个
  都未配置时才退回原有的剪贴板 + 唤起本机 AI 助手流程。
- **模型 ID 硬编码在代码里**（豆包固定用
  `doubao-seed-2-1-pro-260628`，DeepSeek 固定用 `deepseek-chat`），不做成
  可配置项——目前只是"选服务商"，不是"选模型"，配置面越小越不容易配错。

## 后果

- 网络请求路径仍然只有 curl 子进程一条，没有新增生产依赖，符合 ADR 0010
  的既有约束。
- 单个服务商偶发故障（网络问题、限流、账号未开通某模型）不再直接导致
  功能不可用，只要另一个 Key 配置了就能自动接上；两个都失败时错误信息
  会说明具体是哪一步失败的。
- 以后如果要接入第三家服务商，应该继续复用 `call_llm_chat()`，并且只在
  `call_ai_chat_with_fallback()` 这一处扩展优先级链条，不要在各个按钮的
  点击处理里分别加分支。
- "本章总纲"仍然是纯本地静态文档（见 `overview_document`
  字段），不参与这条 AI 调用链——这是 ADR 0010 之后又做的单独修正，两者
  不冲突。
