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

// object_lifetime 用的探针：构造和析构各写一行，让"对象何时开始、何时结束"
// 变成可以直接读到的输出。拷贝被删除，避免把"多了一份对象"混进生命周期的观察。
class LifetimeProbe {
public:
    LifetimeProbe(string label, ostream& output)
        : m_label(std::move(label)), m_output(output) {
        m_output << "构造 " << m_label << '\n';
    }
    LifetimeProbe(const LifetimeProbe&) = delete;
    LifetimeProbe& operator=(const LifetimeProbe&) = delete;
    ~LifetimeProbe() { m_output << "析构 " << m_label << '\n'; }

    const string& label() const { return m_label; }

private:
    string m_label;
    ostream& m_output;
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

        // int uninitialized; 普通局部变量不会清零，先读后写是未定义行为，
        // 因此这里既不声明也不读取——错误只保留在编译期与注释里。
        output << "四种初始化: " << direct << ", " << copied << ", "
               << listed << ", " << zero << '\n';
        output << "值初始化 int{} 确定为: " << zero << '\n';
        output << "圆括号接受窄化: " << source << " -> " << narrowed << '\n';
        output << "花括号拒绝窄化: 编译期错误\n";
        output << "explicit 需要显式进入: " << explicit_number.value() << '\n';
    }

    void object_lifetime(ostream& output) const {
        {
            const LifetimeProbe scoped{"块内对象", output};
            output << "块内: " << scoped.label() << "仍然有效\n";
        } // 块结束，scoped 在这里析构

        LifetimeProbe{"语句里的临时对象", output};
        output << "临时对象在这条语句的分号处就已经结束\n";

        // const 引用绑定临时对象，把它的寿命延长到引用自己的作用域结束。
        const LifetimeProbe& kept = LifetimeProbe{"被 const 引用延长的临时对象", output};
        output << "延长之后仍然读得到: " << kept.label() << '\n';

        // const string& dangling = LifetimeProbe{"x", output}.label();
        // 上面这行只延长临时对象本身，不延长从它取出的成员引用：语句结束后
        // dangling 就悬垂了。悬垂是未定义行为，因此只写在注释里，不放进运行路径。

        output << "函数返回前，kept 绑定的那个临时对象才析构\n";
    }

    void auto_deduction(ostream& output) const {
        int original = 42;
        int& reference = original;

        auto copy = reference;
        copy = 7;
        auto& alias = reference;
        alias = 99;

        const auto& view = original;
        // view = 20; // const auto& 推出 const int&：
        // clang++ -std=c++20 报 "cannot assign to variable 'view' with
        // const-qualified type 'const int &'"。只读的是这条访问路径，
        // 不是 original 本身——它经 alias 改成 99 后，view 读到的就是 99。

        const int locked = 1;
        auto unlocked = locked; // auto 丢弃顶层 const，得到可写的新对象
        unlocked = 2;

        pair record{string("Athena"), 5};
        auto [copied_name, copied_score] = record;
        copied_score = 8;
        auto& [name_alias, score_alias] = record;
        score_alias = 9;

        output << "auto 副本 / 原对象: " << copy << " / " << original << '\n';
        output << "auto& 修改原对象: " << original << '\n';
        output << "const auto& 只读别名读到当前值: " << view << '\n';
        output << "auto 丢弃顶层 const，副本可改: " << unlocked << '\n';
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
        const bool prvalue_has_no_reference =
            is_same_v<decltype(value + 0), int>;

        output << "decltype(value) 是 int（取声明类型）: "
               << yes_no(name_is_int) << '\n';
        output << "decltype((value)) 是 int&（左值表达式）: "
               << yes_no(expression_is_lvalue_reference) << '\n';
        output << "decltype(std::move(value)) 是 int&&（将亡值）: "
               << yes_no(moved_is_rvalue_reference) << '\n';
        output << "decltype(value + 0) 是 int（纯右值不加引用）: "
               << yes_no(prvalue_has_no_reference) << '\n';
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
        // dynamic_cast 要求源类型多态；对没有虚函数的类型使用会编译错误。

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
        output << "reinterpret_cast 指针往返后仍相等: "
               << yes_no(restored == &mutable_value) << '\n';
        output << "但往返相等不证明按其它类型解读一直安全\n";
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
