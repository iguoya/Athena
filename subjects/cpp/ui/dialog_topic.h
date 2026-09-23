#pragma once

#include <string>

using namespace std;

// 学习类对话框需要的知识点上下文，由代码页在点击“AI 讲解”“AI 自测”
// 时按当前行填好。description 和源码位置作为出题、讲解依据。
struct DialogTopic {
    string function_id;
    string title;
    string description;
    string source_path;
    string member_name;
};
