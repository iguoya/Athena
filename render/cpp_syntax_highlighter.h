#pragma once

#include <string>

using namespace std;

// 为 md4c-html 生成的 C++ 围栏代码块增加 token span。输入与输出都是
// HTML 片段；非 cpp/c++/cxx 代码块保持原样。
string highlight_cpp_code_blocks(string html);
