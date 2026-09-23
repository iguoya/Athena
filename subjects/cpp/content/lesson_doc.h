#pragma once

#include <string>
#include <vector>

using namespace std;

// 一章学习页的内容数据（ADR 0055）。
//
// 内容是数据，表现是模板，两者分开：这里只描述「这一节有哪些块、每块装什么」，
// 长什么样由 resources/ui/lesson_blocks.blp 决定，怎么摆由 ui/lesson_renderer 决定。
//
// 九种块用一个宽结构体承载，而不是 variant 或类层次：块类型就这么几种、字段
// 大多是字符串，多一层抽象只会让读的人多跳一次。不用的字段留空。
struct LessonBlock {
    // lead / prose / bullets / code / callout / section / table / steps / figure
    string type;
    // prose、code、lead 的正文
    string text;
    // section 与 callout 的标题
    string title;
    // callout 的语气：why / key / note / trap / use
    string kind;
    // section 的档位：core（核心，展开）/ deeper（进阶，折叠）/
    // optional（选读，折叠）。空等同 core。让难点显式可见，而不是
    // 藏在一长段正文里。
    string tier;
    // code 与 figure 的说明文字
    string caption;
    // table 的表注
    string note;
    // figure 引用的绘制函数 id
    string id;
    // quiz / predict 的正确选项下标
    int answer = -1;
    // bullets 与 steps 的条目
    vector<string> items;
    // table 的表头；为空表示没有表头行
    vector<string> head;
    // table 的数据行
    vector<vector<string>> rows;
    // section 与 callout 的子块
    vector<LessonBlock> blocks;
};

// 随堂考核的一道题（ADR 0054 第 3 条）。它是掌握度的唯一来源——AI 现场出题
// 不再计入，题目写在课文里、有出处、本地判分，可复核也可回归。
//
// 与 ui/checkpoint_view.h 的 CheckpointQuestion 是同一件事的两侧：这里是
// 数据，那边是控件。题目从代码搬进数据之后，新增一节不必再改页面类。
struct LessonCheckpointQuestion {
    string id;
    string stem;
    vector<string> options;
    // 正确选项下标
    int answer = -1;
    string explain;
};

// 一个知识点的随堂考核。成绩按所在知识点落库，所以不必再标覆盖范围。
struct LessonCheckpoint {
    string intro;
    vector<LessonCheckpointQuestion> questions;

    bool empty() const { return questions.empty(); }
};

// 一个知识点的学习页。
struct LessonDoc {
    // 完整函数 ID，例如 cpp.ValueSemantics.move_semantics
    string topic;
    string title;
    string subtitle;
    vector<LessonBlock> blocks;
    // 这个知识点的随堂考核，可能为空（那它就还拿不到掌握度）。
    LessonCheckpoint checkpoint;
};

// 一章的全部学习页，按知识点排列。
struct LessonChapter {
    // 完整章节 ID，例如 cpp.ValueSemantics
    string chapter;
    // 教学大纲：三层分工的第一层（ADR 0028），章节页的第一个标签。
    // 它的 topic 是章节 ID 本身。
    LessonDoc outline;
    vector<LessonDoc> topics;
};

// 从 JSON 文本解码。结构校验归 Python 生成器（ADR 0013），这里信任数据，
// 只在 JSON 本身不合法或缺必填字段时抛 runtime_error。
LessonChapter parse_lesson_chapter(const string& json_text);

// 从 GResource 读一章（/app/lessons/<chapter>.json）。教学内容只从 GResource
// 读，运行期不按文件路径找随程序分发的东西（AGENTS.md）。
LessonChapter load_lesson_chapter(const string& chapter_id);
