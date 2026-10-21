#include <stdio.h>
#include <unistd.h>
#include <stdio.h>

#include <time.h>
#include <stdlib.h>
#include <string.h>
int ff(int(*p)(int, int), int a, int b)//原始写法,阅读不便
{
    return p(a, b);
}

typedef int(*Pfun)(int, int);//定义函数指针类型，同时申明了原型 返回int 两个int形参
int f(Pfun p, int a, int b) //改进写法 易懂
{
    return p(a, b);
}

int add(int a, int b) {
    printf("加法函数add被调用:");
    return a + b;
}

int sub(int a, int b) {
    printf("减法函数sub被调用:");
    return a - b;
}

typedef struct line {
    int len;
    char *contents;
} line;


int main() {
    int a = 1, b = 2;
    printf(" %d+%d=%d\n", a, b, f(add, a, b));
    printf(" %d-%d=%d\n", a, b, f(sub, a, b));
    printf(" %d+%d=%d\n", a, b, ff(add, a, b));
    printf(" %d-%d=%d\n", a, b, ff(sub, a, b));

    srand(time(NULL));
    for (int i = 1; i <= 100; ++i) {
        int num_max = 5;
        int num_min = 1;
        printf("%5d\t", rand() % (num_max - num_min + 1) + num_min);
        if (i % 10 == 0) {
            printf("\n");
        }
    }


    char str[] = "hello world";

    struct line *ptr = (struct line *) malloc(sizeof(line) + strlen(str) + 1);

    ptr->len = strlen(str);
    strcpy((char *) (ptr + 1), str);

   printf("start: %p\n\n", (char*)ptr);

   printf("(char*)(ptr+1)address: %p\n", (char*)(ptr+1));
   printf("(char*)(ptr+1): %s\n\n", (char*)(ptr+1));

   printf("&(ptr->contents): %p\n", &(ptr->contents));
   printf("ptr->contents: %s\n\n", ptr->contents);

   printf("sizeof(int): %d\n", sizeof(int));
   printf("sizeof(line): %d\n", sizeof(line));


    return 0;
}