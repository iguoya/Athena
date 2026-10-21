//
// Created by tiger on 18-11-12.
//
#include <stdio.h>

void move(int n, char a, char b) {
    printf("\t将编号%d圆盘从%c移动到%c\n", n, a, b);
}

void hanoi(int n, char a, char b, char c) {
    if(n) {
        printf("前期计划：准备将编号%d（含）以上的盘从%c通过%c移动到%c\n", n, a, c, b);
        hanoi(n-1, a, c, b);
        printf("前期计划完成：将编号%d（含）以上的盘从%c通过%c移动到%c\n", n, a, c, b);
        move(n, a, c);
        printf("后期计划：准备将编号%d（含）以上的盘从%c通过%c移动到%c\n", n, b, a, c);
        hanoi(n-1, b, a, c);
        printf("后期计划完成：将编号%d（含）以上的盘从%c通过%c移动到%c\n", n, b, a, c);
    }
    printf("-----------------\n移动%d（含）编号以上盘子整体结束\n-------------------\n", n);
}

int main() {
    hanoi(5, 'A', 'B', 'C');
}