/* 参考实现：C 写的数组求和。
 *
 * 不 #include 任何头文件，这样 clang 的 --target 能为任意目标生成汇编，
 * 不需要目标平台的 sysroot（ADR 0006 第 1 条）。 */
int c_sum(const int *a, int n) {
    int sum = 0;
    for (int i = 0; i < n; i++)
        sum += a[i];
    return sum;
}
