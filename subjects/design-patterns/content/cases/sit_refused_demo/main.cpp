// 情境：拒绝遗赠。ReadOnlyDoc 继承了 Doc，却不要 write()——只好一调用就抛异常。
// 所有拿着 Doc* 的代码都得提防「这个 Doc 其实写不了」，类型系统没帮上任何忙。
// 重构手法：下移方法（Push Down Method）、以委托取代超类（Replace Superclass with Delegate）；
// 在 C++ 里更常见的做法是把「读」「写」拆成两个窄接口，各类只实现自己真有的能力。
// 《重构》第 2 版第 3 章「拒绝遗赠」；关联原则：里氏替换（LSP）、接口隔离（ISP）。
//
// 实验：
// 1. 把 Doc 拆成 Readable（read()）与 Writable（write()）两个接口；
//    WritableDoc 实现两者，ReadOnlyDoc 只实现 Readable，不再有会抛异常的 write()。
// 2. saveAll 的参数改为 std::vector<Writable*>，删掉 try/catch。
// 3. 解开 main 里的 TODO(实验) 行：readers 有 2 个、writers 只有 1 个。
//    注释里那行把 pdf 放进 writers 的代码应当编译不过——这就是「拒绝」被类型挡在门外。
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

class Doc {
public:
    virtual ~Doc() = default;
    virtual std::string name() const = 0;
    virtual std::string read() const = 0;
    virtual void write(const std::string& text) = 0;
};

class WritableDoc : public Doc {
public:
    explicit WritableDoc(std::string n) : name_(std::move(n)) {}
    std::string name() const override { return name_; }
    std::string read() const override { return text_; }
    void write(const std::string& text) override { text_ = text; }
private:
    std::string name_, text_;
};

class ReadOnlyDoc : public Doc {
public:
    explicit ReadOnlyDoc(std::string n) : name_(std::move(n)) {}
    std::string name() const override { return name_; }
    std::string read() const override { return "(pdf 内容)"; }
    void write(const std::string&) override { throw std::logic_error(name_ + " 只读"); }
private:
    std::string name_;
};

void saveAll(const std::vector<Doc*>& docs) {
    for (Doc* d : docs) {
        try {
            d->write("saved");
            std::cout << "saved: " << d->name() << "\n";
        } catch (const std::logic_error& e) {
            std::cout << "save failed: " << e.what() << "\n";
        }
    }
}

int main() {
    WritableDoc notes("notes");
    ReadOnlyDoc pdf("report.pdf");
    std::vector<Doc*> docs{&notes, &pdf};
    saveAll(docs);
    for (Doc* d : docs) std::cout << "read: " << d->name() << "\n";
    // TODO(实验)：拆好接口后，解开下面几行（并确认把 pdf 放进 writers 会编译失败）
    // std::vector<Readable*> readers{&notes, &pdf};
    // std::vector<Writable*> writers{&notes};
    // // writers.push_back(&pdf);   // 应当编译不过
    // std::cout << "typed: readers=" << readers.size() << " writers=" << writers.size() << "\n";
}
