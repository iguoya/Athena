#include "demo_registry.h"

#include <gtest/gtest.h>

#include <sstream>
#include <stdexcept>

namespace {

TEST(DemoRegistryTest, BuildsStableIdsFromJsonNames) {
    EXPECT_EQ(
        make_demo_id("cpp", "Reference", "const_reference"),
        "cpp.Reference.const_reference");
}

TEST(DemoRegistryTest, RegistersCurrentReferenceAndRaiiExperiments) {
    const auto registry = create_default_demo_registry();

    EXPECT_EQ(registry.ids().size(), 10);
    EXPECT_TRUE(registry.contains("cpp.Reference.reference_basics"));
    EXPECT_TRUE(registry.contains("cpp.RAII.move_"));
    EXPECT_FALSE(registry.contains("cpp.Functions.not_implemented"));
}

TEST(DemoRegistryTest, RunsAReferenceExperiment) {
    const auto registry = create_default_demo_registry();
    ostringstream output;

    registry.run("cpp.Reference.pass_by_reference", output);

    EXPECT_NE(output.str().find("值传递后"), string::npos);
    EXPECT_NE(output.str().find("引用传递后"), string::npos);
}

TEST(DemoRegistryTest, RunsTheCurrentRaiiSkeleton) {
    const auto registry = create_default_demo_registry();
    ostringstream output;

    registry.run("cpp.RAII.unique", output);

    EXPECT_EQ(output.str(), "[待实现] 独占指针\n");
}

TEST(DemoRegistryTest, RejectsDuplicateAndUnknownIds) {
    DemoRegistry registry;
    registry.add("sample", [](ostream& output) { output << "ok"; });

    EXPECT_THROW(
        registry.add("sample", [](ostream&) {}),
        invalid_argument);
    ostringstream output;
    EXPECT_THROW(registry.run("missing", output), out_of_range);
}

} // namespace
