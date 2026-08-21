# ADR 0009：学习数据持久化采用 SQLite

- 日期：2026-08-16
- 状态：已接受
- 依据提交：`88a1741`、`881385d`

## 背景

掌握状态、知识点笔记和运行历史需要跨会话持久化。备选方案是单个 JSON 状态文件
（沿用 athena.json 的先例）。运行历史是追加型数据且随使用持续增长，JSON 每次写入
都要整文件重写，进程在中途崩溃时还有损坏风险；状态、笔记、历史三类数据放进一个
可查询的存储更自然。

## 决策

- 使用系统自带的 SQLite（macOS 为 `/usr/lib` 系统库，Linux 需 `libsqlite3-dev`），
  由 `cc.find_library('sqlite3')` 探测，不引入 Homebrew 依赖，也不随发行包分发。
- `storage/learning_store` 放入 athena-core，RAII 管理 sqlite3 句柄，头文件不暴露
  sqlite3.h；`:memory:` 可用于单元测试。
- 数据库文件位于 `Glib::get_user_data_dir()/Athena/learning.db`
  （macOS 即 `~/Library/Application Support/Athena/`）。
- 打开失败时应用降级运行：状态、笔记、历史相关控件功能失效，其余不受影响。
- 运行历史记录保存 SourceLocator 提取的成员函数源码快照、运行时 Git 提交
  和工作区脏标记，用于回看与并排比较两次实验的源码和输出。

## 后果

- 学习数据与代码仓库分离，重装应用不丢学习记录；数据可用 sqlite3 CLI 直接查看。
- Linux CI/构建需要安装 sqlite3 开发包。
- 相比 JSON 失去"文本编辑器直接改"的便利，属可接受代价。

## 2026-08-21 补充

知识点笔记后来长期隐藏，没有实际入口，却让代码页保留自动保存和切换加载逻辑，
维护成本高于当前价值，因此界面和运行时 API 已移除。既有数据库的 `note` 列保留且
重新评分时不会覆盖，避免破坏历史数据；新数据库不再创建该列。本 ADR 的 SQLite
选择仍然适用于熟练度、运行历史和少量应用设置。
