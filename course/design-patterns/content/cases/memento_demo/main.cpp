// 备忘录：在不破坏封装性的前提下捕获对象的内部状态，并在对象之外保存，以便日后恢复。
// 实验：编辑器（原发器）把文本存进备忘录，历史栈（管理者）只负责保管，看不到内容。
// 补 TODO：实现 Editor::restore()，从备忘录取回状态——撤销后应输出 after undo: [Hello]。
// 注意 Memento 的状态是私有的，只有 Editor 是它的友元：这就是「不破坏封装」。
#include <iostream>
#include <string>
#include <vector>

class Editor;

// Memento：存储原发器的内部状态，只让原发器访问
class Memento {
    friend class Editor;
    explicit Memento(std::string s) : state_(std::move(s)) {}
    std::string state_;
};

// Originator：创建备忘录记录当前状态，并能用备忘录恢复
class Editor {
public:
    void type(const std::string& s) { text_ += s; }
    const std::string& text() const { return text_; }
    Memento save() const { return Memento(text_); }
    void restore(const Memento& m) {
        // TODO(实验)：把 text_ 恢复成备忘录里保存的状态
        (void)m;
    }
private:
    std::string text_;
};

// Caretaker：负责保存备忘录，不能操作或检查其内容
class History {
public:
    void push(Memento m) { stack_.push_back(std::move(m)); }
    Memento pop() { Memento m = stack_.back(); stack_.pop_back(); return m; }
private:
    std::vector<Memento> stack_;
};

int main() {
    Editor editor;
    History history;
    editor.type("Hello");
    history.push(editor.save());
    editor.type(" World");
    std::cout << "before undo: [" << editor.text() << "]\n";
    editor.restore(history.pop());
    std::cout << "after undo: [" << editor.text() << "]\n";
}
