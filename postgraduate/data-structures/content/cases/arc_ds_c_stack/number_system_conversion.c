#include <stdio.h>
#include <string.h>


typedef  int StackElemType;
#include "stack.h"


char* number_system_conversion(int n, int d) {
    //n除以数制  结果作为下次 运算 的开始 ，余数作为结果，依次入栈
    char *result = malloc(sizeof(char)*1000);
    LinkStack top = init_stack();
    while(n != 0) {
        push(top, n % d);
        printf("%d--%p\n", (*top)->value, (*top)->next);
        n = n / d;
    }

    int i = 0;
    int num = -1;
    while(get_top(top, &num)) {
        if(num >= 0 && num <= 9) {
            num += 48;
        } else {// 10 --- 16
            num += 55;
        }
        result[i] = (char)num;
        pop(top);
        ++i;
    }
    return result;
}

int main() {
    printf("输入待转换整数及数制，逗号分隔:（进制设为0则终止）\n");
    int number , decimal;
    while(true) {
        scanf("%d,%d", &number, &decimal);
        if(decimal == 0) {
            break;
        }
        printf("%s\n", number_system_conversion(number, decimal));
    }

//    traverse(top);
    return 0;
}