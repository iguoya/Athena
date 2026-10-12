// 适配器（对象适配器）：把一个已有类的接口转换成客户期望的接口。
// 实验：runJob() 只认 Logger 接口；第三方库 ThirdPartyLogger 的接口对不上。
// 两边都不许改——补 TODO，让 LoggerAdapter 把 log() 转发给 writeEntry(1, …)。
#include <iostream>
#include <string>

// Target：客户期望的接口
class Logger {
public:
    virtual ~Logger() = default;
    virtual void log(const std::string& msg) = 0;
};

// Adaptee：已经存在、接口不兼容的类（假装是买来的库，不能改）
class ThirdPartyLogger {
public:
    void writeEntry(int level, const char* text) {
        std::cout << "[3rd L" << level << "] " << text << "\n";
    }
};

// Adapter：实现 Target，内部持有 Adaptee（组合，不是继承）
class LoggerAdapter : public Logger {
public:
    explicit LoggerAdapter(ThirdPartyLogger& adaptee) : adaptee_(adaptee) {}
    void log(const std::string& msg) override {
        // TODO(实验)：转发给 adaptee_.writeEntry，级别固定为 1
        (void)msg;
    }
private:
    ThirdPartyLogger& adaptee_;
};

// Client：只依赖 Target
void runJob(Logger& lg) {
    lg.log("job started");
    lg.log("job done");
}

int main() {
    ThirdPartyLogger lib;
    LoggerAdapter adapter(lib);
    runJob(adapter);
    std::cout << "runJob finished\n";
}
