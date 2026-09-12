#pragma once

#include "registry/chapter_catalog.h"

#include <gtkmm.h>

#include <string>
#include <vector>

using namespace std;

// 章节教学大纲的**结构模板**。它和**内容模板**是两件事，配套使用：
//
// - 内容模板（docs/CHAPTER_CONFIG.md 6.2、ADR 0028 第 6 节）规定五节各回答
//   什么问题：痛点与来历、心智模型、讲什么与边界、判断与代价、落点。
// - 这里规定它们在页面上怎么摆，并把能由配置算出来的部分直接生成。
//
// 固定的只有三样：题注在最前、五节齐全、顺序不变。**每节叫什么、里面放什么，
// 由本章自己定**——照抄 type_semantics 的小节名只会抄到形状。
namespace outline {

// 五节的标题。职责固定，名字按本章内容起：type_semantics 把「痛点与来历」
// 写成「五类看起来没问题的风险」，把「判断与代价」写成「读代码时的五个
// 检查点」，都是它的知识点性质决定的。
struct SectionTitles {
    string origin;    // 痛点与来历：没有它之前出什么事，为解决什么被引入
    string model;     // 心智模型：用什么结构理解它，派生哪几个基本问题
    string scope;     // 讲什么与边界：覆盖哪些方向、讲到什么深度
    string tradeoff;  // 判断与代价：写代码时要做哪些选择，各自的代价
    string landing;   // 落点：前置、它是谁的地基、想深入去哪查
};

// 五节的内容容器，往里 append 即可（可配合 ui/lesson_blocks.h 的块）。
struct Sections {
    Gtk::Box* origin = nullptr;
    Gtk::Box* model = nullptr;
    Gtk::Box* scope = nullptr;
    Gtk::Box* tradeoff = nullptr;
    Gtk::Box* landing = nullptr;
};

// 在 host 里搭出大纲骨架。lead 是一句题注（这一章承诺解决什么）。
Sections build(Gtk::Box& host, const string& lead, const SectionTitles& titles);

// 「讲什么与边界」里的一档。members 与 badge 由配置生成，note 由作者写：
// 前者手抄会和 athena.json 漂移，后者是评定判断，不是数据能编出来的。
struct GradeNote {
    MasteryGoal goal = MasteryGoal::Unrated;
    string label;  // 这一档在本章叫什么，如「先拿下」「可以先跳过」
    string note;   // 为什么这样定，由作者写
};

// 按掌握目标分档列出本章知识点。同一档内按配置顺序（已是 requires 拓扑序），
// 档与档之间按 notes 给出的顺序——推荐学习顺序由作者决定，不猜。
void grade_groups(
    Gtk::Box& host, const ChapterMeta& chapter, const vector<GradeNote>& notes);

} // namespace outline
