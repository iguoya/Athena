// 情境：C 里按类型 switch。每个操作函数（read、name）都按设备类型分支，
// 加一种设备就要改所有函数——这是 C 版本的「重复的 switch」。
// 组织手段：函数指针表（操作表）——每种设备提供一张 struct device_ops，
// 里面是它自己的函数；设备对象持有指向这张表的指针，调用方只通过表调用。
// 依据：Linux 内核 VFS 文档（Documentation/filesystems/vfs.rst）中的 struct file_operations——
// 每种文件系统各自提供一张操作表，VFS 只通过表里的函数指针调用它们。
//
// 实验：
// 1. 定义 struct device_ops { const char* name; int (*read)(unsigned char* buf, int n); };
// 2. 为 zero、null 各写一个 read 函数和一张 static const struct device_ops 表；
//    struct device 改为持有 const struct device_ops* ops。
// 3. 新需求：加一种设备 ones（read 把 buf 填满 1，返回 n）——只加一个函数和一张表，
//    不改任何已有函数。删掉旧代码，解开 main 里的 TODO(实验) 段。
// 4. 达标时会输出 ones: read 4 bytes, first=1。
#include <cstdio>
#include <cstring>

enum device_kind { DEV_ZERO, DEV_NULL };

struct device {
    enum device_kind kind;
};

/* 每个操作都要按类型分支 */
int device_read(const struct device* d, unsigned char* buf, int n) {
    switch (d->kind) {
    case DEV_ZERO: memset(buf, 0, n); return n;   /* /dev/zero：读出全是 0 */
    case DEV_NULL: return 0;                      /* /dev/null：读不到任何字节 */
    }
    return -1;
}
const char* device_name(const struct device* d) {
    switch (d->kind) {
    case DEV_ZERO: return "zero";
    case DEV_NULL: return "null";
    }
    return "?";
}

void show(const struct device* d) {
    unsigned char buf[4] = {9, 9, 9, 9};
    int got = device_read(d, buf, 4);
    printf("%s: read %d bytes, first=%d\n", device_name(d), got, buf[0]);
}

int main(void) {
    struct device zero = {DEV_ZERO}, null = {DEV_NULL};
    show(&zero);
    show(&null);

    /* TODO(实验)：改成操作表之后，删掉上面三行与旧的 device_read、device_name，
       把 show() 改成通过 d->ops 调用，再解开下面这段
    struct device zero = {&zero_ops}, null = {&null_ops}, ones = {&ones_ops};
    show(&zero);
    show(&null);
    show(&ones);
    */
    return 0;
}
