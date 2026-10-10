// 抽象工厂：一个工厂接口创建一整族配套产品。
// 实验：render() 只认 WidgetFactory 抽象，造出来的按钮和文本框必然同族。
// 补 TODO：在 main 里加一行，让界面再用 Mac 风格画一遍——只换传进去的工厂，
// render() 一行不改。做完再想：要加 createCheckbox() 的话，哪些类都得改？
#include <iostream>
#include <memory>

class Button { public: virtual ~Button() = default; virtual void paint() = 0; };
class TextBox { public: virtual ~TextBox() = default; virtual void paint() = 0; };
class WinButton : public Button { public: void paint() override { std::cout << "[Win button]\n"; } };
class WinTextBox : public TextBox { public: void paint() override { std::cout << "[Win textbox]\n"; } };
class MacButton : public Button { public: void paint() override { std::cout << "[Mac button]\n"; } };
class MacTextBox : public TextBox { public: void paint() override { std::cout << "[Mac textbox]\n"; } };

class WidgetFactory {
public:
    virtual ~WidgetFactory() = default;
    virtual std::unique_ptr<Button> createButton() const = 0;
    virtual std::unique_ptr<TextBox> createTextBox() const = 0;
};
class WinFactory : public WidgetFactory {
public:
    std::unique_ptr<Button> createButton() const override { return std::make_unique<WinButton>(); }
    std::unique_ptr<TextBox> createTextBox() const override { return std::make_unique<WinTextBox>(); }
};
class MacFactory : public WidgetFactory {
public:
    std::unique_ptr<Button> createButton() const override { return std::make_unique<MacButton>(); }
    std::unique_ptr<TextBox> createTextBox() const override { return std::make_unique<MacTextBox>(); }
};

// 客户端只依赖抽象工厂与抽象产品：想混搭两族，在这里根本写不出来
void render(const WidgetFactory& f) {
    auto b = f.createButton();
    auto t = f.createTextBox();
    b->paint(); t->paint();
}

int main() {
    render(WinFactory{});
    // TODO(实验)：加一行，用 Mac 风格再画一遍
}
