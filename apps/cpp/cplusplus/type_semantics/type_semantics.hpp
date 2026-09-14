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
        : text(std::move(label)), m_output(output) {
        m_output << "构造 " << text << '\n';
    }
    LifetimeProbe(const LifetimeProbe&) = delete;
    LifetimeProbe& operator=(const LifetimeProbe&) = delete;
    ~LifetimeProbe() { m_output << "析构 " << text << '\n'; }

    const string& label() const { return text; }

    // 故意公开，供实验直接绑定子对象；label() 则制造经函数返回引用的对照。
    string text;

private:
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
            // 三个对象依次构造：离开块时按相反顺序析构，这条顺序是确定的，
            // 不靠"看起来是这样"——输出里可以逐行对照。
            const LifetimeProbe first{"块内对象 a", output};
            const LifetimeProbe second{"块内对象 b", output};
            const LifetimeProbe third{"块内对象 c", output};
            output << "块内: " << first.label() << "、" << second.label()
                   << "、" << third.label() << " 都仍然有效\n";
        } // 块结束，三个对象按 c、b、a 的顺序析构

        LifetimeProbe{"语句里的临时对象", output};
        output << "临时对象在这条语句的分号处就已经结束\n";

        // const 引用绑定临时对象，把它的寿命延长到引用自己的作用域结束。
        const LifetimeProbe& kept = LifetimeProbe{"被 const 引用延长的临时对象", output};
        output << "延长之后仍然读得到: " << kept.label() << '\n';

        {
            const string& kept_subobject =
                LifetimeProbe{"直接绑定子对象的临时对象", output}.text;
            output << "直接绑定子对象后仍然读得到: " << kept_subobject << '\n';
        }

        // label() 返回成员的引用，但这条引用绑定到的是函数返回值；外层临时
        // 对象仍在分号处析构。形成悬垂引用本身不是未定义行为，访问它才是。
        [[maybe_unused]] const string& dangling =
            LifetimeProbe{"经成员函数返回引用的临时对象", output}.label();
        output << "临时对象已经析构；不读取已经悬垂的引用 dangling\n";

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
        int value = 42;

        // 名字规则与表达式规则的差别不停留在类型名上：一个声明出独立副本，
        // 另一个声明出别名，赋值落到哪里是能直接看见的。
        decltype(value) copy = value;    // int：未加括号的名字取声明类型
        decltype((value)) alias = value; // int&：(value) 是左值表达式
        copy = 7;
        output << "copy = 7 之后 value = " << value
               << "（decltype(value) 是 int，改的是副本）\n";
        alias = 99;
        output << "alias = 99 之后 value = " << value
               << "（decltype((value)) 是 int&，改的是 value 本身）\n";

        // 同一个 const 引用，auto 和 decltype 给出不同的回答。
        const int fixed = 7;
        const int& ref = fixed;
        auto copied = ref;          // int：引用与顶层 const 都被丢掉
        decltype(ref) kept = fixed; // const int&：原样保留
        copied = 8;
        // kept = 8; // decltype(ref) 推出 const int&：clang++ -std=c++20 报
        // "cannot assign to variable 'kept' with const-qualified type
        // 'const int &'"。这条路径只读，是编译期就被拒绝的写法。
        output << "auto 从 const int& 推出可写的 int 副本: " << copied
               << "，decltype(ref) 仍是 const int&: "
               << yes_no(is_same_v<decltype(kept), const int&>) << '\n';

        // 表达式规则用引用类型编码值类别。
        output << "decltype(std::move(value)) 是 int&&（将亡值）: "
               << yes_no(is_same_v<decltype(std::move(value)), int&&>) << '\n';
        output << "decltype(value + 0) 是 int（纯右值不加引用）: "
               << yes_no(is_same_v<decltype(value + 0), int>) << '\n';

        // 不求值语境：取类型不会执行里面的表达式，计数器不会前进。
        int call_count = 0;
        auto next_id = [&call_count]() { return ++call_count; };
        decltype(next_id()) id = 0;
        output << "decltype(next_id()) 取到类型 int（id = " << id
               << "），但 next_id 的调用次数仍是 " << call_count << '\n';
    }

    void value_category(ostream& output) const {
        string named = "Athena";
        const string readonly = "read only";

        output << "具名对象选择: " << binding(named) << '\n';
        output << "const 具名对象选择: " << binding(readonly) << '\n';
        output << "临时对象选择: " << binding(string("temporary")) << '\n';
        output << "std::move(named) 选择: " << binding(std::move(named)) << '\n';
        output << "没有接收者时原内容仍是: " << named << '\n';

        // 「类型是右值引用」不等于「表达式是右值」：r 有名字、能取地址，
        // 所以表达式 r 是左值。转发时漏掉这一步，右值身份就在这里丢了。
        string&& moved_ref = std::move(named);
        output << "具名的右值引用传出去: " << binding(moved_ref)
               << "（表达式 r 是左值）\n";
        output << "再写一次 std::move 才是右值: "
               << binding(std::move(moved_ref)) << '\n';
    }

    void cast(ostream& output) const {
        // 先看不用写就会发生的那一类：代码里没有任何转换的痕迹，值却变了。
        const int negative = -1;
        const unsigned int positive = 1u;
        output << "有符号与无符号比较 -1 < 1u: " << yes_no(negative < positive)
               << "（比较前 -1 被转成极大的无符号数）\n";

        const int too_large = 300;
        output << "范围放不下时高位被丢掉: 300 -> "
               << static_cast<int>(static_cast<unsigned char>(too_large))
               << "（转换本身良定义：无符号按 2^N 取模，C++20 起有符号同样"
                  "按同余取值；未定义的是算术溢出，如 INT_MAX + 1）\n";

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
        // 先看裸整数放行了什么——不先看见这个，就不知道独立类型挡住的是什么。
        const int closed_flag = 0;
        const int open_flag = 1;
        const int red_light = 1; // 另一组常量，值恰好和 open_flag 相同
        const int loose_state = 42;

        output << "裸整数取组外的值: " << loose_state << "（编译器不过问）\n";
        output << "裸整数之间可以相加: " << (closed_flag + open_flag)
               << "（相加没有意义）\n";
        output << "两组无关常量能直接比较: " << yes_no(open_flag == red_light)
               << "（红灯和“已打开”被判为相等）\n";

        const TrafficLight light = TrafficLight::green;
        [[maybe_unused]] const FileState state = FileState::open;
        // FileState wrong = 42;      // 编译期错误：整数不会隐式变成状态。
        // auto sum = light + light;  // 编译期错误：状态之间没有算术。
        // bool same = light == state; // 编译期错误：不同枚举不能直接比较。

        output << "换成作用域枚举后，上面三件事都编译不过\n";
        output << "可隐式转换为 int: "
               << yes_no(is_convertible_v<TrafficLight, int>) << '\n';
        output << "显式取得底层值: " << static_cast<int>(light) << '\n';

        // 它挡的是意外的隐式转换，不是你自己写下的显式转换。
        const auto forced = static_cast<FileState>(42);
        output << "显式转换仍能造出列表外的值: " << static_cast<int>(forced)
               << "（不在 closed / open 之列）\n";
    }
};
