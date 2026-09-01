#pragma once

#include <functional>
#include <string>
#include <vector>

using namespace std;

struct MarkdownHeading {
    string title;
    string anchor;
    unsigned level = 1;
};

// 渲染期挂载的实验入口：知识点声明"我在哪一节被讲到"（对应
// athena.json 里 subchapter.teaches），文档本身不知道 Athena 存在、
// 不为它改写一个字符。heading 必须和某个 MarkdownHeading.title 完全
// 相等（标准化后的纯文本，不含 Markdown 语法字符）才会命中；没有命中
// 的条目只是不出现卡片，不报错——文档处于重写期时不应因为这个阻断
// 渲染。见 docs/LEARNING_WORKSPACE_BENCH.md。
struct HeadingExperimentLink {
    string heading;
    string knowledge_id; // 完整稳定 ID，如 cpp.TypeSemantics.value_category
    string label;        // 卡片显示文字，通常就是知识点标题
};

// 提取文章目录所需的标题；正文只通过 WebView 显示。
vector<MarkdownHeading> parse_markdown_headings(const string& markdown);

// 把 Markdown 中形如 ![说明](images/xxx.svg) 的本地相对图片引用替换为
// 内联的 data: URI。load_relative 接收引用里的相对路径（如
// "images/value_category.svg"），返回文件内容，找不到时返回空串。
// 打包后文档来自 GResource、没有源码目录，file: 相对引用必然失效，
// 内联 data: URI 让两个 ArticleView 后端都无需自定义 URL scheme。
// 只处理不含协议、不以 / 开头、扩展名为 .svg 的引用；其余原样保留。
string inline_markdown_images(
    const string& markdown,
    const function<string(const string&)>& load_relative);

// 将 Markdown、文章目录和阅读工具栏组合成完整 HTML 文档。experiment_links
// 为空（默认）时行为和之前完全一样，不影响没有配置 teaches 的既有页面。
string render_markdown_html(
    const string& markdown,
    const string& stylesheet,
    const vector<MarkdownHeading>& headings,
    const vector<HeadingExperimentLink>& experiment_links = {});
