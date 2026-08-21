#include "raii.hpp"

#include <memory>
#include <ostream>
#include <stdexcept>

using namespace std;

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

} // namespace

void RAII::basic(ostream& output) const {
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
