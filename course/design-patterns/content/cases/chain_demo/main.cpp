// 职责链：使多个对象都有机会处理请求，把它们连成一条链，请求沿链传递直到有对象处理。
// 实验：报销审批链。组长批 1000 以内，总监批 20000 以内，超出则驳回。
// 补 TODO：实现 Manager（经理批 5000 以内），并把它插进组长与总监之间。
// 先预测：插入之前，3000 元的单子是谁批的？插入之后呢？发起审批的代码要不要改？
#include <iostream>
#include <memory>
#include <string>

// Handler：定义处理请求的接口，并实现后继链
class Approver {
public:
    explicit Approver(int limit) : limit_(limit) {}
    virtual ~Approver() = default;
    Approver* setNext(Approver* next) { next_ = next; return next; }
    void handle(int amount) {
        if (amount <= limit_) {
            std::cout << amount << " approved by " << title() << "\n";
        } else if (next_) {
            next_->handle(amount);
        } else {
            std::cout << amount << " rejected\n";
        }
    }
protected:
    virtual std::string title() const = 0;
private:
    int limit_;
    Approver* next_ = nullptr;
};

// ConcreteHandler
class TeamLead : public Approver {
public:
    TeamLead() : Approver(1000) {}
protected:
    std::string title() const override { return "TeamLead"; }
};
class Director : public Approver {
public:
    Director() : Approver(20000) {}
protected:
    std::string title() const override { return "Director"; }
};

// TODO(实验)：在这里新增 Manager（额度 5000，title 为 "Manager"）

int main() {
    TeamLead lead;
    Director director;
    // TODO(实验)：建一个 Manager，把链改成 lead -> manager -> director
    lead.setNext(&director);

    for (int amount : {800, 3000, 15000, 50000}) lead.handle(amount);   // 客户只认识链头
}
