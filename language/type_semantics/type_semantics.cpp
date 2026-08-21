#include "type_semantics.hpp"

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

const char* reference_binding(string&) { return "可修改左值引用"; }
const char* reference_binding(const string&) { return "const 左值引用"; }
const char* reference_binding(string&&) { return "右值引用"; }

class CastBase {
public:
    virtual ~CastBase() = default;
};

class CastDerived final : public CastBase {
public:
    int marker = 42;
};

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

void TypeSemantics::initialization(ostream& output) const {
    int direct(7);
    int copied = 8;
    int listed{9};
    int zero{};

    double fractional = 3.75;
    int truncated(fractional);
    // int rejected{fractional}; // 编译错误：列表初始化拒绝窄化转换。

    ExplicitNumber explicit_number(11);
    // ExplicitNumber rejected_copy = 11; // explicit 构造函数不能隐式调用。

    [[maybe_unused]] int not_initialized;

    output << "直接初始化 int direct(7): " << direct << '\n';
    output << "拷贝初始化 int copied = 8: " << copied << '\n';
    output << "列表初始化 int listed{9}: " << listed << '\n';
    output << "值初始化 int zero{}: " << zero << '\n';
    output << "直接初始化允许 double 到 int 的窄化结果: " << truncated << '\n';
    output << "列表初始化 int rejected{fractional}: 编译期拒绝窄化\n";
    output << "explicit 构造函数可直接初始化: " << explicit_number.value() << '\n';
    output << "默认初始化的局部 int: 不读取，避免未定义行为\n";
}

void TypeSemantics::type_deduction(ostream& output) const {
    const int original = 42;
    const int& reference = original;

    auto copied = reference;
    auto& alias = reference;
    decltype(reference) exact_reference = original;

    int mutable_value = 7;
    auto [name, score] = pair{string("Athena"), 5};

    output << "auto 按值推导得到 int: "
           << yes_no(is_same_v<decltype(copied), int>) << '\n';
    output << "auto& 保留 const 引用: "
           << yes_no(is_same_v<decltype(alias), const int&>) << '\n';
    output << "decltype(变量名) 保留声明类型: "
           << yes_no(is_same_v<decltype(exact_reference), const int&>) << '\n';
    output << "decltype((左值表达式)) 得到引用: "
           << yes_no(is_same_v<decltype((mutable_value)), int&>) << '\n';
    output << "decltype(std::move(value)) 得到右值引用: "
           << yes_no(is_same_v<decltype(std::move(mutable_value)), int&&>) << '\n';
    output << "结构化绑定拆出的值: " << name << "，" << score << '\n';
}

void TypeSemantics::value_category(ostream& output) const {
    string named = "Athena";
    const string readonly = "只读对象";

    output << "具名对象 named: 左值\n";
    output << "临时对象 string(\"临时值\"): 纯右值\n";
    output << "std::move(named): 将亡值\n";
    output << "具名对象匹配: " << reference_binding(named) << '\n';
    output << "具名 const 对象匹配: " << reference_binding(readonly) << '\n';
    output << "临时对象匹配: " << reference_binding(string("临时值")) << '\n';
    output << "将亡值匹配: " << reference_binding(std::move(named)) << '\n';
    output << "std::move 只改变值类别，原内容仍为: " << named << '\n';
}

void TypeSemantics::cast(ostream& output) const {
    const double fractional = 9.8;
    const int whole = static_cast<int>(fractional);

    CastDerived derived;
    CastBase* base = &derived;
    CastDerived* checked = dynamic_cast<CastDerived*>(base);

    CastBase plain_base;
    CastDerived* rejected = dynamic_cast<CastDerived*>(&plain_base);

    int mutable_value = 7;
    const int& readonly_view = mutable_value;
    int& writable_view = const_cast<int&>(readonly_view);
    writable_view = 9;

    auto* bytes = reinterpret_cast<unsigned char*>(&mutable_value);
    auto* restored = reinterpret_cast<int*>(bytes);

    output << "static_cast 明确数值转换 9.8 -> " << whole << '\n';
    output << "dynamic_cast 匹配真实派生类型: " << yes_no(checked != nullptr)
           << '\n';
    output << "dynamic_cast 不匹配时返回空: " << yes_no(rejected == nullptr)
           << '\n';
    output << "const_cast 修改原本非 const 的对象: " << mutable_value << '\n';
    output << "reinterpret_cast 指针往返仍指向原对象: "
           << yes_no(restored == &mutable_value) << '\n';
}

void TypeSemantics::enum_class(ostream& output) const {
    const TrafficLight light = TrafficLight::green;

    output << "枚举成员使用作用域: TrafficLight::green\n";
    output << "可隐式转换为 int: "
           << yes_no(is_convertible_v<TrafficLight, int>) << '\n';
    output << "显式转换后的底层值: " << static_cast<int>(light) << '\n';
    output << "底层类型是 unsigned char: "
           << yes_no(is_same_v<underlying_type_t<TrafficLight>, unsigned char>)
           << '\n';
    output << "不同 enum class 不能直接比较: 编译期拒绝\n";

    [[maybe_unused]] const FileState state = FileState::open;
    // bool same = light == state; // 编译错误：两个枚举是不同类型。
}
