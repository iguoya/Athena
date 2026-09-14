# 开发文档入口

开始新任务先读对应的当前文档，不需要通读历史 ADR 或全部提案。

| 要解决的问题 | 当前入口 |
|---|---|
| 系统现在怎样工作，代码应放哪里 | [ARCHITECTURE](ARCHITECTURE.md) |
| 学习页怎样讲清原理、安排图示和实践 | [LEARNING_DESIGN](LEARNING_DESIGN.md) |
| 类型推导下一步具体怎样做 | [完整教案与页面方案](lessons/type_deduction.md) |
| 配置字段、稳定 ID 与资源引用 | [CHAPTER_CONFIG](CHAPTER_CONFIG.md) |
| 生成命令、文件所有权与构建接线 | [CODE_GENERATION](CODE_GENERATION.md) |
| 模块该不该拆、怎样协作 | [CODE_ROLES](CODE_ROLES.md) |
| 打包、签名和发布 | [RELEASE](RELEASE.md) |
| 外部内容对照资料 | [CONTENT_REFERENCES](CONTENT_REFERENCES.md) |
| 追溯一个决策的理由 | [ADR 索引](decisions/README.md) |
| 查旧架构、旧布局或未采用提案 | [历史归档](archive/README.md) |

## 文档分工

- **当前规范**记录现状和仍有效的约束；每条规则尽量只在负责它的文档展开，其他位置链接过去。
- **具体教案**记录学习目标、可直接使用的讲解、视觉分镜、练习、证据和实施缺口。
  文档完成不代表应用页面完成。
- **ADR**记录取舍及其后果，不当作实时功能清单。按主题查阅；已被修订的细节以当前规范为准。
- **历史归档**保留原文与当时路径语境，默认不读、不作为实现依据，也不删除其中的历史记录。

新增方向性决定先写 ADR，再同步当前规范；实现后同步“已实现/待实现”，不要把开发日志不断追加到架构正文。
