// 情境：不相关的类型，却要一起当“能 draw 的东西”用。Circle、Square、Triangle 来自三个互不相识的
// 第三方库，都有 std::string draw() const，但没有共同基类，源码也改不了。想按放入的顺序
// 统一处理它们，现在只能为每种类型各存一个 vector，顺序全丢了。
// 组织手段：类型擦除（type erasure）——外面一个值语义的包装类，里面藏一个“概念接口 + 模板模型”：
// 任何有 draw() 的类型都能装进去，不必继承任何东西。std::function、std::any 就是这样实现的。
// 依据：cppreference 对 std::function / std::any 的描述；More C++ Idioms「Type Erasure」
// 与「Polymorphic Value Types」；Sean Parent 的演讲《Value Semantics and Concepts-based Polymorphism》。
//
// 实验：
// 1. 写 class Drawable：内部 struct Concept { virtual ~Concept() = default; virtual std::string draw() const = 0; }；
//    template <typename T> struct Model : Concept { T value; std::string draw() const override { return value.draw(); } }；
//    持有 std::unique_ptr<Concept>；提供模板构造函数 template <typename T> Drawable(T x)，
//    和 std::string draw() const。（Drawable 只需可移动，不必可拷贝。）
// 2. 在 main 里把 Circle、Square、Circle、Triangle 按顺序放进同一个 std::vector<Drawable>，
//    依次调用 draw() 并用逗号连接。解开 TODO(实验) 行。
//    达标时输出 order: circle,square,circle,triangle。往里再放一种新类型，Drawable 本身一行不改。
#include <iostream>
#include <memory>
#include <string>
#include <vector>

// ---- 三个“第三方”类型：没有共同基类，不许修改 ----
struct Circle   { std::string draw() const { return "circle"; } };
struct Square   { std::string draw() const { return "square"; } };
struct Triangle { std::string draw() const { return "triangle"; } };

int main() {
    // 现状：每种类型一个容器，放入的先后顺序丢了
    std::vector<Circle> circles(2);
    std::vector<Square> squares(1);
    std::string out;
    for (const auto& c : circles) out += c.draw() + ",";
    for (const auto& s : squares) out += s.draw() + ",";
    std::cout << "by type: " << out << "\n";
    Triangle t;
    (void)t;
    // TODO(实验)：写好 Drawable 后，解开下面几行
    // std::vector<Drawable> shapes;
    // shapes.push_back(Circle{});
    // shapes.push_back(Square{});
    // shapes.push_back(Circle{});
    // shapes.push_back(Triangle{});
    // std::string order;
    // for (const auto& s : shapes) order += (order.empty() ? "" : ",") + s.draw();
    // std::cout << "order: " << order << "\n";
}
