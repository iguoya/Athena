#include "external_app_launcher.h"

#include <glibmm.h>
#include <nlohmann/json.hpp>

#include <algorithm>
#include <fstream>
#include <iostream>
#include <sstream>

using json = nlohmann::json;

namespace {

string read_file(const string& path) {
    ifstream file(path);
    if (!file) {
        return {};
    }
    ostringstream buffer;
    buffer << file.rdbuf();
    return buffer.str();
}

optional<ExternalApp> parse_app(const string& directory) {
    const string manifest_path = Glib::build_filename(directory, "app.json");
    if (!Glib::file_test(manifest_path, Glib::FileTest::EXISTS)) {
        return nullopt;
    }

    const string source = read_file(manifest_path);
    if (source.empty()) {
        cerr << "External app manifest unreadable: " << manifest_path << endl;
        return nullopt;
    }

    try {
        const json value = json::parse(source);
        ExternalApp app;
        app.id = value.at("id").get<string>();
        app.title = value.at("title").get<string>();
        app.description = value.value("description", string{});
        if (value.contains("icon")) {
            app.icon_name = value.at("icon").value("name", string{});
        }
        app.directory = directory;
        app.executable = Glib::build_filename(
            directory, value.at("executable").get<string>());
        for (const auto& command : value.value("build", json::array())) {
            app.build_commands.push_back(command.get<string>());
        }
        app.built = Glib::file_test(app.executable, Glib::FileTest::IS_EXECUTABLE);
        return app;
    } catch (const exception& error) {
        cerr << "External app manifest invalid (" << manifest_path
             << "): " << error.what() << endl;
        return nullopt;
    }
}

} // namespace

vector<ExternalApp> discover_external_apps(const string& apps_root) {
    vector<ExternalApp> apps;
    if (!Glib::file_test(apps_root, Glib::FileTest::IS_DIR)) {
        return apps;
    }

    try {
        Glib::Dir directory(apps_root);
        vector<string> entries(directory.begin(), directory.end());
        // 目录遍历顺序由文件系统决定，排序后首页上的顺序才是稳定的。
        sort(entries.begin(), entries.end());
        for (const auto& entry : entries) {
            const string path = Glib::build_filename(apps_root, entry);
            if (!Glib::file_test(path, Glib::FileTest::IS_DIR)) {
                continue;
            }
            if (auto app = parse_app(path)) {
                apps.push_back(*app);
            }
        }
    } catch (const Glib::Error& error) {
        cerr << "Failed to scan external apps in " << apps_root << ": "
             << error.what() << endl;
    }
    return apps;
}

optional<string> launch_external_app(const ExternalApp& app) {
    if (!app.built) {
        string message = app.title + " 的启动入口还不在。\n\n在项目根目录执行：";
        for (const auto& command : app.build_commands) {
            message += "\n    " + command;
        }
        return message;
    }

    const vector<string> argv{app.executable};

    try {
        // 异步启动后就不再管它：两个进程各自独立，被启动方崩溃不影响主程序。
        // Tauri 应用这里拉起的是 scripts/dev.sh（热更新），不是打包 .app（ADR 0041）。
        Glib::spawn_async(
            app.directory, argv, Glib::SpawnFlags::DEFAULT);
        return nullopt;
    } catch (const Glib::Error& error) {
        return app.title + " 启动失败：" + string(error.what());
    }
}
