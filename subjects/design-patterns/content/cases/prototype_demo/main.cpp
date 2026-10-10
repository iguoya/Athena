// 原型：用 clone() 复制已有实例，而不是 new。
// 实验：运行观察克隆件与原型值相同、地址不同。然后把 data 改回裸指针并让
// clone 只复制指针（浅拷贝）——运行观察两个对象共享同一块内存的坑，再改回深拷贝。
#include <iostream>
#include <memory>
#include <string>

class Resume {
public:
    explicit Resume(std::string name) : name(std::move(name)), score(std::make_unique<int>(90)) {}
    Resume(const Resume& other)                       // 深拷贝：内部状态一并复制
        : name(other.name), score(std::make_unique<int>(*other.score)) {}
    std::unique_ptr<Resume> clone() const { return std::make_unique<Resume>(*this); }
    void setScore(int s) { *score = s; }
    void show() const { std::cout << name << " @" << this << " score=" << *score << " (int@" << score.get() << ")\n"; }
private:
    std::string name;
    std::unique_ptr<int> score;
};

int main() {
    Resume proto("proto");
    Resume copy("copy");
    proto.show(); copy.show();
    copy.setScore(59);          // 改克隆件的分，不应影响原型
    proto.show(); copy.show();
}
