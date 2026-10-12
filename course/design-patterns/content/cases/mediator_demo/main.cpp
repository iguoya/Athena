// 中介者：用一个中介对象封装一系列对象之间的交互，各对象不需要显式地相互引用。
// 实验：三个用户在同一个聊天室里。User 只认识 ChatRoom，不认识别的 User。
// 补 TODO：实现 ChatRoom::send()——把消息转给除发送者以外的每个成员。
// 想一想：如果没有中介者，三个人要互相持有几个引用？十个人呢？
#include <iostream>
#include <string>
#include <vector>

class User;

// Mediator：定义同事对象之间通信的接口
class ChatMediator {
public:
    virtual ~ChatMediator() = default;
    virtual void send(const std::string& msg, User& from) = 0;
};

// Colleague：只知道它的中介者
class User {
public:
    User(std::string name, ChatMediator& m) : name_(std::move(name)), mediator_(m) {}
    void say(const std::string& msg) { mediator_.send(msg, *this); }
    void receive(const std::string& msg, const User& from) {
        std::cout << name_ << " got: " << msg << " from " << from.name() << "\n";
    }
    const std::string& name() const { return name_; }
private:
    std::string name_;
    ChatMediator& mediator_;
};

// ConcreteMediator：了解并维护各个同事，协调它们的交互
class ChatRoom : public ChatMediator {
public:
    void join(User& u) { members_.push_back(&u); }
    void send(const std::string& msg, User& from) override {
        // TODO(实验)：对 members_ 里除 from 以外的每个人调用 receive(msg, from)
        (void)msg;
        (void)from;
    }
private:
    std::vector<User*> members_;
};

int main() {
    ChatRoom room;
    User alice("alice", room), bob("bob", room), carol("carol", room);
    room.join(alice);
    room.join(bob);
    room.join(carol);
    alice.say("hi");
    std::cout << "end of chat\n";
}
