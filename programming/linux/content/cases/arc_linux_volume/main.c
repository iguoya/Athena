#include <stdio.h>

int main() {
    printf("输入长宽高，逗号分割\n");
    int length, width, high, volumne;
    scanf("%d,%d,%d", &length, &width, &high);
    volumne = length*width*high;
    printf("体积结果：%d\n", volumne);

    int *p_number;

    printf("输入一个数字:\n");
    scanf("%d", p_number);
    printf("指针指向的数据是：%d\n", *p_number);


    return 0;
}
//
//输入长宽高，逗号分割
//2,3,5
//体积结果：30
//输入一个数字:
//666
//指针指向的数据是：666
