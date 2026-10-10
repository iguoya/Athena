// 享元：运用共享技术有效地支持大量细粒度的对象。
// 实验：排版 "hello world" 时，每个字符要一个 Glyph。字符本身是内部状态（可共享），
// 位置是外部状态（调用时传入）。现在的工厂每次都 new，11 个字符造了 11 个对象。
// 先预测：共享之后应该是几个？补 TODO：让 GlyphFactory 先查池子，有就复用。
#include <iostream>
#include <map>
#include <memory>
#include <string>

// Flyweight：只存内部状态；外部状态（位置）由调用方传进来
class Glyph {
public:
    explicit Glyph(char c) : c_(c) { ++created; }
    void draw(int pos) const { (void)pos; /* 真实程序在 pos 处画出字符 c_ */ }
    static int created;
private:
    char c_;
};
int Glyph::created = 0;

// FlyweightFactory：创建并管理享元，保证同一个 key 只有一个实例
class GlyphFactory {
public:
    std::shared_ptr<Glyph> get(char c) {
        // TODO(实验)：先在 pool_ 里找 c，找到就返回已有的；找不到再创建并放进 pool_
        return std::make_shared<Glyph>(c);
    }
private:
    std::map<char, std::shared_ptr<Glyph>> pool_;
};

int main() {
    GlyphFactory factory;
    const std::string text = "hello world";
    for (int i = 0; i < static_cast<int>(text.size()); ++i) {
        factory.get(text[i])->draw(i);
    }
    std::cout << "characters: " << text.size() << "\n";
    std::cout << "glyph objects created: " << Glyph::created << "\n";
    bool shared = factory.get('l') == factory.get('l');
    std::cout << "same glyph for 'l': " << (shared ? "yes" : "no") << "\n";
}
