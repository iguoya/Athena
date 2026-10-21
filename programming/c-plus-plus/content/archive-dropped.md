# 历史归档：未收录的条目（programming/c-plus-plus）

来源是旧 GitHub 仓库 `Practice`（`CPP/`，2020-02）与 `Linux`（`CPlusPlus/`，2022–2023）（ADR 0176）。以下内容**没有**进应用的「历史归档」章节；旧仓库只会被设为 archived，历史完整保留，需要时从那里取回。

## 重复（同一练习的后一代整理）

`Linux/CPlusPlus/11-basic`、`13-class`、`21-sequential_container`、`24-io`、`32-thread` 下的大多数程序，是把 `Practice/CPP` 里的单文件程序拆成一个 CMake 工程一个目录的再整理，内容相同或只差空白与注释。只收 `Practice/CPP` 里的版本，并在条目出处的 `duplicates` 里列出对应的 Linux 路径。有内容差异的（`13-class/10-4copy-constructor`、`11-2-visit-control`、`16-polymorphism`、`26-lamada`、`27-share_ptr`、`11-basic/using`、`11-basic/random_better`）单独收录。

## 不收

| 旧路径 | 原因 |
|---|---|
| `Practice/CPP/define_new.cpp`（28 330 行） | `g++ -E` 的预处理输出（以 `# 1 "define.cpp"` 开头）被当成源码提交，是生成物 |
| `Practice/CPP/define.cpp` | 12 行，只打印四个预定义宏 |
| `Practice/CPP/getline.cpp`、`Linux/CPlusPlus/11-basic/getline` | 依赖 boost 库，本机无法编译；内容只是一次 `boost::split` |
| `Practice/CPP/point.cpp`、`std_list.cpp`、`struct.cpp` | 教程式小例子，写不出 3 条以上的实质批注（`struct.cpp` 里作者字段写着 Runoob，是照抄教程） |
| `Practice/CPP/main.cpp` | 一行 `system("./bin/variable")` |
| `Linux/CPlusPlus/11-basic/1-assign` | 向导生成的 `int a=1;` |
| `Linux/CPlusPlus` 根目录工程（`Basic/`、`Class/`、`Derive/`、`Feature/`、`FrameWork/` 与 Qt 主窗口） | 每个主题只有几行的综合工程，与上面各条目重复；`FrameWork` 里的工厂与单例属于设计模式主题，已和设计模式应用的条目对照 |
| `Linux/CPlusPlus/0-assembly`、`33-cgi`、`31-signal` | 分别归 `programming/machine`（汇编）和 `programming/linux`（CGI、信号） |
| 各目录的 `CMakeLists.txt.user`、`*.project`、`*.workspace`、`.vscode` 等 | IDE 工程与本机配置 |
