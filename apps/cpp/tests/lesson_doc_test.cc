#include "content/lesson_doc.h"

#include <gtest/gtest.h>

#include <stdexcept>

using namespace std;

namespace {

const char* kSample = R"JSON({
  "chapter": "cpp.Sample",
  "topics": [{
    "topic": "cpp.Sample.point",
    "title": "标题",
    "subtitle": "副标题",
    "blocks": [
      { "type": "lead", "text": "导语" },
      { "type": "table",
        "head": ["写法", "保证"],
        "rows": [["a", "!会报错"], ["b", "放行"]],
        "note": "表注" },
      { "type": "section", "title": "小节", "blocks": [
          { "type": "prose", "text": "正文" },
          { "type": "callout", "kind": "trap", "title": "误区", "blocks": [
              { "type": "bullets", "items": ["一", "二"] }
          ]}
      ]},
      { "type": "figure", "id": "some_figure", "caption": "图注" }
    ]
  }]
})JSON";

}  // namespace

TEST(LessonDocTest, DecodesBlocksAndNesting) {
    const LessonChapter chapter = parse_lesson_chapter(kSample);
    EXPECT_EQ(chapter.chapter, "cpp.Sample");
    ASSERT_EQ(chapter.topics.size(), 1u);

    const LessonDoc& doc = chapter.topics[0];
    EXPECT_EQ(doc.topic, "cpp.Sample.point");
    EXPECT_EQ(doc.subtitle, "副标题");
    ASSERT_EQ(doc.blocks.size(), 4u);

    EXPECT_EQ(doc.blocks[0].type, "lead");
    EXPECT_EQ(doc.blocks[0].text, "导语");

    const LessonBlock& table = doc.blocks[1];
    ASSERT_EQ(table.head.size(), 2u);
    ASSERT_EQ(table.rows.size(), 2u);
    EXPECT_EQ(table.rows[0][1], "!会报错");
    EXPECT_EQ(table.note, "表注");

    // 嵌套要能一直传下去：section 里的 callout 里的 bullets。
    const LessonBlock& section = doc.blocks[2];
    ASSERT_EQ(section.blocks.size(), 2u);
    const LessonBlock& callout = section.blocks[1];
    EXPECT_EQ(callout.kind, "trap");
    ASSERT_EQ(callout.blocks.size(), 1u);
    EXPECT_EQ(callout.blocks[0].items.size(), 2u);

    EXPECT_EQ(doc.blocks[3].id, "some_figure");
    EXPECT_EQ(doc.blocks[3].caption, "图注");
}

TEST(LessonDocTest, MissingFieldsAreReported) {
    // 缺必填字段时要说清楚，不能解出一个半成品对象继续往下跑。
    EXPECT_THROW(parse_lesson_chapter(R"({"topics": []})"), runtime_error);
    EXPECT_THROW(parse_lesson_chapter("{ 不是 JSON }"), runtime_error);
    EXPECT_THROW(
        parse_lesson_chapter(R"({"chapter":"c","topics":[{"title":"t","blocks":[]}]})"),
        runtime_error);
}

TEST(LessonDocTest, OptionalFieldsDefaultToEmpty) {
    const LessonChapter chapter = parse_lesson_chapter(R"JSON({
      "chapter": "cpp.Sample",
      "topics": [{ "topic": "t", "title": "标题",
                   "blocks": [{ "type": "prose", "text": "只有正文" }] }]
    })JSON");
    const LessonBlock& block = chapter.topics[0].blocks[0];
    EXPECT_TRUE(chapter.topics[0].subtitle.empty());
    EXPECT_TRUE(block.title.empty());
    EXPECT_TRUE(block.items.empty());
    EXPECT_TRUE(block.blocks.empty());
}
