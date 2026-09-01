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
    EXPECT_NE(html.find("Math.max(19"), string::npos);
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

TEST(MarkdownRendererTest, HighlightsCppFencedCodeWithoutChangingItsText) {
    const string markdown = R"ATHENA(```cpp
#include <iostream>
int main() {
    const string message = "<ready>";
    // 保留注释和缩进
    return 42;
}
```
)ATHENA";
    const string html = render_markdown_html(markdown, "", {});

    EXPECT_NE(html.find("<code class=\"language-cpp\">"), string::npos);
    EXPECT_NE(
        html.find(
            "<span class=\"syntax-preprocessor\">#include "
            "&lt;iostream&gt;</span>"),
        string::npos);
    EXPECT_NE(
        html.find("<span class=\"syntax-type\">int</span> main"),
        string::npos);
    EXPECT_NE(
        html.find("<span class=\"syntax-keyword\">const</span>"),
        string::npos);
    EXPECT_NE(
        html.find(
            "<span class=\"syntax-string\">&quot;&lt;ready&gt;&quot;</span>"),
        string::npos);
    EXPECT_NE(
        html.find("<span class=\"syntax-comment\">// 保留注释和缩进</span>"),
        string::npos);
    EXPECT_NE(
        html.find("<span class=\"syntax-number\">42</span>"),
        string::npos);
    EXPECT_EQ(html.find("<ready>"), string::npos);
}

TEST(MarkdownRendererTest, KeepsTextFencesAsUncoloredCode) {
    const string markdown = "```text\nint main() { return 0; }\n```\n";
    const string html = render_markdown_html(markdown, "", {});

    EXPECT_NE(html.find("<code class=\"language-text\">"), string::npos);
    EXPECT_EQ(html.find("class=\"syntax-"), string::npos);
    EXPECT_NE(html.find("int main() { return 0; }"), string::npos);
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

TEST(MarkdownRendererTest, InlinesLocalSvgImagesAsDataUris) {
    const string markdown =
        "见下图：\n\n![值类别](images/value_category.svg)\n";
    const string inlined = inline_markdown_images(
        markdown, [](const string& relative) {
            EXPECT_EQ(relative, "images/value_category.svg");
            return string("<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>");
        });

    EXPECT_NE(inlined.find("![值类别](data:image/svg+xml;base64,"), string::npos);
    EXPECT_EQ(inlined.find("images/value_category.svg"), string::npos);

    const string html = render_markdown_html(
        inlined, "", parse_markdown_headings(inlined));
    EXPECT_NE(html.find("<img src=\"data:image/svg+xml;base64,"), string::npos);
}

TEST(MarkdownRendererTest, KeepsImageReferenceWhenAssetIsMissing) {
    const string markdown = "![缺图](images/missing.svg)\n";
    const string inlined = inline_markdown_images(
        markdown, [](const string&) { return string(); });

    EXPECT_EQ(inlined, markdown);
}

TEST(MarkdownRendererTest, LeavesRemoteImageReferencesUntouched) {
    const string markdown = "![远程](https://example.com/a.svg)\n";
    const string inlined = inline_markdown_images(
        markdown, [](const string&) {
            ADD_FAILURE() << "remote references must not be resolved";
            return string();
        });

    EXPECT_EQ(inlined, markdown);
}

} // namespace
