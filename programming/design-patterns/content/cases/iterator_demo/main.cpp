// 迭代器：提供一种方法顺序访问一个聚合对象中的各个元素，而又不暴露该对象的内部表示。
// 实验：NameList 内部用数组存名字，客户只通过迭代器遍历（GoF 的 first/next/isDone/currentItem 四件套）。
// 正向迭代器已写好。补 TODO：实现 ReverseIterator 的四个方法，让 main 倒序打印。
// 客户代码 printAll() 一行不改——同一个聚合，换个迭代器就是另一种遍历。
#include <array>
#include <iostream>
#include <memory>
#include <string>

// Iterator：访问和遍历元素的接口
class Iterator {
public:
    virtual ~Iterator() = default;
    virtual void first() = 0;
    virtual void next() = 0;
    virtual bool isDone() const = 0;
    virtual const std::string& currentItem() const = 0;
};

// ConcreteAggregate：内部表示对客户隐藏
class NameList {
public:
    static constexpr int kSize = 3;
    std::unique_ptr<Iterator> createIterator() const;
    std::unique_ptr<Iterator> createReverseIterator() const;
    const std::string& at(int i) const { return names_[i]; }
private:
    std::array<std::string, kSize> names_{"alice", "bob", "carol"};
};

// ConcreteIterator：跟踪遍历的当前位置
class ForwardIterator : public Iterator {
public:
    explicit ForwardIterator(const NameList& l) : list_(l) {}
    void first() override { pos_ = 0; }
    void next() override { ++pos_; }
    bool isDone() const override { return pos_ >= NameList::kSize; }
    const std::string& currentItem() const override { return list_.at(pos_); }
private:
    const NameList& list_;
    int pos_ = 0;
};

class ReverseIterator : public Iterator {
public:
    explicit ReverseIterator(const NameList& l) : list_(l) {}
    // TODO(实验)：从最后一个元素开始，向前走到第一个为止
    void first() override {}
    void next() override {}
    bool isDone() const override { return true; }
    const std::string& currentItem() const override { return list_.at(0); }
private:
    const NameList& list_;
    int pos_ = 0;
};

std::unique_ptr<Iterator> NameList::createIterator() const { return std::make_unique<ForwardIterator>(*this); }
std::unique_ptr<Iterator> NameList::createReverseIterator() const { return std::make_unique<ReverseIterator>(*this); }

// Client：只认 Iterator 接口
void printAll(const char* label, Iterator& it) {
    std::cout << label << ":";
    for (it.first(); !it.isDone(); it.next()) std::cout << " " << it.currentItem();
    std::cout << "\n";
}

int main() {
    NameList list;
    auto fwd = list.createIterator();
    auto rev = list.createReverseIterator();
    printAll("forward", *fwd);
    printAll("reverse", *rev);
}
