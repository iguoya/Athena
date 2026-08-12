#pragma once

#include <string>

// 运行章节对应的类对象，返回输出文本
std::string run_chapter(const std::string& chapter_id);

// 返回章节对应的源文件内容（用于源码框显示）
std::string chapter_source(const std::string& chapter_id);
