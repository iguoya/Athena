#include "content/source_locator.h"

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
