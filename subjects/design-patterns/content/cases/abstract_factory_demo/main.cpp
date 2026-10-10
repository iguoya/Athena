// 抽象工厂：一个工厂接口创建一整族配套产品。
// 实验：运行观察 Factory1 造出的 Win 系产品成套出现。然后给 AbstractFactory
// 加一个 createCheckbox()——体会「加产品种类要改所有工厂接口」的代价。
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

int main() {
    WinFactory wf;
    auto b = wf.createButton();   auto t = wf.createTextBox();   // 同族成套
    b->paint(); t->paint();
}
