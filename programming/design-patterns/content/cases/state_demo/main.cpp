// 状态：允许一个对象在其内部状态改变时改变它的行为。
// 实验：文档发布流程 草稿 → 审核中 → 已发布，同一个 publish() 在不同状态下做不同的事。
// 草稿与已发布两个状态已写好。先预测：现在连按三次 publish，每次之后是什么状态？
// 补 TODO：实现 Moderation::publish()，输出 approved 并切换到 Published。
// 注意 Document 里没有任何 if/switch 判断状态——分支被拆进了各个状态类。
#include <iostream>
#include <memory>
#include <string>

class Document;

// State：封装与 Context 某个状态相关的行为
class State {
public:
    virtual ~State() = default;
    virtual void publish(Document& doc) = 0;
    virtual std::string name() const = 0;
};

// Context：对外提供接口，内部维护当前状态对象
class Document {
public:
    Document();
    void publish() {
        state_->publish(*this);
        // 状态对象在自己的方法里请求切换；等它返回后再替换，免得在成员函数里销毁自己
        if (next_) state_ = std::move(next_);
        std::cout << "state: " << state_->name() << "\n";
    }
    void changeState(std::unique_ptr<State> s) { next_ = std::move(s); }
private:
    std::unique_ptr<State> state_;
    std::unique_ptr<State> next_;
};

class Published : public State {
public:
    void publish(Document&) override { std::cout << "already published\n"; }
    std::string name() const override { return "Published"; }
};

class Moderation : public State {
public:
    void publish(Document& doc) override {
        // TODO(实验)：输出 approved，并切换到 Published（仿照 Draft::publish 的写法）
        (void)doc;
    }
    std::string name() const override { return "Moderation"; }
};

class Draft : public State {
public:
    void publish(Document& doc) override {
        std::cout << "submit for review\n";
        doc.changeState(std::make_unique<Moderation>());
    }
    std::string name() const override { return "Draft"; }
};

Document::Document() : state_(std::make_unique<Draft>()) {}

int main() {
    Document doc;
    doc.publish();
    doc.publish();
    doc.publish();
}
