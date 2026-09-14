#pragma once

#include <string>

using namespace std;

// 教学内容一律从 GResource 读（ADR 0047）：源码、插图、章节目录都随构建打包，
// 运行期不按文件路径找任何东西。这样源码框显示的内容和实验跑的代码永远同版本，
// 也不需要"当前可执行文件在哪"这种没有跨平台 API 的能力。
class ContentLoader {
public:
    string load_resource(const string& resource_path) const;

    // 教学源码，路径相对源码树（如 "cplusplus/reference/reference.hpp"）。
    string load_project_file(const string& relative_path) const;
};
