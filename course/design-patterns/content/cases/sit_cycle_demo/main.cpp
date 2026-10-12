// 情境：两个模块互相要对方。Document 要知道 Printer 才能 print()；Printer 要知道 Document
// 才能取标题和正文。谁都离不开谁，改一个、测一个都得把另一个拖上；现在要打印 Invoice，
// Printer 还得为它再认识一个新类。
// 规范：C++ Core Guidelines SF.9（避免源文件间的循环依赖）；Robert C. Martin 的无环依赖
// 原则（ADP）。解法是依赖倒置：让双方都依赖一个站在「使用方」一侧的小接口。
//
// 实验：
// 1. 定义接口 class Printable { virtual std::string title() const; virtual std::string body() const; }。
// 2. Printer 只依赖 Printable：void print(const Printable&)；不再认识 Document。
// 3. Document 实现 Printable，且不再认识 Printer（去掉 print() 成员与前向声明）。
// 4. 新需求：写 Invoice(int no, int amount) 实现 Printable（title 为 "Invoice #<no>"），
//    用同一个 Printer 打印，Printer 的代码一行不改。解开 main 里的 TODO(实验) 行。
//    达标时会输出 [printer] Report Q3 和 [printer] Invoice #7。
#include <iostream>
#include <string>

class Printer;   // 前向声明只是把环藏起来，并没有拆掉它

class Document {
public:
    Document(std::string title, std::string body) : title_(std::move(title)), body_(std::move(body)) {}
    const std::string& title() const { return title_; }
    const std::string& body() const { return body_; }
    void print(Printer& printer) const;   // Document 认识 Printer
private:
    std::string title_, body_;
};

class Printer {
public:
    void print(const Document& doc) {      // Printer 认识 Document：成环
        std::cout << "[printer] " << doc.title() << "\n" << doc.body() << "\n";
    }
};

void Document::print(Printer& printer) const { printer.print(*this); }

int main() {
    Document report("Report Q3", "revenue up");
    Printer printer;
    report.print(printer);
    // TODO(实验)：拆掉环、写好 Invoice 后，把上面三行换成下面几行
    // Document report("Report Q3", "revenue up");
    // Printer printer;
    // printer.print(report);
    // Invoice invoice(7, 120);
    // printer.print(invoice);
}
