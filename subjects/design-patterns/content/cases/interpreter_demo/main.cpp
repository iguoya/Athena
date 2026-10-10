// 解释器：给定一个语言，定义它文法的一种表示，并定义一个解释器用这个表示来解释句子。
// 实验：文法 expr ::= number | variable | expr '+' expr | expr '-' expr。
// main 里手工搭好了句子 (x + 3) - 2 的抽象语法树，x 的值放在 Context 里。
// 加法与终结符都已实现。补 TODO：实现 Subtract::interpret()。先预测 x=5 时结果是多少。
#include <iostream>
#include <map>
#include <memory>
#include <string>

// Context：解释器之外的全局信息（这里是变量表）
class Context {
public:
    void set(const std::string& name, int v) { vars_[name] = v; }
    int get(const std::string& name) const { return vars_.at(name); }
private:
    std::map<std::string, int> vars_;
};

// AbstractExpression：抽象语法树所有结点共享的解释操作
class Expression {
public:
    virtual ~Expression() = default;
    virtual int interpret(const Context& ctx) const = 0;
};

// TerminalExpression：数字与变量
class Number : public Expression {
public:
    explicit Number(int v) : v_(v) {}
    int interpret(const Context&) const override { return v_; }
private:
    int v_;
};
class Variable : public Expression {
public:
    explicit Variable(std::string name) : name_(std::move(name)) {}
    int interpret(const Context& ctx) const override { return ctx.get(name_); }
private:
    std::string name_;
};

// NonterminalExpression：每条文法规则一个类，持有子表达式
class Add : public Expression {
public:
    Add(std::unique_ptr<Expression> l, std::unique_ptr<Expression> r) : l_(std::move(l)), r_(std::move(r)) {}
    int interpret(const Context& ctx) const override { return l_->interpret(ctx) + r_->interpret(ctx); }
private:
    std::unique_ptr<Expression> l_, r_;
};
class Subtract : public Expression {
public:
    Subtract(std::unique_ptr<Expression> l, std::unique_ptr<Expression> r) : l_(std::move(l)), r_(std::move(r)) {}
    int interpret(const Context& ctx) const override {
        // TODO(实验)：返回左子表达式的值减去右子表达式的值
        (void)ctx;
        return 0;
    }
private:
    std::unique_ptr<Expression> l_, r_;
};

int main() {
    // Client 构建句子 (x + 3) - 2 的抽象语法树
    auto tree = std::make_unique<Subtract>(
        std::make_unique<Add>(std::make_unique<Variable>("x"), std::make_unique<Number>(3)),
        std::make_unique<Number>(2));
    Context ctx;
    ctx.set("x", 5);
    std::cout << "(x + 3) - 2 with x=5, result: " << tree->interpret(ctx) << "\n";
    ctx.set("x", 10);
    std::cout << "(x + 3) - 2 with x=10, result: " << tree->interpret(ctx) << "\n";
}
