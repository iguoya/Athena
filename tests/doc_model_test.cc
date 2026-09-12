#include "content/doc_model.h"

#include <gtest/gtest.h>

#include <fstream>
#include <sstream>

namespace {

TEST(DocModelTest, ParsesCoreBlocksAndInlineMeaning) {
    const auto document = parse_document_blocks(
        "# 标题\n\n"
        "正文有 **重点**、`代码` 和 [链接](https://example.com)。\n\n"
        "- 第一项\n- 第二项\n\n"
        "> 引用\n\n"
        "```cpp\nint answer = 42;\n```\n\n"
        "![示意图](images/example.svg)\n\n"
        "| 工具 | 作用 |\n| --- | --- |\n| auto | 推导 |\n");

    ASSERT_EQ(document.blocks.size(), 7u);
    EXPECT_EQ(document.blocks[0].kind, DocBlockKind::Heading);
    EXPECT_EQ(document.blocks[0].level, 1u);
    ASSERT_EQ(document.blocks[0].inlines.size(), 1u);
    EXPECT_EQ(document.blocks[0].inlines[0].text, "标题");

    EXPECT_EQ(document.blocks[1].kind, DocBlockKind::Paragraph);
    ASSERT_GE(document.blocks[1].inlines.size(), 4u);
    EXPECT_EQ(document.blocks[1].inlines[1].kind, DocInlineKind::Strong);
    EXPECT_EQ(document.blocks[1].inlines[2].kind, DocInlineKind::Text);
    EXPECT_EQ(document.blocks[1].inlines[3].kind, DocInlineKind::Code);

    EXPECT_EQ(document.blocks[2].kind, DocBlockKind::BulletList);
    ASSERT_EQ(document.blocks[2].children.size(), 2u);
    EXPECT_EQ(document.blocks[2].children[0].kind, DocBlockKind::ListItem);
    ASSERT_EQ(document.blocks[2].children[0].children.size(), 1u);
    EXPECT_EQ(
        document.blocks[2].children[0].children[0].kind,
        DocBlockKind::Paragraph);
    ASSERT_EQ(document.blocks[2].children[0].children[0].inlines.size(), 1u);
    EXPECT_EQ(
        document.blocks[2].children[0].children[0].inlines[0].text,
        "第一项");

    EXPECT_EQ(document.blocks[3].kind, DocBlockKind::BlockQuote);
    EXPECT_EQ(document.blocks[4].kind, DocBlockKind::CodeBlock);
    EXPECT_EQ(document.blocks[4].language, "cpp");
    EXPECT_EQ(document.blocks[4].text, "int answer = 42;\n");
    EXPECT_EQ(document.blocks[5].kind, DocBlockKind::Image);
    EXPECT_EQ(document.blocks[5].image_path, "images/example.svg");
    EXPECT_EQ(document.blocks[5].image_alt, "示意图");
    EXPECT_EQ(document.blocks[6].kind, DocBlockKind::Table);
    ASSERT_EQ(document.blocks[6].table_header.size(), 2u);
    ASSERT_EQ(document.blocks[6].table_rows.size(), 1u);
}

TEST(DocModelTest, PreservesOrderedListStartAndLineBreakKinds) {
    const auto document = parse_document_blocks(
        "3. 第三项\n4. 第四项\n\n第一行  "
        "\n第二行\n");

    ASSERT_EQ(document.blocks.size(), 2u);
    EXPECT_EQ(document.blocks[0].kind, DocBlockKind::OrderedList);
    EXPECT_EQ(document.blocks[0].ordered_start, 3u);
    ASSERT_EQ(document.blocks[0].children.size(), 2u);
    ASSERT_EQ(document.blocks[0].children[0].children.size(), 1u);
    ASSERT_EQ(document.blocks[0].children[0].children[0].inlines.size(), 1u);
    EXPECT_EQ(
        document.blocks[0].children[0].children[0].inlines[0].text,
        "第三项");
    ASSERT_EQ(document.blocks[1].inlines.size(), 3u);
    EXPECT_EQ(document.blocks[1].inlines[1].kind, DocInlineKind::LineBreak);
}

TEST(DocModelTest, ParsesEveryBundledLearningDocument) {
    const vector<string> documents = {
        "resources/articles/cpp/reference_overview.md",
        "resources/articles/cpp/raii_overview.md",
        "resources/articles/cpp/program_organization.md",
        "resources/articles/practice/pocket_cube_overview.md",
    };

    for (const auto& path : documents) {
        ifstream input(string(ATHENA_SOURCE_ROOT) + "/" + path);
        ASSERT_TRUE(input) << path;
        ostringstream content;
        content << input.rdbuf();
        EXPECT_FALSE(parse_document_blocks(content.str()).blocks.empty()) << path;
    }
}

} // namespace
