// 工厂方法：每个产品配一个工厂，新增产品不改旧代码。
// 实验：补 TODO——仿照 FileLogger / FileLoggerFactory 新增 ConsoleLogger
// （write 输出 [console] 加消息）与 ConsoleLoggerFactory，再在 main 里用它。
// 只加新类：LoggerFactory、FileLoggerFactory 一行不改，对比简单工厂体会 OCP。
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

// TODO(实验)：在这里新增 ConsoleLogger 与 ConsoleLoggerFactory

int main() {
    FileLoggerFactory f;
    f.clientCode();   // 客户端只依赖两层抽象
    // TODO(实验)：ConsoleLoggerFactory c; c.clientCode();
}
