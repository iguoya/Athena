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

const char* binding_kind(string&) { return "左值引用"; }
const char* binding_kind(const string&) { return "const 左值引用"; }
const char* binding_kind(string&&) { return "右值引用"; }

struct TransferStats {
    int copy_constructions = 0;
    int move_constructions = 0;
    int move_assignments = 0;
};

class MovableBuffer {
public:
    MovableBuffer(size_t size, TransferStats& stats)
        : m_values(size), m_stats(&stats) {}

    MovableBuffer(const MovableBuffer& other)
        : m_values(other.m_values), m_stats(other.m_stats) {
        ++m_stats->copy_constructions;
    }

    MovableBuffer(MovableBuffer&& other) noexcept
        : m_values(std::move(other.m_values)), m_stats(other.m_stats) {
        ++m_stats->move_constructions;
    }

    MovableBuffer& operator=(MovableBuffer&& other) noexcept {
        if (this != &other) {
            m_values = std::move(other.m_values);
            m_stats = other.m_stats;
            ++m_stats->move_assignments;
        }
        return *this;
    }

    const int* data() const { return m_values.data(); }
    size_t size() const { return m_values.size(); }
    void reset(size_t size) { m_values.assign(size, 0); }

private:
    vector<int> m_values;
    TransferStats* m_stats;
};

} // namespace

// RAII 与资源管理
//
// 一个 public 成员函数对应 athena.json 中的一个可运行知识点。
class RAII {
public:
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

    // 移动语义
    void rvalue(ostream& output) const {
        string named = "Athena";
        const string readonly = "只读对象";

        output << "具名可修改对象选择: " << binding_kind(named) << '\n';
        output << "具名 const 对象选择: " << binding_kind(readonly) << '\n';
        output << "临时对象选择: " << binding_kind(string("临时对象")) << '\n';
        output << "std::move 后选择: " << binding_kind(std::move(named)) << '\n';
        output << "只做类型转换后原值仍是: " << named << '\n';
    }

    void move_semantics(ostream& output) const {
        TransferStats stats;
        MovableBuffer original(1024, stats);
        const int* original_storage = original.data();

        MovableBuffer copied = original;
        output << "拷贝构造创建独立存储: "
               << (copied.data() != original_storage ? "是" : "否") << '\n';

        auto&& cast_only = std::move(original);
        output << "std::move 本身搬运存储: "
               << (cast_only.data() != original_storage ? "是" : "否") << '\n';

        MovableBuffer moved = std::move(original);
        output << "移动构造转移原存储: "
               << (moved.data() == original_storage ? "是" : "否") << '\n';

        const int* copied_storage = copied.data();
        MovableBuffer assigned(1, stats);
        assigned = std::move(copied);
        output << "移动赋值转移拷贝对象的存储: "
               << (assigned.data() == copied_storage ? "是" : "否") << '\n';
        output << "统计: 拷贝构造 " << stats.copy_constructions
               << "，移动构造 " << stats.move_constructions
               << "，移动赋值 " << stats.move_assignments << '\n';

        original.reset(3);
        output << "被移动对象重新赋值后元素数: " << original.size() << '\n';
    }
};
