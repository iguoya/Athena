/* 固定的 C 驱动：三个目标共用这一份，只换 asm/ 下的 .s（ADR 0006 第 5 条）。
 *
 * 汇编函数是纯计算，不碰系统调用；输出由这里负责。每个用例同时算 C 参考
 * 实现和汇编实现，不一致就打印 FAIL 并以非 0 退出。 */
#include <stdio.h>

int c_sum(const int *a, int n);
int asm_sum(const int *a, int n);

static int check(const char *name, const int *a, int n) {
    int want = c_sum(a, n);
    int got = asm_sum(a, n);
    printf("%-6s c=%-9d asm=%-9d %s\n", name, want, got, want == got ? "ok" : "FAIL");
    return want == got;
}

int main(void) {
    const int five[] = {1, 2, 3, 4, 5};
    const int mixed[] = {-7, 10, 0, 2147483, -2147483};
    int ok = 1;
    ok &= check("empty", five, 0);
    ok &= check("one", five, 1);
    ok &= check("five", five, 5);
    ok &= check("mixed", mixed, 5);
    return ok ? 0 : 1;
}
