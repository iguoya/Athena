#pragma once

#include <optional>
#include <string>
#include <vector>

using namespace std;

// apps/ 下的独立学习应用（ADR 0032）。每个应用自成一个工程：自己的构建
// 系统、自己的界面技术、自己的内容体系；主程序既不编译它，也不读它的内容，
// 只按 app.json 把它当作一个进程启动。
//
// 新增一个应用 = 在 apps/ 下放一个带 app.json 的目录，这里和 MainWindow
// 都不需要改动。
struct ExternalApp {
    string id;
    string title;
    string description;
    string icon_name;
    string directory;   // 应用根目录的绝对路径
    string executable;  // 可执行文件的绝对路径
    vector<string> build_commands;
    bool built = false; // 可执行文件此刻是否存在
};

// 扫描 apps_root 下每个子目录的 app.json。读不动或格式不对的目录会被跳过
// 并记一行日志，不影响其他应用，也不抛出。
vector<ExternalApp> discover_external_apps(const string& apps_root);

// 以独立进程启动，把共用学习库的路径通过 --store 传过去——路径解析只在
// 主程序做一次，被启动方不必再写一套平台规则。
// 成功返回 nullopt，失败返回可以直接显示给用户的错误说明。
optional<string> launch_external_app(
    const ExternalApp& app, const string& store_path);
