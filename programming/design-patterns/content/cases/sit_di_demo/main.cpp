// 情境：写死的依赖。ReportService 在内部直接创建 FileStorage——想在测试里换成内存存储、
// 或者以后换成数据库，都得改 ReportService 本身。
// 组织手段：依赖注入（构造函数注入）——依赖由外部创建好再传进来
// （Martin Fowler《Inversion of Control Containers and the Dependency Injection pattern》，2004）；
// 对应依赖倒置原则：ReportService 只依赖抽象的 Storage。
//
// 实验：
// 1. 定义抽象类 Storage（纯虚函数 void save(const std::string& key, const std::string& value)），
//    让 FileStorage 实现它。
// 2. 写 MemoryStorage：把数据存进 std::map，并输出 saved to memory: <key>。
// 3. ReportService 改为构造函数接收 Storage&，不再自己 new。
// 4. 删掉 main 里的旧代码，解开 TODO(实验) 段。达标时会输出 saved to memory: report-1。
#include <iostream>
#include <map>
#include <string>

class FileStorage {
public:
    void save(const std::string& key, const std::string& value) {
        // 真实程序会写磁盘；这里只打印
        std::cout << "write file " << key << " (" << value.size() << " bytes)\n";
    }
};

class ReportService {
public:
    void publish(int id) {
        FileStorage storage;   // 依赖写死在这里
        storage.save("report-" + std::to_string(id), "monthly report");
    }
};

int main() {
    ReportService service;
    service.publish(1);

    // TODO(实验)：改成构造函数注入后，删掉上面两行，解开下面这段
    // MemoryStorage memory;              // 测试时注入内存存储
    // ReportService service(memory);
    // service.publish(1);
}
