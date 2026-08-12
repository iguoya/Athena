#include "runner.hpp"
#include "c++/function.hpp"

#include <fstream>
#include <sstream>

// 运行章节类对象：按章节 ID 直接实例化对应类，调 run() 输出
std::string run_chapter(const std::string& chapter_id) {
    std::ostringstream oss;

    if (chapter_id == "06_functions") {
        Functions06 demo;
        demo.run(oss);
    }
    // 更多章节在此添加对应类的实例化...

    return oss.str();
}

// 返回章节源文件内容：直接读对应源文件
std::string chapter_source(const std::string& chapter_id) {
    std::string rel_path;
    if (chapter_id == "06_functions") {
        rel_path = "snippets/c++/function.hpp";
    }
    // 更多章节在此添加源文件相对路径...

    if (rel_path.empty()) {
        return "";
    }

    std::ifstream f(std::string(ATHENA_SOURCE_ROOT) + "/" + rel_path);
    if (!f) {
        return "";
    }
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}
