#include "render/markdown_renderer.h"

#include <gtest/gtest.h>

namespace {

TEST(MarkdownRendererTest, ExtractsHeadingHierarchyAndStableAnchors) {
    const auto headings = parse_markdown_headings(
        "#  标题  \n\n## 带 **强调** 的标题\n\n#### 不进入目录\n");

    ASSERT_EQ(headings.size(), 3);
    EXPECT_EQ(headings[0].title, "标题");
    EXPECT_EQ(headings[0].anchor, "athena-heading-0");
    EXPECT_EQ(headings[0].level, 1);
    EXPECT_EQ(headings[1].title, "带 强调 的标题");
    EXPECT_EQ(headings[1].level, 2);
    EXPECT_EQ(headings[2].level, 4);
}

TEST(MarkdownRendererTest, ProducesACompleteReaderDocument) {
    const string markdown = "# Athena\n\n## 第二节\n\n正文。\n";
    const auto headings = parse_markdown_headings(markdown);
    const string html = render_markdown_html(
        markdown,
        "body { color: #123456; }",
        headings);

    EXPECT_NE(html.find("<!doctype html>"), string::npos);
    EXPECT_NE(html.find("body { color: #123456; }"), string::npos);
    EXPECT_NE(html.find("class=\"article-tools\""), string::npos);
    EXPECT_NE(html.find("class=\"article-toc\""), string::npos);
    EXPECT_NE(html.find("<h1 id=\"athena-heading-0\">Athena</h1>"), string::npos);
    EXPECT_NE(html.find("href=\"#athena-heading-1\""), string::npos);
}

TEST(MarkdownRendererTest, EscapesRawHtmlFromDocuments) {
    const string markdown = "# Safe\n\n<script>alert('x')</script>\n";
    const string html = render_markdown_html(
        markdown,
        "",
        parse_markdown_headings(markdown));

    EXPECT_EQ(html.find("<script>alert('x')</script>"), string::npos);
    EXPECT_NE(html.find("&lt;script&gt;"), string::npos);
}

TEST(MarkdownRendererTest, OmitsTheTocWhenThereAreNoHeadings) {
    const string markdown = "只有正文。\n";
    const string html = render_markdown_html(markdown, "", {});

    EXPECT_EQ(html.find("class=\"article-toc\""), string::npos);
    EXPECT_NE(html.find("article-layout-without-toc"), string::npos);
}

TEST(MarkdownRendererTest, GroupsExperimentsAtTheEndOfTheirSection) {
    const string markdown =
        "# 第一章\n\n## 类型推导\n\n先讲清规则。\n\n## 值类别\n\n下一节。\n";
    const auto headings = parse_markdown_headings(markdown);
    const string html = render_markdown_html(
        markdown,
        "",
        headings,
        {{"类型推导", "cpp.Type.auto", "auto"},
         {"类型推导", "cpp.Type.decltype", "decltype"}});

    const size_t explanation = html.find("先讲清规则。");
    const size_t group = html.find("class=\"athena-experiment-group\"");
    const size_t next_section = html.find(">值类别</h2>");
    ASSERT_NE(explanation, string::npos);
    ASSERT_NE(group, string::npos);
    ASSERT_NE(next_section, string::npos);
    EXPECT_LT(explanation, group);
    EXPECT_LT(group, next_section);
    EXPECT_EQ(
        html.find("class=\"athena-experiment-group\"", group + 1),
        string::npos);
    EXPECT_NE(html.find(">▶ auto</a>"), string::npos);
    EXPECT_NE(html.find(">▶ decltype</a>"), string::npos);
}

} // namespace
