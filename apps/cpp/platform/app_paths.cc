#include "app_paths.h"

#include <glibmm.h>

#include <cstdlib>
#include <vector>

#ifdef __APPLE__
#include <mach-o/dyld.h>
#else
#include <climits>
#include <unistd.h>
#endif

namespace {

string resolve_executable_path() {
#ifdef __APPLE__
    uint32_t size = 0;
    // 第一次调用只为问出需要多大缓冲区，返回非 0 是预期行为。
    _NSGetExecutablePath(nullptr, &size);
    vector<char> buffer(static_cast<size_t>(size) + 1, '\0');
    if (_NSGetExecutablePath(buffer.data(), &size) != 0) {
        return {};
    }
    return string(buffer.data());
#else
    vector<char> buffer(PATH_MAX, '\0');
    const ssize_t length =
        readlink("/proc/self/exe", buffer.data(), buffer.size() - 1);
    if (length <= 0) {
        return {};
    }
    return string(buffer.data(), static_cast<size_t>(length));
#endif
}

string environment_override(const char* name) {
    const char* value = getenv(name);
    return value != nullptr ? string(value) : string();
}

bool has_directory(const string& parent, const string& child) {
    return !parent.empty()
        && Glib::file_test(
               Glib::build_filename(parent, child), Glib::FileTest::IS_DIR);
}

} // namespace

string executable_directory() {
    const string path = resolve_executable_path();
    if (path.empty()) {
        return {};
    }
    // 可执行文件可能是符号链接（Homebrew、AppImage 的常见做法），
    // 先规范化再取目录，否则会算到链接所在目录去。
    char* real = realpath(path.c_str(), nullptr);
    const string resolved = real != nullptr ? string(real) : path;
    free(real);
    return Glib::path_get_dirname(resolved);
}

string content_root() {
    const string override_path = environment_override("ATHENA_CONTENT_ROOT");
    if (!override_path.empty()) {
        return override_path;
    }

    const string exe_dir = executable_directory();
    if (!exe_dir.empty()) {
        const string parent = Glib::path_get_dirname(exe_dir);
        const vector<string> candidates = {
            Glib::build_filename(parent, "Resources"),    // macOS .app
            Glib::build_filename(parent, "share", "athena"), // Linux 安装
            parent,                                        // 开发构建目录
        };
        for (const auto& candidate : candidates) {
            if (has_directory(candidate, "cplusplus")) {
                return candidate;
            }
        }
    }

    // 开发时的保底：从源码树直接运行、或可执行文件被挪到别处时仍能工作。
    const string source_root = ATHENA_SOURCE_ROOT;
    return has_directory(source_root, "cplusplus") ? source_root : string();
}

string external_apps_root() {
    const string override_path = environment_override("ATHENA_APPS_ROOT");
    if (!override_path.empty()) {
        return override_path;
    }

    // 本程序自己也住在 apps/ 下（ADR 0045：C++ 教程是 apps/cpp，和别的学习
    // 应用平级），所以 apps/ 不在内容根里面，而在它上面。从内容根往上找几级：
    // 源码树里 apps/cpp -> apps 一步就到；发行包里找不到，返回空，
    // 调用方会说清楚"独立应用不随本包分发"。
    string directory = content_root();
    for (int depth = 0; depth < 3 && !directory.empty() && directory != "/";
         ++depth) {
        if (Glib::path_get_basename(directory) == "apps"
            && Glib::file_test(directory, Glib::FileTest::IS_DIR)) {
            return directory;
        }
        const string apps = Glib::build_filename(directory, "apps");
        if (Glib::file_test(apps, Glib::FileTest::IS_DIR)) {
            return apps;
        }
        directory = Glib::path_get_dirname(directory);
    }
    return {};
}
