#include "raii.hpp"

#include <ostream>
#include <string>
#include <utility>
#include <vector>

using namespace std;

namespace {

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

void RAII::rvalue(ostream& output) const {
    string named = "Athena";
    const string readonly = "只读对象";

    output << "具名可修改对象选择: " << binding_kind(named) << '\n';
    output << "具名 const 对象选择: " << binding_kind(readonly) << '\n';
    output << "临时对象选择: " << binding_kind(string("临时对象")) << '\n';
    output << "std::move 后选择: " << binding_kind(std::move(named)) << '\n';
    output << "只做类型转换后原值仍是: " << named << '\n';
}

void RAII::move_semantics(ostream& output) const {
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
