#pragma once

#include <gtkmm.h>

#include <string>
#include <vector>

using namespace std;

// 学习页内容块的构建帮手。对应 resources/ui/lesson_blocks.blp 里的模板，
// 按 AGENTS.md「GTK 与 Blueprint 规则」：重复出现的条目做成一份 .blp 模板，
// 代码按数据实例化，而不是在 C++ 里逐个拼控件。
//
// 它解决的是「后续章节照抄两千行」的问题——该复制的是范式，不是行数。
// 但**不要把所有东西都塞进来**：对象图、逐步演示、值类别矩阵这类需要 Cairo
// 自绘、或者结构由运行时数据决定的部分，仍然各写各的。硬套模板会把有教学
// 信息量的差异磨平，那比多写几行更糟。
namespace lesson {

// callout 的五种语气，对应 style.css 里那套 Bootstrap alert 配色：
// Why 解释为什么（信息蓝）、Key 点出要害、Note 补充说明（两者皆警告黄）、
// Trap 常见误区（危险红）、Use 怎么选（成功绿）。
enum class CalloutKind { Why, Key, Note, Trap, Use };

// 往 host 里加一个带标题的内容区，返回可继续 append 的内容容器。
Gtk::Box& section(Gtk::Box& host, const string& title);

// 往 host 里加一个提示框，返回它的正文容器——多段正文就多次 prose()。
Gtk::Box& callout(Gtk::Box& host, CalloutKind kind, const string& title);

// 一段正文。
Gtk::Label& prose(Gtk::Box& host, const string& text);

// 一组要点，每条前面带「·」。
void bullets(Gtk::Box& host, const vector<string>& items);

// 一段代码，可带说明。等宽、可选中、不折行。
void code(Gtk::Box& host, const string& text, const string& caption = "");

// 一张对照表。head 为空表示没有表头行。rows 的每行列数应与 head 一致。
// 单元格文本以「!」开头表示这是一条判定（用强调配色），显示时去掉该前缀。
void table(
    Gtk::Box& host,
    const vector<string>& head,
    const vector<vector<string>>& rows,
    const string& note = "");

// 一组有序步骤，序号自动编号。
void steps(Gtk::Box& host, const vector<string>& items);

// 一张静态插图加图注。数据驱动的图请用 DrawingArea 自己画，别走这里。
void figure(
    Gtk::Box& host,
    const string& resource_path,
    int height,
    const string& caption);

} // namespace lesson
