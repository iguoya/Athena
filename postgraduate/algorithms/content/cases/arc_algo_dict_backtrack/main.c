#include <stdio.h>
#include <stdlib.h>

int main() {
    printf("1-n集合中, 取出r个数的所有组合\n");
    int n = 10, r = 3;
//    printf("输入n,r\n");
//    scanf("%d,%d", &n, &r);

    int data[n];
    int combination[r];

    int total_num  = 0;
    for(int i = 0; i<n;++i) {
        data[i] = i+1;
    }

    for(int i = 0; i <= n-r; ++i) {
        //前r-1个元素
        for(int must_use_i = 0; must_use_i < r-1; ++must_use_i) {
            combination[must_use_i] = data[i+must_use_i];
        }
        //遍历剩余一个元素
        for(int may_use_i = r-1+i; may_use_i < n; ++may_use_i) {
            combination[r-1] = data[may_use_i];
            printf("%3d: ", ++total_num);
            for(int cb_i = 0; cb_i < r; ++cb_i) {
                printf("%d\t",combination[cb_i]);
            }
            printf("\n");
        }
    }

    return 0;
}