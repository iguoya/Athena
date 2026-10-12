// 组合：把对象组合成树形结构表示「部分-整体」，客户统一对待单个对象与组合对象。
// 实验：File 是叶子，Directory 是组合。先预测：目录的大小该怎么算？
// 补 TODO：Directory::size() 返回所有子节点 size() 之和——注意它不需要知道子节点
// 是文件还是目录，这就是「统一对待」。达标时最后一行是 total size: 1750。
#include <iostream>
#include <memory>
#include <string>
#include <vector>

// Component：叶子与组合共用的接口
class Node {
public:
    explicit Node(std::string name) : name_(std::move(name)) {}
    virtual ~Node() = default;
    virtual int size() const = 0;
    virtual void print(int indent) const = 0;
protected:
    std::string name_;
};

// Leaf
class File : public Node {
public:
    File(std::string name, int bytes) : Node(std::move(name)), bytes_(bytes) {}
    int size() const override { return bytes_; }
    void print(int indent) const override {
        std::cout << std::string(indent, ' ') << name_ << " (" << size() << ")\n";
    }
private:
    int bytes_;
};

// Composite：存储子组件，并实现与子组件有关的操作
class Directory : public Node {
public:
    explicit Directory(std::string name) : Node(std::move(name)) {}
    Directory& add(std::unique_ptr<Node> child) {
        children_.push_back(std::move(child));
        return *this;
    }
    int size() const override {
        // TODO(实验)：返回所有 children_ 的 size() 之和
        return 0;
    }
    void print(int indent) const override {
        std::cout << std::string(indent, ' ') << name_ << "/ (" << size() << ")\n";
        for (const auto& c : children_) c->print(indent + 2);
    }
private:
    std::vector<std::unique_ptr<Node>> children_;
};

int main() {
    auto src = std::make_unique<Directory>("src");
    src->add(std::make_unique<File>("main.cpp", 1200)).add(std::make_unique<File>("util.hpp", 300));
    auto docs = std::make_unique<Directory>("docs");
    docs->add(std::make_unique<File>("guide.md", 150));

    Directory root("project");
    root.add(std::make_unique<File>("readme.md", 100)).add(std::move(src)).add(std::move(docs));

    root.print(0);
    const Node& asNode = root;   // 客户只拿着 Component 接口
    std::cout << "total size: " << asNode.size() << "\n";
}
