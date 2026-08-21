#pragma once

#include <cstddef>
#include <optional>
#include <string>
#include <string_view>

using namespace std;

class ContentLoader;

struct SourceRange {
    size_t begin;
    size_t end;
};

optional<SourceRange> locate_cpp_member_function(
    string_view source,
    string_view member_name);

// 读取教学源文件并取出某个知识点成员函数的完整定义文本。运行历史的源码
// 快照、AI 自测的参考实现都用它。源文件读不到或找不到该成员函数时返回
// nullopt，由调用方决定退化行为，不抛出。
optional<string> load_member_source_text(
    const ContentLoader& loader,
    const string& source_path,
    const string& member_name);
