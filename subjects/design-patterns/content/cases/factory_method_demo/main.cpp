// 工厂方法：每个产品配一个工厂，新增产品不改旧代码。
// 实验：运行后仿照 FileLoggerFactory 新增 ConsoleLoggerFactory——
// 只加新类，LoggerClient 与现有工厂一行不改，对比简单工厂体会 OCP。
#include <iostream>
#include <memory>

class Logger {
public:
    virtual ~Logger() = default;
    virtual void write(const char* msg) = 0;
};
class FileLogger : public Logger {
public: void write(const char* msg) override { std::cout << "[file] " << msg << "\n"; }
};

class LoggerFactory {
public:
    virtual ~LoggerFactory() = default;
    virtual std::unique_ptr<Logger> factoryMethod() const = 0;  // 子类决定造哪种
    void clientCode() const { auto lg = factoryMethod(); lg->write("hello"); }
};
class FileLoggerFactory : public LoggerFactory {
public: std::unique_ptr<Logger> factoryMethod() const override { return std::make_unique<FileLogger>(); }
};

int main() {
    FileLoggerFactory f;
    f.clientCode();   // 客户端只依赖两层抽象
}
