#pragma once

#include <string>

using namespace std;

// 运行期定位随程序分发的目录，取代编译期写死的源码树绝对路径
// （`ATHENA_SOURCE_ROOT`）。同一份代码会在三种布局下运行，只有运行期
// 才知道东西在哪：
//
//   开发构建   <源码根>/builddir/Athena   → 内容在 <源码根>
//   macOS 包   Contents/MacOS/Athena      → 内容在 Contents/Resources
//   Linux 安装 /usr/bin/athena            → 内容在 /usr/share/athena
//
// 查找顺序统一是：环境变量覆盖 → 相对可执行文件的候选位置 → 编译期源码根
// （开发时保底）。找不到就返回空串，由调用方决定退化行为，不抛出。
//
// 这是全项目唯一允许出现平台分支的地方之一：取"当前可执行文件路径"没有
// 跨平台 API，差异被关在 app_paths.cc 里，不外泄到任何调用方。

// 当前可执行文件所在目录；取不到时返回空串。
string executable_directory();

// 教学源码、Markdown 文档等按路径读取的内容所在的根目录。
// 判定标志是该目录下有 language/ 子目录。
string content_root();

// apps/ 下独立学习应用的根目录（ADR 0032）。
string external_apps_root();
