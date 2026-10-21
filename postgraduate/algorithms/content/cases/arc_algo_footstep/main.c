//
// Created by tiger on 18-12-7.
//
#include <stdio.h>

int step(int n) {
    static int step_queue[20];
    static int index;
    static int total_method;
    if (n < 0) {
        return -1;
    } else if (n == 0) {
        ++total_method;
        printf("%2d:", total_method);
        for(int i = 0; i < index; ++i) {
            printf("-%d-", step_queue[i]);
        }
        printf("\n");
        return 0;
    } else {
//        printf("\n当前剩余阶梯:%d\n", n);
        for (int i = 1; i < 4; ++i) {
            step_queue[index] = i;
            ++index;
            step(n-i);
            --index;
        }
    }
}

int main() {
    step(4);
    step(10);
}
