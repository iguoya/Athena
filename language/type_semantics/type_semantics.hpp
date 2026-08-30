#pragma once

#include <ostream>
#include <string>
#include <type_traits>
#include <utility>

using namespace std;

namespace {

const char* yes_no(bool value) { return value ? "是" : "否"; }

class ExplicitNumber {
public:
    explicit ExplicitNumber(int value) : m_value(value) {}
    int value() const { return m_value; }

private:
    int m_value;
};

const char* binding(string&) { return "string&"; }
const char* binding(const string&) { return "const string&"; }
const char* binding(string&&) { return "string&&"; }

class CastBase {
public:
    virtual ~CastBase() = default;
};

class CastDerived final : public CastBase {};

enum class TrafficLight : unsigned char {
    red = 1,
    yellow = 2,
    green = 3,
};

enum class FileState : unsigned char {
    closed,
    open,
};

} // namespace

// 第一章实验。正文负责解释规则和形成判断，下面每个短实验只制造一个
// 可观察对照；编译期错误保留为注释，运行路径不包含未定义行为。
class TypeSemantics {
public:
    void initialization(ostream& output) const {
        int direct(7);
        int copied = 8;
        int listed{9};
        int zero{};

        double source = 3.75;
        int narrowed(source);
        // int rejected{source}; // 列表初始化在编译期拒绝窄化。

        ExplicitNumber explicit_number{11};
        // ExplicitNumber hidden = 11; // 拷贝初始化不能隐式使用 explicit。

        [[maybe_unused]] int uninitialized;
        output << "四种初始化: " << direct << ", " << copied << ", "
               << listed << ", " << zero << '\n';
        output << "圆括号接受窄化: " << source << " -> " << narrowed << '\n';
        output << "花括号拒绝窄化: 编译期错误\n";
        output << "explicit 需要显式进入: " << explicit_number.value() << '\n';
        output << "未初始化局部 int: 不读取\n";
    }

    void auto_deduction(ostream& output) const {
        int original = 42;
        int& reference = original;

        auto copy = reference;
        copy = 7;
        auto& alias = reference;
        alias = 99;

        pair record{string("Athena"), 5};
        auto [copied_name, copied_score] = record;
        copied_score = 8;
        auto& [name_alias, score_alias] = record;
        score_alias = 9;

        output << "auto 副本 / 原对象: " << copy << " / " << original << '\n';
        output << "auto& 修改原对象: " << original << '\n';
        output << "结构化绑定副本 / 原值: " << copied_name << ' ' << copied_score
               << " / " << record.first << ' ' << record.second << '\n';
        output << "结构化绑定引用共享对象: " << name_alias << ' ' << score_alias
               << '\n';
    }

    void decltype_deduction(ostream& output) const {
        int value = 7;

        const bool name_is_int = is_same_v<decltype(value), int>;
        const bool expression_is_lvalue_reference =
            is_same_v<decltype((value)), int&>;
        const bool moved_is_rvalue_reference =
            is_same_v<decltype(std::move(value)), int&&>;

        output << "decltype(value) 是 int: " << yes_no(name_is_int) << '\n';
        output << "decltype((value)) 是 int&: "
               << yes_no(expression_is_lvalue_reference) << '\n';
        output << "decltype(std::move(value)) 是 int&&: "
               << yes_no(moved_is_rvalue_reference) << '\n';
    }

    void value_category(ostream& output) const {
        string named = "Athena";
        const string readonly = "read only";

        output << "具名对象选择: " << binding(named) << '\n';
        output << "const 具名对象选择: " << binding(readonly) << '\n';
        output << "临时对象选择: " << binding(string("temporary")) << '\n';
        output << "std::move(named) 选择: " << binding(std::move(named)) << '\n';
        output << "没有接收者时原内容仍是: " << named << '\n';
    }

    void cast(ostream& output) const {
        const double fractional = 9.8;
        const int whole = static_cast<int>(fractional);

        CastDerived derived;
        CastBase* polymorphic = &derived;
        auto* matched = dynamic_cast<CastDerived*>(polymorphic);
        CastBase plain_base;
        auto* rejected = dynamic_cast<CastDerived*>(&plain_base);

        int mutable_value = 7;
        const int& readonly_view = mutable_value;
        int& writable_view = const_cast<int&>(readonly_view);
        writable_view = 9;

        auto* bytes = reinterpret_cast<unsigned char*>(&mutable_value);
        auto* restored = reinterpret_cast<int*>(bytes);

        output << "static_cast 明确接受截断: " << whole << '\n';
        output << "dynamic_cast 成功 / 失败为空: " << yes_no(matched != nullptr)
               << " / " << yes_no(rejected == nullptr) << '\n';
        output << "const_cast 修改原本可写对象: " << mutable_value << '\n';
        output << "reinterpret_cast 只验证指针往返: "
               << yes_no(restored == &mutable_value) << '\n';
    }

    void enum_class(ostream& output) const {
        const TrafficLight light = TrafficLight::green;
        [[maybe_unused]] const FileState state = FileState::open;
        // bool same = light == state; // 不同 enum class 不能直接比较。

        output << "成员必须带作用域: TrafficLight::green\n";
        output << "可隐式转换为 int: "
               << yes_no(is_convertible_v<TrafficLight, int>) << '\n';
        output << "显式取得底层值: " << static_cast<int>(light) << '\n';
        output << "底层类型是 unsigned char: "
               << yes_no(is_same_v<underlying_type_t<TrafficLight>, unsigned char>)
               << '\n';
        output << "不同枚举直接比较: 编译期错误\n";
    }
};
