// 装饰：动态地给一个对象添加额外的职责，装饰器与被装饰者实现同一个接口。
// 实验：已有 Bold 装饰器。补 TODO：仿照它写 Italic（把内容包进 <i>…</i>），
// 然后在 main 里叠两种顺序：Italic(Bold(text)) 与 Bold(Italic(text))。
// 先预测两行输出的区别——装饰是一层套一层的，顺序就是嵌套顺序。
#include <iostream>
#include <memory>
#include <string>

// Component
class Text {
public:
    virtual ~Text() = default;
    virtual std::string render() const = 0;
};

// ConcreteComponent
class PlainText : public Text {
public:
    explicit PlainText(std::string s) : s_(std::move(s)) {}
    std::string render() const override { return s_; }
private:
    std::string s_;
};

// Decorator：持有一个 Component，并实现同一接口
class TextDecorator : public Text {
public:
    explicit TextDecorator(std::unique_ptr<Text> inner) : inner_(std::move(inner)) {}
protected:
    std::unique_ptr<Text> inner_;
};

// ConcreteDecorator：在转发前后加上自己的职责
class Bold : public TextDecorator {
public:
    using TextDecorator::TextDecorator;
    std::string render() const override { return "<b>" + inner_->render() + "</b>"; }
};

// TODO(实验)：在这里新增 Italic

int main() {
    auto bold = std::make_unique<Bold>(std::make_unique<PlainText>("hello"));
    std::cout << bold->render() << "\n";
    // TODO(实验)：分别构造 Italic(Bold(PlainText)) 与 Bold(Italic(PlainText))，各输出一行 render()
}
