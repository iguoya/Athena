// 外观：为子系统中的一组接口提供一个一致的高层接口，让子系统更容易使用。
// 实验：看一部电影要按顺序操作功放、投影仪、播放器三个子系统。
// 补 TODO：实现 HomeTheater::watch()，把这串步骤收进外观里；main 只调一次 watch()。
// 子系统类一行不改，也不知道外观的存在。
#include <iostream>
#include <string>

// 子系统类：各管一摊，没有指向外观的指针
class Amplifier {
public:
    void on() { std::cout << "amp on\n"; }
    void setVolume(int v) { std::cout << "amp volume " << v << "\n"; }
};
class Projector {
public:
    void on() { std::cout << "projector on\n"; }
    void input(const std::string& src) { std::cout << "projector input " << src << "\n"; }
};
class Player {
public:
    void on() { std::cout << "player on\n"; }
    void play(const std::string& movie) { std::cout << "playing " << movie << "\n"; }
};

// Facade：知道哪个子系统负责什么，把客户请求转给它们
class HomeTheater {
public:
    HomeTheater(Amplifier& a, Projector& p, Player& pl) : amp_(a), proj_(p), player_(pl) {}
    void watch(const std::string& movie) {
        // TODO(实验)：依次 amp on、音量 5、projector on、输入 player、player on、播放 movie
        (void)movie;
    }
private:
    Amplifier& amp_;
    Projector& proj_;
    Player& player_;
};

int main() {
    Amplifier amp;
    Projector proj;
    Player player;
    HomeTheater theater(amp, proj, player);
    theater.watch("Inception");   // 客户只认识外观这一个入口
    std::cout << "show time\n";
}
