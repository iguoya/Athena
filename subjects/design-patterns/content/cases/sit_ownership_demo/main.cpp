// 情境：所有权不清。makeWidget() 返回裸指针，看签名根本不知道调用者要不要 delete；
// Panel 里存了一组裸指针，析构时也不知道该不该释放——结果谁都没释放。
// 组织手段：用类型表达所有权——独占用 std::unique_ptr，确实要共享才用 std::shared_ptr，
// 裸指针与引用只表示「借用」。
// 规范：C++ Core Guidelines R.20「用 unique_ptr 或 shared_ptr 表示所有权」、
// R.21「除非需要共享，优先 unique_ptr」、R.3「裸指针不拥有」、I.11「不要用裸指针转移所有权」、
// R.11「避免显式调用 new 和 delete」。
//
// 实验：
// 1. makeWidget() 改为返回 std::unique_ptr<Widget>（用 std::make_unique）。
// 2. Panel 的成员改为 std::vector<std::unique_ptr<Widget>>，add() 接收 unique_ptr 并 std::move 进去。
// 3. 只读访问的 printAll() 不涉及所有权，参数保持 const Panel&。
// 4. 运行后最后一行应是 alive=0：Panel 析构时自动释放全部部件，不写一个 delete。
#include <iostream>
#include <string>
#include <vector>

struct Widget {
    static int alive;
    std::string name;
    explicit Widget(std::string n) : name(std::move(n)) { ++alive; }
    ~Widget() { --alive; }
};
int Widget::alive = 0;

// TODO(实验)：makeWidget 与 Panel 改用 std::unique_ptr 表达所有权
Widget* makeWidget(const std::string& name) {   // 调用者要不要 delete？签名看不出来
    return new Widget(name);
}

class Panel {
public:
    void add(Widget* w) { widgets_.push_back(w); }
    const std::vector<Widget*>& widgets() const { return widgets_; }
private:
    std::vector<Widget*> widgets_;   // 析构时要不要 delete？也看不出来
};

void printAll(const Panel& p) {
    for (const auto& w : p.widgets()) std::cout << "widget " << w->name << "\n";
}

int main() {
    {
        Panel panel;
        panel.add(makeWidget("ok-button"));
        panel.add(makeWidget("cancel-button"));
        printAll(panel);
    }   // panel 在这里析构
    std::cout << "alive=" << Widget::alive << "\n";
}
