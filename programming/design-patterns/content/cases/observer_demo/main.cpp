// 观察者：定义对象间一对多的依赖，目标状态改变时，所有观察者都得到通知并自动更新。
// 实验：气象站（目标）登记了手机与广告牌两个观察者，但 notify() 还是空的，没人收到消息。
// 补 TODO：实现 notify()，对每个登记的观察者调用 update()。
// 然后看 main 后半段：广告牌注销后，再改温度，谁还会收到？
#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

class Subject;

// Observer：为需要获得通知的对象定义更新接口
class Observer {
public:
    virtual ~Observer() = default;
    virtual void update(const Subject& s) = 0;
};

// Subject：知道它的观察者，提供注册与删除接口
class Subject {
public:
    virtual ~Subject() = default;
    void attach(Observer* o) { observers_.push_back(o); }
    void detach(Observer* o) { observers_.erase(std::remove(observers_.begin(), observers_.end(), o), observers_.end()); }
    void notify() {
        // TODO(实验)：遍历 observers_，对每个观察者调用 update(*this)
    }
private:
    std::vector<Observer*> observers_;
};

// ConcreteSubject：状态改变时发出通知
class WeatherStation : public Subject {
public:
    void setTemperature(int t) { temperature_ = t; notify(); }
    int temperature() const { return temperature_; }
private:
    int temperature_ = 0;
};

// ConcreteObserver：从目标取状态，保持与目标一致
class Display : public Observer {
public:
    explicit Display(std::string name) : name_(std::move(name)) {}
    void update(const Subject& s) override {
        const auto& ws = static_cast<const WeatherStation&>(s);
        std::cout << name_ << " shows " << ws.temperature() << "\n";
    }
private:
    std::string name_;
};

int main() {
    WeatherStation station;
    Display phone("phone"), board("board");
    station.attach(&phone);
    station.attach(&board);
    station.setTemperature(25);

    station.detach(&board);
    station.setTemperature(30);
    std::cout << "done\n";
}
