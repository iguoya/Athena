// 情境：中间人。为了「隐藏委托关系」，Person 给 Department 的每个查询都包了一层转发函数；
// 时间一长，Person 接口里一半的函数只是在转发。现在要加一个 Department 的新查询，
// 就得同时去 Person 里再补一个转发——这一层委托已经不再有价值。
// 重构手法：移除中间人（Remove Middle Man），《重构》第 2 版第 3 章「中间人」：
// 它是「隐藏委托关系」（Hide Delegate）的反方向——封装做过头时，让调用方直接和真正
// 知道情况的对象对话。
//
// 实验：
// 1. 给 Person 加 const Department& department() const，删掉 manager()、budget()、
//    headcount() 三个转发函数，调用方改为 person.department().xxx()。
// 2. 新需求：给 Department 加 int costPerHead() const（预算除以人数），
//    在 main 里直接通过 person.department() 调用，Person 一行不动。
//    解开 main 里的 TODO(实验) 行。达标时会输出 cost/head=2500。
#include <iostream>
#include <string>

class Department {
public:
    Department(std::string manager, int budget, int headcount)
        : manager_(std::move(manager)), budget_(budget), headcount_(headcount) {}
    const std::string& manager() const { return manager_; }
    int budget() const { return budget_; }
    int headcount() const { return headcount_; }

private:
    std::string manager_;
    int budget_;
    int headcount_;
};

class Person {
public:
    Person(std::string name, Department dept) : name_(std::move(name)), dept_(std::move(dept)) {}
    const std::string& name() const { return name_; }
    // 三个只管转发的函数——中间人
    const std::string& manager() const { return dept_.manager(); }
    int budget() const { return dept_.budget(); }
    int headcount() const { return dept_.headcount(); }

private:
    std::string name_;
    Department dept_;
};

int main() {
    Person p("王芳", Department("李明", 10000, 4));
    std::cout << p.name() << " reports to " << p.manager() << ", budget=" << p.budget()
              << ", headcount=" << p.headcount() << "\n";
    // TODO(实验)：移除中间人、写好 costPerHead() 后，把上面的输出改成通过 department() 访问，并解开下一行
    // std::cout << "cost/head=" << p.department().costPerHead() << "\n";
}
