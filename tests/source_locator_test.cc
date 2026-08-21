#include "content/source_locator.h"

#include "content/content_loader.h"

#include <gtest/gtest.h>

using namespace std;

TEST(SourceLocatorTest, FindsDefinitionInsteadOfEarlierCall) {
    const string source = R"cpp(
class Example {
public:
    void run() { const_reference(); }

    void const_reference() {
        const char* text = "a brace } inside a string";
        // A comment with another } brace.
        if (text) {
        }
    }
};
)cpp";

    const auto range = locate_cpp_member_function(source, "const_reference");

    ASSERT_TRUE(range.has_value());
    const auto selected = source.substr(
        range->begin,
        range->end - range->begin);
    EXPECT_EQ(selected.find("    void const_reference() {"), 0);
    EXPECT_NE(selected.find("if (text)"), string::npos);
    EXPECT_EQ(selected.back(), '\n');
}

TEST(SourceLocatorTest, ReturnsNothingForUnknownMember) {
    EXPECT_FALSE(locate_cpp_member_function(
        "class Example {};",
        "missing").has_value());
}

// 运行历史的源码快照和 AI 自测的参考实现都取自这个函数，因此它必须在
// 真实教学源码上取到成员函数全文。
TEST(SourceLocatorTest, LoadsMemberSourceFromTeachingFile) {
    const ContentLoader loader(ATHENA_SOURCE_ROOT);

    const auto body = load_member_source_text(
        loader, "language/references/reference.hpp", "reference_basics");

    ASSERT_TRUE(body.has_value());
    EXPECT_NE(body->find("reference_basics"), string::npos);
}

TEST(SourceLocatorTest, ReturnsNothingWhenSourceOrMemberIsMissing) {
    const ContentLoader loader(ATHENA_SOURCE_ROOT);

    EXPECT_FALSE(
        load_member_source_text(loader, "language/missing.hpp", "anything")
            .has_value());
    EXPECT_FALSE(load_member_source_text(
                     loader,
                     "language/references/reference.hpp",
                     "not_a_member")
                     .has_value());
}
