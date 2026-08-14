#pragma once

#include <iosfwd>

using namespace std;

// RAII 与资源管理
//
// 一个 public 成员函数对应 athena.json 中的一个可运行知识点。
// 实现按三个视觉分组拆分到独立 .cpp 文件，类本身保持为一个主题。
class RAII {
public:
    // RAII 思想
    void basic(ostream& output);

    // 智能指针
    void unique(ostream& output);
    void shared(ostream& output);
    void weak(ostream& output);

    // 移动语义
    void rvalue(ostream& output);
    void move_(ostream& output);
};
