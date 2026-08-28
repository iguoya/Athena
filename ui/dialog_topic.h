#pragma once

#include <string>

using namespace std;

// 学习类对话框需要的知识点上下文，由代码页在点击“运行历史”“AI 讲解”
// “AI 自测”时按当前行填好。`description` 只有 AI 自测和 AI 讲解用得到
// （作为出题/讲解依据），运行历史不读取它。
struct DialogTopic {
    string function_id;
    string title;
    string description;
    string source_path;
    string member_name;
};
