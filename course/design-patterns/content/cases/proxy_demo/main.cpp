// 代理（虚代理）：为其他对象提供一种代理以控制对它的访问，这里控制的是「何时创建」。
// 实验：RealImage 构造时就要从磁盘加载，开销很大。ImageProxy 与它实现同一接口。
// 现在的代理每次 display() 都新建一个 RealImage，加载了两次。
// 补 TODO：只在第一次 display() 时创建 RealImage 并缓存，之后直接转发——加载次数变成 1。
#include <iostream>
#include <memory>
#include <string>

// Subject
class Image {
public:
    virtual ~Image() = default;
    virtual void display() = 0;
};

// RealSubject：真正干活、创建开销大的对象
class RealImage : public Image {
public:
    explicit RealImage(std::string file) : file_(std::move(file)) {
        ++loads;
        std::cout << "loading " << file_ << " from disk\n";
    }
    void display() override { std::cout << "display " << file_ << "\n"; }
    static int loads;
private:
    std::string file_;
};
int RealImage::loads = 0;

// Proxy：与 RealSubject 同接口，控制对它的访问
class ImageProxy : public Image {
public:
    explicit ImageProxy(std::string file) : file_(std::move(file)) {}
    void display() override {
        // TODO(实验)：real_ 为空时才创建，之后复用；再把请求转发给 real_
        RealImage tmp(file_);
        tmp.display();
    }
private:
    std::string file_;
    std::unique_ptr<RealImage> real_;
};

int main() {
    ImageProxy photo("photo.png");
    std::cout << "proxy created, nothing loaded yet\n";
    photo.display();
    photo.display();
    std::cout << "loads: " << RealImage::loads << "\n";
}
