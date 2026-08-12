#pragma once

#include <map>
#include <string>
#include <sstream>
#include <functional>
#include <iostream>

// ============================================================
// 章节演示类
// 每个章节对应一个类，run() 把结果输出到传入的 ostream
// 这些类直接编译进 Athena，运行时点"运行"即实例化对象调用 run()
// ============================================================

// 06_functions: 函数基础 —— 值传递 vs 引用传递
class Functions06 {
public:
    void run(std::ostream& os) {
        int x = 5, y = 10;

        swapByValue(x, y);
        os << "值传递后:  x=" << x << ", y=" << y << "  (未改变)" << std::endl;

        swapByRef(x, y);
        os << "引用传递后: x=" << x << ", y=" << y << "  (已交换)" << std::endl;
    }

private:
    void swapByValue(int a, int b) {
        int temp = a;
        a = b;
        b = temp;
    }

    void swapByRef(int& a, int& b) {
        int temp = a;
        a = b;
        b = temp;
    }
};

// ============================================================
// 章节片段注册表
// ============================================================

struct ChapterSnippet {
    const char* source;                // 类代码文本（源代码框显示用）
    std::function<std::string()> run;  // 运行：实例化对象 + 调 run() + 捕获输出
};

inline std::map<std::string, ChapterSnippet> g_chapter_snippets = {
    {"06_functions", {
        R"SNIP(class Functions06 {
public:
    void run(std::ostream& os) {
        int x = 5, y = 10;

        swapByValue(x, y);
        os << "值传递后:  x=" << x << ", y=" << y << "  (未改变)" << std::endl;

        swapByRef(x, y);
        os << "引用传递后: x=" << x << ", y=" << y << "  (已交换)" << std::endl;
    }

private:
    void swapByValue(int a, int b) {
        int temp = a;
        a = b;
        b = temp;
    }

    void swapByRef(int& a, int& b) {
        int temp = a;
        a = b;
        b = temp;
    }
};)SNIP",
        []() -> std::string {
            Functions06 demo;
            std::ostringstream oss;
            demo.run(oss);
            return oss.str();
        }
    }},
};
