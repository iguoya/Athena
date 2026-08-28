#pragma once

#include "content/content_loader.h"

#include <gtksourceview/gtksource.h>

#include <string>

using namespace std;

// 在只读源码框展示真实教学源码，并可选定位、高亮一个成员函数定义。
void display_project_source(
    GtkSourceView* source_view,
    const ContentLoader& content_loader,
    const string& relative_path,
    const string& member_name = "");
