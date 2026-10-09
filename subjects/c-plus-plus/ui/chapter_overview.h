#pragma once

#include "registry/chapter_catalog.h"

// 没有静态 overview_document 时的本机 AI 退路：复制章节上下文并唤起
// 用户配置的本机助手。静态文档跳转仍由 MainWindow 协调。
void launch_local_chapter_overview(const ChapterMeta& chapter);
