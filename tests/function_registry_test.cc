#include "registry/function_registry.h"

#include <gtest/gtest.h>

#include <sstream>
#include <stdexcept>

namespace {

TEST(FunctionRegistryTest, RegistersCurrentChapterExperiments) {
    const auto registry = create_default_function_registry();

    EXPECT_EQ(registry.ids().size(), 22);
    EXPECT_TRUE(registry.contains("cpp.TypeSemantics.initialization"));
    EXPECT_TRUE(registry.contains("cpp.Reference.reference_basics"));
    EXPECT_TRUE(registry.contains("cpp.FunctionCallable.overload"));
    EXPECT_TRUE(registry.contains("cpp.RAII.move_semantics"));
    EXPECT_TRUE(registry.contains("practice.PocketCube.run"));
    EXPECT_FALSE(registry.contains("cpp.Functions.not_implemented"));
}

TEST(FunctionRegistryTest, RunsAReferenceExperiment) {
    const auto registry = create_default_function_registry();
    ostringstream output;

    registry.run("cpp.Reference.pass_by_reference", output);

    EXPECT_NE(output.str().find("值传递后"), string::npos);
    EXPECT_NE(output.str().find("引用传递后"), string::npos);
}

TEST(FunctionRegistryTest, RunsARaiiExperiment) {
    const auto registry = create_default_function_registry();
    ostringstream output;

    registry.run("cpp.RAII.unique", output);

    EXPECT_NE(output.str().find("所有权转移后原指针为空: 是"), string::npos);
    EXPECT_NE(output.str().find("离开作用域后析构次数: 1"), string::npos);
    EXPECT_EQ(output.str().find("[待实现]"), string::npos);
}

TEST(FunctionRegistryTest, RunsAFunctionCallableExperiment) {
    const auto registry = create_default_function_registry();
    ostringstream output;

    registry.run("cpp.FunctionCallable.function_wrapper", output);

    EXPECT_NE(output.str().find("bad_function_call"), string::npos);
    EXPECT_EQ(output.str().find("[待实现]"), string::npos);
}

TEST(FunctionRegistryTest, RunsATypeSemanticsExperiment) {
    const auto registry = create_default_function_registry();
    ostringstream output;

    registry.run("cpp.TypeSemantics.decltype_deduction", output);

    EXPECT_NE(output.str().find("decltype(变量名) 保留声明类型: 是"), string::npos);
    EXPECT_NE(
        output.str().find("decltype((左值表达式)) 得到引用: 是"),
        string::npos);
    EXPECT_EQ(output.str().find("[待实现]"), string::npos);
}

TEST(FunctionRegistryTest, RejectsDuplicateAndUnknownIds) {
    FunctionRegistry registry;
    registry.add("sample", [](ostream& output) { output << "ok"; });

    EXPECT_THROW(
        registry.add("sample", [](ostream&) {}),
        invalid_argument);
    ostringstream output;
    EXPECT_THROW(registry.run("missing", output), out_of_range);
}

} // namespace
