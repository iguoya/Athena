// 原型：用 clone() 复制已有实例，而不是 new。
// 实验：先预测——改了克隆件的分数，原型的分数会不会跟着变？运行核对。
// score 用 shared_ptr 持有，下面的拷贝构造只复制指针（浅拷贝），两个对象共享同一个 int。
// 补 TODO：把拷贝构造改成深拷贝（为克隆件新分配一个 int），
// 让最后一行输出 proto score=90 after copy changed。
#include <iostream>
#include <memory>
#include <string>

class Resume {
public:
    explicit Resume(std::string name) : name(std::move(name)), score(std::make_shared<int>(90)) {}
    // TODO(实验)：浅拷贝——score 与原型指向同一块内存。改成深拷贝。
    Resume(const Resume& other) : name(other.name), score(other.score) {}
    std::unique_ptr<Resume> clone() const { return std::make_unique<Resume>(*this); }
    void rename(std::string n) { name = std::move(n); }
    void setScore(int s) { *score = s; }
    int getScore() const { return *score; }
    void show() const { std::cout << name << " @" << this << " score=" << *score << " (int@" << score.get() << ")\n"; }
private:
    std::string name;
    std::shared_ptr<int> score;
};

int main() {
    Resume proto("proto");
    auto copy = proto.clone();   // 客户端不 new Resume，而是让原型复制自己
    copy->rename("copy");
    proto.show(); copy->show();
    copy->setScore(59);          // 改克隆件的分，不应影响原型
    proto.show(); copy->show();
    std::cout << "proto score=" << proto.getScore() << " after copy changed\n";
}
