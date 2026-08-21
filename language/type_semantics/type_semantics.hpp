#pragma once

#include <iosfwd>

using namespace std;

// 类型、初始化与值语义
//
// 每个 public 成员函数对应一个可独立运行的知识点。编译期错误示例只以
// 注释保留，运行路径本身始终是定义良好、输出稳定的 C++20 程序。
class TypeSemantics {
public:
    void initialization(ostream& output) const;
    void auto_deduction(ostream& output) const;
    void decltype_deduction(ostream& output) const;
    void value_category(ostream& output) const;
    void cast(ostream& output) const;
    void enum_class(ostream& output) const;
};
