#pragma once

#include <string>
#include <vector>

using namespace std;

// 学习文档的结构化中间表示（ADR 0024）。作者仍写 Markdown，解析后不再
// 转成 HTML，而是转成这里的「块序列」；运行期由控件文档渲染器遍历块序列，
// 按类型实例化 GTK 控件。这一层不依赖 GTK，可用 Google Test 独立验证。

enum class DocInlineKind {
    Text,       // 普通文字
    Code,       // `行内代码`
    Emphasis,   // *斜体*
    Strong,     // **加粗**（AGENTS.md：琥珀色重点）
    Link,       // [文字](href)
    Image,      // ![alt](src)，通常独占一段，见 DocBlockKind::Image
    SoftBreak,  // 源码换行，渲染为空格
    LineBreak,  // 行尾两个空格或反斜杠，渲染为硬换行
};

struct DocInline {
    DocInlineKind kind = DocInlineKind::Text;
    string text;                // Text / Code：文字；Image：alt
    string href;                // Link：链接目标；Image：图片相对路径
    vector<DocInline> children; // Emphasis / Strong / Link：内部内容
};

enum class DocBlockKind {
    Heading,       // level 1-6 + inlines
    Paragraph,     // inlines
    CodeBlock,     // language + text（原样保留，含缩进和注释）
    BulletList,    // children 是若干 ListItem
    OrderedList,   // children 是若干 ListItem，从 ordered_start 编号
    ListItem,      // children 是块序列（通常一个 Paragraph）
    Table,         // table_header + table_rows
    Image,         // image_path + image_alt（由“只含一张图的段落”转来）
    BlockQuote,    // children 是块序列
    ThematicBreak, // ---
};

struct DocTableCell {
    vector<DocInline> inlines;
};

struct DocBlock {
    DocBlockKind kind = DocBlockKind::Paragraph;
    unsigned level = 0;                       // Heading：1-6
    string language;                          // CodeBlock：围栏语言（可空）
    string text;                              // CodeBlock：原文
    string image_path;                        // Image：相对路径
    string image_alt;                         // Image：替代文字
    unsigned ordered_start = 1;              // OrderedList：起始序号
    vector<DocInline> inlines;                // Heading / Paragraph
    vector<DocBlock> children;                // List / ListItem / BlockQuote
    vector<DocTableCell> table_header;        // Table：表头一行
    vector<vector<DocTableCell>> table_rows;  // Table：正文各行
};

struct DocModel {
    vector<DocBlock> blocks;
};

// 解析 Markdown 为块序列（GitHub 方言 + 禁用裸 HTML）。解析失败抛
// runtime_error。
DocModel parse_document_blocks(const string& markdown);
