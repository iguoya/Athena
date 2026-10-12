// 情境：C 没有 private。Stack 的结构体定义放在「头文件」里，调用方就能绕过函数直接改
// top——栈的不变式（0 <= top <= 容量）被一行赋值破坏。
// 组织手段：不透明类型——头文件里只声明 struct Stack 而不给出定义，调用方只能拿到指针、
// 只能通过函数操作；结构体的定义藏在实现文件里。
// 依据：SEI CERT C 编码规范 DCL12-C「用不透明类型实现抽象数据类型」；
// Linux 内核编码规范第 5 节：typedef 只用于「完全不透明的对象」。
//
// 本文件用分隔注释模拟三个文件：stack.h（公开）、main.c（调用方）、stack.c（实现）。
// 代码按 C 的写法写，用本应用的 C++ 编译器编译（所以 malloc 的结果要显式转换类型）。
//
// 实验：
// 1. 把 struct Stack 的完整定义从「stack.h」挪到「stack.c」，stack.h 只留 typedef struct Stack Stack;
//    与函数声明；新增 Stack* stack_create(void) 与 void stack_destroy(Stack*)（用 malloc/free）。
// 2. 调用方只能通过函数操作。删掉 main 里的旧代码，解开 TODO(实验) 段。
//    此时如果再写 s->top = 99，编译器会报错——这就是不透明类型的保护。
// 3. 达标时会输出 size=2、pop=20 与 pop on empty rejected。
#include <cstdio>
#include <cstdlib>

/* ======== stack.h（公开给调用方） ======== */
#define STACK_CAP 8
struct Stack {          // TODO(实验)：把定义挪到 stack.c，这里只留 typedef struct Stack Stack;
    int items[STACK_CAP];
    int top;
};
typedef struct Stack Stack;
int stack_push(Stack* s, int v);          /* 成功返回 0，满了返回 -1 */
int stack_pop(Stack* s, int* out);        /* 成功返回 0，空了返回 -1 */
int stack_size(const Stack* s);

/* ======== main.c（调用方） ======== */
int main(void) {
    Stack s;
    s.top = 0;
    stack_push(&s, 10);
    s.top = 99;                            /* 绕过函数直接改，编译器不拦 */
    printf("size=%d\n", stack_size(&s));

    /* TODO(实验)：改成不透明类型后，删掉上面五行，解开下面这段
    Stack* p = stack_create();
    stack_push(p, 10);
    stack_push(p, 20);
    printf("size=%d\n", stack_size(p));
    int v = 0;
    stack_pop(p, &v);
    printf("pop=%d\n", v);
    stack_pop(p, &v);
    if (stack_pop(p, &v) != 0) printf("pop on empty rejected\n");
    stack_destroy(p);
    */
    return 0;
}

/* ======== stack.c（实现） ======== */
int stack_push(Stack* s, int v) {
    if (s->top >= STACK_CAP) return -1;
    s->items[s->top++] = v;
    return 0;
}
int stack_pop(Stack* s, int* out) {
    if (s->top <= 0) return -1;
    *out = s->items[--s->top];
    return 0;
}
int stack_size(const Stack* s) { return s->top; }
