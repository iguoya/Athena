# Athena 项目生成规范

## 1. 单一入口

`resources/athena.json` 是分类、章节、知识点、实现入口和资源引用的唯一数据源。
所有校验和派生输出统一由 `scripts/generate_project.py` 进入。命令入口保持很薄，
实现按职责放在 `scripts/project_generator/`：

```text
generate_project.py              命令解析与生成文件安全写入
project_generator/model.py       读取、校验并建立唯一内部模型
project_generator/resources.py   GResource 与 Blueprint 构建输入
project_generator/registry.py    FunctionRegistry 生成
project_generator/scaffold.py    首次章节骨架创建
```

四个子命令共用 `model.py`，因此资源清单、函数注册表和章节骨架不会各自重新解释
JSON，也不会重新形成多套数据来源。

所有命令都显式接收项目根目录和配置文件：

```sh
python3 scripts/generate_project.py \
  --project-root . --config resources/athena.json check
```

## 2. 四个子命令

### 2.1 `check`

只读取和校验，不写文件：

```sh
python3 scripts/generate_project.py \
  --project-root . --config resources/athena.json check
```

校验范围包括 schema、必填字段、名称合法性与唯一性、跨分类课程类名、内容类型、分组引用、
Blueprint 输出冲突，以及 Markdown、源码、实现头文件和资源图标路径。失败时输出
包含章节或字段位置的错误并返回非零退出码。Meson 已把它注册为
`athena-project-check` 测试。

### 2.2 `resources`

生成 GResource XML，并在标准输出逐行返回 Meson 需要编译的 Blueprint：

```sh
python3 scripts/generate_project.py \
  --project-root . --config resources/athena.json \
  resources --output builddir/app.gresource.xml
```

标准输出格式为 `target_id|blueprint_path|ui_filename`。XML 包含主窗口、共享样式、
文章、章节 UI、`athena.json`、配置引用的教学源码和非隐藏图标资源。`app.gresource.xml` 是构建产物，
位于 Meson 构建目录，不提交到 Git，也不手工维护。

### 2.3 `registry`

从声明了 `implementation.header` 的 `code` 章节生成注册表：

```sh
python3 scripts/generate_project.py \
  --project-root . --config resources/athena.json \
  registry --output builddir/function_registry.generated.cc
```

映射完全由现有字段派生：

```text
category.name   -> 函数 ID 的分类部分，不重复生成 C++ 命名空间
chapter.name    -> 全局 C++ 类名
subchapter.name -> public 成员函数名
三者组合        -> category.chapter.subchapter 稳定函数 ID
```

生成文件带有 `DO NOT EDIT` 标记，由构建系统完全拥有。人工代码只实现通用
`FunctionRegistry` 容器和各课程类，不维护第二份章节映射。

### 2.4 `scaffold`

为一个未来的 `code` 章节首次创建头文件和源文件：

```sh
python3 scripts/generate_project.py \
  --project-root . --config resources/athena.json \
  scaffold --chapter cpp.TypeSemantics
```

使用前必须先在 `athena.json` 定义章节及其 `subchapters`，并声明
`implementation.header`。可以另外声明 `implementation.source`；省略时从头文件
路径把扩展名替换为 `.cpp`。

骨架包含章节类、每个知识点的 public 成员函数和明确的“待实现”输出。文件使用
排他创建；任何目标文件已经存在时只报告 `kept`，绝不截断、合并或覆盖人工教学
代码。分成多个源文件的特殊章节应维护已有实现，不对它运行默认骨架生成。

## 3. 文件所有权

构建系统拥有：

```text
builddir/app.gresource.xml
builddir/function_registry.generated.cc
builddir/*.ui
```

开发者或 Codex 拥有：

```text
resources/athena.json
resources/articles/**/*.md
resources/ui/**/*.blp
language/**/*.hpp
language/**/*.cpp
tests/**
```

修改课程结构时先改 JSON；修改教学内容时编辑人工源码、文章和测试；禁止直接修改
构建目录中的生成文件。

## 4. 确定性与安全

- 生成结果固定使用 UTF-8 和 `\n`，不包含时间、用户名、绝对路径或随机值。
- 资源、头文件和输出条目使用稳定排序；成员函数保持 JSON 中的教学顺序。
- JSON 中的项目路径必须是安全相对路径，拒绝绝对路径、`.` 和 `..`。
- 可覆盖的构建产物先写临时文件再原子替换；内容未变化时不改写。
- `scaffold` 使用仅新建语义，构建过程不会隐式创建或修改人工课程实现。
- 自然语言 `description` 是教学需求，不直接转换成未经审查的最终 C++ 代码。

## 5. Meson 和测试

Meson 配置阶段调用 `resources`，取得 Blueprint 目标并在 `builddir` 生成 XML；构建
阶段通过 `custom_target` 调用 `registry`。`athena.json` 是两个过程的输入依赖。
`scaffold` 只允许开发者显式执行，不是普通构建副作用。

项目提供两项生成器相关测试：

- `athena-project-check`：校验真实项目配置和全部引用。
- `athena-project-generator`：在临时工程端到端运行四个子命令，并验证二次
  `scaffold` 不覆盖已有文件。

修改 `athena.json` 或生成器后至少运行：

```sh
python3 scripts/generate_project.py \
  --project-root . --config resources/athena.json check
meson setup builddir --reconfigure
meson compile -C builddir
meson test -C builddir --print-errorlogs
```

实现 `code` 章节时，应读取章节和知识点的 `description`，使用骨架作为起点编写
可观察、可重复的教学实验，并补充测试。实现 `article` 章节时只编辑 `document`
指向的 Markdown，不创建 C++ 类、运行按钮或注册项。
