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
    string executable;  // 启动入口的绝对路径：Tauri 应用是 scripts/dev.sh（ADR 0041），C 应用是构建产物
    vector<string> build_commands;
    bool built = false; // 启动入口此刻是否存在且可执行
};

// 扫描 apps_root 下每个子目录的 app.json。读不动或格式不对的目录会被跳过
// 并记一行日志，不影响其他应用，也不抛出。
vector<ExternalApp> discover_external_apps(const string& apps_root);

// 以独立进程启动。进度库不再共享——每个应用自建、自管自己的库（ADR 0037），
// 所以这里除了把进程拉起来不传任何状态。
// 成功返回 nullopt，失败返回可以直接显示给用户的错误说明。
optional<string> launch_external_app(const ExternalApp& app);
