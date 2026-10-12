// 情境：回调拿不到自己的上下文。for_each 只接受 void (*fn)(int)，回调要累加，
// 只好把结果放进全局变量——想同时算两个独立的和（偶数和、奇数和）就做不到，
// 也无法在多线程里安全地用。
// 组织手段：回调多带一个 void* 上下文参数，调用方把自己的数据地址传进去，
// 回调再转回具体类型使用。这是 C 里「闭包」的标准写法。
// 依据：POSIX pthread_create 的 void* (*start_routine)(void*) 与 void* arg；
// glibc 的 qsort_r 与 C11 附录 K 的 qsort_s 也都为比较函数多带了一个上下文参数。
//
// 实验：
// 1. 把 for_each 改成 void for_each(const int* a, int n, void (*fn)(int, void*), void* ctx)。
// 2. 写 struct sums { int even; int odd; }; 与回调 void add_by_parity(int v, void* ctx)：
//    把 ctx 转成 struct sums* 后按奇偶累加。
// 3. 删掉全局变量 g_sum 和旧回调，解开 main 里的 TODO(实验) 段。达标时会输出 even=6 odd=9。
#include <cstdio>

int g_sum = 0;                         /* 回调只能写全局变量 */

void add(int v) { g_sum += v; }

void for_each(const int* a, int n, void (*fn)(int)) {
    for (int i = 0; i < n; ++i) fn(a[i]);
}

int main(void) {
    int a[] = {1, 2, 3, 4, 5};
    for_each(a, 5, add);
    printf("sum=%d\n", g_sum);

    /* TODO(实验)：改成带上下文的回调后，删掉上面两行，解开下面这段
    struct sums s = {0, 0};
    for_each(a, 5, add_by_parity, &s);
    printf("even=%d odd=%d\n", s.even, s.odd);
    */
    return 0;
}
