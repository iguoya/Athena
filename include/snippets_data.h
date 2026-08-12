#pragma once

#include <map>
#include <string>

// 代码片段：源码 + 构建期真实运行得到的结果
struct SnippetData {
    const char* source;  // 源码文本（用于界面显示）
    const char* result;  // 运行结果（构建期真实执行得到）
};

// 构建期生成的结果表，键为章节 ID
extern std::map<std::string, SnippetData> g_snippets;
