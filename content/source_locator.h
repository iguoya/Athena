#pragma once

#include <cstddef>
#include <optional>
#include <string_view>

using namespace std;

struct SourceRange {
    size_t begin;
    size_t end;
};

optional<SourceRange> locate_cpp_member_function(
    string_view source,
    string_view member_name);
