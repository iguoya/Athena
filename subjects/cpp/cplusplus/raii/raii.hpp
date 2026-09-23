#pragma once

#include <memory>
#include <ostream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

using namespace std;

// 匿名命名空间里的辅助类型只服务本文件的知识点演示；每个包含本文件的
// 翻译单元各自拿到一份内部链接的副本，不会跨翻译单元冲突。
namespace {

class ScopedBuffer {
public:
    ScopedBuffer(size_t size, bool& released)
        : m_data(make_unique<int[]>(size)), m_released(released) {
        m_released = false;
    }

    ~ScopedBuffer() { m_released = true; }

    int& operator[](size_t index) { return m_data[index]; }

private:
    unique_ptr<int[]> m_data;
    bool& m_released;
};

class TrackedResource {
public:
    TrackedResource(string name, int& destruction_count)
        : m_name(std::move(name)), m_destruction_count(destruction_count) {}

    ~TrackedResource() { ++m_destruction_count; }

    const string& name() const { return m_name; }

private:
    string m_name;
    int& m_destruction_count;
};

class LinkedNode {
public:
    LinkedNode(string name, int& destruction_count)
        : name(std::move(name)), m_destruction_count(destruction_count) {}

    ~LinkedNode() { ++m_destruction_count; }

    string name;
    shared_ptr<LinkedNode> next;
    weak_ptr<LinkedNode> previous;

private:
    int& m_destruction_count;
};

class CycleNode {
public:
    explicit CycleNode(int& destruction_count)
        : m_destruction_count(destruction_count) {}

    ~CycleNode() { ++m_destruction_count; }

    shared_ptr<CycleNode> peer;

private:
    int& m_destruction_count;
};

} // namespace

// RAII 与资源管理
//
// 一个 public 成员函数对应 athena.json 中的一个可运行知识点。
class RAII {
public:
    // 裸指针与所有权
    void raw_pointer_ownership(ostream& output) const {
        // 三个变量类型完全相同，含义完全不同——签名上分辨不出来。
        int on_stack = 42;
        int* observer = &on_stack;      // 观察者：不拥有，delete 它是灾难
        int* owner = new int(7);        // 拥有者：不 delete 就泄漏
        vector<int> numbers{1, 2, 3};
        int* first = numbers.data();    // 一段数组的起点：容器拥有它

        output << "observer -> 栈上对象: " << *observer << '\n';
        output << "owner    -> 堆上对象: " << *owner << '\n';
        output << "first    -> 容器首元素: " << *first << '\n';
        output << "三个都是 int*，但只有 owner 该被 delete。\n";

        delete owner;
        output << "delete owner 之后，另外两个仍然有效: "
               << *observer << ' ' << *first << '\n';
        output << "类型系统没有记录这个区别，只有注释和约定记着——"
               << "这正是智能指针要解决的问题。\n";
    }

    // RAII 思想
    void basic(ostream& output) const {
        bool released = false;
        try {
            ScopedBuffer buffer(3, released);
            buffer[0] = 42;
            output << "构造对象后资源可用: " << buffer[0] << '\n';
            output << "作用域内资源已释放: " << (released ? "是" : "否") << '\n';
            throw runtime_error("模拟异常");
        } catch (const runtime_error& error) {
            output << "捕获异常: " << error.what() << '\n';
        }
        output << "异常离开作用域后资源已释放: "
               << (released ? "是" : "否") << '\n';
    }

    // 智能指针
    void unique(ostream& output) const {
        int destruction_count = 0;
        {
            auto owner = make_unique<TrackedResource>("独占资源", destruction_count);
            output << "创建后持有: " << owner->name() << '\n';
            output << "unique_ptr 可拷贝: "
                   << (is_copy_constructible_v<unique_ptr<TrackedResource>> ? "是" : "否")
                   << '\n';

            auto new_owner = std::move(owner);
            output << "所有权转移后原指针为空: " << (!owner ? "是" : "否") << '\n';
            output << "新指针持有: " << new_owner->name() << '\n';
        }
        output << "离开作用域后析构次数: " << destruction_count << '\n';
    }

    void shared(ostream& output) const {
        int destruction_count = 0;
        weak_ptr<TrackedResource> observer;
        {
            auto first = make_shared<TrackedResource>("共享资源", destruction_count);
            observer = first;
            output << "第一个持有者创建后 use_count: " << first.use_count() << '\n';
            {
                auto second = first;
                output << "复制 shared_ptr 后 use_count: " << first.use_count() << '\n';
                output << "两个指针访问同一对象: "
                       << (first.get() == second.get() ? "是" : "否") << '\n';
            }
            output << "第二个持有者销毁后 use_count: " << first.use_count() << '\n';
            output << "对象已析构: " << (destruction_count > 0 ? "是" : "否") << '\n';
        }
        output << "最后持有者销毁后析构次数: " << destruction_count << '\n';
        output << "控制块观察到对象已过期: " << (observer.expired() ? "是" : "否")
               << '\n';
        output << "提示: make_shared 通常把对象和控制块合并为一次分配；"
                  "引用计数安全不等于对象线程安全。\n";
    }

    void weak(ostream& output) const {
        int cycle_destruction_count = 0;
        weak_ptr<CycleNode> cycle_observer;
        {
            auto left = make_shared<CycleNode>(cycle_destruction_count);
            auto right = make_shared<CycleNode>(cycle_destruction_count);
            left->peer = right;
            right->peer = left;
            cycle_observer = left;
        }
        output << "纯 shared_ptr 循环在外部持有者离开后仍存活: "
               << (!cycle_observer.expired() ? "是" : "否") << '\n';
        if (auto left = cycle_observer.lock()) {
            auto right = left->peer;
            left->peer.reset();
            right->peer.reset();
        }
        output << "手动拆环后析构节点数: " << cycle_destruction_count << '\n';

        int destruction_count = 0;
        weak_ptr<LinkedNode> observer;
        {
            auto first = make_shared<LinkedNode>("前驱", destruction_count);
            auto second = make_shared<LinkedNode>("后继", destruction_count);
            first->next = second;
            second->previous = first;
            observer = second;

            output << "反向 weak_ptr 不增加前驱计数: " << first.use_count() << '\n';
            output << "后继由局部变量和前驱共同拥有，计数: "
                   << second.use_count() << '\n';
            second.reset();
            output << "局部后继释放后 lock 成功: "
                   << (observer.lock() ? "是" : "否") << '\n';
        }
        output << "拥有者全部离开后析构节点数: " << destruction_count << '\n';
        output << "对象销毁后 lock 返回空: " << (!observer.lock() ? "是" : "否")
               << '\n';
    }

};
