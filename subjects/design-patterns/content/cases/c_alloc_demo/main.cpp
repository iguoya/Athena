/* 情境：谁分配、谁释放。make_greeting() 在函数内部 malloc 一块内存返回给调用方，
 * 全靠注释写着“调用方负责 free”。调用方一多，总有人忘记（泄漏）；换个写法让被调函数
 * 在出错分支里替调用方 free，又会变成重复释放。
 * 规范：SEI CERT C MEM00-C「在同一个模块、同一抽象层级分配和释放内存」；
 * 惯用法：调用方提供缓冲区和大小，被调函数返回“需要的长度”——和标准库 snprintf 的约定一致
 * （cppreference：snprintf 返回的是在缓冲区足够大时本应写入的字符数）。
 * 本实验按 C 的写法写，但用同一个 C++ 编译器编译（malloc 的结果显式转换）。
 *
 * 实验：
 * 1. 写 int format_greeting(char* buf, size_t size, const char* name)：用 snprintf 把
 *    "hello, <name>" 写进 buf（最多 size-1 个字符），返回“完整内容需要的长度”（不含结尾 '\0'）。
 *    函数内部不得 malloc。
 * 2. 同样的约定再写 int format_farewell(...)，内容是 "bye, <name>"。
 * 3. 解开 main 里的 TODO(实验) 行：栈上缓冲区够用时正常输出；故意给一个放不下的长名字，
 *    调用方通过返回值发现被截断。达标时 live=0（没有任何堆分配），并输出
 *    hello, Wang / truncated: need 21 / bye, Wang。
 */
#include <cstdio>
#include <cstdlib>
#include <cstring>

static int live = 0;   // 当前尚未释放的堆块数，用来暴露泄漏
static void* xmalloc(size_t n) { ++live; return std::malloc(n); }
static void xfree(void* p) { if (p) { --live; std::free(p); } }

/* 返回堆内存，调用方负责 xfree。 */
char* make_greeting(const char* name) {
    size_t n = std::strlen(name) + 8;
    char* s = static_cast<char*>(xmalloc(n));
    std::snprintf(s, n, "hello, %s", name);
    return s;
}

int main() {
    char* a = make_greeting("Wang");
    std::puts(a);
    xfree(a);
    char* b = make_greeting("Li");
    std::puts(b);   /* 忘了释放 b */
    std::printf("live=%d\n", live);
    /* TODO(实验)：写好 format_greeting() 与 format_farewell() 后，把上面从 make_greeting 起的内容换成下面几行
    char buf[16];
    format_greeting(buf, sizeof buf, "Wang");
    std::puts(buf);
    int need = format_greeting(buf, sizeof buf, "Wang the Third");
    if (need >= static_cast<int>(sizeof buf)) std::printf("truncated: need %d\n", need);
    format_farewell(buf, sizeof buf, "Wang");
    std::puts(buf);
    std::printf("live=%d\n", live);
    */
}
