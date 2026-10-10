// 命令：把一个请求封装为一个对象，从而可以参数化、排队、记日志，并支持撤销。
// 实验：遥控器（Invoker）只认识 Command 接口，执行过的命令压进历史栈。
// LightOnCommand 已写好。补 TODO：写 LightOffCommand（execute 关灯，undo 开灯），
// 并在 main 里按 开 → 关 → 撤销 的顺序操作。遥控器一行不改。
#include <iostream>
#include <memory>
#include <vector>

// Receiver：知道如何实施与请求相关的操作
class Light {
public:
    void on() { std::cout << "light: ON\n"; }
    void off() { std::cout << "light: OFF\n"; }
};

// Command：声明执行操作的接口
class Command {
public:
    virtual ~Command() = default;
    virtual void execute() = 0;
    virtual void undo() = 0;
};

// ConcreteCommand：把一个接收者绑定到一个动作上
class LightOnCommand : public Command {
public:
    explicit LightOnCommand(Light& l) : light_(l) {}
    void execute() override { light_.on(); }
    void undo() override { light_.off(); }
private:
    Light& light_;
};

// TODO(实验)：在这里新增 LightOffCommand

// Invoker：要求命令执行请求，并记下历史以便撤销
class RemoteControl {
public:
    void press(std::unique_ptr<Command> cmd) {
        cmd->execute();
        history_.push_back(std::move(cmd));
    }
    void undo() {
        if (history_.empty()) return;
        std::cout << "undo -> ";
        history_.back()->undo();
        history_.pop_back();
    }
private:
    std::vector<std::unique_ptr<Command>> history_;
};

int main() {
    Light light;
    RemoteControl remote;
    remote.press(std::make_unique<LightOnCommand>(light));
    // TODO(实验)：remote.press(std::make_unique<LightOffCommand>(light)); remote.undo();
}
