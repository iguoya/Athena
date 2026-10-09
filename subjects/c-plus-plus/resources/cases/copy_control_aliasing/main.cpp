// 逐成员拷贝对裸资源做了什么
//
// 真让它双重释放会直接崩掉，那样只看得到一个崩溃，看不到过程。这里用一本
// 账替代真实的堆：分配和释放都记账，重复释放被记成一次「错误」而不是崩溃，
// 于是「同一块内存被释放两次」变成可观察的数字。

#include <iostream>
#include <map>

using namespace std;

// 假堆：块 id → 是否还活着。
struct Ledger {
    static inline map<int, bool> alive;
    static inline int next_id = 1;
    static inline int double_frees = 0;

    static int allocate(const char* who) {
        const int id = next_id++;
        alive[id] = true;
        cout << "  分配 #" << id << "（" << who << "）\n";
        return id;
    }
    static void release(int id, const char* who) {
        if (id == 0) {
            cout << "  释放 空（" << who << "）——什么也没发生\n";
            return;
        }
        if (!alive[id]) {
            ++double_frees;
            cout << "  释放 #" << id << "（" << who << "）——它已经被释放过了！\n";
            return;
        }
        alive[id] = false;
        cout << "  释放 #" << id << "（" << who << "）\n";
    }
};

// —— 示范：没有自定义拷贝，编译器给的是逐成员拷贝 ——
struct Shallow {
    int block;

    Shallow() : block(Ledger::allocate("Shallow 构造")) {}
    ~Shallow() { Ledger::release(block, "Shallow 析构"); }
    // 没有写拷贝构造：编译器生成的版本复制 block 这个整数本身，
    // 于是两个对象记着同一个块号。
};

void demo_shallow() {
    cout << "[逐成员拷贝]\n";
    Shallow a;
    Shallow b = a;          // b.block == a.block
    cout << "  a.block=" << a.block << "  b.block=" << b.block << "\n";
    cout << "  (离开作用域，两个对象各析构一次)\n";
}

// —— 待填 ——
// TODO(学员)：给 Deep 补上拷贝构造，让它复制出**自己的**块。
// 签名：Deep(const Deep& other)
//
// 先预测再写：
//   1. 补上之后，"分配" 会出现几次？
//   2. 末尾的「重复释放」计数会变成多少？
//   3. 如果只写拷贝构造、不写拷贝赋值，Deep d = c; 和 d = c; 哪个还是浅的？
struct Deep {
    int block;

    Deep() : block(Ledger::allocate("Deep 构造")) {}
    ~Deep() { Ledger::release(block, "Deep 析构"); }

    // 在这里写拷贝构造。
};

void demo_deep() {
    cout << "[自己接管拷贝]\n";
    Deep c;
    Deep d = c;
    cout << "  c.block=" << c.block << "  d.block=" << d.block << "\n";
    cout << "  (两个块号相同说明拷贝构造还没写)\n";
}

// —— 以下驱动请勿改 ——
int main() {
    demo_shallow();
    cout << "---\n";
    demo_deep();
    cout << "---\n";
    cout << "重复释放次数：" << Ledger::double_frees << "\n";
    cout << "（真实程序里每一次都是未定义行为）\n";
    return 0;
}
