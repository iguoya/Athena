// 情境：C 没有析构函数。setup() 要依次申请三块资源，任何一步失败都要把前面申请到的
// 释放掉。逐个 if 嵌套、在每个出口重复写释放代码，很容易漏掉一条路径。
// 组织手段：集中出口——出错时 goto 到函数末尾按申请的逆序排列的释放标签，
// 每个出口只跳不写释放代码。
// 依据：Linux 内核编码规范（Documentation/process/coding-style.rst）第 7 节
// 「Centralized exiting of functions」：标签名说明它做什么（如 out_free_buffer），
// 不要用 err1、err2 这样的编号。
//
// 实验：
// 1. 重写 setup()：依次申请 a、b、c，失败时 goto 到对应的标签；
//    标签按逆序排列：out_free_b 释放 b，然后落到 out_free_a 释放 a，最后 return -1。
// 2. 用 C++ 编译器编译时，goto 不能跳过带初始化的变量声明——把 a、b、c 都在函数开头
//    声明并初始化为 NULL。
// 3. 达标时最后一行是 leaked=0（模拟第三步申请失败）。
#include <cstdio>
#include <cstdlib>

int g_live = 0;
int g_fail_at = 3;                      /* 模拟：第 3 次申请失败 */
int g_calls = 0;

void* acquire(const char* what) {
    if (++g_calls == g_fail_at) { printf("acquire %s failed\n", what); return NULL; }
    ++g_live;
    printf("acquire %s\n", what);
    return malloc(16);
}
void release(void* p, const char* what) {
    if (!p) return;
    --g_live;
    printf("release %s\n", what);
    free(p);
}

int setup(void) {
    void* a = acquire("a");
    if (a) {
        void* b = acquire("b");
        if (b) {
            void* c = acquire("c");
            if (c) {
                printf("all ready\n");
                release(c, "c");
                release(b, "b");
                release(a, "a");
                return 0;
            }
            /* 这里忘了释放 b */
        }
        release(a, "a");
    }
    return -1;
}

int main(void) {
    /* TODO(实验)：用集中出口重写 setup() */
    int rc = setup();
    printf("rc=%d leaked=%d\n", rc, g_live);
    return 0;
}
