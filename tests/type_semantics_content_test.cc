#include "type_semantics/type_semantics.hpp"

#include <gtest/gtest.h>

#include <sstream>

namespace {

using Experiment = void (TypeSemantics::*)(ostream&) const;

string run_experiment(Experiment experiment) {
    TypeSemantics chapter;
    ostringstream output;
    (chapter.*experiment)(output);
    return output.str();
}

TEST(TypeSemanticsContentTest, ComparesInitializationFormsWithoutReadingUndefinedValues) {
    EXPECT_EQ(
        run_experiment(&TypeSemantics::initialization),
        "直接初始化 int direct(7): 7\n"
        "拷贝初始化 int copied = 8: 8\n"
        "列表初始化 int listed{9}: 9\n"
        "值初始化 int zero{}: 0\n"
        "直接初始化允许 double 到 int 的窄化结果: 3\n"
        "列表初始化 int rejected{fractional}: 编译期拒绝窄化\n"
        "explicit 构造函数可直接初始化: 11\n"
        "默认初始化的局部 int: 不读取，避免未定义行为\n");
}

TEST(TypeSemanticsContentTest, ShowsWhichQualifiersTypeDeductionPreserves) {
    EXPECT_EQ(
        run_experiment(&TypeSemantics::type_deduction),
        "auto 按值推导得到 int: 是\n"
        "auto& 保留 const 引用: 是\n"
        "decltype(变量名) 保留声明类型: 是\n"
        "decltype((左值表达式)) 得到引用: 是\n"
        "decltype(std::move(value)) 得到右值引用: 是\n"
        "结构化绑定拆出的值: Athena，5\n");
}

TEST(TypeSemanticsContentTest, SelectsReferenceBindingsFromValueCategories) {
    EXPECT_EQ(
        run_experiment(&TypeSemantics::value_category),
        "具名对象 named: 左值\n"
        "临时对象 string(\"临时值\"): 纯右值\n"
        "std::move(named): 将亡值\n"
        "具名对象匹配: 可修改左值引用\n"
        "具名 const 对象匹配: const 左值引用\n"
        "临时对象匹配: 右值引用\n"
        "将亡值匹配: 右值引用\n"
        "std::move 只改变值类别，原内容仍为: Athena\n");
}

TEST(TypeSemanticsContentTest, DemonstratesTheBoundariesOfNamedCasts) {
    EXPECT_EQ(
        run_experiment(&TypeSemantics::cast),
        "static_cast 明确数值转换 9.8 -> 9\n"
        "dynamic_cast 匹配真实派生类型: 是\n"
        "dynamic_cast 不匹配时返回空: 是\n"
        "const_cast 修改原本非 const 的对象: 9\n"
        "reinterpret_cast 指针往返仍指向原对象: 是\n");
}

TEST(TypeSemanticsContentTest, KeepsScopedEnumsTypeSafe) {
    EXPECT_EQ(
        run_experiment(&TypeSemantics::enum_class),
        "枚举成员使用作用域: TrafficLight::green\n"
        "可隐式转换为 int: 否\n"
        "显式转换后的底层值: 3\n"
        "底层类型是 unsigned char: 是\n"
        "不同 enum class 不能直接比较: 编译期拒绝\n");
}

} // namespace
