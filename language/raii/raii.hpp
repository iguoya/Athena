#pragma once

#include <iosfwd>

using namespace std;

// RAII 与资源管理
//
// 一个 public 成员函数对应 athena.json 中的一个可运行知识点。
// 实现按知识点内容拆分到独立 .cpp 文件，类本身保持为一个主题。
class RAII {
public:
    // RAII 思想
    void basic(ostream& output) const;

    // 智能指针
    void unique(ostream& output) const;
    void shared(ostream& output) const;
    void weak(ostream& output) const;

    // 移动语义
    void rvalue(ostream& output) const;
    void move_semantics(ostream& output) const;
};
