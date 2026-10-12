// 桥接：把抽象部分（形状）与实现部分（渲染方式）分离，两边各自扩展。
// 实验：已有 Circle 与两种渲染器。补 TODO：新增 Square（边长 3，用 4 次 line 画出），
// 并在 main 里分别交给两种渲染器画——Renderer 一侧一行不改。
// 对比：不用桥接的话，2 种形状 × 2 种渲染要写 4 个子类，再加一种渲染就是 6 个。
#include <iostream>

// Implementor：只提供基本操作
class Renderer {
public:
    virtual ~Renderer() = default;
    virtual void circle(int r) = 0;
    virtual void line(int len) = 0;
};
class VectorRenderer : public Renderer {
public:
    void circle(int r) override { std::cout << "[vector] circle " << r << "\n"; }
    void line(int len) override { std::cout << "[vector] line " << len << "\n"; }
};
class RasterRenderer : public Renderer {
public:
    void circle(int r) override { std::cout << "[raster] circle " << r << "\n"; }
    void line(int len) override { std::cout << "[raster] line " << len << "\n"; }
};

// Abstraction：维护一个指向 Implementor 的引用，用基本操作拼出高层操作
class Shape {
public:
    explicit Shape(Renderer& r) : renderer_(r) {}
    virtual ~Shape() = default;
    virtual void draw() = 0;
protected:
    Renderer& renderer_;
};

// RefinedAbstraction
class Circle : public Shape {
public:
    Circle(Renderer& r, int radius) : Shape(r), radius_(radius) {}
    void draw() override { renderer_.circle(radius_); }
private:
    int radius_;
};

// TODO(实验)：在这里新增 Square，draw() 调 4 次 renderer_.line(side_)

int main() {
    VectorRenderer vec;
    RasterRenderer ras;
    Circle c1(vec, 5), c2(ras, 5);
    c1.draw();
    c2.draw();
    // TODO(实验)：Square s1(vec, 3), s2(ras, 3); s1.draw(); s2.draw();
}
