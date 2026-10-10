// 情境：重复的 switch。按「形状种类」分支的 switch 在 area() 和 name() 里各出现一次，
// 每加一种形状，就要找遍所有 switch 一起改（漏一处就是 bug）。
// 重构手法：以多态取代条件表达式（Replace Conditional with Polymorphism，《重构》第 2 版）。
//
// 实验：
// 1. 把 Shape 改成抽象基类（纯虚函数 area()、name()），每种形状一个子类：Circle、Square。
// 2. 新需求：加一种等边三角形 Triangle（边长 a，面积 = sqrt(3)/4 * a * a）。
// 3. 删掉 main 里的旧循环，解开 TODO(实验) 那段新驱动代码。达标时会输出 Triangle area=1.73。
// 改造后再加形状只需新增一个子类，不用再找 switch。
#include <cmath>
#include <iomanip>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

enum class ShapeKind { Circle, Square };

struct Shape {
    ShapeKind kind;
    double size;   // 圆是半径，正方形是边长
};

double area(const Shape& s) {
    switch (s.kind) {
    case ShapeKind::Circle: return 3.14159265 * s.size * s.size;
    case ShapeKind::Square: return s.size * s.size;
    }
    return 0;
}

std::string name(const Shape& s) {
    switch (s.kind) {
    case ShapeKind::Circle: return "Circle";
    case ShapeKind::Square: return "Square";
    }
    return "?";
}

int main() {
    std::cout << std::fixed << std::setprecision(2);
    std::vector<Shape> shapes{{ShapeKind::Circle, 1.0}, {ShapeKind::Square, 2.0}};
    for (const auto& s : shapes) std::cout << name(s) << " area=" << area(s) << "\n";

    // TODO(实验)：改造完成后删掉上面两行，解开下面这段
    // std::vector<std::unique_ptr<Shape>> shapes;
    // shapes.push_back(std::make_unique<Circle>(1.0));
    // shapes.push_back(std::make_unique<Square>(2.0));
    // shapes.push_back(std::make_unique<Triangle>(2.0));
    // for (const auto& s : shapes) std::cout << s->name() << " area=" << s->area() << "\n";
}
