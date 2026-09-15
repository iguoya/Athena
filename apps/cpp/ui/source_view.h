#pragma once

#include "content/content_loader.h"

#include <gtksourceview/gtksource.h>

#include <string>

using namespace std;

// 给源码框配上 C++ 语法高亮、括号匹配和配色方案。只读的真实源码和
// 可编辑的骨架案例（ADR 0053）共用这一份设置。
void apply_cpp_highlighting(GtkSourceView* source_view);

// 在只读源码框展示真实教学源码，并可选定位、高亮一个成员函数定义。
void display_project_source(
    GtkSourceView* source_view,
    const ContentLoader& content_loader,
    const string& relative_path,
    const string& member_name = "");

// 在不重载文本、不重建标记的前提下，把当前插入标记带入视口。供隐藏
// 源码框首次完成布局后补一次滚动。
void scroll_source_to_cursor(GtkSourceView* source_view);
