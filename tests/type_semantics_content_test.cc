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
        "四种初始化: 7, 8, 9, 0\n"
        "值初始化 int{} 确定为: 0\n"
        "圆括号接受窄化: 3.75 -> 3\n"
        "花括号拒绝窄化: 编译期错误\n"
        "explicit 需要显式进入: 11\n");
}

TEST(TypeSemanticsContentTest, ShowsWhenObjectsBeginAndEnd) {
    EXPECT_EQ(
        run_experiment(&TypeSemantics::object_lifetime),
        "构造 块内对象\n"
        "块内: 块内对象仍然有效\n"
        "析构 块内对象\n"
        "构造 语句里的临时对象\n"
        "析构 语句里的临时对象\n"
        "临时对象在这条语句的分号处就已经结束\n"
        "构造 被 const 引用延长的临时对象\n"
        "延长之后仍然读得到: 被 const 引用延长的临时对象\n"
        "函数返回前，kept 绑定的那个临时对象才析构\n"
        "析构 被 const 引用延长的临时对象\n");
}

TEST(TypeSemanticsContentTest, ShowsAutoBehaviorThroughObservableMutation) {
    EXPECT_EQ(
        run_experiment(&TypeSemantics::auto_deduction),
        "auto 副本 / 原对象: 7 / 99\n"
        "auto& 修改原对象: 99\n"
        "const auto& 只读别名读到当前值: 99\n"
        "auto 丢弃顶层 const，副本可改: 2\n"
        "结构化绑定副本 / 原值: Athena 8 / Athena 9\n"
        "结构化绑定引用共享对象: Athena 9\n");
}

TEST(TypeSemanticsContentTest, ShowsWhichValueCategoryDecltypePreserves) {
    EXPECT_EQ(
        run_experiment(&TypeSemantics::decltype_deduction),
        "decltype(value) 是 int（取声明类型）: 是\n"
        "decltype((value)) 是 int&（左值表达式）: 是\n"
        "decltype(std::move(value)) 是 int&&（将亡值）: 是\n"
        "decltype(value + 0) 是 int（纯右值不加引用）: 是\n");
}

TEST(TypeSemanticsContentTest, SelectsReferenceBindingsFromValueCategories) {
    EXPECT_EQ(
        run_experiment(&TypeSemantics::value_category),
        "具名对象选择: string&\n"
        "const 具名对象选择: const string&\n"
        "临时对象选择: string&&\n"
        "std::move(named) 选择: string&&\n"
        "没有接收者时原内容仍是: Athena\n");
}

TEST(TypeSemanticsContentTest, DemonstratesTheBoundariesOfNamedCasts) {
    EXPECT_EQ(
        run_experiment(&TypeSemantics::cast),
        "static_cast 明确接受截断: 9\n"
        "dynamic_cast 成功 / 失败为空: 是 / 是\n"
        "const_cast 修改原本可写对象: 9\n"
        "reinterpret_cast 指针往返后仍相等: 是\n"
        "但往返相等不证明按其它类型解读一直安全\n");
}

TEST(TypeSemanticsContentTest, KeepsScopedEnumsTypeSafe) {
    EXPECT_EQ(
        run_experiment(&TypeSemantics::enum_class),
        "成员必须带作用域: TrafficLight::green\n"
        "可隐式转换为 int: 否\n"
        "显式取得底层值: 3\n"
        "底层类型是 unsigned char: 是\n"
        "不同枚举直接比较: 编译期错误\n");
}

} // namespace
